import json
import redis.asyncio as aioredis
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import AuctionItem, Bid

@database_sync_to_async
def get_auction_info(item_id):
    try:
        item = AuctionItem.objects.get(pk=item_id)
        current = float(item.current_bid) if item.current_bid is not None else float(item.start_price)
        return {
            'is_active': item.is_active,
            'current_bid': current,
            'start_price': float(item.start_price)
        }
    except AuctionItem.DoesNotExist:
        return None

@database_sync_to_async
def record_bid(user, item_id, amount):
    item = AuctionItem.objects.get(pk=item_id)
    new_bid = Bid.objects.create(user=user, item=item, amount=amount)
    item.current_bid = amount
    item.save(update_fields=['current_bid'])
    return new_bid

class AuctionConsumer(AsyncWebsocketConsumer):
    LUA_ATOMIC_BID = """
    local current = redis.call('GET', KEYS[1])
    local new_val = tonumber(ARGV[1])

    if not current then
        redis.call('SET', KEYS[1], ARGV[1])
        return 1
    end

    if new_val > tonumber(current) then
        redis.call('SET', KEYS[1], ARGV[1])
        return 1
    else
        return 0
    end
    """

    async def connect(self):
        self.item_id = self.scope['url_route']['kwargs']['item_id']
        self.group_name = f'auction_{self.item_id}'
        self.redis_bid_key = f'auction:{self.item_id}:highest_bid'
        self.redis = aioredis.from_url("redis://localhost:6379/0")

        # Verify item exists and seed initial baseline price in Redis if not set
        item_info = await get_auction_info(self.item_id)
        if item_info is None or not item_info['is_active']:
            await self.close()
            return

        cached_bid = await self.redis.get(self.redis_bid_key)
        if cached_bid is None:
            await self.redis.set(self.redis_bid_key, str(item_info['current_bid']))

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'redis'):
            await self.redis.aclose()
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Authentication required to place a bid.'
            }))
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format.'
            }))
            return

        if data.get('type') == 'bid':
            try:
                amount = float(data.get('amount', 0))
            except (ValueError, TypeError):
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Invalid bid amount.'
                }))
                return

            item_info = await get_auction_info(self.item_id)
            if not item_info or not item_info['is_active']:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'This auction has ended or is inactive.'
                }))
                return

            # Atomically evaluate bid against Redis in-memory highest bid
            is_highest = await self.redis.eval(
                self.LUA_ATOMIC_BID,
                1,
                self.redis_bid_key,
                str(amount)
            )

            if is_highest == 1:
                # Save approved bid to PostgreSQL
                await record_bid(user, self.item_id, amount)

                # Broadcast live update to all connected clients in the room
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'bid_update',
                        'user': user.username,
                        'item_id': self.item_id,
                        'amount': str(amount),
                    }
                )
            else:
                current_val = await self.redis.get(self.redis_bid_key)
                if isinstance(current_val, bytes):
                    current_val = current_val.decode('utf-8')
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Bid too low. Highest bid is currently {current_val}.'
                }))

    async def bid_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'bid_update',
            'user': event['user'],
            'item_id': event['item_id'],
            'amount': event['amount'],
        }))

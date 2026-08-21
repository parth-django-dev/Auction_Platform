from celery import shared_task
from django.db import transaction
from .models import AuctionItem, Bid
from django.utils import timezone

@shared_task
def finalize_auction(item_id):
    try:
        with transaction.atomic():
            item = AuctionItem.objects.select_for_update().get(id=item_id)
            if item.is_active and item.end_time < timezone.now():
                bids = Bid.objects.filter(item=item).order_by('-amount')
                if bids.exists():
                    item.current_bid = bids[0].amount
                    item.winner = bids[0].user
                item.is_active = False
                item.save()
    except AuctionItem.DoesNotExist:
        print(f"Auction with ID {item_id} does not exist.")
    except Exception as e:
        print(f"Error finalizing auction: {e}")
import json
from django.shortcuts import render, get_object_or_404
import json
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from .models import AuctionItem, Bid

# Create your views here.

# Resource Retrieval views
def active_auctions(request):
    # List of all bidding that are currently active
    current_active = AuctionItem.objects.filter(is_active=True)
    
    AuctionList = []
    for item in current_active:
        AuctionList.append({
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'start_time': item.start_time,
            'end_time': item.end_time,
            'start_price': item.start_price,
            'current_bid': item.current_bid,
            'is_active': item.is_active
        })
    
    return JsonResponse({'AuctionList': AuctionList})

def auction_details(request, id):
    item = get_object_or_404(AuctionItem, pk=id)
    
    # All the bids on the item yet.
    item_bids = Bid.objects.filter(item=item).order_by('-bid_time')
    bids_List = []
    for bid in item_bids:
        bids_List.append({
            'id': bid.id,
            'user': bid.user.username,
            'amount': bid.amount,
            'bid_time': bid.bid_time
        })

    if item.is_active:
        winner = None
    else:
        winner = item.winner.username if item.winner is not None else None

    if item.current_bid is not None:
        current_price = item.current_bid + 100
    else:
        current_price = item.start_price
    
    return JsonResponse({
        'title': item.title,
        'description': item.description,
        'start_time': item.start_time,
        'end_time': item.end_time,
        'start_price': item.start_price,
        'current_price': current_price,
        'is_active': item.is_active,
        'winner': winner,
        'bids_List': bids_List
    })

# Authentication and Session management views.
def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})

def register_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    if not username or not email or not password:
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Username already taken'}, status=400)

    User.objects.create_user(username=username, email=email, password=password)
    return JsonResponse({'message': 'User registered successfully'}, status=201)

def login_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({'message': 'Login successful'})
    else:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

def logout_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    logout(request)
    return JsonResponse({'message': 'Logged out successfully'})
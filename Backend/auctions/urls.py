from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('active-auctions/', views.active_auctions, name='active_auctions'),
    path('auction/<int:id>/', views.auction_details, name='auction_details'),
    path('register/', views.register_user, name='register_user'),
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path('user/', views.get_current_user, name='get_current_user'),
    path('csrf-token/', views.get_csrf_token, name='get_csrf_token'),
    path('my-bids/', views.my_bids, name='my_bids'),
    path('my-listings/', views.my_listings, name='my_listings'),
    path('create-auction/', views.create_auction, name='create_auction'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.contrib import admin
from .models import AuctionItem, Bid

class BidInline(admin.TabularInline):
    model = Bid
    extra = 0
    readonly_fields = ('bid_time', 'amount')

@admin.register(AuctionItem)
class AuctionItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'current_bid', 'start_price', 'is_active', 'end_time')
    list_filter = ('is_active', 'end_time')
    search_fields = ('title',)
    inlines = [BidInline]

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'amount', 'bid_time')
    list_filter = ('bid_time',)
    search_fields = ('user__username', 'item__title')


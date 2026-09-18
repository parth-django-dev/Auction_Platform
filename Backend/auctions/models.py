from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class AuctionItem(models.Model):
    id= models.AutoField(primary_key=True)
    seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='listed_items')
    title =models.CharField(max_length=50)
    description = models.TextField()
    image = models.ImageField(upload_to="auction_images/", blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    start_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_bid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            try:
                from .tasks import finalize_auction
                finalize_auction.apply_async(args=[self.id], eta=self.end_time)
            except Exception as e:
                pass

    
from django.core.exceptions import ValidationError

class Bid(models.Model):
    id = models.AutoField(primary_key=True)
    item = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='bids')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bid_time = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if hasattr(self, 'item') and self.item:
            from django.utils import timezone
            if self.item.seller and self.user == self.item.seller:
                raise ValidationError("You cannot bid on an item you are selling.")
            if not self.item.is_active or self.item.end_time <= timezone.now():
                raise ValidationError("This auction has ended or is inactive.")
            highest_bid_obj = Bid.objects.filter(item=self.item).order_by('-amount').first()
            if highest_bid_obj and highest_bid_obj.user == self.user:
                raise ValidationError(f"You ({self.user.username}) are already the highest bidder on this item.")
            highest = self.item.current_bid if self.item.current_bid is not None else self.item.start_price
            if self.amount <= highest:
                raise ValidationError(f"Bid amount (₹{self.amount}) must be strictly higher than the current highest bid (₹{highest}).")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        if self.item.current_bid is None or self.amount > self.item.current_bid:
            self.item.current_bid = self.amount
            self.item.save(update_fields=['current_bid'])

    def __str__(self):
        return f"{self.user} bid {self.amount} on {self.item}"
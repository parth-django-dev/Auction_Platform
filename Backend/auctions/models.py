from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class AuctionItem(models.Model):
    id= models.AutoField(primary_key=True)
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
            from .tasks import finalize_auction
            finalize_auction.apply_async(args=[self.id], eta=self.end_time)

    
class Bid(models.Model):
    id = models.AutoField(primary_key=True)
    item = models.ForeignKey(AuctionItem, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bid_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} bid {self.amount} on {self.item}"
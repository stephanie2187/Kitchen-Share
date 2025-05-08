from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.contrib.auth.models import User
import random
import string

class Item(models.Model):
    CONDITION_CHOICES = [
        ('brand_new', 'Brand New'),
        ('gently_used', 'Gently Used'),
        ('good', 'Good Condition'),
        ('worn', 'Worn Condition'),
    ]

    CATEGORY_CHOICES = [
        ('cookware', 'Cookware'),
        ('spices', 'Spices'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('checked in', 'Checked In'),
        ('in circulation', 'In Circulation'),
        ('being repaired', 'Being Repaired'),
        ('lost', 'Lost'),
    ]

    photo = models.ImageField(upload_to='item_photos/', blank=True, null=True)
    title = models.CharField(max_length=70)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="other")
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_items")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Checked In')
    location = models.CharField(max_length=50, default='Charlottesville, VA')
    primary_identifier = models.CharField(max_length=200, unique=True)
    published_date = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.primary_identifier:
            self.primary_identifier = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        super(Item, self).save(*args, **kwargs)

    def average_rating(self):
        ratings = self.ratings.all()
        if ratings:
            return sum([rating.rating for rating in ratings]) / len(ratings)
        return 0

    def __str__(self):
        return self.title

class Rating(models.Model):
    item = models.ForeignKey(Item, related_name='ratings', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # Ratings from 1 to 5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating by {self.user.username} for {self.item.title}"

class Comment(models.Model):
    item = models.ForeignKey(Item, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.item.title}"

class BorrowRequest(models.Model):
    patron = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("denied", "Denied"),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending"
    )
    request_date = models.DateTimeField(auto_now_add=True)
    librarian = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_borrows")
    due_date = models.DateField(null=True, blank=True)
    returned = models.BooleanField(default=False)
    returned_at = models.DateTimeField(null=True, blank=True)
    is_seen_by_patron = models.BooleanField(default=False)
    is_seen_by_librarian = models.BooleanField(default=False)

    def was_late_return(self):
        return self.returned and self.returned_at and self.due_date and self.returned_at.date() > self.due_date

    def __str__(self):
        return f"{self.patron.username} requested {self.item.title} ({self.status})"

class Collection(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collections_created'
    )
    # default is public
    is_private = models.BooleanField(default=False)
    # items can belong to multiple collections
    items = models.ManyToManyField(Item, related_name='collections', blank=True)
    allowed_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='private_collections'
    )

    def __str__(self):
        return self.title
    

class CollectionAccessRequest(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied')
    ], default='pending')
    request_date = models.DateTimeField(auto_now_add=True)
    is_seen_by_patron = models.BooleanField(default=False)
    is_seen_by_librarian = models.BooleanField(default=False)

    class Meta:
        unique_together = ('collection', 'user')

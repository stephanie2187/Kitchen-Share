from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('Patron', 'Patron'),
        ('Librarian', 'Librarian'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class PatronRating(models.Model):
    patron = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_ratings")
    librarian = models.ForeignKey(User, on_delete=models.CASCADE, related_name="given_ratings")
    rating = models.IntegerField()  # e.g. 1 to 5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.librarian} rated {self.patron} - {self.rating}/5"
    
    class Meta:
        unique_together = ('librarian', 'patron')

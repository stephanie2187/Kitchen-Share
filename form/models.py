from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

STATUS_CHOICES = [
    ('Unreviewed', 'Unreviewed'),
    ('Reviewed', 'Reviewed'),
    ('In Progress', 'In Progress'),
    ('Accepted', 'Accepted'),
    ('Denied', 'Denied'),
]

ISSUE_TYPE_CHOICES = [
    ('damaged_item', 'Damaged Item'),
    ('lost_item', 'Lost or Missing Item'),
    ('website_issue', 'Website Technical Issue'),
    ('equipment_malfunction', 'Equipment Malfunction'),
    ('cleanliness', 'Cleanliness Issue'),
    ('inventory_error', 'Inventory Discrepancy'),
    ('reservation_problem', 'Reservation Problem'),
    ('staff_assistance', 'Staff Assistance Needed'),
    ('other', 'Other Issue')
]

class ItemRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    quantity = models.IntegerField()
    urgency = models.CharField(
        max_length=10,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]
    )
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Unreviewed'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    librarian = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_requests")
    due_date = models.DateField(null=True, blank=True)
    returned = models.BooleanField(default=False)
    returned_at = models.DateTimeField(null=True, blank=True)
    is_seen_by_patron = models.BooleanField(default=False)
    is_seen_by_librarian = models.BooleanField(default=False)

    def was_late_return(self):
        return self.returned and self.returned_at and self.due_date and self.returned_at.date() > self.due_date

    def __str__(self):
        return f"{self.item_name} - {self.status}"


class IssueReport(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    issue_type = models.CharField(
        max_length=30,
        choices=ISSUE_TYPE_CHOICES
    )
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Unreviewed'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.status}"

from .models import Item
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver


@receiver(pre_delete, sender=Item)
def delete_item_photo(sender, instance, **kwargs):
    if instance.photo:
        instance.photo.delete(False)

        
@receiver(pre_save, sender=Item)
def auto_delete_old_item_photo(sender, instance, **kwargs):
    if not instance.pk:
        return  # new instance
    try:
        old_file = Item.objects.get(pk=instance.pk).photo
    except Item.DoesNotExist:
        return
    new_file = instance.photo
    if old_file and old_file != new_file:
        old_file.delete(False)
from django import forms
from .models import Item, Collection

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'description', 'category', 'condition', 'location', 'photo']



class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['title', 'description', 'is_private', 'allowed_users', 'items']
        widgets = {
            'allowed_users': forms.CheckboxSelectMultiple,
            'items': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        role = kwargs.pop('role', "Patron")
        super().__init__(*args, **kwargs)

        if role == "Patron":
            #print("DETELED")
            self.fields.pop('is_private')
            self.fields.pop('allowed_users')
        else:
            self.fields['allowed_users'].label_from_instance = lambda obj: obj.username

        private_collections = Collection.objects.filter(is_private=True)
        item_to_private_collections = {}

        for collection in private_collections:
            for item in collection.items.all():
                item_to_private_collections.setdefault(item.id, set()).add(collection.id)

        locked_item_ids = set()

        for item_id, collection_ids in item_to_private_collections.items():
            if not self.instance or self.instance.id not in collection_ids:
                locked_item_ids.add(item_id)

        self.fields['items'].queryset = Item.objects.exclude(id__in=locked_item_ids).distinct()
    
    def save(self, commit=True):
        collection = super().save(commit=False)
        selected_items = self.cleaned_data.get('items', [])

        if commit:
            collection.save()
            self.save_m2m()

            if collection.is_private:
                for item in selected_items:
                    item.collections.clear()
                    collection.items.add(item)


        return collection
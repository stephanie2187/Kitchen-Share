from django import forms
from .models import Message
from django.contrib.auth.models import User

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'content']

    def __init__(self, *args, **kwargs):
        sender = kwargs.pop('sender', None)
        super().__init__(*args, **kwargs)

        if sender:
            if sender.groups.filter(name="Librarian").exists():
                self.fields['receiver'].queryset = User.objects.filter(groups__name='Patron')
                print("IN LIBRARIAN")
            elif sender.groups.filter(name="Patron").exists():
                print("IN PATRON")
                self.fields['receiver'].queryset = User.objects.filter(groups__name='Librarian')
            else:
                print("NO ROLE FOR MESSAGING")
                self.fields['receiver'].queryset = User.objects.none()
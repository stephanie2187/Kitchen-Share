from django import forms
from .models import ItemRequest, IssueReport
from inventory.models import BorrowRequest
from datetime import date

class ItemRequestForm(forms.ModelForm):
    class Meta:
        model = ItemRequest
        fields = ['item_name', 'quantity', 'urgency', 'description']

class BorrowRequestForm(forms.ModelForm):
    class Meta:
        model = BorrowRequest
        fields = []  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['readonly'] = 'readonly'

class ReportIssueForm(forms.ModelForm):
    class Meta:
        model = IssueReport
        fields = ['title', 'issue_type', 'description']

# New librarian forms that include the status field
class LibrarianItemRequestForm(forms.ModelForm):
    user_display = forms.CharField(label="User", required=False, disabled=True)  
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Due Date (for approved items)"
    )

    class Meta:
        model = ItemRequest
        fields = ['item_name', 'user_display', 'quantity', 'urgency', 'description', 'status', 'due_date']
        widgets = {
            'item_name': forms.TextInput(attrs={'readonly': 'readonly'}),
            'quantity': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'description': forms.Textarea(attrs={'readonly': 'readonly'}),
            'urgency': forms.Select(attrs={'readonly': 'readonly'}),  # Make urgency readonly
        }
        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.user:
            self.fields['user_display'].initial = self.instance.user.get_full_name() or self.instance.user.username

        for field_name, field in self.fields.items():
            if field_name not in ['status', 'due_date']: 
                field.widget.attrs['readonly'] = True

        self.fields['urgency'].required = False 
        self.fields['due_date'].widget.attrs['min'] = date.today().strftime('%Y-%m-%d')

    def clean_urgency(self):
        return self.cleaned_data.get('urgency', self.instance.urgency)

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        due_date = cleaned_data.get('due_date')

        if status == "Accepted" and not due_date:
            self.add_error('due_date', 'Due date is required when status is Accepted.')
        elif status != "Accepted":
            cleaned_data["due_date"] = None

        return cleaned_data
    
   

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.instance and self.instance.urgency:
            instance.urgency = self.cleaned_data.get('urgency', self.instance.urgency)

        if commit:
            instance.save()
        return instance



class LibrarianReportIssueForm(forms.ModelForm):
    class Meta:
        model = IssueReport
        fields = ['title', 'issue_type', 'description', 'status']




class LibrarianBorrowRequestForm(forms.ModelForm):
    patron_username = forms.CharField(
        label="Patron", required=False, disabled=True
    )

    item_name = forms.CharField(
        label="Item", required=False, disabled=True
    )

    request_date = forms.DateTimeField(
        label="Request Date", required=False, disabled=True
    )

    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Due Date (required if approved)"
    )

    class Meta:
        model = BorrowRequest
        fields = ['status', 'due_date']  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.patron:
            self.fields['patron_username'].initial = self.instance.patron.username
        if self.instance and self.instance.item:
            self.fields['item_name'].initial = self.instance.item.title
        if self.instance and self.instance.request_date:
            self.fields['request_date'].initial = self.instance.request_date

        for field_name in self.fields:
            if field_name not in ['status', 'due_date']:
                self.fields[field_name].widget.attrs['readonly'] = True

        self.fields['due_date'].widget.attrs['min'] = date.today().strftime('%Y-%m-%d')

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        due_date = cleaned_data.get("due_date")

        if status == "approved" and not due_date:
            self.add_error('due_date', "You must set a due date when approving this request.")
        elif status != "approved":
            cleaned_data["due_date"] = None

        return cleaned_data

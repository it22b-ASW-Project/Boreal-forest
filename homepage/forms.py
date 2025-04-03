from django import forms

from .models import Priority, Type, Severity, Status
from allauth.socialaccount.models import SocialAccount

class EditParamsForm(forms.Form):
    priority = forms.ModelChoiceField(
        queryset=Priority.objects.all(),  # Debe ser un queryset de objetos
        required=True,
        empty_label=None
    )
    type = forms.ModelChoiceField(
        queryset=Type.objects.all(),
        required=True,
        empty_label=None
    )
    severity = forms.ModelChoiceField(
        queryset=Severity.objects.all(),
        required=True,
        empty_label=None
    )
    status = forms.ModelChoiceField(
        queryset=Status.objects.all(),
        required=True,
        empty_label=None
    )
    deadline = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['priority'].label_from_instance = lambda obj: obj.name
        self.fields['type'].label_from_instance = lambda obj: obj.name
        self.fields['severity'].label_from_instance = lambda obj: obj.name
        self.fields['status'].label_from_instance = lambda obj: obj.name

class EditAssigne(forms.Form):
    assigned = forms.ModelChoiceField(
        queryset = SocialAccount.objects.all(),  # Debe ser un queryset de objetos
        required = False,
        empty_label = '--',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned'].label_from_instance = lambda obj: obj.extra_data.get('name', None) if obj else None 
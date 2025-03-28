from django import forms

from .models import Priority, Type, Severity, Status

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizamos cómo se muestra cada opción en los selects
        self.fields['priority'].label_from_instance = lambda obj: obj.name
        self.fields['type'].label_from_instance = lambda obj: obj.name
        self.fields['severity'].label_from_instance = lambda obj: obj.name
        self.fields['status'].label_from_instance = lambda obj: obj.name

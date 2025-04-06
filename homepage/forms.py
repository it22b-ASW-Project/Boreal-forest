from django import forms

from .models import Priority, Type, Severity, Status, Comments

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

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ['comment']  
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 5, 
                'cols': 40, 
                'placeholder': 'Escribe tu comentario aquí...',  
            }),
        }

class BulkIssueForm(forms.Form):
    bulk_text = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'placeholder': 'Escribe cada issue en una línea diferente...',
            'rows': 6,
            'cols': 40,
        })
    )
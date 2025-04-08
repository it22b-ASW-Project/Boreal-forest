from django import forms
from .models import Priority, Type, Severity, Status, Comments, UserProfile


class EditParamsForm(forms.Form):
    priority = forms.ModelChoiceField(
        queryset=Priority.objects.all(),  # Debe ser un queryset de objetos
        required=True,
        empty_label=None,
        widget=forms.Select(attrs={"onchange": "this.form.submit();", "class": "form-style"})
    )
    type = forms.ModelChoiceField(
        queryset=Type.objects.all(),
        required=True,
        empty_label=None,
        widget=forms.Select(attrs={"onchange": "this.form.submit();" , "class": "form-style"})
    )
    severity = forms.ModelChoiceField(
        queryset=Severity.objects.all(),
        required=True,
        empty_label=None,
        widget=forms.Select(attrs={"onchange": "this.form.submit();" , "class": "form-style"})
    )
    status = forms.ModelChoiceField(
        queryset=Status.objects.all(),
        required=True,
        empty_label=None,
        widget=forms.Select(attrs={"onchange": "this.form.submit();"})
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
                'class': 'textarea-comment',
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
class EditBioForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Write your bio here...'
            }),
        }
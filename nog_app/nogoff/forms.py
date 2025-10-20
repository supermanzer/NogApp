from django import forms
from .models import Event, Nog

class VoteForm(forms.ModelForm):
    nogs = forms.ModelMultipleChoiceField(queryset=Nog.objects.all())
    
    class Meta:
        model = Event
        fields = ['nogs']

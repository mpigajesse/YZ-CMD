from django import forms
from .models import GoogleSheetConfig

class GoogleSheetConfigForm(forms.ModelForm):
    class Meta:
        model = GoogleSheetConfig
        fields = ['sheet_url', 'sheet_name', 'is_active']
        widgets = {
            'sheet_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'URL du Google Sheet'}),
            'sheet_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la feuille'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'sheet_url': 'URL du Google Sheet',
            'sheet_name': 'Nom de la feuille',
            'is_active': 'Actif',
        }
    
    def clean_sheet_url(self):
        url = self.cleaned_data.get('sheet_url')
        if not url.startswith('https://docs.google.com/spreadsheets/'):
            raise forms.ValidationError("L'URL doit être une URL valide de Google Sheets.")
        return url 
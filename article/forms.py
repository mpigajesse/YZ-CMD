from django import forms
from django.utils import timezone
from .models import Promotion, Article, MouvementStock
from django.db.models import Q

class FilteredSelectMultiple(forms.SelectMultiple):
    """Widget personnalisé pour améliorer la sélection multiple des articles"""
    class Media:
        css = {
            'all': ('admin/css/widgets.css',)
        }
        js = ('admin/js/jquery.init.js', 'admin/js/SelectFilter2.js')

class PromotionForm(forms.ModelForm):
    articles = forms.ModelMultipleChoiceField(
        queryset=Article.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = Promotion
        fields = [
            'nom', 
            'description', 
            'pourcentage_reduction', 
            'date_debut', 
            'date_fin', 
            'articles'
        ]
        widgets = {
            'date_debut': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'nom': "Nom de la promotion",
            'description': "Description",
            'pourcentage_reduction': "Pourcentage de remise (%)",
            'date_debut': "Date de début",
            'date_fin': "Date de fin",
            'articles': "Articles en promotion",
        }

    def __init__(self, *args, **kwargs):
        super(PromotionForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['articles'].initial = self.instance.articles.all()

    def save(self, commit=True):
        instance = super(PromotionForm, self).save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
        return instance

class AjustementStockForm(forms.Form):
    nouvelle_quantite = forms.IntegerField(
        label="Nouvelle Quantité en Stock",
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'placeholder': 'Entrez la quantité réelle'})
    )
    commentaire = forms.CharField(
        label="Raison de l'ajustement",
        required=True,
        widget=forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'rows': 3, 'placeholder': 'Ex: Inventaire, Correction d\'erreur, Produit défectueux...'})
    ) 
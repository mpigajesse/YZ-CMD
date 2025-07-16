from django import forms
from article.models import Article

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            'nom', 'reference', 'couleur', 'pointure', 'prix_unitaire', 
            'categorie', 'phase', 'description', 'image', 'actif'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'reference': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'couleur': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'pointure': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'prix_unitaire': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'categorie': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'phase': forms.Select(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'description': forms.Textarea(attrs={'class': 'w-full p-3 border rounded-lg', 'rows': 4}),
            'image': forms.ClearableFileInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'actif': forms.CheckboxInput(attrs={'class': 'h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
        }

class AjusterStockForm(forms.Form):
    TYPE_MOUVEMENT_CHOICES = [
        ('entree', 'Entrée de stock'),
        ('sortie', 'Sortie de stock'),
        ('ajustement_pos', 'Ajustement Positif (Inventaire)'),
        ('ajustement_neg', 'Ajustement Négatif (Inventaire)'),
        ('retour_client', 'Retour Client'),
    ]

    type_mouvement = forms.ChoiceField(
        choices=TYPE_MOUVEMENT_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full p-3 border rounded-lg'})
    )
    quantite = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg', 'placeholder': 'Ex: 10'})
    )
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'w-full p-3 border rounded-lg', 'rows': 3, 'placeholder': 'Ex: Inventaire mensuel'}),
        required=False
    ) 
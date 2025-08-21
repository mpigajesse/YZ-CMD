from django import forms
from article.models import Article, VarianteArticle, Categorie, Couleur, Pointure

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            'nom', 'reference', 'prix_unitaire', 'prix_achat', 'prix_actuel',
            'categorie', 'phase', 'description', 'image', 'image_url', 'actif',
            'isUpsell', 'prix_upsell_1', 'prix_upsell_2', 'prix_upsell_3', 'prix_upsell_4'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'reference': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'prix_unitaire': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg', 'step': '0.01'}),
            'prix_achat': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg', 'step': '0.01'}),
            'prix_actuel': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg', 'step': '0.01'}),
            'categorie': forms.Select(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'phase': forms.Select(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'description': forms.Textarea(attrs={'class': 'w-full p-3 border rounded-lg', 'rows': 4}),
            'image': forms.ClearableFileInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'image_url': forms.URLInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'actif': forms.CheckboxInput(attrs={'class': 'h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
            'isUpsell': forms.CheckboxInput(attrs={'class': 'h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
            'prix_upsell_1': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg', 'step': '0.01'}),
            'prix_upsell_2': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg', 'step': '0.01'}),
            'prix_upsell_3': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg', 'step': '0.01'}),
            'prix_upsell_4': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Charger les choix pour la catégorie
        self.fields['categorie'].queryset = Categorie.objects.filter(actif=True)
        self.fields['categorie'].empty_label = "Sélectionnez une catégorie"

class VarianteArticleForm(forms.ModelForm):
    """Formulaire pour créer/modifier les variantes d'articles (couleur + pointure)"""
    
    class Meta:
        model = VarianteArticle
        fields = ['couleur', 'pointure', 'qte_disponible', 'actif']
        widgets = {
            'couleur': forms.Select(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'pointure': forms.Select(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'qte_disponible': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg', 'min': '0'}),
            'actif': forms.CheckboxInput(attrs={'class': 'h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Charger les choix pour couleur et pointure
        self.fields['couleur'].queryset = Couleur.objects.filter(actif=True)
        self.fields['couleur'].empty_label = "Sélectionnez une couleur"
        self.fields['pointure'].queryset = Pointure.objects.filter(actif=True)
        self.fields['pointure'].empty_label = "Sélectionnez une pointure"

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
    variante = forms.ModelChoiceField(
        queryset=VarianteArticle.objects.none(),
        required=False,
        empty_label="Mouvement global (toutes les variantes)",
        widget=forms.Select(attrs={'class': 'w-full p-3 border rounded-lg'}),
        help_text="Sélectionnez une variante spécifique ou laissez vide pour un mouvement global"
    )
    quantite = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg', 'placeholder': 'Ex: 10'})
    )
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'w-full p-3 border rounded-lg', 'rows': 3, 'placeholder': 'Ex: Inventaire mensuel'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        article = kwargs.pop('article', None)
        super().__init__(*args, **kwargs)
        if article:
            self.fields['variante'].queryset = VarianteArticle.objects.filter(
                article=article, actif=True
            ).order_by('couleur__nom', 'pointure__pointure') 
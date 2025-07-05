from django import forms
from django.utils import timezone
from .models import Promotion, Article
from django.db.models import Q

class FilteredSelectMultiple(forms.SelectMultiple):
    """Widget personnalisé pour améliorer la sélection multiple des articles"""
    class Media:
        css = {
            'all': ('admin/css/widgets.css',)
        }
        js = ('admin/js/jquery.init.js', 'admin/js/SelectFilter2.js')

class PromotionForm(forms.ModelForm):
    # Champ de recherche pour les articles
    article_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Rechercher un article...',
            'class': 'article-search-input',
            'data-target': 'article-selection'
        }),
        label="Rechercher un article"
    )
    
    # Filtres pour les articles
    article_filter_categorie = forms.ChoiceField(
        required=False,
        choices=[('', 'Toutes catégories')],  # Sera rempli dynamiquement
        widget=forms.Select(attrs={'class': 'article-filter', 'data-filter': 'categorie'}),
        label="Filtrer par catégorie"
    )
    
    article_filter_couleur = forms.ChoiceField(
        required=False,
        choices=[('', 'Toutes couleurs')],  # Sera rempli dynamiquement
        widget=forms.Select(attrs={'class': 'article-filter', 'data-filter': 'couleur'}),
        label="Filtrer par couleur"
    )
    
    class Meta:
        model = Promotion
        fields = ['nom', 'description', 'pourcentage_reduction', 'date_debut', 'date_fin', 'articles', 'active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'pourcentage_reduction': forms.NumberInput(attrs={'min': '0', 'max': '100', 'step': '0.01'}),
            'date_debut': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'articles': forms.CheckboxSelectMultiple(attrs={'class': 'article-selection'}),
        }
        labels = {
            'date_debut': "Date de début",
            'date_fin': "Date de fin",
            'articles': "Articles en promotion"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        now = timezone.now()
        
        # Construire la requête de base pour les articles disponibles
        base_query = Q(phase='EN_COURS', actif=True)
        
        # Exclure les articles en promotion active (sauf ceux de la promotion actuelle)
        exclusion_query = Q(
            promotions__active=True,
            promotions__date_debut__lte=now,
            promotions__date_fin__gte=now
        )
        
        if self.instance.pk:
            # Ne pas exclure les articles de la promotion actuelle
            exclusion_query &= ~Q(promotions=self.instance)
        
        # Récupérer tous les articles disponibles
        articles_disponibles = Article.objects.filter(base_query).exclude(exclusion_query).distinct()
        
        # Limiter les choix d'articles
        if 'articles' in self.fields:
            self.fields['articles'].queryset = articles_disponibles
            self.fields['articles'].widget.attrs['data-selectable'] = 'true'
        
        # Conversion des dates au format ISO pour les champs datetime-local
        if self.instance.pk:
            if 'date_debut' in self.fields and self.instance.date_debut:
                self.initial['date_debut'] = self.instance.date_debut.strftime('%Y-%m-%dT%H:%M')
            if 'date_fin' in self.fields and self.instance.date_fin:
                self.initial['date_fin'] = self.instance.date_fin.strftime('%Y-%m-%dT%H:%M')
        
        # Remplir les options pour les filtres de catégorie et couleur
        categories = sorted(set(articles_disponibles.values_list('categorie', flat=True)))
        couleurs = sorted(set(articles_disponibles.values_list('couleur', flat=True)))
        
        self.fields['article_filter_categorie'].choices += [(cat, cat) for cat in categories]
        self.fields['article_filter_couleur'].choices += [(coul, coul) for coul in couleurs]
        
        # Définir les champs initiaux pour la date/heure au format ISO
        if not self.instance.pk:  # Si c'est une nouvelle promotion
            if 'date_debut' in self.fields:
                self.initial['date_debut'] = now.strftime('%Y-%m-%dT%H:%M')
            if 'date_fin' in self.fields:
                self.initial['date_fin'] = now.replace(hour=23, minute=59, second=59).strftime('%Y-%m-%dT%H:%M')
            if 'active' in self.fields:
                self.initial['active'] = True

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        pourcentage = cleaned_data.get('pourcentage_reduction')
        articles = cleaned_data.get('articles', [])

        # Validation des dates
        if date_debut and date_fin:
            if date_fin <= date_debut:
                self.add_error('date_fin', "La date de fin doit être postérieure à la date de début")

        # Validation du pourcentage
        if pourcentage is not None:
            if pourcentage <= 0:
                self.add_error('pourcentage_reduction', "Le pourcentage de réduction doit être supérieur à 0")
            elif pourcentage > 100:
                self.add_error('pourcentage_reduction', "Le pourcentage de réduction ne peut pas dépasser 100")
        
        # Validation des articles (phase EN_COURS)
        if articles:
            articles_non_valides = [a for a in articles if a.phase != 'EN_COURS']
            if articles_non_valides:
                article_names = [f"{a.nom} - {a.couleur} - {a.pointure}" for a in articles_non_valides]
                self.add_error('articles', f"Seuls les articles en phase 'En Cours' peuvent être ajoutés à une promotion. "
                                         f"Articles non valides : {', '.join(article_names)}")
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Désactive automatiquement la promo si la date de fin est dépassée
        now = timezone.now()
        if instance.date_fin < now:
            instance.active = False
        elif not instance.pk:  # Nouvelle instance
            instance.active = True
            
        if commit:
            instance.save()
            self.save_m2m()
        return instance 

class AjustementStockForm(forms.Form):
    """
    Formulaire pour ajuster le stock d'un article
    """
    nouvelle_quantite = forms.IntegerField(
        min_value=0,
        label="Nouvelle quantité",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez la nouvelle quantité',
            'min': '0'
        }),
        help_text="Quantité en stock après ajustement"
    )
    
    commentaire = forms.CharField(
        required=False,
        max_length=500,
        label="Commentaire",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Motif de l\'ajustement (optionnel)...'
        }),
        help_text="Raison de l'ajustement de stock"
    )
    
    def __init__(self, *args, **kwargs):
        self.article = kwargs.pop('article', None)
        super().__init__(*args, **kwargs)
        
        if self.article:
            self.fields['nouvelle_quantite'].initial = self.article.qte_disponible
            self.fields['nouvelle_quantite'].help_text = f"Quantité actuelle : {self.article.qte_disponible}"
    
    def clean_nouvelle_quantite(self):
        nouvelle_quantite = self.cleaned_data['nouvelle_quantite']
        
        if nouvelle_quantite < 0:
            raise forms.ValidationError("La quantité ne peut pas être négative.")
            
        return nouvelle_quantite 
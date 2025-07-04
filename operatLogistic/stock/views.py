from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from article.models import Article, MouvementStock, Categorie
from article.forms import AjustementStockForm
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, F, Case, When, IntegerField
from django.utils import timezone
from datetime import date, datetime, timedelta

@login_required
def ajuster_stock(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    if request.method == 'POST':
        form = AjustementStockForm(request.POST)
        if form.is_valid():
            nouvelle_quantite = form.cleaned_data['nouvelle_quantite']
            commentaire = form.cleaned_data['commentaire']
            
            try:
                with transaction.atomic():
                    quantite_actuelle = article.qte_disponible
                    difference = nouvelle_quantite - quantite_actuelle
                    
                    if difference == 0:
                        messages.info(request, "La quantité est identique. Aucune modification n'a été apportée.")
                        return redirect('operatLogistic:detail_article', article_id=article.id)

                    type_mouvement = 'ajustement_pos' if difference > 0 else 'ajustement_neg'
                    
                    # 1. Mettre à jour la quantité de l'article
                    article.qte_disponible = nouvelle_quantite
                    article.save()
                    
                    # 2. Créer un mouvement de stock
                    MouvementStock.objects.create(
                        article=article,
                        type_mouvement=type_mouvement,
                        quantite=abs(difference),
                        qte_apres_mouvement=nouvelle_quantite,
                        operateur=request.user.profil_operateur,
                        commentaire=commentaire
                    )
                    
                messages.success(request, f"Le stock de l'article '{article.nom}' a été mis à jour avec succès.")
            except Exception as e:
                messages.error(request, f"Une erreur est survenue lors de la mise à jour du stock : {e}")
                
            return redirect('operatLogistic:detail_article', article_id=article.id)
    else:
        form = AjustementStockForm(initial={'nouvelle_quantite': article.qte_disponible})

    context = {
        'form': form,
        'article': article,
        'page_title': f"Ajuster le Stock - {article.nom}",
        'page_subtitle': f"Modification de la quantité en stock pour l'article {article.reference}"
    }
    return render(request, 'operatLogistic/stock/ajuster_stock.html', context)

@login_required
def detail_article(request, article_id):
    """Affiche les détails d'un article."""
    article = get_object_or_404(Article, pk=article_id)
    mouvements = MouvementStock.objects.filter(article=article).order_by('-date_mouvement')[:10]
    
    context = {
        'article': article,
        'mouvements': mouvements,
        'page_title': f"Détail Article - {article.nom}",
        'page_subtitle': f"Informations complètes sur l'article {article.reference}"
    }
    return render(request, 'operatLogistic/stock/detail_article.html', context)

@login_required
def liste_articles(request):
    """Affiche la liste des articles avec filtres et statistiques."""
    
    # Calcul des statistiques globales (avant tout filtrage)
    articles_qs = Article.objects.all()
    articles_total = articles_qs.count()
    articles_actifs = articles_qs.filter(actif=True).count()
    articles_inactifs = articles_qs.filter(actif=False).count()
    articles_rupture = articles_qs.filter(qte_disponible__lte=0).count()
    
    # Articles créés aujourd'hui
    today = timezone.now().date()
    articles_crees_aujourd_hui = articles_qs.filter(date_creation__date=today).count()

    # Récupération des articles pour la liste, filtrée
    articles_list = Article.objects.all()
    
    # Filtres de recherche améliorés
    query = request.GET.get('q', '').strip()
    categorie_filter = request.GET.get('categorie', '').strip()
    statut_filter = request.GET.get('statut', '').strip()
    stock_filter = request.GET.get('stock', '').strip()
    prix_min = request.GET.get('prix_min', '').strip()
    prix_max = request.GET.get('prix_max', '').strip()
    couleur_filter = request.GET.get('couleur', '').strip()
    phase_filter = request.GET.get('phase', '').strip()
    tri = request.GET.get('tri', 'date_creation').strip()
    
    # Recherche textuelle intelligente
    if query:
        # Recherche dans plusieurs champs avec pondération
        articles_list = articles_list.filter(
            Q(nom__icontains=query) |
            Q(reference__icontains=query) |
            Q(description__icontains=query) |
            Q(categorie__icontains=query) |
            Q(couleur__icontains=query)
        )
    
    # Filtre par catégorie
    if categorie_filter:
        articles_list = articles_list.filter(categorie__icontains=categorie_filter)
    
    # Filtre par statut
    if statut_filter:
        if statut_filter == 'actif':
            articles_list = articles_list.filter(actif=True)
        elif statut_filter == 'inactif':
            articles_list = articles_list.filter(actif=False)
    
    # Filtre par niveau de stock
    if stock_filter:
        if stock_filter == 'rupture':
            articles_list = articles_list.filter(qte_disponible__lte=0)
        elif stock_filter == 'faible':
            articles_list = articles_list.filter(qte_disponible__gt=0, qte_disponible__lte=10)
        elif stock_filter == 'normal':
            articles_list = articles_list.filter(qte_disponible__gt=10, qte_disponible__lte=50)
        elif stock_filter == 'eleve':
            articles_list = articles_list.filter(qte_disponible__gt=50)
    
    # Filtre par prix
    if prix_min:
        try:
            prix_min_val = float(prix_min.replace(',', '.'))
            articles_list = articles_list.filter(prix_unitaire__gte=prix_min_val)
        except (ValueError, TypeError):
            pass
    
    if prix_max:
        try:
            prix_max_val = float(prix_max.replace(',', '.'))
            articles_list = articles_list.filter(prix_unitaire__lte=prix_max_val)
        except (ValueError, TypeError):
            pass
    
    # Filtre par couleur
    if couleur_filter:
        articles_list = articles_list.filter(couleur__icontains=couleur_filter)
    
    # Filtre par phase
    if phase_filter:
        articles_list = articles_list.filter(phase=phase_filter)
    
    # Tri des résultats
    if tri == 'nom':
        articles_list = articles_list.order_by('nom')
    elif tri == 'prix_asc':
        articles_list = articles_list.order_by('prix_unitaire')
    elif tri == 'prix_desc':
        articles_list = articles_list.order_by('-prix_unitaire')
    elif tri == 'stock_asc':
        articles_list = articles_list.order_by('qte_disponible')
    elif tri == 'stock_desc':
        articles_list = articles_list.order_by('-qte_disponible')
    elif tri == 'date_creation':
        articles_list = articles_list.order_by('-date_creation')
    elif tri == 'reference':
        articles_list = articles_list.order_by('reference')
    else:
        articles_list = articles_list.order_by('-date_creation')
    
    # Récupération des valeurs uniques pour les filtres
    categories_uniques = Article.objects.values_list('categorie', flat=True).distinct().exclude(categorie__isnull=True).exclude(categorie__exact='')
    couleurs_uniques = Article.objects.values_list('couleur', flat=True).distinct().exclude(couleur__isnull=True).exclude(couleur__exact='')
    phases_uniques = Article.objects.values_list('phase', flat=True).distinct().exclude(phase__isnull=True).exclude(phase__exact='')

    # Pagination
    paginator = Paginator(articles_list, 12) # 12 articles par page pour mieux s'adapter à la grille
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'articles': page_obj,
        'categories_uniques': categories_uniques,
        'couleurs_uniques': couleurs_uniques,
        'phases_uniques': phases_uniques,
        'articles_total': articles_total,
        'articles_actifs': articles_actifs,
        'articles_inactifs': articles_inactifs,
        'articles_rupture': articles_rupture,
        'articles_crees_aujourd_hui': articles_crees_aujourd_hui,
        'page_title': "Liste des Articles",
        'page_subtitle': "Inventaire complet et gestion du stock",
        'request': request, # Pour la pagination avec filtres
        'query': query,
        'current_filters': {
            'categorie': categorie_filter,
            'statut': statut_filter,
            'stock': stock_filter,
            'prix_min': prix_min,
            'prix_max': prix_max,
            'couleur': couleur_filter,
            'phase': phase_filter,
            'tri': tri,
        }
    }
    return render(request, 'operatLogistic/stock/liste_articles.html', context)

@login_required
def mouvements_stock(request):
    """Vue pour afficher l'historique des mouvements de stock"""
    from django.db.models import Q
    from django.core.paginator import Paginator
    
    # Récupération de tous les mouvements
    mouvements_list = MouvementStock.objects.select_related('article', 'operateur').order_by('-date_mouvement')
    
    # Filtres de recherche
    article_filter = request.GET.get('article', '').strip()
    type_filter = request.GET.get('type', '').strip()
    date_filter = request.GET.get('date_range', '').strip()
    
    # Filtre par article (nom ou référence)
    if article_filter:
        mouvements_list = mouvements_list.filter(
            Q(article__nom__icontains=article_filter) |
            Q(article__reference__icontains=article_filter)
        )
    
    # Filtre par type de mouvement
    if type_filter:
        if type_filter == 'entree':
            mouvements_list = mouvements_list.filter(type_mouvement='entree')
        elif type_filter == 'sortie':
            mouvements_list = mouvements_list.filter(type_mouvement='sortie')
        elif type_filter == 'ajustement':
            mouvements_list = mouvements_list.filter(
                type_mouvement__in=['ajustement_pos', 'ajustement_neg']
            )
    
    # Filtre par date
    if date_filter:
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_filter, '%Y-%m-%d').date()
            mouvements_list = mouvements_list.filter(date_mouvement__date=date_obj)
        except ValueError:
            pass  # Date invalide, on ignore le filtre
    
    # Pagination
    paginator = Paginator(mouvements_list, 25)  # 25 mouvements par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques rapides
    total_mouvements = mouvements_list.count()
    mouvements_aujourd_hui = MouvementStock.objects.filter(
        date_mouvement__date=timezone.now().date()
    ).count()
    
    context = {
        'mouvements': page_obj,
        'total_mouvements': total_mouvements,
        'mouvements_aujourd_hui': mouvements_aujourd_hui,
        'page_title': 'Mouvements de Stock',
        'current_filters': {
            'article': article_filter,
            'type': type_filter,
            'date_range': date_filter,
        }
    }
    return render(request, 'operatLogistic/stock/mouvements_stock.html', context)

@login_required
def alertes_stock(request):
    """Vue pour afficher les alertes de stock (rupture, seuil minimum)"""
    from django.db.models import Q, Count, Sum, Avg
    from datetime import datetime, timedelta
    
    # Paramètres de seuils (peuvent être configurés)
    SEUIL_RUPTURE = 0
    SEUIL_STOCK_FAIBLE = 10
    SEUIL_A_COMMANDER = 20
    
    # Récupération de tous les articles actifs
    articles_actifs = Article.objects.filter(actif=True)
    
    # Filtres par niveau d'alerte
    filtre_alerte = request.GET.get('filtre', 'tous')
    
    if filtre_alerte == 'rupture':
        articles_alerte = articles_actifs.filter(qte_disponible__lte=SEUIL_RUPTURE)
    elif filtre_alerte == 'faible':
        articles_alerte = articles_actifs.filter(
            qte_disponible__gt=SEUIL_RUPTURE,
            qte_disponible__lte=SEUIL_STOCK_FAIBLE
        )
    elif filtre_alerte == 'a_commander':
        articles_alerte = articles_actifs.filter(
            qte_disponible__gt=SEUIL_STOCK_FAIBLE,
            qte_disponible__lte=SEUIL_A_COMMANDER
        )
    else:
        # Tous les articles nécessitant une attention
        articles_alerte = articles_actifs.filter(qte_disponible__lte=SEUIL_A_COMMANDER)
    
    # Tri des résultats
    tri = request.GET.get('tri', 'stock_asc')
    if tri == 'stock_asc':
        articles_alerte = articles_alerte.order_by('qte_disponible')
    elif tri == 'stock_desc':
        articles_alerte = articles_alerte.order_by('-qte_disponible')
    elif tri == 'nom':
        articles_alerte = articles_alerte.order_by('nom')
    elif tri == 'reference':
        articles_alerte = articles_alerte.order_by('reference')
    elif tri == 'categorie':
        articles_alerte = articles_alerte.order_by('categorie')
    else:
        articles_alerte = articles_alerte.order_by('qte_disponible')
    
    # Statistiques détaillées
    stats = {
        'total_articles': articles_actifs.count(),
        'rupture_stock': articles_actifs.filter(qte_disponible__lte=SEUIL_RUPTURE).count(),
        'stock_faible': articles_actifs.filter(
            qte_disponible__gt=SEUIL_RUPTURE,
            qte_disponible__lte=SEUIL_STOCK_FAIBLE
        ).count(),
        'a_commander': articles_actifs.filter(
            qte_disponible__gt=SEUIL_STOCK_FAIBLE,
            qte_disponible__lte=SEUIL_A_COMMANDER
        ).count(),
        'stock_ok': articles_actifs.filter(qte_disponible__gt=SEUIL_A_COMMANDER).count(),
    }
    
    # Alertes critiques (articles les plus urgents)
    alertes_critiques = articles_actifs.filter(qte_disponible__lte=SEUIL_RUPTURE).order_by('qte_disponible')[:5]
    
    # Analyse par catégorie
    categories_alertes = articles_actifs.values('categorie').annotate(
        total=Count('id'),
        rupture=Count('id', filter=Q(qte_disponible__lte=SEUIL_RUPTURE)),
        faible=Count('id', filter=Q(qte_disponible__gt=SEUIL_RUPTURE, qte_disponible__lte=SEUIL_STOCK_FAIBLE)),
        a_commander=Count('id', filter=Q(qte_disponible__gt=SEUIL_STOCK_FAIBLE, qte_disponible__lte=SEUIL_A_COMMANDER)),
        stock_moyen=Avg('qte_disponible'),
        valeur_stock=Sum('qte_disponible')
    ).exclude(categorie__isnull=True).exclude(categorie__exact='').order_by('-rupture', '-faible')
    
    # Historique des mouvements récents pour les articles en alerte
    mouvements_recents = MouvementStock.objects.filter(
        article__in=articles_alerte,
        date_mouvement__gte=timezone.now() - timedelta(days=30)
    ).select_related('article', 'operateur').order_by('-date_mouvement')[:10]
    
    # Suggestions d'actions
    suggestions = []
    
    if stats['rupture_stock'] > 0:
        suggestions.append({
            'type': 'danger',
            'titre': 'Rupture de Stock Critique',
            'message': f'{stats["rupture_stock"]} article(s) en rupture totale nécessitent un réapprovisionnement immédiat.',
            'action': 'Contacter les fournisseurs',
            'icone': 'fas fa-exclamation-triangle'
        })
    
    if stats['stock_faible'] > 0:
        suggestions.append({
            'type': 'warning',
            'titre': 'Stock Faible',
            'message': f'{stats["stock_faible"]} article(s) ont un stock faible. Planifier les commandes.',
            'action': 'Préparer les commandes',
            'icone': 'fas fa-exclamation-circle'
        })
    
    if stats['a_commander'] > 0:
        suggestions.append({
            'type': 'info',
            'titre': 'À Commander Bientôt',
            'message': f'{stats["a_commander"]} article(s) devront être commandés prochainement.',
            'action': 'Surveiller l\'évolution',
            'icone': 'fas fa-info-circle'
        })
    
    # Pagination
    paginator = Paginator(articles_alerte, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'articles': page_obj,
        'stats': stats,
        'alertes_critiques': alertes_critiques,
        'categories_alertes': categories_alertes,
        'mouvements_recents': mouvements_recents,
        'suggestions': suggestions,
        'filtre_actuel': filtre_alerte,
        'tri_actuel': tri,
        'seuils': {
            'rupture': SEUIL_RUPTURE,
            'faible': SEUIL_STOCK_FAIBLE,
            'a_commander': SEUIL_A_COMMANDER
        },
        'page_title': 'Alertes Stock',
        'page_subtitle': 'Articles nécessitant une attention immédiate'
    }
    return render(request, 'operatLogistic/stock/alertes_stock.html', context)

@login_required
def statistiques_stock(request):
    """Vue pour afficher les statistiques de stock"""
    from django.db.models import Q, Count, Sum, Avg, F, Case, When, IntegerField
    from datetime import datetime, timedelta
    
    # Paramètres de filtrage
    periode = int(request.GET.get('periode', 30))
    categorie_filter = request.GET.get('categorie', '')
    
    # Date de début selon la période
    date_debut = timezone.now() - timedelta(days=periode)
    
    # Articles de base
    articles_qs = Article.objects.filter(actif=True)
    
    # Filtrage par catégorie si spécifié
    if categorie_filter:
        articles_qs = articles_qs.filter(categorie=categorie_filter)
    
    # === STATISTIQUES GÉNÉRALES ===
    
    # Valeur totale du stock
    valeur_stock = articles_qs.aggregate(
        valeur_totale=Sum(F('qte_disponible') * F('prix_unitaire'))
    )['valeur_totale'] or 0
    
    # Nombre total d'articles en stock
    articles_en_stock = articles_qs.filter(qte_disponible__gt=0).count()
    
    # Articles par niveau de stock
    stats_niveaux = articles_qs.aggregate(
        total_articles=Count('id'),
        rupture=Count('id', filter=Q(qte_disponible=0)),
        stock_faible=Count('id', filter=Q(qte_disponible__gt=0, qte_disponible__lte=10)),
        stock_normal=Count('id', filter=Q(qte_disponible__gt=10, qte_disponible__lte=50)),
        stock_eleve=Count('id', filter=Q(qte_disponible__gt=50))
    )
    
    # Taux de rupture
    taux_rupture = (stats_niveaux['rupture'] / stats_niveaux['total_articles'] * 100) if stats_niveaux['total_articles'] > 0 else 0
    
    # === ANALYSE PAR CATÉGORIE ===
    
    # Statistiques détaillées par catégorie
    stats_categories = articles_qs.values('categorie').annotate(
        total_articles=Count('id'),
        stock_total=Sum('qte_disponible'),
        valeur_totale=Sum(F('qte_disponible') * F('prix_unitaire')),
        prix_moyen=Avg('prix_unitaire'),
        stock_moyen=Avg('qte_disponible'),
        articles_rupture=Count('id', filter=Q(qte_disponible=0)),
        articles_faible=Count('id', filter=Q(qte_disponible__gt=0, qte_disponible__lte=10))
    ).exclude(categorie__isnull=True).exclude(categorie__exact='').order_by('-valeur_totale')
    
    # === TOP ARTICLES ===
    
    # Top 10 articles par valeur en stock
    top_articles_valeur = articles_qs.annotate(
        valeur_stock=F('qte_disponible') * F('prix_unitaire')
    ).filter(qte_disponible__gt=0).order_by('-valeur_stock')[:10]
    
    # Top 10 articles par quantité
    top_articles_quantite = articles_qs.filter(qte_disponible__gt=0).order_by('-qte_disponible')[:10]
    
    # === MOUVEMENTS DE STOCK ===
    
    # Mouvements récents pour calcul de rotation
    mouvements_periode = MouvementStock.objects.filter(
        date_mouvement__gte=date_debut,
        article__in=articles_qs
    ).select_related('article')
    
    # Calcul de la rotation du stock (approximatif)
    mouvements_sortie = mouvements_periode.filter(
        type_mouvement__in=['sortie', 'ajustement_neg']
    ).aggregate(total_sorties=Sum('quantite'))['total_sorties'] or 0
    
    rotation_stock = (mouvements_sortie / valeur_stock * 100) if valeur_stock > 0 else 0
    
    # === ÉVOLUTION TEMPORELLE ===
    
    # Données pour graphique d'évolution (par semaine sur la période)
    evolution_donnees = []
    nb_semaines = min(periode // 7, 12)  # Maximum 12 points
    
    for i in range(nb_semaines):
        date_fin = timezone.now() - timedelta(days=i*7)
        date_debut_semaine = date_fin - timedelta(days=7)
        
        # Calculer la valeur du stock à cette date (approximation)
        valeur_semaine = articles_qs.aggregate(
            valeur=Sum(F('qte_disponible') * F('prix_unitaire'))
        )['valeur'] or 0
        
        evolution_donnees.append({
            'date': date_fin.strftime('%d/%m'),
            'valeur': float(valeur_semaine)
        })
    
    evolution_donnees.reverse()  # Ordre chronologique
    
    # === ALERTES ET RECOMMANDATIONS ===
    
    alertes = []
    
    if stats_niveaux['rupture'] > 0:
        alertes.append({
            'type': 'danger',
            'titre': 'Articles en Rupture',
            'message': f'{stats_niveaux["rupture"]} article(s) en rupture de stock',
            'valeur': stats_niveaux['rupture']
        })
    
    if taux_rupture > 10:
        alertes.append({
            'type': 'warning',
            'titre': 'Taux de Rupture Élevé',
            'message': f'Taux de rupture de {taux_rupture:.1f}% (seuil recommandé: 5%)',
            'valeur': f'{taux_rupture:.1f}%'
        })
    
    if rotation_stock < 2:
        alertes.append({
            'type': 'info',
            'titre': 'Rotation Faible',
            'message': 'La rotation du stock est faible, optimisation possible',
            'valeur': f'{rotation_stock:.1f}'
        })
    
    # === DONNÉES POUR LES GRAPHIQUES ===
    
    # Données pour graphique en secteurs des catégories
    categories_chart_data = {
        'labels': [cat['categorie'] for cat in stats_categories],
        'values': [float(cat['valeur_totale'] or 0) for cat in stats_categories],
        'colors': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
    }
    
    # Données pour graphique des top articles
    top_articles_chart_data = {
        'labels': [art.nom[:20] for art in top_articles_valeur[:5]],
        'values': [float((art.qte_disponible or 0) * (art.prix_unitaire or 0)) for art in top_articles_valeur[:5]]
    }
    
    # Liste des catégories pour le dropdown
    categories_disponibles = Article.objects.filter(actif=True).values_list('categorie', flat=True).distinct().exclude(categorie__isnull=True).exclude(categorie__exact='').order_by('categorie')
    
    context = {
        'page_title': 'Statistiques Stock',
        'page_subtitle': 'Analyse de la performance et de la valeur de l\'inventaire',
        
        # Statistiques principales
        'valeur_stock': valeur_stock,
        'articles_en_stock': articles_en_stock,
        'rotation_stock': rotation_stock,
        'taux_rupture': taux_rupture,
        
        # Détails par niveau
        'stats_niveaux': stats_niveaux,
        
        # Analyses
        'stats_categories': stats_categories,
        'top_articles_valeur': top_articles_valeur,
        'top_articles_quantite': top_articles_quantite,
        
        # Données temporelles
        'evolution_donnees': evolution_donnees,
        
        # Alertes
        'alertes': alertes,
        
        # Données pour graphiques
        'categories_chart_data': categories_chart_data,
        'top_articles_chart_data': top_articles_chart_data,
        
        # Filtres
        'categories_disponibles': categories_disponibles,
        'periode_actuelle': periode,
        'categorie_actuelle': categorie_filter,
    }
    return render(request, 'operatLogistic/stock/statistiques_stock.html', context)

@login_required
def modifier_article(request, article_id):
    """Affiche un formulaire pour modifier un article existant."""
    article = get_object_or_404(Article, pk=article_id)
    
    if request.method == 'POST':
        # Récupération des données du formulaire
        article.nom = request.POST.get('nom', article.nom)
        article.reference = request.POST.get('reference', article.reference)
        article.categorie = request.POST.get('categorie', article.categorie)
        article.couleur = request.POST.get('couleur', article.couleur)
        
        # Nettoyage des champs numériques
        pointure_str = request.POST.get('pointure', '').strip()
        if pointure_str:
            article.pointure = pointure_str
        # Si vide, on ne modifie pas la valeur existante car le champ peut être obligatoire.

        prix_str = request.POST.get('prix_unitaire', '').strip().replace(',', '.')
        if prix_str:
            try:
                article.prix_unitaire = float(prix_str)
            except (ValueError, TypeError):
                messages.error(request, f"La valeur du prix '{prix_str}' est invalide. Le prix n'a pas été modifié.")
        else:
            # Le champ est vide, mais il est obligatoire (NOT NULL). On ne change rien et on prévient l'utilisateur.
            messages.warning(request, "Le champ 'Prix Unitaire' ne peut pas être vide. La valeur précédente a été conservée.")

        article.phase = request.POST.get('phase', article.phase)
        article.description = request.POST.get('description', article.description)
        article.actif = 'actif' in request.POST

        # Gestion de l'image
        if 'image' in request.FILES:
            article.image = request.FILES['image']
        
        article.save()
        messages.success(request, f"L'article '{article.nom}' a été modifié avec succès.")
        return redirect('operatLogistic:detail_article', article_id=article.id)

    context = {
        'article': article,
        'page_title': "Modifier l'Article",
        'page_subtitle': f"Mise à jour de {article.nom}"
    }
    return render(request, 'operatLogistic/stock/modifier_article.html', context)

@login_required
def creer_article(request):
    """Affiche un formulaire pour créer un nouvel article."""
    
    if request.method == 'POST':
        # Récupération des données
        nom = request.POST.get('nom')
        reference = request.POST.get('reference')
        categorie = request.POST.get('categorie')
        couleur = request.POST.get('couleur')
        pointure_str = request.POST.get('pointure', '').strip()
        phase = request.POST.get('phase')
        prix_str = request.POST.get('prix_unitaire', '').strip().replace(',', '.')
        description = request.POST.get('description')
        qte_disponible_str = request.POST.get('qte_disponible', '0').strip()
        actif = 'actif' in request.POST
        image = request.FILES.get('image')

        if not all([nom, reference, categorie, prix_str]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires (Nom, Référence, Catégorie, Prix).")
        else:
            try:
                prix_unitaire = float(prix_str)
                qte_disponible = int(qte_disponible_str) if qte_disponible_str else 0
                pointure = pointure_str if pointure_str else None

                article = Article.objects.create(
                    nom=nom,
                    reference=reference,
                    categorie=categorie,
                    couleur=couleur,
                    pointure=pointure,
                    phase=phase,
                    prix_unitaire=prix_unitaire,
                    description=description,
                    qte_disponible=qte_disponible,
                    actif=actif,
                    image=image
                )
                messages.success(request, f"L'article '{article.nom}' a été créé avec succès.")
                return redirect('operatLogistic:stock_articles')
            except (ValueError, TypeError):
                messages.error(request, "Le prix et la quantité doivent être des nombres valides.")

    context = {
        'article_phases': Article.PHASE_CHOICES,
        'page_title': "Créer un Nouvel Article",
        'page_subtitle': "Ajouter un article au catalogue"
    }
    return render(request, 'operatLogistic/stock/creer_article.html', context) 
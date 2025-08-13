from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum, Min, Max
from .models import Article, Promotion
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .forms import PromotionForm
from decimal import Decimal
import json

# Create your views here.

@login_required
def liste_articles(request):
    """Liste des articles avec recherche, filtres et pagination"""
    articles = Article.objects.filter(actif=True).order_by('nom', 'couleur', 'pointure')
    
    # Formulaire de promotion pour la modal
    form_promotion = PromotionForm()
    
    # Récupérer les paramètres de filtrage
    filtre_phase = request.GET.get('filtre_phase', 'tous')
    filtre_promotion = request.GET.get('filtre_promotion', '')
    filtre_stock = request.GET.get('filtre_stock', '')
    search = request.GET.get('search', '')
    
    # Filtrage par phase
    if filtre_phase and filtre_phase != 'tous':
        articles = articles.filter(phase=filtre_phase)
    
    # Filtrage par promotion
    now = timezone.now()
    if filtre_promotion == 'avec_promo':
        articles = articles.filter(
            promotions__active=True,
            promotions__date_debut__lte=now,
            promotions__date_fin__gte=now
        ).distinct()
    elif filtre_promotion == 'sans_promo':
        articles = articles.exclude(
            promotions__active=True,
            promotions__date_debut__lte=now,
            promotions__date_fin__gte=now
        ).distinct()
    
    # Filtrage par stock
    if filtre_stock == 'disponible':
        articles = articles.filter(qte_disponible__gt=0)
    elif filtre_stock == 'rupture':
        articles = articles.filter(qte_disponible=0)
    elif filtre_stock == 'stock_faible':
        articles = articles.filter(qte_disponible__gt=0, qte_disponible__lt=5)
    
    # Recherche unique sur plusieurs champs
    if search:
        # Essayer de convertir la recherche en nombre pour le prix
        try:
            # Si c'est un nombre, on cherche le prix exact ou dans une marge de ±10 DH
            search_price = float(search.replace(',', '.'))
            price_query = Q(prix_unitaire__gte=search_price-10) & Q(prix_unitaire__lte=search_price+10)
        except ValueError:
            price_query = Q()  # Query vide si ce n'est pas un prix

        # Vérifier si c'est une fourchette de prix (ex: 100-200)
        if '-' in search and all(part.strip().replace(',', '.').replace('.', '').isdigit() for part in search.split('-')):
            try:
                min_price, max_price = map(lambda x: float(x.strip().replace(',', '.')), search.split('-'))
                price_query = Q(prix_unitaire__gte=min_price) & Q(prix_unitaire__lte=max_price)
            except ValueError:
                pass

        articles = articles.filter(
            Q(reference__icontains=search) |    # Recherche par référence
            Q(nom__icontains=search) |          # Recherche par nom
            Q(couleur__icontains=search) |      # Recherche par couleur
            Q(pointure__icontains=search) |     # Recherche par pointure
            Q(categorie__icontains=search) |    # Recherche par catégorie
            price_query                         # Recherche par prix
        ).distinct()
    
    # Gestion de la pagination flexible
    items_per_page = request.GET.get('items_per_page', 12)
    start_range = request.GET.get('start_range', '')
    end_range = request.GET.get('end_range', '')
    
    # Conserver une copie des articles non paginés pour les statistiques
    articles_non_pagines = articles
    
    # Gestion de la plage personnalisée
    if start_range and end_range:
        try:
            start_idx = int(start_range) - 1  # Index commence à 0
            end_idx = int(end_range)
            if start_idx >= 0 and end_idx > start_idx:
                articles = list(articles)[start_idx:end_idx]
                # Créer un paginator factice pour la plage
                paginator = Paginator(articles, len(articles))
                page_obj = paginator.get_page(1)
        except (ValueError, TypeError):
            # En cas d'erreur, utiliser la pagination normale
            items_per_page = 12
            paginator = Paginator(articles, items_per_page)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
    else:
        # Pagination normale
        page_number = request.GET.get('page', 1)
        if items_per_page == 'all':
            # Afficher tous les articles
            paginator = Paginator(articles, articles.count())
            page_obj = paginator.get_page(1)
        else:
            try:
                items_per_page = int(items_per_page)
                if items_per_page <= 0:
                    items_per_page = 12
            except (ValueError, TypeError):
                items_per_page = 12
            
            paginator = Paginator(articles, items_per_page)
            page_obj = paginator.get_page(page_number)
    
    # Statistiques mises à jour selon les filtres appliqués
    all_articles = Article.objects.filter(actif=True)
    stats = {
        'total_articles': all_articles.count(),
        'articles_disponibles': all_articles.filter(qte_disponible__gt=0).count(),
        'articles_en_cours': all_articles.filter(phase='EN_COURS').count(),
        'articles_liquidation': all_articles.filter(phase='LIQUIDATION').count(),
        'articles_test': all_articles.filter(phase='EN_TEST').count(),
        'articles_promotion': all_articles.filter(
            promotions__active=True,
            promotions__date_debut__lte=now,
            promotions__date_fin__gte=now
        ).distinct().count(),
        'articles_rupture': all_articles.filter(qte_disponible=0).count(),
        'articles_stock_faible': all_articles.filter(qte_disponible__gt=0, qte_disponible__lt=5).count(),
    }
    
    # Vérifier si c'est une requête AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        
        # Rendre les templates partiels pour AJAX
        html_cards_body = render_to_string('article/partials/_articles_cards_body.html', {
            'page_obj': page_obj
        }, request=request)
        
        html_table_body = render_to_string('article/partials/_articles_table_body.html', {
            'page_obj': page_obj
        }, request=request)
        
        html_pagination = render_to_string('article/partials/_articles_pagination.html', {
            'page_obj': page_obj,
            'search': search,
            'filtre_phase': filtre_phase,
            'filtre_promotion': filtre_promotion,
            'filtre_stock': filtre_stock,
            'items_per_page': items_per_page,
            'start_range': start_range,
            'end_range': end_range
        }, request=request)
        
        html_pagination_info = render_to_string('article/partials/_articles_pagination_info.html', {
            'page_obj': page_obj
        }, request=request)
        
        return JsonResponse({
            'success': True,
            'html_cards_body': html_cards_body,
            'html_table_body': html_table_body,
            'html_pagination': html_pagination,
            'html_pagination_info': html_pagination_info,
            'total_count': articles_non_pagines.count()
        })

    context = {
        'page_obj': page_obj,
        'search': search,
        'stats': stats,
        'form_promotion': form_promotion,
        'filtre_phase': filtre_phase,
        'filtre_promotion': filtre_promotion,
        'filtre_stock': filtre_stock,
        'items_per_page': items_per_page,
        'start_range': start_range,
        'end_range': end_range,
    }
    return render(request, 'article/liste.html', context)

@login_required
def detail_article(request, id):
    """Détail d'un article"""
    article = get_object_or_404(Article, id=id, actif=True)
    
    # Articles similaires (même catégorie, couleur différente)
    articles_similaires = Article.objects.filter(
        categorie=article.categorie,
        actif=True
    ).exclude(id=article.id).order_by('nom', 'couleur')[:6]
    
    # Récupérer l'URL de la page précédente, avec fallback
    previous_page = request.META.get('HTTP_REFERER', reverse('article:liste'))
    
    context = {
        'article': article,
        'articles_similaires': articles_similaires,
        'previous_page': previous_page,
    }
    return render(request, 'article/detail.html', context)

@login_required
def creer_article(request):
    """Créer un nouvel article"""
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            nom = request.POST.get('nom')
            couleur = request.POST.get('couleur')
            pointure = request.POST.get('pointure')

            # Vérifier l'unicité de la combinaison nom, couleur, pointure
            if Article.objects.filter(nom=nom, couleur=couleur, pointure=pointure).exists():
                messages.error(request, "Un article avec le même nom, couleur et pointure existe déjà.")
                # Renvoyer le formulaire avec les données saisies
                return render(request, 'article/creer.html', {'form_data': request.POST})

            # Valider et convertir le prix
            prix_str = request.POST.get('prix_unitaire', '').strip().replace(',', '.')
            if not prix_str:
                messages.error(request, "Le prix unitaire est obligatoire.")
                return render(request, 'article/creer.html', {'form_data': request.POST})
            
            try:
                prix_unitaire = float(prix_str)
                if prix_unitaire <= 0:
                    messages.error(request, "Le prix unitaire doit être supérieur à 0.")
                    return render(request, 'article/creer.html', {'form_data': request.POST})
            except ValueError:
                messages.error(request, "Le prix unitaire doit être un nombre valide.")
                return render(request, 'article/creer.html', {'form_data': request.POST})

            # Valider la pointure
            pointure_str = request.POST.get('pointure', '').strip()
            if not pointure_str:
                messages.error(request, "La pointure est obligatoire.")
                return render(request, 'article/creer.html', {'form_data': request.POST})
            
            try:
                pointure = int(pointure_str)
                if pointure < 30:
                    messages.error(request, "La pointure ne peut pas être inférieure à 30.")
                    return render(request, 'article/creer.html', {'form_data': request.POST})
            except ValueError:
                messages.error(request, "La pointure doit être un nombre entier valide.")
                return render(request, 'article/creer.html', {'form_data': request.POST})

            # Valider la quantité
            qte_str = request.POST.get('qte_disponible', '').strip()
            if not qte_str:
                messages.error(request, "La quantité disponible est obligatoire.")
                return render(request, 'article/creer.html', {'form_data': request.POST})
            
            try:
                qte_disponible = int(qte_str)
                if qte_disponible < 0:
                    messages.error(request, "La quantité disponible ne peut pas être négative.")
                    return render(request, 'article/creer.html', {'form_data': request.POST})
            except ValueError:
                messages.error(request, "La quantité disponible doit être un nombre entier valide.")
                return render(request, 'article/creer.html', {'form_data': request.POST})

            article = Article()
            article.nom = nom
            article.couleur = couleur
            article.pointure = pointure_str  # Utiliser la chaîne de caractères pour la pointure
            article.reference = request.POST.get('reference')
            article.description = request.POST.get('description')
            article.prix_unitaire = prix_unitaire
            article.prix_actuel = prix_unitaire  # Assurer que le prix actuel = prix unitaire
            article.qte_disponible = qte_disponible
            article.categorie = request.POST.get('categorie')
            
            # Gérer le prix d'achat
            prix_achat_str = request.POST.get('prix_achat', '').strip().replace(',', '.')
            if prix_achat_str:
                try:
                    prix_achat = float(prix_achat_str)
                    if prix_achat >= 0:
                        article.prix_achat = prix_achat
                except ValueError:
                    # Ignorer les valeurs non numériques
                    pass
            
            # Gérer les nouveaux champs
            article.isUpsell = request.POST.get('isUpsell') == 'on'
            article.Compteur = 0  # Initialiser le compteur à 0
            
            # Gérer l'image si elle est fournie
            if 'image' in request.FILES:
                article.image = request.FILES['image']
            
            # Gérer les prix de substitution (upsell)
            for i in range(1, 5):
                prix_upsell_str = request.POST.get(f'prix_upsell_{i}', '').strip().replace(',', '.')
                if prix_upsell_str:
                    try:
                        prix_upsell = float(prix_upsell_str)
                        if prix_upsell > 0:
                            setattr(article, f'prix_upsell_{i}', prix_upsell)
                    except ValueError:
                        # Ignorer les valeurs non numériques
                        pass
            
            article.save()
            
            messages.success(request, f"L'article '{article.nom}' a été créé avec succès.")
            return redirect('article:liste')
            
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la création de l'article : {str(e)}")
            return render(request, 'article/creer.html', {'form_data': request.POST})
    
    return render(request, 'article/creer.html')

@login_required
def modifier_article(request, id):
    """Modifier un article existant"""
    article = get_object_or_404(Article, id=id, actif=True)

    if request.method == 'POST':
        try:
            nom = request.POST.get('nom')
            couleur = request.POST.get('couleur')
            pointure = request.POST.get('pointure')

            # Vérifier l'unicité de la combinaison nom, couleur, pointure
            if Article.objects.filter(nom=nom, couleur=couleur, pointure=pointure).exclude(pk=id).exists():
                messages.error(request, "Un autre article avec le même nom, couleur et pointure existe déjà.")
                return render(request, 'article/modifier.html', {'article': article, 'form_data': request.POST})

            # Valider et convertir le prix
            prix_str = request.POST.get('prix_unitaire', '').strip().replace(',', '.')
            if not prix_str:
                messages.error(request, "Le prix unitaire est obligatoire.")
                return render(request, 'article/modifier.html', {'article': article, 'form_data': request.POST})
            
            try:
                prix_unitaire = float(prix_str)
                if prix_unitaire <= 0:
                    messages.error(request, "Le prix unitaire doit être supérieur à 0.")
                    return render(request, 'article/modifier.html', {'article': article, 'form_data': request.POST})
            except ValueError:
                messages.error(request, "Le prix unitaire doit être un nombre valide.")
                return render(request, 'article/modifier.html', {'article': article, 'form_data': request.POST})

            # Valider la quantité
            qte_str = request.POST.get('qte_disponible', '').strip()
            if not qte_str:
                messages.error(request, "La quantité disponible est obligatoire.")
                return render(request, 'article/modifier.html', {'article': article, 'form_data': request.POST})
            
            try:
                qte_disponible = int(qte_str)
                if qte_disponible < 0:
                    messages.error(request, "La quantité disponible ne peut pas être négative.")
                    return render(request, 'article/modifier.html', {'article': article, 'form_data': request.POST})
            except ValueError:
                messages.error(request, "La quantité disponible doit être un nombre entier valide.")
                return render(request, 'article/modifier.html', {'article': article, 'form_data': request.POST})

            article.nom = nom
            article.couleur = couleur
            article.pointure = pointure
            article.reference = request.POST.get('reference')
            article.description = request.POST.get('description')
            article.prix_unitaire = prix_unitaire
            article.qte_disponible = qte_disponible
            article.categorie = request.POST.get('categorie')
            
            # Gérer le prix d'achat
            prix_achat_str = request.POST.get('prix_achat', '').strip().replace(',', '.')
            if prix_achat_str:
                try:
                    prix_achat = float(prix_achat_str)
                    if prix_achat >= 0:
                        article.prix_achat = prix_achat
                except ValueError:
                    # Ignorer les valeurs non numériques
                    pass
            
            # Gérer les nouveaux champs
            article.isUpsell = request.POST.get('isUpsell') == 'on'
            # Ne pas modifier le compteur existant - il est géré par d'autres processus
            
            # Récupérer et définir la phase
            phase = request.POST.get('phase')
            # Vérifier si l'article est en promotion avant de changer sa phase
            if phase and phase in dict(Article.PHASE_CHOICES).keys():
                if article.has_promo_active:
                    messages.warning(request, f"Impossible de changer la phase de l'article car il est actuellement en promotion.")
                else:
                    # Vérifier si l'upsell était actif avant le changement
                    upsell_was_active = article.isUpsell
                    old_phase = article.phase
                    
                    article.phase = phase
                    
                    # Message avec info sur l'upsell si désactivé
                    upsell_message = ""
                    if upsell_was_active and phase in ['LIQUIDATION', 'EN_TEST'] and old_phase != phase:
                        upsell_message = " L'upsell a été automatiquement désactivé."
                    
                    if phase == 'LIQUIDATION':
                        messages.warning(request, f"L'article '{article.nom}' a été mis en liquidation.{upsell_message}")
                    elif phase == 'EN_TEST':
                        messages.info(request, f"L'article '{article.nom}' a été mis en phase de test.{upsell_message}")
                    elif phase == 'PROMO':
                        messages.success(request, f"L'article '{article.nom}' a été mis en phase promotion.{upsell_message}")
                    elif phase == 'EN_COURS':
                        messages.success(request, f"L'article '{article.nom}' a été remis en phase par défaut (En Cours).{upsell_message}")
            
            # Gérer l'image si elle est fournie
            if 'image' in request.FILES:
                article.image = request.FILES['image']
            
            # Gérer les prix de substitution (upsell)
            # Réinitialiser les prix upsell
            article.prix_upsell_1 = None
            article.prix_upsell_2 = None
            article.prix_upsell_3 = None
            article.prix_upsell_4 = None
            
            for i in range(1, 5):
                prix_upsell_str = request.POST.get(f'prix_upsell_{i}', '').strip().replace(',', '.')
                if prix_upsell_str:
                    try:
                        prix_upsell = float(prix_upsell_str)
                        if prix_upsell > 0:
                            setattr(article, f'prix_upsell_{i}', prix_upsell)
                    except ValueError:
                        # Ignorer les valeurs non numériques
                        pass
            
            # Mettre à jour le prix actuel pour qu'il soit égal au prix unitaire
            # sauf si l'article est en promotion active
            if not article.has_promo_active:
                article.prix_actuel = article.prix_unitaire
            
            article.save()
            messages.success(request, f"L'article '{article.nom}' a été modifié avec succès.")
            return redirect('article:detail', id=article.id)
            
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la modification de l'article : {str(e)}")
            return render(request, 'article/modifier.html', {'article': article, 'form_data': request.POST})
    
    context = {
        'article': article
    }
    return render(request, 'article/modifier.html', context)

@login_required
def supprimer_article(request, id):
    """Supprimer un article (méthode POST requise)"""
    article = get_object_or_404(Article, id=id)
    if request.method == 'POST':
        try:
            article.delete()
            messages.success(request, f"L'article '{article.nom}' a été supprimé avec succès.")
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la suppression de l'article : {e}")
        return redirect('article:liste')
    # Si la méthode n'est pas POST, on redirige simplement vers la liste
    return redirect('article:liste')

@require_POST
@login_required
def supprimer_articles_masse(request):
    selected_ids = request.POST.getlist('ids[]')
    if not selected_ids:
        messages.error(request, "Aucun article sélectionné pour la suppression.")
        return redirect('article:liste')

    try:
        count = Article.objects.filter(pk__in=selected_ids).delete()[0]
        messages.success(request, f"{count} article(s) supprimé(s) avec succès.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression en masse : {e}")
    
    return redirect('article:liste')

@login_required
def articles_par_categorie(request, categorie):
    """Articles filtrés par catégorie"""
    articles = Article.objects.filter(
        categorie__icontains=categorie,
        actif=True
    ).order_by('nom', 'couleur', 'pointure')
    
    # Recherche dans la catégorie
    search = request.GET.get('search')
    if search:
        articles = articles.filter(
            Q(nom__icontains=search) | 
            Q(couleur__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(articles, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categorie': categorie,
        'search': search,
        'total_articles': articles.count(),
    }
    return render(request, 'article/categorie.html', context)

@login_required
def stock_faible(request):
    """Articles avec stock faible (moins de 5 unités)"""
    articles = Article.objects.filter(
        qte_disponible__lt=5,
        qte_disponible__gt=0,
        actif=True
    ).order_by('qte_disponible', 'nom')
    
    # Pagination
    paginator = Paginator(articles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_articles': articles.count(),
    }
    return render(request, 'article/stock_faible.html', context)

@login_required
def rupture_stock(request):
    """Articles en rupture de stock"""
    articles = Article.objects.filter(
        qte_disponible=0,
        actif=True
    ).order_by('nom', 'couleur', 'pointure')
    
    # Pagination
    paginator = Paginator(articles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_articles': articles.count(),
    }
    return render(request, 'article/rupture_stock.html', context)

@login_required
def liste_promotions(request):
    """Liste des promotions avec recherche et filtres"""
    promotions = Promotion.objects.all().order_by('-date_creation')
    
    # Formulaire de promotion pour le modal
    form_promotion = PromotionForm()
    
    # Filtres
    filtre = request.GET.get('filtre', 'toutes')
    now = timezone.now()
    
    if filtre == 'actives':
        promotions = promotions.filter(active=True, date_debut__lte=now, date_fin__gte=now)
    elif filtre == 'futures':
        promotions = promotions.filter(active=True, date_debut__gt=now)
    elif filtre == 'expirees':
        promotions = promotions.filter(date_fin__lt=now)
    
    # Recherche
    search = request.GET.get('search')
    if search:
        promotions = promotions.filter(
            Q(nom__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Gestion de la pagination flexible
    items_per_page = request.GET.get('items_per_page', 10)
    start_range = request.GET.get('start_range', '')
    end_range = request.GET.get('end_range', '')
    
    # Conserver une copie des promotions non paginées pour les statistiques
    promotions_non_paginees = promotions
    
    # Gestion de la plage personnalisée
    if start_range and end_range:
        try:
            start_idx = int(start_range) - 1  # Index commence à 0
            end_idx = int(end_range)
            if start_idx >= 0 and end_idx > start_idx:
                promotions = list(promotions)[start_idx:end_idx]
                # Créer un paginator factice pour la plage
                paginator = Paginator(promotions, len(promotions))
                page_obj = paginator.get_page(1)
        except (ValueError, TypeError):
            # En cas d'erreur, utiliser la pagination normale
            items_per_page = 10
            paginator = Paginator(promotions, items_per_page)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
    else:
        # Pagination normale
        page_number = request.GET.get('page', 1)
        if items_per_page == 'all':
            # Afficher toutes les promotions
            paginator = Paginator(promotions, promotions.count())
            page_obj = paginator.get_page(1)
        else:
            try:
                items_per_page = int(items_per_page)
                if items_per_page <= 0:
                    items_per_page = 10
            except (ValueError, TypeError):
                items_per_page = 10
            
            paginator = Paginator(promotions, items_per_page)
            page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': Promotion.objects.count(),
        'actives': Promotion.objects.filter(
            active=True,
            date_debut__lte=now,
            date_fin__gte=now
        ).count(),
        'futures': Promotion.objects.filter(
            active=True,
            date_debut__gt=now
        ).count(),
        'articles_en_promo': Article.objects.filter(
            promotions__active=True,
            promotions__date_debut__lte=now,
            promotions__date_fin__gte=now
        ).distinct().count()
    }
    
    # Vérifier si c'est une requête AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        
        # Rendre les templates partiels pour AJAX
        html_table_body = render_to_string('article/partials/_promotions_table_body.html', {
            'page_obj': page_obj
        }, request=request)
        
        html_pagination = render_to_string('article/partials/_promotions_pagination.html', {
            'page_obj': page_obj,
            'search': search,
            'filtre': filtre,
            'items_per_page': items_per_page,
            'start_range': start_range,
            'end_range': end_range
        }, request=request)
        
        html_pagination_info = render_to_string('article/partials/_promotions_pagination_info.html', {
            'page_obj': page_obj
        }, request=request)
        
        return JsonResponse({
            'success': True,
            'html_table_body': html_table_body,
            'html_pagination': html_pagination,
            'html_pagination_info': html_pagination_info,
            'total_count': promotions_non_paginees.count()
        })

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'filtre': filtre,
        'search': search,
        'form_promotion': form_promotion,
        'items_per_page': items_per_page,
        'start_range': start_range,
        'end_range': end_range,
    }
    return render(request, 'article/liste_promotions.html', context)

@login_required
def detail_promotion(request, id):
    """Détail d'une promotion"""
    promotion = get_object_or_404(Promotion, id=id)
    
    # Articles en promotion
    articles = promotion.articles.all().order_by('nom', 'couleur', 'pointure')
    
    context = {
        'promotion': promotion,
        'articles': articles
    }
    return render(request, 'article/detail_promotion.html', context)

@login_required
def creer_promotion(request):
    """Créer une nouvelle promotion"""
    if request.method == 'POST':
        form = PromotionForm(request.POST)
        if form.is_valid():
            try:
                # Récupérer les articles sélectionnés avant de sauvegarder
                articles_selectionnes = form.cleaned_data.get('articles', [])
                
                # Créer la promotion sans les articles pour l'instant
                promotion = form.save(commit=False)
                promotion.cree_par = request.user
                promotion.save()
                
                # Maintenant que la promotion a un ID, ajouter les articles
                if articles_selectionnes:
                    promotion.articles.set(articles_selectionnes)
                
                    # Vérifier si la promotion doit être active automatiquement
                    now = timezone.now()
                    if promotion.active and promotion.date_debut <= now <= promotion.date_fin:
                        # Compter les articles avec upsell actif avant application
                        articles_avec_upsell = sum(1 for article in articles_selectionnes if article.isUpsell)
                        
                        # Appliquer la promotion aux articles sélectionnés
                        promotion.activer_promotion()
                        
                        # Message avec info sur les upsells désactivés
                        upsell_message = ""
                        if articles_avec_upsell > 0:
                            upsell_message = f" {articles_avec_upsell} upsell(s) ont été automatiquement désactivé(s)."
                        
                        messages.success(request, f"La promotion '{promotion.nom}' a été créée et activée avec succès. Les réductions ont été appliquées aux {len(articles_selectionnes)} article(s) sélectionné(s).{upsell_message}")
                    else:
                        messages.success(request, f"La promotion '{promotion.nom}' a été créée avec succès.")
                else:
                    messages.success(request, f"La promotion '{promotion.nom}' a été créée avec succès.")
                
                return redirect('article:detail_promotion', id=promotion.id)
            except Exception as e:
                messages.error(request, f"Erreur lors de la création de la promotion : {str(e)}")
                # Renommer form en form_promotion pour correspondre au template
                return render(request, 'article/liste_promotions.html', {
                    'form_promotion': form,
                    'page_obj': Promotion.objects.all().order_by('-date_creation')[:10]
                })
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
            # Renommer form en form_promotion pour correspondre au template
            return render(request, 'article/liste_promotions.html', {
                'form_promotion': form,
                'page_obj': Promotion.objects.all().order_by('-date_creation')[:10]
            })
    else:
        # Cette partie ne devrait pas être appelée directement, mais au cas où
        form = PromotionForm()
        return redirect('article:liste_promotions')

@login_required
def modifier_promotion(request, id):
    """Modifier une promotion existante"""
    promotion = get_object_or_404(Promotion, id=id)
    
    if request.method == 'POST':
        # Conserver les anciens articles pour comparaison
        anciens_articles = list(promotion.articles.all())
        
        form = PromotionForm(request.POST, instance=promotion)
        if form.is_valid():
            promotion_modifiee = form.save()
            
            # Récupérer les nouveaux articles
            nouveaux_articles = list(promotion_modifiee.articles.all())
            
            # Vérifier si la promotion doit être active
            now = timezone.now()
            if promotion_modifiee.active and promotion_modifiee.date_debut <= now <= promotion_modifiee.date_fin:
                # Retirer la promotion des anciens articles qui ne sont plus dans la promotion
                for article in anciens_articles:
                    if article not in nouveaux_articles:
                        # Vérifier si l'article n'a pas d'autres promotions actives
                        autres_promotions_actives = article.promotions.filter(
                            active=True,
                            date_debut__lte=now,
                            date_fin__gte=now
                        ).exclude(id=promotion_modifiee.id).exists()
                        
                        if not autres_promotions_actives:
                            article.retirer_promotion()
                        else:
                            article.update_prix_actuel()
                
                # Appliquer la promotion aux nouveaux articles
                for article in nouveaux_articles:
                    article.appliquer_promotion(promotion_modifiee)
                
                messages.success(request, f"La promotion '{promotion.nom}' a été modifiée avec succès. Les prix ont été mis à jour.")
            else:
                # Si la promotion n'est pas active, retirer la promotion de tous les anciens articles
                for article in anciens_articles:
                    autres_promotions_actives = article.promotions.filter(
                        active=True,
                        date_debut__lte=now,
                        date_fin__gte=now
                    ).exclude(id=promotion_modifiee.id).exists()
                    
                    if not autres_promotions_actives:
                        article.retirer_promotion()
                    else:
                        article.update_prix_actuel()
                
            messages.success(request, f"La promotion '{promotion.nom}' a été modifiée avec succès.")
            
            return redirect('article:detail_promotion', id=promotion.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
    else:
        form = PromotionForm(instance=promotion)
    
    context = {
        'promotion': promotion,
        'form': form,
    }
    return render(request, 'article/modifier_promotion.html', context)

@login_required
def supprimer_promotion(request, id):
    """Supprimer une promotion"""
    promotion = get_object_or_404(Promotion, id=id)
    
    if request.method == 'POST':
        nom = promotion.nom
        promotion.delete()
        messages.success(request, f"La promotion '{nom}' a été supprimée avec succès.")
        return redirect('article:liste_promotions')
    
    return render(request, 'article/supprimer_promotion.html', {'promotion': promotion})

@login_required
def activer_desactiver_promotion(request, id):
    """Activer ou désactiver une promotion"""
    promotion = get_object_or_404(Promotion, id=id)
    
    if promotion.active:
        # Désactiver la promotion
        promotion.desactiver_promotion()
        action = "désactivée"
        messages.success(request, f"La promotion '{promotion.nom}' a été {action} avec succès. Les prix des articles ont été remis à leur état initial.")
    else:
        # Compter les articles avec upsell actif avant activation
        articles_avec_upsell = sum(1 for article in promotion.articles.all() if article.isUpsell)
        
        # Activer la promotion
        promotion.activer_promotion()
        action = "activée"
        
        # Message avec info sur les upsells désactivés
        upsell_message = ""
        if articles_avec_upsell > 0:
            upsell_message = f" {articles_avec_upsell} upsell(s) ont été automatiquement désactivé(s)."
        
        messages.success(request, f"La promotion '{promotion.nom}' a été {action} avec succès. Les réductions ont été appliquées aux articles.{upsell_message}")
    
    # Rediriger vers la page précédente ou la liste des promotions
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('article:liste_promotions')

@login_required
def changer_phase(request, id):
    """Changer la phase d'un article"""
    article = get_object_or_404(Article, id=id)
    now = timezone.now()
    
    if request.method == 'POST':
        # Vérifier si l'article est en promotion active
        if article.has_promo_active:
            messages.error(request, f"Impossible de changer la phase de l'article '{article.nom}' car il est actuellement en promotion.")
        else:
            phase = request.POST.get('phase')
            if phase in dict(Article.PHASE_CHOICES).keys():
                # Vérifier si l'upsell était actif avant le changement
                upsell_was_active = article.isUpsell
                
                article.phase = phase
                # L'upsell sera automatiquement désactivé par la méthode save() si nécessaire
                article.save()
                
                # Message en fonction de la phase avec info sur l'upsell
                upsell_message = " L'upsell a été automatiquement désactivé." if upsell_was_active and phase in ['LIQUIDATION', 'EN_TEST'] else ""
                
                if phase == 'EN_COURS':
                    messages.success(request, f"L'article '{article.nom}' a été remis en phase par défaut (En Cours).{upsell_message}")
                elif phase == 'LIQUIDATION':
                    messages.warning(request, f"L'article '{article.nom}' a été mis en liquidation.{upsell_message}")
                elif phase == 'EN_TEST':
                    messages.info(request, f"L'article '{article.nom}' a été mis en phase de test.{upsell_message}")
                elif phase == 'PROMO':
                    messages.success(request, f"L'article '{article.nom}' a été mis en phase promotion.{upsell_message}")
                
    # Rediriger vers la page précédente ou la page de détail
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('article:detail', id=article.id)

@login_required
@require_POST
def appliquer_liquidation(request, id):
    """Applique une réduction de liquidation à un article"""
    article = get_object_or_404(Article, id=id)
    
    # Vérifier si l'article est déjà en promotion
    if article.has_promo_active:
        messages.error(request, "Impossible d'appliquer une liquidation car l'article est en promotion.")
        return redirect('article:detail', id=article.id)
    
    try:
        pourcentage = Decimal(request.POST.get('pourcentage', '0'))
        if pourcentage <= 0 or pourcentage > 90:
            messages.error(request, "Le pourcentage de réduction doit être compris entre 0 et 90%.")
            return redirect('article:detail', id=article.id)
        
        # Désactiver l'upsell avant de mettre en liquidation
        upsell_was_active = article.isUpsell
        
        # Mettre l'article en liquidation
        article.phase = 'LIQUIDATION'
        # Calculer et appliquer la réduction
        reduction = article.prix_unitaire * (pourcentage / 100)
        article.prix_actuel = article.prix_unitaire - reduction
        # L'upsell sera automatiquement désactivé par la méthode save()
        article.save()
        
        if upsell_was_active:
            messages.success(request, f"L'article a été mis en liquidation avec une réduction de {pourcentage}%. L'upsell a été automatiquement désactivé.")
        else:
            messages.success(request, f"L'article a été mis en liquidation avec une réduction de {pourcentage}%.")
        
    except (ValueError, TypeError):
        messages.error(request, "Le pourcentage de réduction n'est pas valide.")
    
    return redirect('article:detail', id=article.id)

@login_required
@require_POST
def reinitialiser_prix(request, id):
    """Réinitialise le prix d'un article à son prix unitaire par défaut"""
    article = get_object_or_404(Article, id=id)
    
    # Réinitialiser le prix actuel au prix unitaire
    article.prix_actuel = article.prix_unitaire
    # Remettre la phase en EN_COURS
    article.phase = 'EN_COURS'
    article.save()
    
    messages.success(request, f"Le prix de l'article '{article.nom}' a été réinitialisé avec succès.")
    
    # Rediriger vers la page précédente ou la page de détail
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('article:detail', id=article.id)



@login_required
def gerer_promotions_automatiquement(request):
    """Gère automatiquement toutes les promotions selon leur date et statut"""
    now = timezone.now()
    
    # Statistiques
    stats = {
        'activated': 0,
        'deactivated': 0,
        'articles_updated': 0
    }
    
    # Récupérer toutes les promotions
    all_promotions = Promotion.objects.all()
    
    for promotion in all_promotions:
        result = promotion.verifier_et_appliquer_automatiquement()
        
        if result == "activated":
            stats['activated'] += 1
            stats['articles_updated'] += promotion.articles.count()
        elif result == "deactivated":
            stats['deactivated'] += 1
            stats['articles_updated'] += promotion.articles.count()
    
    # Messages de feedback
    messages_list = []
    if stats['activated'] > 0:
        messages_list.append(f"{stats['activated']} promotion(s) activée(s)")
    if stats['deactivated'] > 0:
        messages_list.append(f"{stats['deactivated']} promotion(s) désactivée(s)")
    if stats['articles_updated'] > 0:
        messages_list.append(f"{stats['articles_updated']} article(s) mis à jour")
    
    if messages_list:
        messages.success(request, "Gestion automatique terminée : " + " et ".join(messages_list) + ".")
    else:
        messages.info(request, "Aucune promotion à traiter automatiquement.")
    
    # Rediriger vers la liste des promotions
    return redirect('article:liste_promotions')



@login_required
def corriger_upsells(request):
    """Corrige les upsells qui devraient être désactivés (vue web)"""
    try:
        # Compter les articles avec upsell qui devraient être désactivés
        articles_avec_upsell = Article.objects.filter(isUpsell=True, actif=True)
        
        articles_a_corriger = []
        stats = {'liquidation': 0, 'test': 0, 'promotion': 0}
        
        for article in articles_avec_upsell:
            if article.should_disable_upsell():
                articles_a_corriger.append(article)
                
                # Compter les raisons
                if article.phase == 'LIQUIDATION':
                    stats['liquidation'] += 1
                elif article.phase == 'EN_TEST':
                    stats['test'] += 1
                if article.has_promo_active:
                    stats['promotion'] += 1
        
        if not articles_a_corriger:
            messages.info(request, "✅ Tous les upsells sont correctement configurés.")
        else:
            # Appliquer les corrections
            corrected_count = 0
            for article in articles_a_corriger:
                article.isUpsell = False
                article.save(update_fields=['isUpsell'])
                corrected_count += 1
            
            # Message détaillé
            details = []
            if stats['liquidation'] > 0:
                details.append(f"{stats['liquidation']} en liquidation")
            if stats['test'] > 0:
                details.append(f"{stats['test']} en test")
            if stats['promotion'] > 0:
                details.append(f"{stats['promotion']} en promotion")
            
            detail_str = " (" + ", ".join(details) + ")" if details else ""
            
            messages.success(request, 
                f"✅ Correction des upsells terminée ! "
                f"{corrected_count} article(s) mis à jour{detail_str}."
            )
        
    except Exception as e:
        messages.error(request, f"❌ Erreur lors de la correction des upsells : {str(e)}")
    
    # Rediriger vers la liste des articles
    return redirect('article:liste')
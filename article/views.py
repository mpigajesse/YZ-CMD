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

# Create your views here.

@login_required
def liste_articles(request):
    """Liste des articles avec recherche simple et pagination"""
    articles = Article.objects.filter(actif=True).order_by('nom', 'couleur', 'pointure')
    
    # Recherche unique sur plusieurs champs
    search = request.GET.get('search')
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
    
    # Pagination
    paginator = Paginator(articles, 24)  # 24 articles par page (grille 4x6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques simples
    all_articles = Article.objects.filter(actif=True)
    stats = {
        'total_articles': all_articles.count(),
        'articles_disponibles': all_articles.filter(qte_disponible__gt=0).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'search': search,
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
            article.qte_disponible = qte_disponible
            article.categorie = request.POST.get('categorie')
            
            # Gérer l'image si elle est fournie
            if 'image' in request.FILES:
                article.image = request.FILES['image']
            
            # Gérer les prix de substitution (upsell)
            for i in range(1, 4):
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
            
            # Gérer l'image si elle est fournie
            if 'image' in request.FILES:
                article.image = request.FILES['image']
            
            # Gérer les prix de substitution (upsell)
            # Réinitialiser les prix upsell
            article.prix_upsell_1 = None
            article.prix_upsell_2 = None
            article.prix_upsell_3 = None
            
            for i in range(1, 4):
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
    
    # Filtres
    filtre = request.GET.get('filtre', 'toutes')
    if filtre == 'actives':
        now = timezone.now()
        promotions = promotions.filter(active=True, date_debut__lte=now, date_fin__gte=now)
    elif filtre == 'futures':
        promotions = promotions.filter(active=True, date_debut__gt=timezone.now())
    elif filtre == 'expirees':
        promotions = promotions.filter(date_fin__lt=timezone.now())
    elif filtre == 'inactives':
        promotions = promotions.filter(active=False)
    
    # Recherche
    search = request.GET.get('search')
    if search:
        promotions = promotions.filter(
            Q(nom__icontains=search) |
            Q(description__icontains=search) |
            Q(code_promo__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(promotions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': Promotion.objects.count(),
        'actives': Promotion.objects.filter(
            active=True,
            date_debut__lte=timezone.now(),
            date_fin__gte=timezone.now()
        ).count(),
        'futures': Promotion.objects.filter(
            active=True,
            date_debut__gt=timezone.now()
        ).count(),
        'articles_en_promo': Article.objects.filter(
            promotions__active=True,
            promotions__date_debut__lte=timezone.now(),
            promotions__date_fin__gte=timezone.now()
        ).distinct().count()
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'filtre': filtre,
        'search': search
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
        try:
            # Récupérer les données du formulaire
            nom = request.POST.get('nom')
            description = request.POST.get('description', '')
            pourcentage_str = request.POST.get('pourcentage_reduction', '').strip().replace(',', '.')
            date_debut_str = request.POST.get('date_debut')
            date_fin_str = request.POST.get('date_fin')
            code_promo = request.POST.get('code_promo', '')
            
            # Valider le pourcentage
            try:
                pourcentage = float(pourcentage_str)
                if pourcentage <= 0 or pourcentage > 100:
                    messages.error(request, "Le pourcentage de réduction doit être entre 0 et 100.")
                    return render(request, 'article/creer_promotion.html', {'form_data': request.POST})
            except ValueError:
                messages.error(request, "Le pourcentage de réduction doit être un nombre valide.")
                return render(request, 'article/creer_promotion.html', {'form_data': request.POST})
            
            # Valider les dates
            from datetime import datetime
            try:
                date_debut = datetime.fromisoformat(date_debut_str)
                date_fin = datetime.fromisoformat(date_fin_str)
                
                if date_fin <= date_debut:
                    messages.error(request, "La date de fin doit être postérieure à la date de début.")
                    return render(request, 'article/creer_promotion.html', {'form_data': request.POST})
            except ValueError:
                messages.error(request, "Les dates doivent être au format valide.")
                return render(request, 'article/creer_promotion.html', {'form_data': request.POST})
            
            # Vérifier l'unicité du code promo
            if code_promo and Promotion.objects.filter(code_promo=code_promo).exists():
                messages.error(request, "Ce code promo existe déjà.")
                return render(request, 'article/creer_promotion.html', {'form_data': request.POST})
            
            # Créer la promotion
            promotion = Promotion()
            promotion.nom = nom
            promotion.description = description
            promotion.pourcentage_reduction = pourcentage
            promotion.date_debut = date_debut
            promotion.date_fin = date_fin
            promotion.code_promo = code_promo if code_promo else None
            promotion.cree_par = request.user
            promotion.active = request.POST.get('active') == 'on'
            
            promotion.save()
            
            # Ajouter les articles sélectionnés
            article_ids = request.POST.getlist('articles')
            if article_ids:
                articles = Article.objects.filter(id__in=article_ids)
                promotion.articles.add(*articles)
            
            messages.success(request, f"La promotion '{promotion.nom}' a été créée avec succès.")
            return redirect('article:liste_promotions')
            
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la création de la promotion : {str(e)}")
            return render(request, 'article/creer_promotion.html', {'form_data': request.POST})
    
    # Pour le formulaire GET, récupérer tous les articles pour la sélection
    articles = Article.objects.filter(actif=True).order_by('nom', 'couleur', 'pointure')
    
    context = {
        'articles': articles
    }
    return render(request, 'article/creer_promotion.html', context)

@login_required
def modifier_promotion(request, id):
    """Modifier une promotion existante"""
    promotion = get_object_or_404(Promotion, id=id)
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            nom = request.POST.get('nom')
            description = request.POST.get('description', '')
            pourcentage_str = request.POST.get('pourcentage_reduction', '').strip().replace(',', '.')
            date_debut_str = request.POST.get('date_debut')
            date_fin_str = request.POST.get('date_fin')
            code_promo = request.POST.get('code_promo', '')
            
            # Valider le pourcentage
            try:
                pourcentage = float(pourcentage_str)
                if pourcentage <= 0 or pourcentage > 100:
                    messages.error(request, "Le pourcentage de réduction doit être entre 0 et 100.")
                    return render(request, 'article/modifier_promotion.html', {'promotion': promotion, 'form_data': request.POST})
            except ValueError:
                messages.error(request, "Le pourcentage de réduction doit être un nombre valide.")
                return render(request, 'article/modifier_promotion.html', {'promotion': promotion, 'form_data': request.POST})
            
            # Valider les dates
            from datetime import datetime
            try:
                date_debut = datetime.fromisoformat(date_debut_str)
                date_fin = datetime.fromisoformat(date_fin_str)
                
                if date_fin <= date_debut:
                    messages.error(request, "La date de fin doit être postérieure à la date de début.")
                    return render(request, 'article/modifier_promotion.html', {'promotion': promotion, 'form_data': request.POST})
            except ValueError:
                messages.error(request, "Les dates doivent être au format valide.")
                return render(request, 'article/modifier_promotion.html', {'promotion': promotion, 'form_data': request.POST})
            
            # Vérifier l'unicité du code promo
            if code_promo and Promotion.objects.filter(code_promo=code_promo).exclude(id=promotion.id).exists():
                messages.error(request, "Ce code promo existe déjà.")
                return render(request, 'article/modifier_promotion.html', {'promotion': promotion, 'form_data': request.POST})
            
            # Mettre à jour la promotion
            promotion.nom = nom
            promotion.description = description
            promotion.pourcentage_reduction = pourcentage
            promotion.date_debut = date_debut
            promotion.date_fin = date_fin
            promotion.code_promo = code_promo if code_promo else None
            promotion.active = request.POST.get('active') == 'on'
            
            promotion.save()
            
            # Mettre à jour les articles sélectionnés
            article_ids = request.POST.getlist('articles')
            promotion.articles.clear()
            if article_ids:
                articles = Article.objects.filter(id__in=article_ids)
                promotion.articles.add(*articles)
            
            messages.success(request, f"La promotion '{promotion.nom}' a été modifiée avec succès.")
            return redirect('article:detail_promotion', id=promotion.id)
            
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la modification de la promotion : {str(e)}")
            return render(request, 'article/modifier_promotion.html', {'promotion': promotion, 'form_data': request.POST})
    
    # Pour le formulaire GET
    articles = Article.objects.filter(actif=True).order_by('nom', 'couleur', 'pointure')
    articles_selectionnes = promotion.articles.all().values_list('id', flat=True)
    
    context = {
        'promotion': promotion,
        'articles': articles,
        'articles_selectionnes': list(articles_selectionnes)
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
    
    promotion.active = not promotion.active
    promotion.save()
    
    action = "activée" if promotion.active else "désactivée"
    messages.success(request, f"La promotion '{promotion.nom}' a été {action} avec succès.")
    
    # Rediriger vers la page précédente ou la liste des promotions
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('article:liste_promotions')

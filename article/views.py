from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum, Min, Max
from .models import Article
from django.urls import reverse
from django.views.decorators.http import require_POST

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
        # Récupérer les données du formulaire
        nom = request.POST.get('nom')
        couleur = request.POST.get('couleur')
        pointure = request.POST.get('pointure')

        # Vérifier l'unicité de la combinaison nom, couleur, pointure
        if Article.objects.filter(nom=nom, couleur=couleur, pointure=pointure).exists():
            messages.error(request, "Un article avec le même nom, couleur et pointure existe déjà.")
            # Renvoyer le formulaire avec les données saisies
            return render(request, 'article/creer.html', {'form_data': request.POST})

        article = Article()
        article.nom = nom
        article.couleur = couleur
        article.pointure = pointure
        article.reference = request.POST.get('reference')
        article.description = request.POST.get('description')
        
        # Assurer la conversion correcte du prix
        prix_str = request.POST.get('prix_unitaire', '0').replace(',', '.')
        article.prix_unitaire = prix_str
        
        article.qte_disponible = request.POST.get('qte_disponible')
        article.categorie = request.POST.get('categorie')
        
        # Gérer l'image si elle est fournie
        if 'image' in request.FILES:
            article.image = request.FILES['image']
        
        article.save()
        messages.success(request, f"L'article '{article.nom}' a été créé avec succès.")
        return redirect('article:liste')
    
    return render(request, 'article/creer.html')

@login_required
def modifier_article(request, id):
    """Modifier un article existant"""
    article = get_object_or_404(Article, id=id, actif=True)

    if request.method == 'POST':
        nom = request.POST.get('nom')
        couleur = request.POST.get('couleur')
        pointure = request.POST.get('pointure')

        # Vérifier l'unicité de la combinaison nom, couleur, pointure
        if Article.objects.filter(nom=nom, couleur=couleur, pointure=pointure).exclude(pk=id).exists():
            messages.error(request, "Un autre article avec le même nom, couleur et pointure existe déjà.")
        else:
            article.nom = nom
            article.reference = request.POST.get('reference')
            article.couleur = couleur
            article.pointure = pointure
        article.description = request.POST.get('description')
            # Assurer la conversion correcte du prix
        prix_str = request.POST.get('prix_unitaire', '0').replace(',', '.')
        article.prix_unitaire = prix_str
        article.qte_disponible = request.POST.get('qte_disponible')
        article.categorie = request.POST.get('categorie')
            
        if 'image' in request.FILES:
            article.image = request.FILES['image']
        
        article.save()
        messages.success(request, "L'article a été modifié avec succès.")
        return redirect('article:liste')
    
    context = {
        'article': article,
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

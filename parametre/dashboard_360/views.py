from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.db.models import Count, Q
from django.core.paginator import Paginator
from parametre.models import Operateur
from article.models import Article
from commande.models import Commande, EtatCommande, EnumEtatCmd
from client.models import Client
import csv
import io
import zipfile
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from django.utils.encoding import smart_str

@staff_member_required
@login_required
def page_360(request):
    """Page 360 - Vue d'overview et exportation des données"""
    # Statistiques générales
    total_articles = Article.objects.count()
    total_clients = Client.objects.count()
    total_commandes = Commande.objects.count()
    total_operateurs = Operateur.objects.count()
    
    # Récupérer toutes les commandes avec filtres et pagination - optimisé avec only()
    commandes_360 = Commande.objects.select_related(
        'client', 
        'ville', 
        'ville__region'
    ).prefetch_related(
        'etats__enum_etat',
        'etats__operateur', # Pour récupérer l'opérateur qui a fait l'état
        'paniers__article' # Accéder aux articles via les paniers
    ).only(
        'id', 'num_cmd', 'id_yz', 'date_cmd', 'total_cmd', 'is_upsell',
        'client__nom', 'client__prenom', 'client__numero_tel', 'client__adresse',
        'ville__nom', 'ville__region__nom_region'
    )
    
    # Filtres de recherche
    search = request.GET.get('search')
    if search:
        commandes_360 = commandes_360.filter(
            Q(num_cmd__icontains=search) |
            Q(id_yz__icontains=search) |
            Q(client__nom__icontains=search) |
            Q(client__prenom__icontains=search) |
            Q(client__numero_tel__icontains=search)
        )
    
    date_debut = request.GET.get('date_debut')
    if date_debut:
        commandes_360 = commandes_360.filter(date_cmd__gte=date_debut)
        
    date_fin = request.GET.get('date_fin')
    if date_fin:
        commandes_360 = commandes_360.filter(date_cmd__lte=date_fin)
    
    commandes_360 = commandes_360.order_by('-date_cmd')
    
    # Pagination - 50 commandes par page
    paginator = Paginator(commandes_360, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Préparer les données pour le template
    data_for_template = []
    for cmd in page_obj:
        confirmation_info = cmd.etats.filter(enum_etat__libelle__icontains='Confirmée').first()
        preparation_info = cmd.etats.filter(enum_etat__libelle__icontains='Préparation en cours').first()
        
        # Récupérer les informations de livraison et paiement depuis les EtatsCommande
        etat_livraison_obj = cmd.etats.filter(enum_etat__libelle__icontains='Livrée').first() # Exemple: Libellé pour l'état livré
        etat_paiement_obj = cmd.etats.filter(enum_etat__libelle__icontains='Payée').first() # Exemple: Libellé pour l'état payé
        piece_retournee_obj = cmd.etats.filter(enum_etat__libelle__icontains='Retournée').first() # Exemple pour pièce retournée

        etat_paiement = etat_paiement_obj.enum_etat.libelle if etat_paiement_obj else "Non Payé"
        etat_livraison = etat_livraison_obj.enum_etat.libelle if etat_livraison_obj else "En attente"
        piece_retournee = "Oui" if piece_retournee_obj else "Non"
        
        # Pour le panier: Joindre les noms des articles du panier
        articles_noms = ", ".join([panier.article.nom for panier in cmd.paniers.all()]) or "N/A"

        # Opérateur Assigné: Chercher l'opérateur lié à l'état 'Affectée' ou un autre état pertinent
        operateur_assigne_obj = cmd.etats.filter(enum_etat__libelle__icontains='Affectée').first()
        operateur_assigne_nom = operateur_assigne_obj.operateur.mail if operateur_assigne_obj and operateur_assigne_obj.operateur else "N/A"
        
        # Agent Confirmation: Opérateur lié à l'état 'Confirmée'
        agent_confirmation_nom = confirmation_info.operateur.mail if confirmation_info and confirmation_info.operateur else "N/A"

        tarif_livraison = 0.0 # À dériver si un état spécifique ou un champ existe dans Commande
        reste_a_payer = cmd.total_cmd # À ajuster si un montant payé peut être déduit des états
        date_paiement = "N/A" # À dériver si un état spécifique ou un champ existe dans EtatCommande pour le paiement
        observation_livraison = piece_retournee_obj.commentaire if piece_retournee_obj else "" # Ou un autre état pertinent

        data_for_template.append({
            'num_cmd': cmd.num_cmd,
            'id_yz': cmd.id_yz,
            'client_nom_prenom': f"{cmd.client.prenom} {cmd.client.nom}" if cmd.client else "N/A",
            'client_telephone': cmd.client.numero_tel if cmd.client else "N/A",
            'client_adresse': cmd.client.adresse if cmd.client else "N/A",
            'ville': cmd.ville.nom if cmd.ville else "N/A",
            'region': cmd.ville.region.nom_region if cmd.ville and cmd.ville.region else "N/A",
            'panier': articles_noms,
            'prix_total_dh': cmd.total_cmd,
            'date_commande': cmd.date_cmd.strftime('%d/%m/%Y') if cmd.date_cmd else "N/A",
            'confirmation_status': confirmation_info.enum_etat.libelle if confirmation_info else "Non Confirmée",
            'date_confirmation': confirmation_info.date_debut.strftime('%d/%m/%Y %H:%M') if confirmation_info and confirmation_info.date_debut else "N/A",
            'observations_confirmation': confirmation_info.commentaire if confirmation_info else "",
            'operateur_assigne': operateur_assigne_nom,
            'agent_confirmation': agent_confirmation_nom,
            'client_fidele': "future qui seras des les tables models plustard dans le projet",
            'upsell_display': "Oui" if cmd.is_upsell else "Non",
            'preparation_status': preparation_info.enum_etat.libelle if preparation_info else "Non Préparée",
            'etat_livraison': etat_livraison,
            'etat_paiement': etat_paiement,
            'tarif_livraison': tarif_livraison,
            'reste_a_payer': reste_a_payer,
            'date_paiement': date_paiement,
            'piece_retournee': piece_retournee,
            'observation_livraison': observation_livraison,
        })

    context = {
        'total_articles': total_articles,
        'total_clients': total_clients,
        'total_commandes': total_commandes,
        'total_operateurs': total_operateurs,
        'commandes_data': data_for_template,
        'page_obj': page_obj,
        'search': search,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    return render(request, 'parametre/360.html', context)

@staff_member_required
@login_required
def export_all_data_csv(request):
    # Assurez-vous que la méthode de requête est POST
    if request.method == 'POST':
        # Récupérer les filtres pour appliquer les mêmes que dans la vue
        search = request.POST.get('search') or request.GET.get('search')
        date_debut = request.POST.get('date_debut') or request.GET.get('date_debut')
        date_fin = request.POST.get('date_fin') or request.GET.get('date_fin')
        
        # Utiliser une réponse streaming pour de gros volumes
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="export_commandes_avec_paniers_360.csv"'
        
        # Utiliser un writer CSV directement sur la réponse
        writer = csv.writer(response)

        # En-têtes du CSV consolidé avec détails des paniers
        headers = [
            'N°', 'Identifiant Yoozak', 'CLIENT', 'TELEPHONE', 'ADRESSE', 'VILLE', 'REGION',
            'ARTICLE NOM', 'ARTICLE REFERENCE', 'ARTICLE COULEUR', 'ARTICLE POINTURE', 
            'QUANTITE', 'PRIX UNITAIRE', 'SOUS TOTAL ARTICLE',
            'PRIX TOTAL COMMANDE (DH)', 'DATE COMMANDE', 'CONFIRMATION', 'DATE CONFIRMATION',
            'OBSERVATIONS CONFIRMATION', 'OPERATEUR', 'AGENT CONFIRMATION',
            'CLIENT FIDELE', 'UPSELL', 'PREPARATION', 'ETAT LIVRAISON',
            'ETAT PAIEMENT', 'TARIF', 'RESTE A PAYER', 'DATE PAIEMENT', 'PIECE RETOURNEE',
            'OBSERVATION LIVRAISON'
        ]
        writer.writerow(headers)
            
        # Traitement par batch de 1000 commandes pour éviter de surcharger la mémoire
        batch_size = 1000
        offset = 0
        
        while True:
            # Construire la requête avec les mêmes filtres que la vue
            commandes_query = Commande.objects.select_related(
                'client', 
                'ville', 
                'ville__region'
            ).prefetch_related(
                'etats__enum_etat',
                'etats__operateur',
                'paniers__article'
            ).only(
                'id', 'num_cmd', 'id_yz', 'date_cmd', 'total_cmd', 'is_upsell',
                'client__nom', 'client__prenom', 'client__numero_tel', 'client__adresse',
                'ville__nom', 'ville__region__nom_region'
            )
            
            # Appliquer les filtres
            if search:
                commandes_query = commandes_query.filter(
                    Q(num_cmd__icontains=search) |
                    Q(id_yz__icontains=search) |
                    Q(client__nom__icontains=search) |
                    Q(client__prenom__icontains=search) |
                    Q(client__numero_tel__icontains=search)
                )
            
            if date_debut:
                commandes_query = commandes_query.filter(date_cmd__gte=date_debut)
            
            if date_fin:
                commandes_query = commandes_query.filter(date_cmd__lte=date_fin)
            
            commandes_batch = commandes_query.order_by('-date_cmd')[offset:offset + batch_size]
            
            if not commandes_batch:
                break
                
            for cmd in commandes_batch:
                confirmation_info = cmd.etats.filter(enum_etat__libelle__icontains='Confirmée').first()
                preparation_info = cmd.etats.filter(enum_etat__libelle__icontains='Préparation en cours').first()
                
                etat_livraison_obj = cmd.etats.filter(enum_etat__libelle__icontains='Livrée').first()
                etat_paiement_obj = cmd.etats.filter(enum_etat__libelle__icontains='Payée').first()
                piece_retournee_obj = cmd.etats.filter(enum_etat__libelle__icontains='Retournée').first()

                etat_paiement = etat_paiement_obj.enum_etat.libelle if etat_paiement_obj else "Non Payé"
                etat_livraison = etat_livraison_obj.enum_etat.libelle if etat_livraison_obj else "En attente"
                piece_retournee = "Oui" if piece_retournee_obj else "Non"

                operateur_assigne_obj = cmd.etats.filter(enum_etat__libelle__icontains='Affectée').first()
                operateur_assigne_nom = operateur_assigne_obj.operateur.mail if operateur_assigne_obj and operateur_assigne_obj.operateur else "N/A"
                
                agent_confirmation_nom = confirmation_info.operateur.mail if confirmation_info and confirmation_info.operateur else "N/A"

                tarif_livraison = 0.0
                reste_a_payer = cmd.total_cmd
                date_paiement = "N/A"
                observation_livraison = piece_retournee_obj.commentaire if piece_retournee_obj else ""

                # Informations communes à la commande
                commande_info = [
                    cmd.num_cmd,
                    cmd.id_yz,
                    f"{cmd.client.prenom} {cmd.client.nom}" if cmd.client else "N/A",
                    cmd.client.numero_tel if cmd.client else "N/A",
                    cmd.client.adresse if cmd.client else "N/A",
                    cmd.ville.nom if cmd.ville else "N/A",
                    cmd.ville.region.nom_region if cmd.ville and cmd.ville.region else "N/A",
                ]
                
                # Données communes de fin
                commande_fin_info = [
                    cmd.total_cmd,
                    cmd.date_cmd.strftime('%d/%m/%Y') if cmd.date_cmd else "N/A",
                    confirmation_info.enum_etat.libelle if confirmation_info else "Non Confirmée",
                    confirmation_info.date_debut.strftime('%d/%m/%Y %H:%M') if confirmation_info and confirmation_info.date_debut else "N/A",
                    confirmation_info.commentaire if confirmation_info else "",
                    operateur_assigne_nom,
                    agent_confirmation_nom,
                    "future qui seras des les tables models plustard dans le projet", # Client Fidèle
                    "Oui" if cmd.is_upsell else "Non", # UPSELL
                    preparation_info.enum_etat.libelle if preparation_info else "Non Préparée",
                    etat_livraison,
                    etat_paiement,
                    tarif_livraison,
                    reste_a_payer,
                    date_paiement,
                    piece_retournee,
                    observation_livraison,
                ]
                
                # Si la commande a des articles, créer une ligne par article
                paniers = cmd.paniers.all()
                if paniers:
                    for panier in paniers:
                        # Détails de l'article
                        article_info = [
                            panier.article.nom or "N/A",
                            panier.article.reference or "N/A",
                            panier.article.couleur or "N/A",
                            panier.article.pointure or "N/A",
                            panier.quantite,
                            panier.article.prix_unitaire,
                            panier.sous_total,
                        ]
                        
                        # Combiner toutes les informations
                        row_data = commande_info + article_info + commande_fin_info
                        writer.writerow(row_data)
                else:
                    # Si pas d'articles, créer une ligne avec des valeurs N/A
                    article_info = ["N/A", "N/A", "N/A", "N/A", 0, 0, 0]
                    row_data = commande_info + article_info + commande_fin_info
                    writer.writerow(row_data)

            offset += batch_size

        return response
    return redirect('app_admin:page_360')

@staff_member_required
@login_required
def export_all_data_excel(request):
    # Récupérer les filtres
    search = request.GET.get('search')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    # Créer un fichier Excel temporaire avec streaming
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="export_commandes_avec_paniers_360.xlsx"'
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Commandes avec Paniers"

    # En-têtes Excel avec style - Inclure les détails des paniers
    headers = [
        "N°", "Identifiant Yoozak", "CLIENT", "TELEPHONE", "ADRESSE", "VILLE", "REGION",
        "ARTICLE NOM", "ARTICLE REFERENCE", "ARTICLE COULEUR", "ARTICLE POINTURE", 
        "QUANTITE", "PRIX UNITAIRE", "SOUS TOTAL ARTICLE",
        "PRIX TOTAL COMMANDE (DH)", "DATE COMMANDE", "CONFIRMATION", "DATE CONFIRMATION",
        "OBSERVATIONS CONFIRMATION", "OPERATEUR", "AGENT CONFIRMATION",
        "CLIENT FIDELE", "UPSELL", "PREPARATION", "ETAT LIVRAISON",
        "ETAT PAIEMENT", "TARIF", "RESTE A PAYER", "DATE PAIEMENT", "PIECE RETOURNEE",
        "OBSERVATION LIVRAISON"
    ]
    ws.append(headers)

    # Style des en-têtes
    from openpyxl.styles import Font, PatternFill
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
    
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    # Traitement par batch pour Excel aussi
    batch_size = 500  # Plus petit pour Excel car plus lourd
    offset = 0
    
    while True:
        # Construire la requête avec les mêmes filtres que la vue
        commandes_query = Commande.objects.select_related(
            'client', 
            'ville', 
            'ville__region'
        ).prefetch_related(
            'etats__enum_etat', 
            'etats__operateur', 
            'paniers__article'
        ).only(
            'id', 'num_cmd', 'id_yz', 'date_cmd', 'total_cmd', 'is_upsell',
            'client__nom', 'client__prenom', 'client__numero_tel', 'client__adresse',
            'ville__nom', 'ville__region__nom_region'
        )
        
        # Appliquer les filtres
        if search:
            commandes_query = commandes_query.filter(
                Q(num_cmd__icontains=search) |
                Q(id_yz__icontains=search) |
                Q(client__nom__icontains=search) |
                Q(client__prenom__icontains=search) |
                Q(client__numero_tel__icontains=search)
            )
        
        if date_debut:
            commandes_query = commandes_query.filter(date_cmd__gte=date_debut)
            
        if date_fin:
            commandes_query = commandes_query.filter(date_cmd__lte=date_fin)
        
        commandes_batch = commandes_query.order_by('-date_cmd')[offset:offset + batch_size]
        
        if not commandes_batch:
            break
            
        for cmd in commandes_batch:
            confirmation_info = cmd.etats.filter(enum_etat__libelle__icontains='Confirmée').first()
            preparation_info = cmd.etats.filter(enum_etat__libelle__icontains='Préparation en cours').first()
            
            # Récupérer les informations de livraison et paiement depuis les EtatsCommande
            etat_livraison_obj = cmd.etats.filter(enum_etat__libelle__icontains='Livrée').first()
            etat_paiement_obj = cmd.etats.filter(enum_etat__libelle__icontains='Payée').first()
            piece_retournee_obj = cmd.etats.filter(enum_etat__libelle__icontains='Retournée').first()

            etat_paiement = etat_paiement_obj.enum_etat.libelle if etat_paiement_obj else "Non Payé"
            etat_livraison = etat_livraison_obj.enum_etat.libelle if etat_livraison_obj else "En attente"
            piece_retournee = "Oui" if piece_retournee_obj else "Non"

            # Opérateur Assigné: Chercher l'opérateur lié à l'état 'Affectée' ou un autre état pertinent
            operateur_assigne_obj = cmd.etats.filter(enum_etat__libelle__icontains='Affectée').first()
            operateur_assigne_nom = operateur_assigne_obj.operateur.mail if operateur_assigne_obj and operateur_assigne_obj.operateur else "N/A"
            
            # Agent Confirmation: Opérateur lié à l'état 'Confirmée'
            agent_confirmation_nom = confirmation_info.operateur.mail if confirmation_info and confirmation_info.operateur else "N/A"

            tarif_livraison = 0.0
            reste_a_payer = cmd.total_cmd
            date_paiement = "N/A"
            observation_livraison = piece_retournee_obj.commentaire if piece_retournee_obj else ""

            # Informations communes à la commande
            commande_info = [
                cmd.num_cmd,
                cmd.id_yz,
                f"{cmd.client.prenom} {cmd.client.nom}" if cmd.client else "N/A",
                cmd.client.numero_tel if cmd.client else "N/A",
                cmd.client.adresse if cmd.client else "N/A",
                cmd.ville.nom if cmd.ville else "N/A",
                cmd.ville.region.nom_region if cmd.ville and cmd.ville.region else "N/A",
            ]
            
            # Données communes de fin
            commande_fin_info = [
                cmd.total_cmd,
                cmd.date_cmd.strftime('%d/%m/%Y') if cmd.date_cmd else "N/A",
                confirmation_info.enum_etat.libelle if confirmation_info else "Non Confirmée",
                confirmation_info.date_debut.strftime('%d/%m/%Y %H:%M') if confirmation_info and confirmation_info.date_debut else "N/A",
                confirmation_info.commentaire if confirmation_info else "",
                operateur_assigne_nom,
                agent_confirmation_nom,
                "future qui seras des les tables models plustard dans le projet", # Client Fidèle
                "Oui" if cmd.is_upsell else "Non", # UPSELL
                preparation_info.enum_etat.libelle if preparation_info else "Non Préparée",
                etat_livraison,
                etat_paiement,
                tarif_livraison,
                reste_a_payer,
                date_paiement,
                piece_retournee,
                observation_livraison,
            ]
            
            # Si la commande a des articles, créer une ligne par article
            paniers = cmd.paniers.all()
            if paniers:
                for panier in paniers:
                    # Détails de l'article
                    article_info = [
                        panier.article.nom or "N/A",
                        panier.article.reference or "N/A",
                        panier.article.couleur or "N/A",
                        panier.article.pointure or "N/A",
                        panier.quantite,
                        panier.article.prix_unitaire,
                        panier.sous_total,
                    ]
                    
                    # Combiner toutes les informations
                    row_data = commande_info + article_info + commande_fin_info
                    ws.append(row_data)
            else:
                # Si pas d'articles, créer une ligne avec des valeurs N/A
                article_info = ["N/A", "N/A", "N/A", "N/A", 0, 0, 0]
                row_data = commande_info + article_info + commande_fin_info
                ws.append(row_data)
            
        offset += batch_size

    # Ajuster la largeur des colonnes
    for i, col in enumerate(headers, 1):
        if i <= 7:  # Colonnes de base commande
            ws.column_dimensions[get_column_letter(i)].width = 20
        elif i <= 14:  # Colonnes articles
            ws.column_dimensions[get_column_letter(i)].width = 15
        else:  # Autres colonnes
            ws.column_dimensions[get_column_letter(i)].width = 18

    wb.save(response)
    return response 

# ============================================================================
# API VUES TEMPS RÉEL VUE 360
# ============================================================================

@staff_member_required
@login_required
def vue_360_realtime_data(request):
    """API pour les données temps réel de la vue 360"""
    from django.http import JsonResponse
    from django.utils import timezone
    from datetime import timedelta
    
    # Statistiques en temps réel
    total_commandes = Commande.objects.count()
    commandes_aujourd_hui = Commande.objects.filter(
        date_cmd__date=timezone.now().date()
    ).count()
    commandes_semaine = Commande.objects.filter(
        date_cmd__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Commandes par état
    commandes_confirmees = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True
    ).count()
    
    commandes_preparees = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_fin__isnull=True
    ).count()
    
    commandes_livrees = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée',
        etats__date_fin__isnull=True
    ).count()
    
    data = {
        'total_commandes': total_commandes,
        'commandes_aujourd_hui': commandes_aujourd_hui,
        'commandes_semaine': commandes_semaine,
        'commandes_confirmees': commandes_confirmees,
        'commandes_preparees': commandes_preparees,
        'commandes_livrees': commandes_livrees,
        'timestamp': timezone.now().isoformat()
    }
    
    return JsonResponse(data)

@staff_member_required
@login_required
def vue_360_statistics_update(request):
    """API pour la mise à jour des statistiques de la vue 360"""
    from django.http import JsonResponse
    from django.db.models import Count, Sum
    from django.utils import timezone
    from datetime import timedelta
    
    # Statistiques par région
    stats_par_region = Commande.objects.filter(
        ville__region__isnull=False
    ).values(
        'ville__region__nom_region'
    ).annotate(
        nb_commandes=Count('id'),
        total_montant=Sum('total_cmd')
    ).order_by('-nb_commandes')
    
    # Statistiques par jour (7 derniers jours)
    stats_par_jour = []
    for i in range(7):
        date = timezone.now().date() - timedelta(days=i)
        nb_commandes = Commande.objects.filter(
            date_cmd__date=date
        ).count()
        stats_par_jour.append({
            'date': date.strftime('%d/%m'),
            'nb_commandes': nb_commandes
        })
    
    data = {
        'stats_par_region': list(stats_par_region),
        'stats_par_jour': stats_par_jour
    }
    
    return JsonResponse(data)

@staff_member_required
@login_required
def vue_360_etats_tracking(request):
    """API pour le suivi des états des commandes"""
    from django.http import JsonResponse
    from commande.models import EnumEtatCmd
    
    # Récupérer tous les états disponibles
    etats = EnumEtatCmd.objects.all()
    
    # Compter les commandes par état
    stats_par_etat = []
    for etat in etats:
        nb_commandes = Commande.objects.filter(
            etats__enum_etat=etat,
            etats__date_fin__isnull=True
        ).count()
        
        if nb_commandes > 0:  # Ne retourner que les états avec des commandes
            stats_par_etat.append({
                'etat': etat.libelle,
                'nb_commandes': nb_commandes,
                'couleur': get_etat_color(etat.libelle)
            })
    
    data = {
        'stats_par_etat': stats_par_etat
    }
    
    return JsonResponse(data)

@staff_member_required
@login_required
def vue_360_panier_tracking(request):
    """API pour le suivi des paniers"""
    from django.http import JsonResponse
    from article.models import Article
    
    # Statistiques des articles les plus commandés
    articles_populaires = Article.objects.filter(
        paniers__isnull=False
    ).annotate(
        nb_commandes=Count('paniers__commande', distinct=True)
    ).order_by('-nb_commandes')[:10]
    
    # Statistiques des paniers
    total_paniers = sum(article.paniers.count() for article in Article.objects.all())
    paniers_aujourd_hui = sum(
        article.paniers.filter(
            commande__date_cmd__date=timezone.now().date()
        ).count() 
        for article in Article.objects.all()
    )
    
    data = {
        'articles_populaires': [
            {
                'nom': article.nom,
                'reference': article.reference,
                'nb_commandes': article.nb_commandes
            }
            for article in articles_populaires
        ],
        'total_paniers': total_paniers,
        'paniers_aujourd_hui': paniers_aujourd_hui
    }
    
    return JsonResponse(data)

def get_etat_color(etat_libelle):
    """Fonction utilitaire pour obtenir la couleur d'un état"""
    couleurs = {
        'Confirmée': '#10b981',  # Vert
        'Préparée': '#3b82f6',   # Bleu
        'Livrée': '#059669',      # Vert foncé
        'Annulée': '#ef4444',     # Rouge
        'Retournée': '#f59e0b',   # Orange
        'En cours de livraison': '#8b5cf6',  # Violet
        'À imprimer': '#06b6d4',  # Cyan
        'En préparation': '#f97316',  # Orange foncé
    }
    return couleurs.get(etat_libelle, '#6b7280')  # Gris par défaut 
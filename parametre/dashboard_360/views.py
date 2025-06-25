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
        response['Content-Disposition'] = 'attachment; filename="export_commandes_360.csv"'
        
        # Utiliser un writer CSV directement sur la réponse
        writer = csv.writer(response)

            # En-têtes du CSV consolidé
        headers = [
                'N°', 'Identifiant Yoozak', 'CLIENT', 'TELEPHONE', 'ADRESSE', 'VILLE', 'REGION',
                'PANIER', 'PRIX TOTAL (DH)', 'DATE COMMANDE', 'CONFIRMATION', 'DATE CONFIRMATION',
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
                
                articles_noms = ", ".join([panier.article.nom for panier in cmd.paniers.all()]) or "N/A"

                operateur_assigne_obj = cmd.etats.filter(enum_etat__libelle__icontains='Affectée').first()
                operateur_assigne_nom = operateur_assigne_obj.operateur.mail if operateur_assigne_obj and operateur_assigne_obj.operateur else "N/A"
                
                agent_confirmation_nom = confirmation_info.operateur.mail if confirmation_info and confirmation_info.operateur else "N/A"

                tarif_livraison = 0.0
                reste_a_payer = cmd.total_cmd
                date_paiement = "N/A"
                observation_livraison = piece_retournee_obj.commentaire if piece_retournee_obj else ""

                row_data = [
                    cmd.num_cmd,
                    cmd.id_yz,
                    f"{cmd.client.prenom} {cmd.client.nom}" if cmd.client else "N/A",
                    cmd.client.numero_tel if cmd.client else "N/A",
                    cmd.client.adresse if cmd.client else "N/A",
                    cmd.ville.nom if cmd.ville else "N/A",
                    cmd.ville.region.nom_region if cmd.ville and cmd.ville.region else "N/A",
                    articles_noms,
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
    response['Content-Disposition'] = 'attachment; filename="export_commandes_360.xlsx"'
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Commandes 360"

    # En-têtes Excel avec style
    headers = [
        "N°", "Identifiant Yoozak", "CLIENT", "TELEPHONE", "ADRESSE", "VILLE", "REGION",
        "PANIER", "PRIX TOTAL (DH)", "DATE COMMANDE", "CONFIRMATION", "DATE CONFIRMATION",
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
            
            # Pour le panier: Joindre les noms des articles du panier
            articles_noms = ", ".join([panier.article.nom for panier in cmd.paniers.all()]) or "N/A"

            # Opérateur Assigné: Chercher l'opérateur lié à l'état 'Affectée' ou un autre état pertinent
            operateur_assigne_obj = cmd.etats.filter(enum_etat__libelle__icontains='Affectée').first()
            operateur_assigne_nom = operateur_assigne_obj.operateur.mail if operateur_assigne_obj and operateur_assigne_obj.operateur else "N/A"
            
            # Agent Confirmation: Opérateur lié à l'état 'Confirmée'
            agent_confirmation_nom = confirmation_info.operateur.mail if confirmation_info and confirmation_info.operateur else "N/A"

            tarif_livraison = 0.0
            reste_a_payer = cmd.total_cmd
            date_paiement = "N/A"
            observation_livraison = piece_retournee_obj.commentaire if piece_retournee_obj else ""

            row_data = [
                cmd.num_cmd,
                cmd.id_yz,
                f"{cmd.client.prenom} {cmd.client.nom}" if cmd.client else "N/A",
                cmd.client.numero_tel if cmd.client else "N/A",
                cmd.client.adresse if cmd.client else "N/A",
                cmd.ville.nom if cmd.ville else "N/A",
                cmd.ville.region.nom_region if cmd.ville and cmd.ville.region else "N/A",
                articles_noms,
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
            ws.append(row_data)
            
        offset += batch_size

    # Ajuster la largeur des colonnes
    for i, col in enumerate(headers, 1):
        ws.column_dimensions[get_column_letter(i)].width = 20

    wb.save(response)
    return response 
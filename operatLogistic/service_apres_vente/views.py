from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from commande.models import Commande, EtatCommande, EnumEtatCmd, Envoi
from django.db import transaction
from datetime import datetime
import json
from article.models import Article

@login_required
@require_POST
def changer_etat_livraison(request, commande_id):
    """
    Vue générique pour changer l'état de livraison d'une commande
    par un opérateur logistique.
    """
    try:
        commande = Commande.objects.get(id=commande_id)
        operateur = request.user.profil_operateur
        
        # Vérifier que l'opérateur est bien un opérateur logistique
        if not operateur or not operateur.is_logistique:
            messages.error(request, "Vous n'avez pas les droits pour effectuer cette action.")
            return redirect('operatLogistic:detail_commande', commande_id=commande_id)
        
        nouvel_etat = request.POST.get('nouvel_etat')
        commentaire = request.POST.get('commentaire')
        
        if not nouvel_etat or not commentaire:
            messages.error(request, "L'état et le commentaire sont obligatoires.")
            return redirect('operatLogistic:detail_commande', commande_id=commande_id)

        with transaction.atomic():
            # Fermer l'état actuel s'il existe
            etat_actuel = commande.etat_actuel
            if etat_actuel:
                etat_actuel.date_fin = timezone.now()
                etat_actuel.save()

            # Créer le nouvel état
            enum_etat = EnumEtatCmd.objects.get(libelle=nouvel_etat)
            
            # Traitement spécifique selon l'état
            details_supplementaires = ""
            
            # Récupérer ou créer l'envoi en cours
            envoi = commande.envois.filter(status='en_attente').first()
            if not envoi:
                envoi = Envoi.objects.create(
                    commande=commande,
                    date_livraison_prevue=timezone.now().date(),
                    operateur=operateur
                )
            
            if nouvel_etat == 'Reportée':
                # Récupérer et valider la date de report
                date_str = request.POST.get('date_report')
                if not date_str:
                    messages.error(request, "La date de report est obligatoire.")
                    return redirect('operatLogistic:detail_commande', commande_id=commande_id)
                
                try:
                    date_report = datetime.strptime(date_str, '%Y-%m-%d').date()
                    if date_report < timezone.now().date():
                        messages.error(request, "La date de report ne peut pas être dans le passé")
                        return redirect('operatLogistic:detail_commande', commande_id=commande_id)
                    
                    # Mettre à jour l'envoi
                    envoi.reporter(date_report, commentaire, operateur)
                    
                    # Ajouter la date de report au commentaire
                    details_supplementaires = f"\n\nDate de report : {date_report.strftime('%d/%m/%Y')}"
                    details_supplementaires += "\nArticles concernés :"
                    for panier in commande.paniers.all():
                        details_supplementaires += f"\n- {panier.article.nom} (Quantité: {panier.quantite})"
                except ValueError:
                    messages.error(request, "Format de date invalide")
                    return redirect('operatLogistic:detail_commande', commande_id=commande_id)

            elif nouvel_etat == 'Livrée':
                # Marquer l'envoi comme livré
                envoi.marquer_comme_livre(operateur)
                details_supplementaires = f"\nLivraison effectuée le : {timezone.now().strftime('%d/%m/%Y à %H:%M')}"

            elif nouvel_etat == 'Annulée (SAV)':
                type_annulation = request.POST.get('type_annulation')
                if not type_annulation:
                    messages.error(request, "Le type d'annulation est obligatoire.")
                    return redirect('operatLogistic:detail_commande', commande_id=commande_id)
                
                # Annuler l'envoi
                envoi.annuler(operateur, commentaire)
                
                details_supplementaires = f"\nType d'annulation : {type_annulation}"
                
                # Réincrémenter le stock si c'est une bonne annulation
                if type_annulation == 'bonne':
                    for panier in commande.paniers.all():
                        article = panier.article
                        article.stock += panier.quantite
                        article.save()
                        details_supplementaires += f"\nStock réincrémenté pour {article.nom} : +{panier.quantite}"

            # Créer le nouvel état avec le commentaire complet
            commentaire_complet = commentaire + details_supplementaires
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=enum_etat,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=commentaire_complet
            )

            messages.success(request, f"État de la commande mis à jour : {nouvel_etat}")
            
    except Exception as e:
        messages.error(request, f"Une erreur est survenue : {str(e)}")
    
    return redirect('operatLogistic:detail_commande', commande_id=commande_id)

def _render_sav_list(request, commandes, page_title, page_subtitle):
    """Fonction utilitaire pour rendre la liste SAV avec le template standard."""
    context = {
        'commandes': commandes,
        'page_title': page_title,
        'page_subtitle': page_subtitle,
    }
    return render(request, 'operatLogistic/sav/liste_commandes_sav.html', context)

@login_required
def commandes_reportees(request):
    """Affiche les commandes dont la livraison est reportée."""
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Reportée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur',
        'envois', 'paniers__article'
    ).order_by('-etats__date_debut').distinct()
    
    # Enrichir les données pour chaque commande
    for commande in commandes:
        # Trouver l'état actuel (Reportée)
        commande.etat_actuel_sav = commande.etats.filter(
            enum_etat__libelle='Reportée',
            date_fin__isnull=True
        ).first()
        
        # Calculer le nombre d'articles dans la commande
        commande.nombre_articles = commande.paniers.count()
        
        # Trouver l'envoi associé
        commande.envoi = commande.envois.filter(status='en_attente').first()
        
        # Analyser les articles pour identifier ceux livrés partiellement (si applicable)
        commande.articles_livres_partiellement = []
        commande.articles_renvoyes = []
        
        # Chercher les informations dans les opérations liées à la livraison partielle
        from commande.models import Operation
        operation_livraison_partielle = Operation.objects.filter(
            commande=commande,
            type_operation='LIVRAISON_PARTIELLE'
        ).order_by('-date_operation').first()
        
        if operation_livraison_partielle:
            # Analyser la conclusion pour extraire les informations sur les articles
            conclusion = operation_livraison_partielle.conclusion
            
            # Identifier les articles dans la commande actuelle (ceux qui ont été livrés partiellement)
            for panier in commande.paniers.all():
                # Si l'article est encore dans la commande, c'est qu'il a été livré partiellement
                commande.articles_livres_partiellement.append({
                    'article': panier.article,
                    'quantite_livree': panier.quantite
                })
    
    return _render_sav_list(request, commandes, 'Commandes Reportées', 'Liste des livraisons reportées.')

@login_required
def commandes_livrees_partiellement(request):
    """Affiche les commandes livrées partiellement."""
    # Récupérer toutes les commandes qui ont eu une livraison partielle
    # (même si elles ont été renvoyées en préparation ensuite)
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée Partiellement'
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur',
        'envois', 'paniers__article'  # Ajouter les paniers et articles
    ).order_by('-etats__date_debut').distinct()
    
    # Enrichir les données pour chaque commande
    for commande in commandes:
        # Trouver l'état "Livrée Partiellement" le plus récent
        etat_livraison_partielle = commande.etats.filter(
            enum_etat__libelle='Livrée Partiellement'
        ).order_by('-date_debut').first()
        
        if etat_livraison_partielle:
            commande.date_livraison_partielle = etat_livraison_partielle.date_debut
            commande.commentaire_livraison_partielle = etat_livraison_partielle.commentaire
            commande.operateur_livraison = etat_livraison_partielle.operateur
        
        # Déterminer le statut actuel de la commande
        etat_actuel = commande.etats.filter(date_fin__isnull=True).first()
        if etat_actuel:
            commande.etat_actuel_sav = etat_actuel
            commande.statut_actuel = etat_actuel.enum_etat.libelle
            commande.est_renvoyee_preparation = etat_actuel.enum_etat.libelle in ['En préparation', 'À imprimer']
        else:
            commande.etat_actuel_sav = None
            commande.statut_actuel = "Inconnu"
            commande.est_renvoyee_preparation = False
        
        # Calculer le nombre d'articles dans la commande
        commande.nombre_articles = commande.paniers.count()
        
        # Trouver l'envoi associé
        commande.envoi = commande.envois.filter(status='en_attente').first()
        
        # Analyser les articles pour identifier ceux livrés partiellement
        commande.articles_livres_partiellement = []
        commande.articles_renvoyes = []
        
        # Chercher les informations dans les opérations liées à la livraison partielle
        from commande.models import Operation
        operation_livraison_partielle = Operation.objects.filter(
            commande=commande,
            type_operation='LIVRAISON_PARTIELLE'
        ).order_by('-date_operation').first()

        conclusion_content = ""
        articles_renvoyes_json = []
        if operation_livraison_partielle and operation_livraison_partielle.conclusion:
            conclusion_content = operation_livraison_partielle.conclusion

        try:
            if conclusion_content:
                parsed_conclusion = json.loads(conclusion_content)
                temp_articles_livres = []
                for item in parsed_conclusion.get('articles_livres', []):
                    try:
                        article_obj = Article.objects.get(id=item['article_id'])
                        temp_articles_livres.append({
                            'article_id': item['article_id'], # Ajout de article_id
                            'nom': article_obj.nom,
                            'reference': article_obj.reference,
                            'pointure': getattr(article_obj, 'pointure', ''),
                            'couleur': getattr(article_obj, 'couleur', ''),
                            'quantite_livree': item['quantite'],
                            'prix_unitaire': item.get('prix_unitaire', 0.0)
                        })
                    except Article.DoesNotExist:
                        temp_articles_livres.append({
                            'article_id': item.get('article_id'), # Ajout de article_id même si Article non trouvé
                            'nom': 'Inconnu',
                            'reference': '',
                            'pointure': '',
                            'couleur': '',
                            'quantite_livree': item.get('quantite', 0),
                            'prix_unitaire': item.get('prix_unitaire', 0.0)
                        })
                commande.articles_livres_partiellement = temp_articles_livres

                temp_articles_renvoyes = []
                for item in parsed_conclusion.get('recap_articles_renvoyes', []):
                    try:
                        article_obj = Article.objects.get(id=item['article_id'])
                        temp_articles_renvoyes.append({
                            'article_id': item['article_id'], # Ajout de article_id
                            'nom': article_obj.nom,
                            'reference': article_obj.reference,
                            'pointure': getattr(article_obj, 'pointure', ''),
                            'couleur': getattr(article_obj, 'couleur', ''),
                            'quantite': item.get('quantite', 0),
                            'prix_unitaire': item.get('prix_unitaire', 0.0),
                            'etat': item.get('etat', 'inconnu').lower() # Convertir en minuscules pour la cohérence
                        })
                    except Article.DoesNotExist:
                        temp_articles_renvoyes.append({
                            'article_id': item.get('article_id'), # Ajout de article_id même si Article non trouvé
                            'nom': 'Inconnu',
                            'reference': '',
                            'pointure': '',
                            'couleur': '',
                            'quantite': item.get('quantite', 0),
                            'prix_unitaire': item.get('prix_unitaire', 0.0),
                            'etat': item.get('etat', 'inconnu').lower() # Convertir en minuscules
                        })
                commande.articles_renvoyes = temp_articles_renvoyes
            else:
                commande.articles_livres_partiellement = []
                commande.articles_renvoyes = []
        except json.JSONDecodeError as e:
            commande.articles_livres_partiellement = []
            commande.articles_renvoyes = []
        except Exception as e:
            commande.articles_livres_partiellement = []
            commande.articles_renvoyes = []

        # Cette section est supprimée car les articles renvoyés et leurs états sont extraits
        # directement de la conclusion de l'opération de livraison partielle.
        # La logique de recherche de `commande_renvoi` n'est pas pertinente pour l'affichage des états
        # dans la modale de détails des articles de la commande originale.

    return _render_sav_list(request, commandes, 'Commandes Livrées Partiellement', 'Liste des livraisons partielles.')

@login_required
def commandes_livrees_avec_changement(request):
    """Affiche les commandes livrées avec des changements."""
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée avec changement',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur',
        'envois', 'paniers__article'
    ).order_by('-etats__date_debut').distinct()
    
    # Enrichir les données pour chaque commande
    for commande in commandes:
        # Trouver l'état actuel
        commande.etat_actuel_sav = commande.etats.filter(
            enum_etat__libelle='Livrée avec changement',
            date_fin__isnull=True
        ).first()
        
        # Calculer le nombre d'articles dans la commande
        commande.nombre_articles = commande.paniers.count()
    
    return _render_sav_list(request, commandes, 'Commandes Livrées avec Changement', 'Liste des livraisons avec modifications.')

@login_required
def commandes_annulees_sav(request):
    """Affiche les commandes annulées au stade de la livraison."""
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Annulée (SAV)',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur',
        'envois', 'paniers__article'
    ).order_by('-etats__date_debut').distinct()
    
    # Enrichir les données pour chaque commande
    for commande in commandes:
        # Trouver l'état actuel
        commande.etat_actuel_sav = commande.etats.filter(
            enum_etat__libelle='Annulée (SAV)',
            date_fin__isnull=True
        ).first()
        
        # Calculer le nombre d'articles dans la commande
        commande.nombre_articles = commande.paniers.count()
    
    return _render_sav_list(request, commandes, 'Commandes Annulées (SAV)', 'Liste des commandes annulées lors de la livraison.')

@login_required
def commandes_retournees(request):
    """Affiche les commandes retournées par l'opérateur logistique."""
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Retournée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur',
        'envois', 'paniers__article'
    ).order_by('-etats__date_debut').distinct()
    
    # Enrichir les données pour chaque commande
    for commande in commandes:
        # Trouver l'état actuel
        commande.etat_actuel_sav = commande.etats.filter(
            enum_etat__libelle='Retournée',
            date_fin__isnull=True
        ).first()
        
        # Calculer le nombre d'articles dans la commande
        commande.nombre_articles = commande.paniers.count()
    
    return _render_sav_list(request, commandes, 'Commandes Retournées', 'Liste des commandes retournées par l\'opérateur logistique.')

@login_required
def commandes_livrees(request):
    """Affiche les commandes livrées avec succès."""
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur',
        'envois', 'paniers__article'
    ).order_by('-etats__date_debut').distinct()
    
    # Enrichir les données pour chaque commande
    for commande in commandes:
        # Trouver l'état actuel
        commande.etat_actuel_sav = commande.etats.filter(
            enum_etat__libelle='Livrée',
            date_fin__isnull=True
        ).first()
        
        # Calculer le nombre d'articles dans la commande
        commande.nombre_articles = commande.paniers.count()
    
    return _render_sav_list(request, commandes, 'Commandes Livrées', 'Liste des commandes livrées avec succès.') 
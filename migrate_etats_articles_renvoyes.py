import json
from django.db import transaction
from django.db.models import Q
from commande.models import Commande, Operation, EtatArticleRenvoye, EnumEtatCmd
from article.models import Article # Assure-toi que cet import est correct

# Pour exécuter ce script via `manage.py runscript`
# Ajoute 'scripts' à INSTALLED_APPS si ce n'est pas déjà fait.

def run():
    print("Début de la migration des états d'articles renvoyés...")

    # Récupérer les objets EnumEtatCmd pour 'Bon état' et 'Défectueux'
    try:
        bon_etat_obj = EnumEtatCmd.objects.get(libelle='Bon état')
        defectueux_etat_obj = EnumEtatCmd.objects.get(libelle='Défectueux')
        inconnu_etat_obj = EnumEtatCmd.objects.get(libelle='Inconnu') # Assure-toi que cet état existe ou gère-le
    except EnumEtatCmd.DoesNotExist as e:
        print(f"Erreur: Un état nécessaire (Bon état, Défectueux, Inconnu) n'existe pas dans EnumEtatCmd. Veuillez les créer. Détail: {e}")
        return

    # Filtrer les opérations de type 'LIVRAISON_PARTIELLE'
    # et celles qui n'ont pas encore été traitées dans la nouvelle table
    operations_livraison_partielle = Operation.objects.filter(
        type_operation='LIVRAISON_PARTIELLE'
    ).exclude(
        # Exclure les commandes qui ont déjà des entrées dans EtatArticleRenvoye
        commande__etats_articles_renvoyes__isnull=False
    ).order_by('date_operation')

    total_operations = operations_livraison_partielle.count()
    print(f"{total_operations} opérations de livraison partielle à traiter.")

    migrated_count = 0
    failed_parses = 0
    
    with transaction.atomic():
        for i, op in enumerate(operations_livraison_partielle):
            print(f"[{i+1}/{total_operations}] Traitement de l'opération ID {op.id} pour la commande YZ-{op.commande.id_yz}...")
            
            recap_articles_renvoyes = []
            try:
                # Tenter de charger le JSON
                if op.conclusion:
                    details = json.loads(op.conclusion)
                    if 'recap_articles_renvoyes' in details:
                        recap_articles_renvoyes = details['recap_articles_renvoyes']
            except json.JSONDecodeError as e:
                print(f"  AVERTISSEMENT: Erreur de parsing JSON pour l'opération {op.id} (Commande YZ-{op.commande.id_yz}): {e}")
                failed_parses += 1
                continue # Passer à l'opération suivante si le JSON est invalide
            except TypeError as e:
                 print(f"  AVERTISSEMENT: TypeError lors du parsing JSON pour l'opération {op.id} (Commande YZ-{op.commande.id_yz}): {e}")
                 failed_parses += 1
                 continue
            except Exception as e:
                print(f"  AVERTISSEMENT: Erreur inattendue lors du traitement de l'opération {op.id} (Commande YZ-{op.commande.id_yz}): {e}")
                failed_parses += 1
                continue

            if not recap_articles_renvoyes:
                print(f"  INFO: Aucun article renvoyé trouvé dans la conclusion de l'opération {op.id}.")
                continue

            for item in recap_articles_renvoyes:
                article_id = item.get('article_id')
                etat_str = item.get('etat')
                quantite = item.get('quantite', 1)

                if not article_id or not etat_str:
                    print(f"    AVERTISSEMENT: Données manquantes (article_id ou etat) pour un article dans l'opération {op.id}.")
                    continue

                try:
                    article_obj = Article.objects.get(id=article_id)
                except Article.DoesNotExist:
                    print(f"    AVERTISSEMENT: Article avec ID {article_id} introuvable pour l'opération {op.id}. Article ignoré.")
                    continue

                etat_obj = None
                if etat_str == 'bon':
                    etat_obj = bon_etat_obj
                elif etat_str == 'defectueux':
                    etat_obj = defectueux_etat_obj
                else:
                    print(f"    AVERTISSEMENT: État '{etat_str}' non reconnu pour l'article {article_obj.nom} dans l'opération {op.id}. Utilisant 'Inconnu'.")
                    etat_obj = inconnu_etat_obj # Utiliser l'état 'Inconnu' pour les cas non gérés

                # Créer ou mettre à jour l'entrée EtatArticleRenvoye
                # Utiliser update_or_create pour éviter les doublons en cas de re-exécution
                try:
                    etat_article_renvoye, created = EtatArticleRenvoye.objects.update_or_create(
                        commande=op.commande,
                        article=article_obj,
                        defaults={
                            'etat': etat_obj,
                            'quantite': quantite
                        }
                    )
                    if created:
                        print(f"    Créé: {etat_article_renvoye}")
                    else:
                        print(f"    Mis à jour: {etat_article_renvoye}")
                    migrated_count += 1
                except Exception as e:
                    print(f"    ERREUR: Impossible de créer/mettre à jour EtatArticleRenvoye pour article {article_id} (Commande YZ-{op.commande.id_yz}): {e}")
            
    print(f"\nMigration terminée.")
    print(f"Total des entrées EtatArticleRenvoye créées/mises à jour : {migrated_count}")
    print(f"Opérations avec erreurs de parsing JSON : {failed_parses}")
    print("Veuillez vérifier les logs pour les avertissements et erreurs.")

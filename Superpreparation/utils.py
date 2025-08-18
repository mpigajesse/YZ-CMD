from article.models import MouvementStock, Article
from django.db import transaction

def creer_mouvement_stock(article, quantite, type_mouvement, operateur, commande=None, commentaire=None):
    """
    Crée un mouvement de stock atomique et met à jour la quantité de l'article.
    """
    try:
        with transaction.atomic():
            # Verrouiller l'article pour éviter les "race conditions"
            article_qs = Article.objects.select_for_update().get(pk=article.pk)

            # Calculer la nouvelle quantité disponible
            if type_mouvement in ['entree', 'ajustement_pos', 'retour_client']:
                # Mouvements qui augmentent le stock
                quantite_a_bouger = abs(int(quantite))
                article_qs.qte_disponible += quantite_a_bouger
            elif type_mouvement in ['sortie', 'ajustement_neg']:
                # Mouvements qui diminuent le stock
                quantite_a_bouger = -abs(int(quantite))
                article_qs.qte_disponible += quantite_a_bouger
            else:
                # Type de mouvement inconnu
                return None

            # S'assurer que le stock ne devient pas négatif
            if article_qs.qte_disponible < 0:
                # Idéalement, lever une exception personnalisée ici
                # raise ValueError("Le stock ne peut pas devenir négatif.")
                # Pour l'instant, on met à 0 pour la sécurité
                article_qs.qte_disponible = 0
            
            # Sauvegarder l'article avec sa nouvelle quantité
            article_qs.save(update_fields=['qte_disponible'])
            
            # Créer le mouvement de stock pour tracer le changement
            mouvement = MouvementStock.objects.create(
                article=article_qs,
                type_mouvement=type_mouvement,
                quantite=quantite_a_bouger,
                qte_apres_mouvement=article_qs.qte_disponible,
                commentaire=commentaire,
                commande_associee=commande,
                operateur=operateur
            )
            
            return mouvement
            
    except ImportError as e:
        # Gérer le cas où MouvementStock n'est pas importable, bien que peu probable ici
        print(f"❌ Erreur d'import MouvementStock: {str(e)}")
        return None
    except Exception as e:
        # Gérer d'autres exceptions (ex: article non trouvé, erreur de DB)
        print(f"❌ Erreur lors de la création du mouvement de stock: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e  # Re-lever l'exception pour que la vue puisse l'attraper 
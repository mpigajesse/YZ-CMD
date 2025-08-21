from article.models import MouvementStock, Article, VarianteArticle
from django.db import transaction
from django.core.exceptions import ValidationError

def creer_mouvement_stock(article, quantite, type_mouvement, operateur, commande=None, commentaire=None, variante=None):
    """
    Crée un mouvement de stock atomique et met à jour la quantité des variantes de l'article.
    Compatible avec le nouveau modèle Article + VarianteArticle.
    """
    try:
        with transaction.atomic():
            # Verrouiller l'article pour éviter les "race conditions"
            article_qs = Article.objects.select_for_update().get(pk=article.pk)

            # Calculer la quantité à déplacer
            if type_mouvement in ['entree', 'ajustement_pos', 'retour_client']:
                # Mouvements qui augmentent le stock
                quantite_a_bouger = abs(int(quantite))
            elif type_mouvement in ['sortie', 'ajustement_neg']:
                # Mouvements qui diminuent le stock
                quantite_a_bouger = -abs(int(quantite))
            else:
                # Type de mouvement inconnu
                raise ValidationError(f"Type de mouvement inconnu : {type_mouvement}")

            # Déterminer sur quelle variante appliquer le mouvement
            if variante:
                # Mouvement sur une variante spécifique
                variante_obj = VarianteArticle.objects.select_for_update().get(
                    pk=variante.pk, article=article_qs
                )
                variantes_a_mettre_a_jour = [variante_obj]
            else:
                # Mouvement global : répartir sur toutes les variantes actives
                variantes_a_mettre_a_jour = list(
                    VarianteArticle.objects.select_for_update().filter(
                        article=article_qs, actif=True
                    ).order_by('-qte_disponible')  # Commencer par les plus stockées
                )
                
                if not variantes_a_mettre_a_jour:
                    # Si aucune variante, créer une variante par défaut
                    from article.models import Couleur, Pointure
                    couleur_defaut, _ = Couleur.objects.get_or_create(nom="Standard", defaults={'actif': True})
                    pointure_defaut, _ = Pointure.objects.get_or_create(pointure="Unique", defaults={'actif': True})
                    
                    variante_defaut = VarianteArticle.objects.create(
                        article=article_qs,
                        couleur=couleur_defaut,
                        pointure=pointure_defaut,
                        qte_disponible=0,
                        actif=True
                    )
                    variantes_a_mettre_a_jour = [variante_defaut]

            # Appliquer le mouvement aux variantes
            quantite_restante = quantite_a_bouger
            qte_totale_apres = 0
            
            for variante_obj in variantes_a_mettre_a_jour:
                if quantite_restante == 0:
                    break
                    
                if quantite_a_bouger > 0:
                    # Entrée de stock : ajouter tout à la première variante
                    variante_obj.qte_disponible += quantite_restante
                    quantite_restante = 0
                else:
                    # Sortie de stock : déduire de cette variante (sans aller en négatif)
                    qte_a_retirer = min(variante_obj.qte_disponible, -quantite_restante)
                    variante_obj.qte_disponible -= qte_a_retirer
                    quantite_restante += qte_a_retirer
                
                # S'assurer que la quantité ne devient jamais négative
                if variante_obj.qte_disponible < 0:
                    variante_obj.qte_disponible = 0
                
                variante_obj.save(update_fields=['qte_disponible'])
                qte_totale_apres += variante_obj.qte_disponible
            
            # Si on ne peut pas satisfaire toute la sortie, lever une exception
            if quantite_a_bouger < 0 and quantite_restante < 0:
                raise ValidationError(
                    f"Stock insuffisant : impossible de retirer {abs(quantite_a_bouger)} unités. "
                    f"Stock disponible : {qte_totale_apres + abs(quantite_restante)}"
                )
            
            # Créer le mouvement de stock pour tracer le changement
            mouvement = MouvementStock.objects.create(
                article=article_qs,
                variante=variante if len(variantes_a_mettre_a_jour) == 1 else None,
                type_mouvement=type_mouvement,
                quantite=quantite_a_bouger,
                qte_apres_mouvement=qte_totale_apres,
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
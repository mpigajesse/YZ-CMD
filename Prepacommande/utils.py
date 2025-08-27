from article.models import MouvementStock, Article, VarianteArticle
from django.db import transaction
from django.core.exceptions import ValidationError

def creer_mouvement_stock(article, quantite, type_mouvement, operateur, commande=None, commentaire=None, variante=None):
    """
    Crée un mouvement de stock atomique en ajustant les variantes de l'article.
    Aligné avec la logique de Superpreparation (pas d'écriture sur Article.qte_disponible).
    """
    try:
        with transaction.atomic():
            article_qs = Article.objects.select_for_update().get(pk=article.pk)

            # Normaliser la quantité selon le type
            if type_mouvement in ['entree', 'ajustement_pos', 'retour_client']:
                quantite_a_bouger = abs(int(quantite))
            elif type_mouvement in ['sortie', 'ajustement_neg']:
                quantite_a_bouger = -abs(int(quantite))
            else:
                raise ValidationError(f"Type de mouvement inconnu : {type_mouvement}")

            # Cible: variante spécifique ou répartition globale
            if variante:
                variante_obj = VarianteArticle.objects.select_for_update().get(
                    pk=variante.pk, article=article_qs
                )
                variantes_a_mettre_a_jour = [variante_obj]
            else:
                variantes_a_mettre_a_jour = list(
                    VarianteArticle.objects.select_for_update()
                    .filter(article=article_qs, actif=True)
                    .order_by('-qte_disponible')
                )
                if not variantes_a_mettre_a_jour:
                    # Aucune variante existante: créer une variante par défaut
                    from article.models import Couleur, Pointure
                    couleur_defaut, _ = Couleur.objects.get_or_create(nom="Standard", defaults={'actif': True})
                    pointure_defaut, _ = Pointure.objects.get_or_create(pointure="Unique", defaults={'actif': True})
                    variante_defaut = VarianteArticle.objects.create(
                        article=article_qs,
                        couleur=couleur_defaut,
                        pointure=pointure_defaut,
                        qte_disponible=0,
                        actif=True,
                    )
                    variantes_a_mettre_a_jour = [variante_defaut]

            # Appliquer le mouvement
            quantite_restante = quantite_a_bouger
            qte_totale_apres = 0
            for var in variantes_a_mettre_a_jour:
                if quantite_restante == 0:
                    break
                if quantite_a_bouger > 0:
                    var.qte_disponible += quantite_restante
                    quantite_restante = 0
                else:
                    retirer = min(var.qte_disponible, -quantite_restante)
                    var.qte_disponible -= retirer
                    quantite_restante += retirer
                if var.qte_disponible < 0:
                    var.qte_disponible = 0
                var.save(update_fields=['qte_disponible'])
                qte_totale_apres += var.qte_disponible

            if quantite_a_bouger < 0 and quantite_restante < 0:
                raise ValidationError("Stock insuffisant pour effectuer la sortie demandée")

            mouvement = MouvementStock.objects.create(
                article=article_qs,
                variante=variante if len(variantes_a_mettre_a_jour) == 1 else None,
                type_mouvement=type_mouvement,
                quantite=quantite_a_bouger,
                qte_apres_mouvement=qte_totale_apres,
                commentaire=commentaire,
                commande_associee=commande,
                operateur=operateur,
            )
            return mouvement

    except Exception as e:
        print(f"❌ Erreur lors de la création du mouvement de stock (Prépa): {str(e)}")
        import traceback
        traceback.print_exc()
        raise e
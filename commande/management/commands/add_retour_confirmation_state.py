from django.core.management.base import BaseCommand
from commande.models import EnumEtatCmd

class Command(BaseCommand):
    help = 'Ajoute l\'état de commande "Retour Confirmation" s\'il n\'existe pas déjà'

    def handle(self, *args, **options):
        # Définir les détails du nouvel état
        nouvel_etat_libelle = "Retour Confirmation"
        
        # Valeurs pour les autres champs
        nouvel_etat_ordre = 45  # S'insère entre "Confirmée" (40) et "Erronée" (50)
        nouvel_etat_couleur = "#F59E0B"  # Couleur ambre pour indiquer un avertissement/retour

        # Vérifier si l'état existe déjà
        if EnumEtatCmd.objects.filter(libelle=nouvel_etat_libelle).exists():
            self.stdout.write(self.style.WARNING(f'L\'état "{nouvel_etat_libelle}" existe déjà.'))
        else:
            # Créer le nouvel état
            EnumEtatCmd.objects.create(
                libelle=nouvel_etat_libelle,
                ordre=nouvel_etat_ordre,
                couleur=nouvel_etat_couleur
            )
            self.stdout.write(self.style.SUCCESS(f'L\'état "{nouvel_etat_libelle}" a été ajouté avec succès.')) 
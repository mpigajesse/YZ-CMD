from django.core.management.base import BaseCommand
from commande.models import Commande, EnumEtatCmd, EtatCommande
from django.utils import timezone


class Command(BaseCommand):
    help = 'Corrige les commandes qui n\'ont pas d\'état en leur attribuant "Non affectée"'

    def handle(self, *args, **options):
        # Récupérer l'état "Non affectée"
        try:
            enum_non_affectee = EnumEtatCmd.objects.get(libelle='Non affectée')
        except EnumEtatCmd.DoesNotExist:
            self.stdout.write(self.style.ERROR('État "Non affectée" non trouvé. Création en cours...'))
            enum_non_affectee = EnumEtatCmd.objects.create(
                libelle='Non affectée',
                ordre=1,
                couleur='#EF4444'
            )
            self.stdout.write(self.style.SUCCESS('État "Non affectée" créé'))
        
        # Trouver toutes les commandes sans état actuel
        commandes_sans_etat = []
        total_commandes = Commande.objects.count()
        
        self.stdout.write(f'Vérification de {total_commandes} commandes...')
        
        for commande in Commande.objects.all():
            if not commande.etat_actuel:
                commandes_sans_etat.append(commande)
        
        self.stdout.write(f'Trouvé {len(commandes_sans_etat)} commandes sans état')
        
        if not commandes_sans_etat:
            self.stdout.write(self.style.SUCCESS('Toutes les commandes ont déjà un état !'))
            return
        
        # Demander confirmation
        if not self.confirm_action(len(commandes_sans_etat)):
            self.stdout.write('Opération annulée.')
            return
        
        # Créer les états manquants
        created_count = 0
        for commande in commandes_sans_etat:
            try:
                EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=enum_non_affectee,
                    date_debut=timezone.now(),
                    operateur=None,
                    commentaire="État créé automatiquement par correction"
                )
                created_count += 1
                if created_count % 50 == 0:
                    self.stdout.write(f'Traité {created_count}/{len(commandes_sans_etat)} commandes...')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erreur pour commande {commande.num_cmd}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'✅ {created_count} états créés avec succès !'))
        
        # Vérification finale
        commandes_toujours_sans_etat = []
        for commande in Commande.objects.all():
            if not commande.etat_actuel:
                commandes_toujours_sans_etat.append(commande)
        
        if commandes_toujours_sans_etat:
            self.stdout.write(self.style.WARNING(f'⚠️ {len(commandes_toujours_sans_etat)} commandes n\'ont toujours pas d\'état'))
        else:
            self.stdout.write(self.style.SUCCESS('🎉 Toutes les commandes ont maintenant un état !'))
    
    def confirm_action(self, count):
        """Demande confirmation à l'utilisateur"""
        response = input(f'Voulez-vous créer {count} états "Non affectée" ? (oui/non): ')
        return response.lower() in ['oui', 'o', 'yes', 'y']

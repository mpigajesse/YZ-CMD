from django.core.management.base import BaseCommand
from commande.models import Commande, EnumEtatCmd, EtatCommande


class Command(BaseCommand):
    help = 'Diagnostique les états des commandes'

    def handle(self, *args, **options):
        self.stdout.write('=== DIAGNOSTIC DES ÉTATS ===')
        self.stdout.write(f'Nombre total de commandes: {Commande.objects.count()}')
        self.stdout.write(f'Nombre total d\'EnumEtatCmd: {EnumEtatCmd.objects.count()}')
        self.stdout.write(f'Nombre total d\'EtatCommande: {EtatCommande.objects.count()}')
        self.stdout.write('')

        self.stdout.write('=== EnumEtatCmd existants ===')
        for enum_etat in EnumEtatCmd.objects.all():
            self.stdout.write(f'- {enum_etat.libelle} (ID: {enum_etat.id})')
        self.stdout.write('')

        self.stdout.write('=== Commandes récentes (5 dernières) ===')
        for cmd in Commande.objects.order_by('-id')[:5]:
            etat_actuel = cmd.etat_actuel
            if etat_actuel:
                self.stdout.write(f'Commande {cmd.num_cmd}: État = {etat_actuel.enum_etat.libelle}')
            else:
                self.stdout.write(f'Commande {cmd.num_cmd}: AUCUN ÉTAT ACTUEL')
                # Vérifier s'il y a des états pour cette commande
                etats_count = cmd.etats.count()
                self.stdout.write(f'  -> Nombre d\'états total: {etats_count}')
                if etats_count > 0:
                    dernier_etat = cmd.etats.first()
                    self.stdout.write(f'  -> Dernier état: {dernier_etat.enum_etat.libelle} (date_fin: {dernier_etat.date_fin})')
                    
        self.stdout.write('')
        self.stdout.write('=== Test de la propriété etat_actuel ===')
        # Tester la logique de etat_actuel
        cmd_test = Commande.objects.first()
        if cmd_test:
            self.stdout.write(f'Commande test: {cmd_test.num_cmd}')
            etats_actifs = cmd_test.etats.filter(date_fin__isnull=True)
            self.stdout.write(f'États actifs (date_fin=NULL): {etats_actifs.count()}')
            for etat in etats_actifs:
                self.stdout.write(f'  -> {etat.enum_etat.libelle} (ID: {etat.id}, date_debut: {etat.date_debut})')
        
        self.stdout.write('')
        self.stdout.write('=== Commandes synchronisées récemment ===')
        # Vérifier spécifiquement les commandes synchronisées
        cmd_sync = Commande.objects.filter(origine='SYNC').order_by('-id')[:3]
        for cmd in cmd_sync:
            self.stdout.write(f'Commande sync {cmd.num_cmd}:')
            self.stdout.write(f'  -> etat_actuel: {cmd.etat_actuel}')
            self.stdout.write(f'  -> Nombre d\'états: {cmd.etats.count()}')
            for etat in cmd.etats.all():
                self.stdout.write(f'     - {etat.enum_etat.libelle} (date_fin: {etat.date_fin})')

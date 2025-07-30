from django.core.management.base import BaseCommand
from django.utils import timezone
from commande.models import Commande, EnumEtatCmd, EtatCommande


class Command(BaseCommand):
    help = 'Assigne des états par défaut aux commandes existantes qui n\'ont pas d\'état'

    def add_arguments(self, parser):
        parser.add_argument(
            '--default-state',
            type=str,
            default='En attente',
            help='L\'état par défaut à assigner aux commandes sans état (défaut: "En attente")'
        )

    def handle(self, *args, **options):
        default_state_libelle = options['default_state']
        
        try:
            # Récupérer l'état par défaut
            default_enum_etat = EnumEtatCmd.objects.get(libelle=default_state_libelle)
        except EnumEtatCmd.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ L\'état "{default_state_libelle}" n\'existe pas dans EnumEtatCmd')
            )
            self.stdout.write('États disponibles:')
            for etat in EnumEtatCmd.objects.all():
                self.stdout.write(f'  - {etat.libelle}')
            return

        # Trouver les commandes sans état
        commandes_sans_etat = Commande.objects.filter(etats__isnull=True)
        total_commandes = commandes_sans_etat.count()
        
        if total_commandes == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ Toutes les commandes ont déjà des états assignés')
            )
            return

        self.stdout.write(f'🔍 Trouvé {total_commandes} commandes sans état')
        
        # Demander confirmation
        if not options.get('verbosity') == 0:
            confirm = input(f'Voulez-vous assigner l\'état "{default_state_libelle}" à ces {total_commandes} commandes ? [y/N]: ')
            if confirm.lower() not in ['y', 'yes', 'o', 'oui']:
                self.stdout.write('❌ Opération annulée')
                return

        created_count = 0
        error_count = 0

        # Assigner l'état par défaut à chaque commande sans état
        for commande in commandes_sans_etat:
            try:
                EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=default_enum_etat,
                    date_debut=commande.date_creation,  # Utiliser la date de création de la commande
                    commentaire=f'État assigné automatiquement lors de la migration des données existantes'
                )
                created_count += 1
                
                if created_count % 100 == 0:  # Afficher le progrès tous les 100
                    self.stdout.write(f'📊 Progression: {created_count}/{total_commandes}')
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Erreur pour la commande {commande.num_cmd}: {str(e)}')
                )

        # Résumé
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'✨ Terminé! {created_count} états créés avec succès'
            )
        )
        
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f'⚠️  {error_count} erreurs rencontrées')
            )

        # Vérification finale
        remaining_without_states = Commande.objects.filter(etats__isnull=True).count()
        self.stdout.write(
            self.style.HTTP_INFO(
                f'📊 Commandes restantes sans état: {remaining_without_states}'
            )
        ) 
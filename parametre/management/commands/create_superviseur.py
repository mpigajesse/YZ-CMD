from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, User
from parametre.models import Operateur


class Command(BaseCommand):
    help = 'Crée le groupe superviseur et assigne des utilisateurs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-group',
            action='store_true',
            help='Créer le groupe superviseur s\'il n\'existe pas',
        )
        parser.add_argument(
            '--assign-users',
            nargs='+',
            type=str,
            help='Liste des noms d\'utilisateur à assigner au groupe superviseur',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Lister tous les superviseurs actuels',
        )
        parser.add_argument(
            '--check-consistency',
            action='store_true',
            help='Vérifier la cohérence des groupes pour tous les opérateurs',
        )
        parser.add_argument(
            '--sync-all',
            action='store_true',
            help='Synchroniser tous les groupes Django avec les types d\'opérateur',
        )

    def handle(self, *args, **options):
        if options['create_group']:
            self.create_superviseur_group()
        
        if options['assign_users']:
            self.assign_users_to_superviseur(options['assign_users'])
        
        if options['list']:
            self.list_superviseurs()
        
        if options['check_consistency']:
            self.check_all_consistency()
        
        if options['sync_all']:
            self.sync_all_groups()
        
        # Si aucune option n'est spécifiée, afficher l'aide
        if not any([options['create_group'], options['assign_users'], options['list'], options['check_consistency'], options['sync_all']]):
            self.stdout.write(
                self.style.WARNING('Aucune action spécifiée. Utilisez --help pour voir les options disponibles.')
            )

    def create_superviseur_group(self):
        """Crée le groupe superviseur s'il n'existe pas"""
        group, created = Group.objects.get_or_create(name='superviseur')
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Groupe "superviseur" créé avec succès (ID: {group.id})')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'ℹ️  Groupe "superviseur" existe déjà (ID: {group.id})')
            )
        
        return group

    def assign_users_to_superviseur(self, usernames):
        """Assigne des utilisateurs au groupe superviseur"""
        success_count = 0
        
        for username in usernames:
            try:
                user = User.objects.get(username=username)
                
                # Utiliser la nouvelle méthode du modèle pour créer le superviseur
                operateur = Operateur.create_superviseur_from_user(user)
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Utilisateur {username} assigné au groupe superviseur')
                )
                success_count += 1
                
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Utilisateur {username} non trouvé')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erreur lors de l\'assignation de {username}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ {success_count}/{len(usernames)} utilisateur(s) assigné(s) avec succès')
        )

    def list_superviseurs(self):
        """Liste tous les superviseurs"""
        try:
            superviseur_group = Group.objects.get(name='superviseur')
            users = superviseur_group.user_set.all()
            
            self.stdout.write(
                self.style.SUCCESS(f'\n👥 Utilisateurs dans le groupe superviseur ({users.count()}):')
            )
            
            for user in users:
                try:
                    operateur = user.profil_operateur
                    self.stdout.write(
                        f'  - {user.username} ({operateur.nom_complet}) - {operateur.get_type_operateur_display()}'
                    )
                except Operateur.DoesNotExist:
                    self.stdout.write(
                        f'  - {user.username} (pas de profil Operateur)'
                    )
            
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('ℹ️  Le groupe superviseur n\'existe pas encore. Utilisez --create-group pour le créer.')
            )
    
    def check_all_consistency(self):
        """Vérifie la cohérence de tous les opérateurs"""
        operateurs = Operateur.objects.all()
        total = operateurs.count()
        consistent = 0
        inconsistent = 0
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🔍 Vérification de la cohérence pour {total} opérateur(s)...')
        )
        
        for operateur in operateurs:
            is_consistent, message = operateur.check_group_consistency()
            if is_consistent:
                consistent += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {operateur.user.username}: {message}')
                )
            else:
                inconsistent += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ {operateur.user.username}: {message}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n📊 Résumé: {consistent} cohérent(s), {inconsistent} incohérent(s)')
        )
    
    def sync_all_groups(self):
        """Synchronise tous les groupes Django"""
        operateurs = Operateur.objects.all()
        total = operateurs.count()
        synced = 0
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🔄 Synchronisation des groupes pour {total} opérateur(s)...')
        )
        
        for operateur in operateurs:
            try:
                operateur.sync_django_groups()
                synced += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {operateur.user.username}: Groupes synchronisés')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ {operateur.user.username}: Erreur lors de la synchronisation - {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ {synced}/{total} opérateur(s) synchronisé(s) avec succès')
        )

from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
import json


class Command(BaseCommand):
    help = 'Nettoie les sessions problématiques créées par le middleware de redirection'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nom d\'utilisateur spécifique à nettoyer',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Nettoyer toutes les sessions problématiques',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        all_sessions = options.get('all')
        
        if not username and not all_sessions:
            self.stdout.write(
                self.style.ERROR('Vous devez spécifier --username ou --all')
            )
            return

        sessions_cleaned = 0
        sessions_checked = 0
        
        # Parcourir toutes les sessions actives
        for session in Session.objects.all():
            sessions_checked += 1
            try:
                session_data = session.get_decoded()
                
                # Chercher les clés de redirection du middleware
                middleware_keys = [
                    key for key in session_data.keys() 
                    if key.startswith('middleware_redirect_')
                ]
                
                if middleware_keys:
                    # Si un utilisateur spécifique est demandé, vérifier
                    if username:
                        user_id = session_data.get('_auth_user_id')
                        if user_id:
                            try:
                                user = User.objects.get(id=user_id)
                                if user.username != username:
                                    continue
                            except User.DoesNotExist:
                                continue
                    
                    # Nettoyer les clés problématiques
                    for key in middleware_keys:
                        del session_data[key]
                    
                    # Sauvegarder la session modifiée
                    session.session_data = session.encode(session_data)
                    session.save()
                    sessions_cleaned += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Session nettoyée: {session.session_key} (clés: {", ".join(middleware_keys)})'
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'Erreur lors du traitement de la session {session.session_key}: {e}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Terminé! {sessions_cleaned} session(s) nettoyée(s) sur {sessions_checked} vérifiée(s).'
            )
        )
        
        if sessions_cleaned == 0:
            self.stdout.write(
                self.style.WARNING('Aucune session problématique trouvée.')
            ) 
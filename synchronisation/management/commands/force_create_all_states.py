from django.core.management.base import BaseCommand
from commande.models import Commande, EnumEtatCmd, EtatCommande
from synchronisation.models import GoogleSheetConfig
from synchronisation.google_sheet_sync import GoogleSheetSync
from django.utils import timezone


class Command(BaseCommand):
    help = 'Force la création d\'états pour toutes les commandes selon leur statut dans la feuille Google Sheets'

    def handle(self, *args, **options):
        self.stdout.write('🔄 FORÇAGE DE LA CRÉATION D\'ÉTATS POUR TOUTES LES COMMANDES')
        self.stdout.write('=' * 60)
        
        try:
            # Récupérer la configuration
            config = GoogleSheetConfig.objects.first()
            if not config:
                self.stdout.write(self.style.ERROR('❌ Aucune configuration Google Sheets trouvée'))
                return
            
            self.stdout.write(f'📋 Configuration: {config.sheet_name}')
            
            # Créer une instance de synchronisation
            sync = GoogleSheetSync(config, verbose=False)
            
            # Authentification
            self.stdout.write('🔐 Authentification...')
            client = sync.authenticate()
            if not client:
                self.stdout.write(self.style.ERROR('❌ Échec de l\'authentification'))
                return
            
            # Récupérer la feuille
            worksheet = sync.get_sheet(client)
            if not worksheet:
                self.stdout.write(self.style.ERROR('❌ Échec de récupération de la feuille'))
                return
            
            # Récupérer toutes les données
            all_data = worksheet.get_all_values()
            if not all_data:
                self.stdout.write(self.style.ERROR('❌ Aucune donnée trouvée'))
                return
            
            headers = all_data[0]
            rows = all_data[1:]
            
            # Trouver la colonne Statut
            status_pos = None
            for i, header in enumerate(headers):
                if 'statut' in header.lower():
                    status_pos = i
                    break
            
            if status_pos is None:
                self.stdout.write(self.style.ERROR('❌ Colonne Statut non trouvée'))
                return
            
            self.stdout.write(f'✅ Colonne Statut trouvée à la position {status_pos + 1}')
            
            # Créer un dictionnaire commande -> statut
            commande_statuts = {}
            for row in rows:
                if len(row) > status_pos:
                    num_cmd = row[0].strip() if row[0] else None
                    statut = row[status_pos].strip() if row[status_pos] else None
                    if num_cmd and statut:
                        commande_statuts[num_cmd] = statut
            
            self.stdout.write(f'📊 {len(commande_statuts)} commandes avec statuts trouvées dans la feuille')
            
            # Analyser les statuts uniques
            statuts_uniques = set(commande_statuts.values())
            self.stdout.write(f'🔍 Statuts uniques: {", ".join(sorted(statuts_uniques))}')
            
            # Vérifier que tous les EnumEtatCmd existent
            for statut in statuts_uniques:
                mapped_statut = sync._map_status(statut)
                if mapped_statut:
                    enum_etat, created = EnumEtatCmd.objects.get_or_create(
                        libelle=mapped_statut,
                        defaults={'ordre': 999, 'couleur': '#6B7280'}
                    )
                    if created:
                        self.stdout.write(f'✅ EnumEtatCmd créé: {mapped_statut}')
                else:
                    self.stdout.write(self.style.WARNING(f'⚠️ Statut non reconnu: {statut}'))
            
            # Traiter chaque commande
            total_commandes = Commande.objects.count()
            commandes_traitees = 0
            etats_crees = 0
            erreurs = 0
            
            self.stdout.write(f'\n🔄 Traitement de {total_commandes} commandes...')
            
            for commande in Commande.objects.all():
                try:
                    # Vérifier si la commande a un statut dans la feuille
                    statut_from_sheet = commande_statuts.get(commande.num_cmd)
                    
                    if not statut_from_sheet:
                        self.stdout.write(f'⚠️ Commande {commande.num_cmd} non trouvée dans la feuille')
                        continue
                    
                    # Mapper le statut
                    mapped_statut = sync._map_status(statut_from_sheet)
                    if not mapped_statut:
                        self.stdout.write(f'⚠️ Statut non reconnu pour {commande.num_cmd}: {statut_from_sheet}')
                        continue
                    
                    # Vérifier si la commande a déjà un état actuel
                    etat_actuel = commande.etat_actuel
                    if etat_actuel and etat_actuel.enum_etat.libelle == mapped_statut:
                        # L'état est déjà correct
                        continue
                    
                    # Créer le nouvel état
                    try:
                        # Terminer l'état actuel s'il existe
                        if etat_actuel:
                            etat_actuel.terminer_etat(None)
                        
                        # Récupérer l'énumération d'état
                        enum_etat = EnumEtatCmd.objects.get(libelle=mapped_statut)
                        
                        # Créer le nouvel état
                        nouvel_etat = EtatCommande.objects.create(
                            commande=commande,
                            enum_etat=enum_etat,
                            date_debut=timezone.now(),
                            operateur=None,
                            commentaire=f"État forcé depuis Google Sheets: {statut_from_sheet}"
                        )
                        
                        etats_crees += 1
                        if etats_crees % 50 == 0:
                            self.stdout.write(f'✅ {etats_crees} états créés...')
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'❌ Erreur pour {commande.num_cmd}: {e}'))
                        erreurs += 1
                    
                    commandes_traitees += 1
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Erreur générale pour {commande.num_cmd}: {e}'))
                    erreurs += 1
            
            # Résumé final
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.SUCCESS(f'🎉 TRAITEMENT TERMINÉ !'))
            self.stdout.write(f'📊 Commandes traitées: {commandes_traitees}')
            self.stdout.write(f'✅ États créés: {etats_crees}')
            if erreurs > 0:
                self.stdout.write(self.style.WARNING(f'⚠️ Erreurs: {erreurs}'))
            
            # Vérification finale
            total_etats = EtatCommande.objects.count()
            self.stdout.write(f'📈 Total états dans la base: {total_etats}')
            
            # Vérifier que toutes les commandes ont maintenant un état
            cmd_sans_etat = Commande.objects.filter(etats__isnull=True).count()
            if cmd_sans_etat == 0:
                self.stdout.write(self.style.SUCCESS('🎯 Toutes les commandes ont maintenant un état !'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ {cmd_sans_etat} commandes n\'ont toujours pas d\'état'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur générale: {str(e)}'))
            import traceback
            traceback.print_exc()

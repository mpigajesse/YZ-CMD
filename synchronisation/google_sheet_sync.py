import os
import gspread
from google.oauth2.service_account import Credentials
from django.conf import settings
from django.utils import timezone
from client.models import Client
from commande.models import Commande, EtatCommande, EnumEtatCmd, Panier
from parametre.models import Operateur, Ville, Region
from synchronisation.models import SyncLog, GoogleSheetConfig
import pandas as pd
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Q
import re

class GoogleSheetSync:
    """Classe pour gérer la synchronisation avec Google Sheets"""
    
    def __init__(self, sheet_config, triggered_by="admin", verbose=False):
        self.sheet_config = sheet_config
        self.triggered_by = triggered_by
        self.verbose = verbose  # Contrôle l'affichage des messages détaillés
        self.records_imported = 0
        self.errors = []
        self.warnings = []
        
        # Nouveaux attributs pour les détails d'exécution
        self.start_time = None
        self.end_time = None
        self.total_rows = 0
        self.processed_rows = 0
        self.skipped_rows = 0
        self.sheet_title = ""
        self.execution_details = {}
        
        # Nouveaux compteurs pour distinguer les types d'opérations
        self.new_orders_created = 0      # Nouvelles commandes créées
        self.existing_orders_updated = 0  # Commandes existantes mises à jour
        self.existing_orders_skipped = 0  # Commandes existantes inchangées
        self.duplicate_orders_found = 0   # Commandes en double détectées
        self.protected_orders_count = 0   # Commandes protégées contre la régression d'état
    
    def _log(self, message, level="info"):
        """Log conditionnel selon le mode verbose"""
        if self.verbose:
            print(f"🔄 {message}")
        # Toujours enregistrer les erreurs dans self.errors
        if level == "error":
            self.errors.append(message)
        
    def authenticate(self):
        """Authentification avec l'API Google Sheets"""
        try:
            scope = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            credentials = Credentials.from_service_account_file(
                settings.GOOGLE_CREDENTIALS_FILE, 
                scopes=scope
            )
            client = gspread.authorize(credentials)
            return client
        except Exception as e:
            self.errors.append(f"Erreur d'authentification: {str(e)}")
            return None
    
    def get_sheet(self, client):
        """Récupère la feuille Google Sheet"""
        try:
            # Ouvrir par URL ou par clé selon ce qui est fourni
            if 'docs.google.com' in self.sheet_config.sheet_url:
                spreadsheet = client.open_by_url(self.sheet_config.sheet_url)
            else:
                spreadsheet = client.open_by_key(self.sheet_config.sheet_url)
                
            # Sélectionner la feuille par nom
            worksheet = spreadsheet.worksheet(self.sheet_config.sheet_name)
            return worksheet
        except Exception as e:
            self.errors.append(f"Erreur d'accès à la feuille: {str(e)}")
            return None
    
    # Méthode parse_product supprimée car plus nécessaire avec la refactorisation des articles
    # Les produits sont maintenant stockés directement dans la commande sans parsing complexe
    
    def _parse_date(self, date_str):
        """Parse une date depuis différents formats possibles"""
        if not date_str:
            return timezone.now().date()
        
        # Formats de date possibles
        date_formats = [
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y-%m-%d',
            '%d/%m/%y',
            '%d-%m-%y',
            '%Y/%m/%d',
            '%m/%d/%Y',
            '%m-%d-%Y',
        ]
        
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), date_format)
                return parsed_date.date()
            except ValueError:
                continue
        
        # Si aucun format ne fonctionne, retourner la date actuelle
        self.errors.append(f"Format de date non reconnu: {date_str}")
        return timezone.now().date()
    
    @staticmethod
    def clean_phone_number(phone_str):
        """Nettoie et valide un numéro de téléphone"""
        if not phone_str:
            return ''
        
        # Convertir en string et nettoyer
        phone = str(phone_str).strip()
        
        # Supprimer les caractères non numériques courants (espaces, tirets, points, parenthèses)
        phone = re.sub(r'[\s\-\.\(\)\+]', '', phone)
        
        # Limiter à 30 caractères maximum (limite du modèle Client)
        if len(phone) > 30:
            phone = phone[:30]
        
        return phone
    
    def _clean_phone_number(self, phone_str):
        """Nettoie et valide un numéro de téléphone avec logging des warnings"""
        phone = self.clean_phone_number(phone_str)
        
        # Log warning si le numéro a été tronqué
        if phone_str and len(str(phone_str).strip()) > 30:
            self.warnings.append(f"Numéro de téléphone tronqué: {phone_str} -> {phone}")
        
        return phone
    
    def process_row(self, row_data, headers):
        """Traite une ligne de données - nouvelles commandes uniquement, évite les doublons"""
        try:
            # Créer un dictionnaire avec les données de la ligne
            data = dict(zip(headers, row_data))
            
            # Debug: Afficher les données reçues
            if self.verbose:
                print(f"🔍 Données reçues pour la ligne : {data}")
            
            # Vérifier si la commande existe déjà - essayer différentes variantes de clés
            order_number = data.get('N° Commande') or data.get('Numéro') or data.get('N°Commande') or data.get('Numero')
            if not order_number or not order_number.strip():
                self._log(f"Ligne rejetée : numéro de commande manquant ou vide. Données reçues: {data}", "error")
                return False
            
            self._log(f"Vérification commande {order_number}")
            
            # Vérifier si la commande existe déjà
            existing_commande = Commande.objects.filter(num_cmd=order_number).first()
            if existing_commande:
                # Commande existe déjà - pas d'insertion
                self._log(f"Commande {order_number} existe déjà (ID YZ: {existing_commande.id_yz}) - IGNORÉE")
                self.duplicate_orders_found += 1
                
                # TOUJOURS mettre à jour les états, même si les autres données sont inchangées
                self._log(f"Mise à jour des états pour commande existante {order_number}")
                success = self._update_existing_command(existing_commande, data, headers)
                if success:
                        self.existing_orders_updated += 1
                return success
            
            # Récupérer ou créer le client
            client_phone_raw = data.get('Téléphone', '')
            client_phone = self._clean_phone_number(client_phone_raw)
            client_nom_prenom = data.get('Client', '').split(' ', 1) # Tente de séparer nom et prénom
            client_nom = client_nom_prenom[0] if client_nom_prenom else ''
            client_prenom = client_nom_prenom[1] if len(client_nom_prenom) > 1 else ''
            
            client_obj, created = Client.objects.get_or_create(
                numero_tel=client_phone,
                defaults={'nom': client_nom, 'prenom': client_prenom, 'adresse': data.get('Adresse', '')}
            )
            # Mettre à jour les infos client si la fiche n'est pas nouvelle et des données sont dispo
            if not created:
                if client_nom and client_obj.nom != client_nom:
                    client_obj.nom = client_nom
                if client_prenom and client_obj.prenom != client_prenom:
                    client_obj.prenom = client_prenom
                if data.get('Adresse') and client_obj.adresse != data.get('Adresse', ''):
                    client_obj.adresse = data.get('Adresse', '')
                client_obj.save()

            # Récupérer la ville du fichier sans essayer de la lier à la table Ville
            ville_nom = data.get('Ville', '').strip()
            ville_obj = None  # On ne lie plus à un objet Ville

            # Gérer le prix de manière sécurisée
            try:
                total_cmd_price = float(data.get('Prix', 0)) or float(data.get('Total', 0))
            except (ValueError, TypeError):
                total_cmd_price = 0.0

            # Créer une NOUVELLE commande (vérification déjà effectuée)
           
            commande = Commande.objects.create(
                num_cmd=order_number,
                date_cmd=self._parse_date(data.get('Date Création', '') or data.get('Date', '')),
                total_cmd=total_cmd_price,
                adresse=data.get('Adresse', ''),
                client=client_obj,
                ville=None,
                ville_init=data.get('Ville', '').strip(),
                produit_init=data.get('Produit', ''),
                origine='SYNC',
                last_sync_date=timezone.now() # Définir la date de dernière synchronisation
            )
            self._log(f"✅ NOUVELLE commande créée avec ID YZ: {commande.id_yz} et numéro externe: {commande.num_cmd}", "info")
            self.new_orders_created += 1

            # Parser le produit et créer l'article de commande et le panier
            # Avec la refactorisation des articles, on ne crée plus d'articles
            # On stocke seulement les informations du produit dans la commande
            product_str = data.get('Produit', '').strip()
            
            if product_str:
                self._log(f"Produit détecté pour la commande {commande.num_cmd}: {product_str}")
                # Stocker le produit dans la commande sans créer d'article
                commande.produit_init = product_str
                commande.save(update_fields=['produit_init'])
            else:
                self._log(f"Aucun produit spécifié pour la commande {commande.num_cmd}")
                # Marquer la commande comme n'ayant pas de produit
                commande.produit_init = "Produit non spécifié"
                commande.save(update_fields=['produit_init'])

            # Créer un panier vide pour la commande
            # SUPPRIMÉ : Un panier ne peut pas être vide selon le modèle (champs article, quantite, sous_total obligatoires)
            # Le panier sera créé plus tard quand des articles seront ajoutés à la commande
            self._log(f"Pas de panier créé pour la commande {commande.num_cmd} - sera créé lors de l'ajout d'articles")

            # Si un opérateur est spécifié et que la commande est affectée
            operator_name = data.get('Opérateur', '')
            operateur_obj = None
            if operator_name:
                try:
                    operateur_obj = Operateur.objects.get(nom_complet__iexact=operator_name)
                except Operateur.DoesNotExist:
                    self.errors.append(f"Opérateur non trouvé: {operator_name}")

            # Créer l'état de commande selon le statut
            status_from_sheet = data.get('Statut', '')
            if not status_from_sheet or not status_from_sheet.strip():
                # Le statut est obligatoire - rejeter la commande
                error_msg = f"Statut manquant pour la commande {order_number} - la commande est rejetée"
                self._log(error_msg, "error")
                # Supprimer la commande créée car elle n'est pas valide
                commande.delete()
                return False
            
            # Essayer de mapper le statut, mais être plus flexible
            status_libelle = None
            etat_created = False
            
            try:
                status_libelle = self._map_status(status_from_sheet)
                self._log(f"Statut reconnu: {status_libelle}")
                if status_libelle:
                    # Statut reconnu - créer l'état
                    self._log(f"Création de l'état '{status_libelle}' pour la commande {order_number}")
                    etat_created = self._create_etat_commande(commande, status_libelle, operateur_obj)
                    if etat_created:
                        self._log(f"État '{status_libelle}' créé avec succès pour la commande {order_number}")
                    else:
                        self._log(f"Échec de création de l'état '{status_libelle}' pour la commande {order_number}", "error")
                else:
                    # Statut non reconnu mais pas vide - utiliser un statut par défaut
                    self._log(f"Statut non reconnu '{status_from_sheet}' pour la commande {order_number} - utilisation du statut par défaut 'Non affectée'", "warning")
                    etat_created = self._create_etat_commande(commande, 'Non affectée', operateur_obj)
                    if not etat_created:
                        self._log(f"Échec de création de l'état par défaut pour la commande {order_number}", "error")
            except Exception as e:
                # En cas d'erreur, utiliser le statut par défaut
                self._log(f"Erreur lors du mapping du statut '{status_from_sheet}' pour la commande {order_number}: {str(e)} - utilisation du statut par défaut 'Non affectée'", "warning")
                etat_created = self._create_etat_commande(commande, 'Non affectée', operateur_obj)
                if not etat_created:
                    self._log(f"Échec de création de l'état par défaut pour la commande {order_number}", "error")

            try:
                # Forcer le rafraîchissement depuis la base
                commande.refresh_from_db()
                etat_final = commande.etat_actuel
                
                if etat_final:
                    print(f"✅ État final confirmé: '{etat_final.enum_etat.libelle}'")
                    print(f"   📋 ID état: {etat_final.id}")
                    print(f"   📋 Date début: {etat_final.date_debut}")
                    print(f"   📋 Date fin: {etat_final.date_fin}")
                else:
                    print(f"❌ PROBLÈME: Aucun état final trouvé!")
                    print(f"   📋 Tentative de récupération manuelle...")
                    
                    # Vérifier manuellement dans la base
                    from commande.models import EtatCommande
                    etat_manuel = EtatCommande.objects.filter(commande=commande).order_by('-date_debut').first()
                    if etat_manuel:
                        print(f"   📋 État trouvé manuellement: {etat_manuel.enum_etat.libelle}")
                        print(f"   📋 ID: {etat_manuel.id}")
                        print(f"   📋 Date début: {etat_manuel.date_debut}")
                    else:
                        print(f"   📋 Aucun état trouvé manuellement!")
                        
            except Exception as e:
                print(f"⚠️ Erreur lors de la vérification finale: {str(e)}")
            
            print(f"📈 Compteur de commandes importées: {self.records_imported}")
            print(f"🔍 === FIN TRAITEMENT LIGNE ===\n")

            self.records_imported += 1
            return True
            
        except Exception as e:
            self.errors.append(f"Erreur lors du traitement de la ligne: {str(e)}")
            return False
    
    def _should_update_command(self, existing_commande, data):
        """Détermine si une commande existante doit être mise à jour"""
        # Vérifier si le statut a changé
        current_status = existing_commande.etat_actuel.enum_etat.libelle if existing_commande.etat_actuel else 'Non affectée'
        
        # Le statut est obligatoire, donc on doit pouvoir le mapper
        try:
            new_status_raw = self._map_status(data.get('Statut', ''))
            new_status = new_status_raw
        except ValueError as e:
            # Si le statut n'est pas reconnu, ne pas mettre à jour la commande
            self._log(f"Statut non reconnu lors de la mise à jour: {str(e)} - commande {existing_commande.num_cmd} non mise à jour")
            return False
        
        # PROTECTION CONTRE LA RÉGRESSION D'ÉTATS
        # Si la commande a déjà un état avancé, ne pas la réinitialiser à "Non affectée" ou "En attente"
        if self._is_advanced_status(current_status) and self._is_basic_status(new_status):
            self._log(f"Protection activée: Commande {existing_commande.num_cmd} a l'état avancé '{current_status}' - ne pas régresser vers '{new_status}'")
            self.protected_orders_count += 1  # Incrémenter le compteur de protection
            # Ne pas mettre à jour le statut, mais continuer à vérifier les autres champs
            new_status = current_status  # Garder le statut actuel
        
        if current_status != new_status:
            return True
        
        # Vérifier si le prix a changé
        try:
            new_price = float(data.get('Prix', 0)) or float(data.get('Total', 0))
            if abs(float(existing_commande.total_cmd) - new_price) > 0.01:  # Différence de plus de 1 centime
                return True
        except (ValueError, TypeError):
            pass
        
        # Vérifier si l'adresse a changé
        new_address = data.get('Adresse', '')
        if new_address and existing_commande.adresse != new_address:
            return True
        
        # Vérifier si la ville_init a changé
        new_ville_nom = data.get('Ville', '').strip()
        if new_ville_nom and existing_commande.ville_init != new_ville_nom:
            return True
        
        # Vérifier si l'opérateur a changé
        new_operator = data.get('Opérateur', '')
        current_operator = existing_commande.etat_actuel.operateur.nom_complet if (existing_commande.etat_actuel and existing_commande.etat_actuel.operateur) else ''
        if new_operator and current_operator != new_operator:
            return True
        
        return False
    
    def _is_advanced_status(self, status):
        """Détermine si un statut est considéré comme avancé (ne doit pas être régressé)"""
        advanced_statuses = [
            'Affectée', 'En cours de confirmation', 'Confirmée', 'En préparation', 
            'En livraison', 'Livrée', 'Expédiée', 'Payé', 'Partiellement payé'
        ]
        return status in advanced_statuses
    
    def _is_basic_status(self, status):
        """Détermine si un statut est considéré comme basique (peut être régressé)"""
        basic_statuses = [
            'Non affectée', 'En attente', 'Erronée', 'Doublon', 'Annulée', 
            'Reportée', 'Hors zone', 'Injoignable', 'Pas de réponse', 
            'Numéro incorrect', 'Échoué', 'Retournée', 'Non payé'
        ]
        return status in basic_statuses
    
    def _update_existing_command(self, existing_commande, data, headers):
        """Met à jour une commande existante avec les nouvelles données (PAS D'INSERTION)"""
        try:
            updated = False
            command_changes = []  # Renommé pour éviter tout conflit
            
            print(f"🔄 Mise à jour en arrière-plan pour commande existante {existing_commande.num_cmd}")
            
            # Mettre à jour le prix si nécessaire
            try:
                new_price = float(data.get('Prix', 0)) or float(data.get('Total', 0))
                if abs(float(existing_commande.total_cmd) - new_price) > 0.01:
                    old_price = existing_commande.total_cmd
                    existing_commande.total_cmd = new_price
                    command_changes.append(f"Prix: {old_price} → {new_price}")
                    updated = True
            except (ValueError, TypeError):
                pass
            
            # Mettre à jour l'adresse si nécessaire
            new_address = data.get('Adresse', '')
            if new_address and existing_commande.adresse != new_address:
                old_address = existing_commande.adresse
                existing_commande.adresse = new_address
                command_changes.append(f"Adresse: '{old_address}' → '{new_address}'")
                updated = True
            
            # Mettre à jour la ville_init si nécessaire
            new_ville_nom = data.get('Ville', '').strip()
            if new_ville_nom and existing_commande.ville_init != new_ville_nom:
                old_ville_init = existing_commande.ville_init
                existing_commande.ville_init = new_ville_nom
                command_changes.append(f"Ville: '{old_ville_init}' → '{new_ville_nom}'")
                updated = True
            
            # Sauvegarder les changements de la commande
            if updated:
                existing_commande.last_sync_date = timezone.now() # Mettre à jour la date de dernière synchronisation
                existing_commande.save()
                print(f"📝 Commande mise à jour: ID YZ {existing_commande.id_yz} - Changements: {', '.join(command_changes)}")
            
            # Gérer le statut de la commande (séparé pour éviter les conflits)
            status_updated = self._update_command_status(existing_commande, data)
            
            # Mettre à jour les informations du client si nécessaire
            self._update_client_info(existing_commande, data, new_address)
            
            return True
            
        except Exception as e:
            error_msg = f"Erreur lors de la mise à jour de la commande existante {existing_commande.num_cmd}: {str(e)}"
            self._log(error_msg, "error")
            return False
    
    def _update_command_status(self, existing_commande, data):
        """Met à jour le statut d'une commande existante"""
        try:
            # Mettre à jour le statut si nécessaire
            new_status_raw = self._map_status(data.get('Statut', ''))
            if new_status_raw:
                # Statut reconnu - procéder à la mise à jour
                current_status = existing_commande.etat_actuel.enum_etat.libelle if existing_commande.etat_actuel else 'Non affectée'
                
                # PROTECTION CONTRE LA RÉGRESSION D'ÉTATS
                # Si la commande a déjà un état avancé, ne pas la réinitialiser à un état basique
                if self._is_advanced_status(current_status) and self._is_basic_status(new_status_raw):
                    self._log(f"Protection activée lors de la mise à jour: Commande {existing_commande.num_cmd} garde l'état avancé '{current_status}' au lieu de régresser vers '{new_status_raw}'")
                    self.protected_orders_count += 1  # Incrémenter le compteur de protection
                    new_status_raw = current_status  # Garder le statut actuel
                
                # TOUJOURS créer/mettre à jour l'état, même si le statut est identique
                # Récupérer l'opérateur si spécifié
                operateur_obj = None
                operator_name = data.get('Opérateur', '')
                if operator_name:
                    try:
                        operateur_obj = Operateur.objects.get(nom_complet__iexact=operator_name)
                    except Operateur.DoesNotExist:
                        self.errors.append(f"Opérateur non trouvé: {operator_name}")
                    
                # Créer l'état de commande
                success = self._create_etat_commande(existing_commande, new_status_raw, operateur_obj)
                
                if current_status != new_status_raw:
                    print(f"📊 État mis à jour pour commande existante ID YZ {existing_commande.id_yz}: {current_status} → {new_status_raw}")
                else:
                    self._log(f"Statut identique pour commande {existing_commande.num_cmd}: {current_status} - création/mise à jour de l'état forcée")
                    print(f"📊 État maintenu pour commande existante ID YZ {existing_commande.id_yz}: {current_status}")
                
                return success
            else:
                # Statut non reconnu - utiliser le statut par défaut
                self._log(f"Statut non reconnu pour commande {existing_commande.num_cmd} - utilisation du statut par défaut 'Non affectée'")
                default_status = 'Non affectée'
                
                # Créer/mettre à jour l'état avec le statut par défaut
                operateur_obj = None
                operator_name = data.get('Opérateur', '')
                if operator_name:
                    try:
                        operateur_obj = Operateur.objects.get(nom_complet__iexact=operator_name)
                    except Operateur.DoesNotExist:
                        self.errors.append(f"Opérateur non trouvé: {operator_name}")
                
                success = self._create_etat_commande(existing_commande, default_status, operateur_obj)
                print(f"📊 État par défaut créé pour commande existante ID YZ {existing_commande.id_yz}: {default_status}")
                return success
                
        except Exception as e:
            error_msg = f"Erreur lors de la mise à jour du statut pour {existing_commande.num_cmd}: {str(e)}"
            self._log(error_msg, "error")
            return False
    
    def _update_client_info(self, existing_commande, data, new_address):
        """Met à jour les informations du client d'une commande"""
        try:
            # Mettre à jour les informations du client si nécessaire
            client_phone_raw = data.get('Téléphone', '')
            client_phone = self._clean_phone_number(client_phone_raw)
            if client_phone and existing_commande.client:
                client_obj = existing_commande.client
                client_nom_prenom = data.get('Client', '').split(' ', 1)
                client_nom = client_nom_prenom[0] if client_nom_prenom else ''
                client_prenom = client_nom_prenom[1] if len(client_nom_prenom) > 1 else ''
                
                client_updated = False
                client_changes = []
                if client_nom and client_obj.nom != client_nom:
                    client_changes.append(f"Nom: '{client_obj.nom}' → '{client_nom}'")
                    client_obj.nom = client_nom
                    client_updated = True
                if client_prenom and client_obj.prenom != client_prenom:
                    client_changes.append(f"Prénom: '{client_obj.prenom}' → '{client_prenom}'")
                    client_obj.prenom = client_prenom
                    client_updated = True
                if new_address and client_obj.adresse != new_address:
                    client_changes.append(f"Adresse client: '{client_obj.adresse}' → '{new_address}'")
                    client_obj.adresse = new_address
                    client_updated = True
                
                if client_updated:
                    client_obj.save()
                    client_full_name = f"{client_obj.nom} {client_obj.prenom}".strip()
                    print(f"👤 Client mis à jour: {client_full_name} - {', '.join(client_changes)}")
            
        except Exception as e:
            error_msg = f"Erreur lors de la mise à jour du client pour {existing_commande.num_cmd}: {str(e)}"
            self._log(error_msg, "error")
    
    def _map_status(self, status):
        """Mappe les statuts du fichier aux libellés des états dans la base de données"""
        print(f"🔄 === MAPPING STATUT ===")
        print(f"📥 Statut reçu: '{status}'")
        print(f"🔍 Type de statut: {type(status)}")
        
        status_map = {
            'Non affectée': 'Non affectée',
            'Affectée': 'Affectée',
            'Erronée': 'Erronée',
            'Doublon': 'Doublon',
            'À confirmer': 'En cours de confirmation',
            'En cours de confirmation': 'En cours de confirmation',
            'Confirmée': 'Confirmée',
            'Annulée': 'Annulée',
            'En attente': 'En attente',
            'Reportée': 'Reportée',
            'Hors zone': 'Hors zone',
            'Injoignable': 'Injoignable',
            'Pas de réponse': 'Pas de réponse',
            'Numéro incorrect': 'Numéro incorrect',
            'Échoué': 'Échoué',
            'Expédiée': 'Expédiée',
            'En préparation': 'En préparation',
            'En livraison': 'En livraison',
            'Livrée': 'Livrée',
            'Retournée': 'Retournée',
            'Non payé': 'Non payé',
            'Partiellement payé': 'Partiellement payé',
            'Payé': 'Payé',
            # Variantes possibles
            'Erronee': 'Erronée',
            'Errone': 'Erronée',
            'Erroné': 'Erronée',
            'Doublons': 'Doublon',
            'Non affectee': 'Non affectée',
            'Non affecté': 'Non affectée',
            'Affecte': 'Affectée',
            'Affecté': 'Affectée',
            'Confirmee': 'Confirmée',
            'Confirmé': 'Confirmée',
            'Annulee': 'Annulée',
            'Annulé': 'Annulée',
            'Livree': 'Livrée',
            'Livré': 'Livrée',
            'Retournee': 'Retournée',
            'Retourné': 'Retournée',
        }
        
        print(f"📋 Nombre total de statuts dans le mapping: {len(status_map)}")
        print(f"🔍 Statuts disponibles: {list(status_map.keys())}")
        
        # Nettoyer le statut reçu
        print(f"🧹 === NETTOYAGE STATUT ===")
        if status is None:
            print(f"⚠️ Statut reçu est None")
            cleaned_status = ''
        else:
            print(f"📝 Statut brut: '{status}' (longueur: {len(str(status))})")
            cleaned_status = str(status).strip()
            print(f"🧹 Statut après strip: '{cleaned_status}' (longueur: {len(cleaned_status)})")
        
        # Si le statut est vide ou null, retourner None pour indiquer qu'aucun changement n'est nécessaire
        if not cleaned_status:
            print(f"❌ Statut vide ou null → None")
            print(f"🔍 === FIN MAPPING STATUT ===\n")
            return None
        
        print(f"✅ Statut non vide, recherche en cours...")
        
        # Chercher dans le dictionnaire (recherche exacte puis insensible à la casse)
        print(f"🔍 === RECHERCHE EXACTE ===")
        if cleaned_status in status_map:
            result = status_map[cleaned_status]
            print(f"✅ Statut trouvé exactement: '{cleaned_status}' → '{result}'")
            print(f"🔍 === FIN MAPPING STATUT ===\n")
            return result
        
        print(f"❌ Recherche exacte échouée, tentative insensible à la casse...")
        
        # Recherche insensible à la casse
        print(f"🔍 === RECHERCHE INSENSIBLE À LA CASSE ===")
        for key, value in status_map.items():
            print(f"🔍 Comparaison: '{key.lower()}' vs '{cleaned_status.lower()}'")
            if key.lower() == cleaned_status.lower():
                print(f"✅ Statut trouvé (insensible à la casse): '{key}' → '{value}'")
                print(f"🔍 === FIN MAPPING STATUT ===\n")
                return value
        
        # Si aucun statut ne correspond, retourner None pour indiquer qu'un statut par défaut doit être utilisé
        print(f"❌ Aucun statut trouvé pour '{cleaned_status}'")
        print(f"⚠️ Utilisation du statut par défaut 'Non affectée'")
        self._log(f"Statut non reconnu: '{cleaned_status}' - utilisation du statut par défaut", "warning")
        print(f"🔍 === FIN MAPPING STATUT ===\n")
        return None

    def _ensure_enum_etats_exist(self):
        """S'assure que tous les EnumEtatCmd de base existent"""
        print(f"🏗️ === INITIALISATION DES ÉTATS DE BASE ===")
        print(f"📋 Vérification de l'existence des états de base...")
        
        try:
            from commande.models import EnumEtatCmd
            
            # États de base nécessaires pour la synchronisation
            etats_base = [
                {'libelle': 'Non affectée', 'ordre': 1, 'couleur': '#EF4444'},
                {'libelle': 'Affectée', 'ordre': 2, 'couleur': '#F59E0B'},
                {'libelle': 'Erronée', 'ordre': 3, 'couleur': '#DC2626'},
                {'libelle': 'Doublon', 'ordre': 4, 'couleur': '#7C2D12'},
                {'libelle': 'En cours de confirmation', 'ordre': 5, 'couleur': '#3B82F6'},
                {'libelle': 'Confirmée', 'ordre': 6, 'couleur': '#10B981'},
                {'libelle': 'Annulée', 'ordre': 7, 'couleur': '#6B7280'},
                {'libelle': 'En attente', 'ordre': 8, 'couleur': '#F59E0B'},
                {'libelle': 'Reportée', 'ordre': 9, 'couleur': '#8B5CF6'},
                {'libelle': 'Hors zone', 'ordre': 10, 'couleur': '#EF4444'},
                {'libelle': 'Injoignable', 'ordre': 11, 'couleur': '#6B7280'},
                {'libelle': 'Pas de réponse', 'ordre': 12, 'couleur': '#6B7280'},
                {'libelle': 'Numéro incorrect', 'ordre': 13, 'couleur': '#DC2626'},
                {'libelle': 'Échoué', 'ordre': 14, 'couleur': '#DC2626'},
                {'libelle': 'Expédiée', 'ordre': 15, 'couleur': '#3B82F6'},
                {'libelle': 'En préparation', 'ordre': 16, 'couleur': '#F59E0B'},
                {'libelle': 'En livraison', 'ordre': 17, 'couleur': '#8B5CF6'},
                {'libelle': 'Livrée', 'ordre': 18, 'couleur': '#10B981'},
                {'libelle': 'Retournée', 'ordre': 19, 'couleur': '#EF4444'},
                {'libelle': 'Non payé', 'ordre': 20, 'couleur': '#DC2626'},
                {'libelle': 'Partiellement payé', 'ordre': 21, 'couleur': '#F59E0B'},
                {'libelle': 'Payé', 'ordre': 22, 'couleur': '#10B981'},
            ]
            
            print(f"📊 Nombre total d'états à vérifier: {len(etats_base)}")
            print(f"🔍 États à vérifier: {[etat['libelle'] for etat in etats_base]}")
            
            created_count = 0
            existing_count = 0
            
            print(f"🔄 === VÉRIFICATION ÉTAT PAR ÉTAT ===")
            for i, etat_data in enumerate(etats_base, 1):
                print(f"🔍 [{i}/{len(etats_base)}] Vérification de l'état: '{etat_data['libelle']}'")
                
                try:
                    etat, created = EnumEtatCmd.objects.get_or_create(
                        libelle=etat_data['libelle'],
                        defaults={
                            'ordre': etat_data['ordre'],
                            'couleur': etat_data['couleur']
                        }
                    )
                    
                    if created:
                        created_count += 1
                        print(f"✅ NOUVEAU: État '{etat.libelle}' créé (ID: {etat.id}, Ordre: {etat.ordre}, Couleur: {etat.couleur})")
                        self._log(f"EnumEtatCmd créé: {etat.libelle}")
                    else:
                        existing_count += 1
                        print(f"ℹ️ EXISTANT: État '{etat.libelle}' déjà présent (ID: {etat.id}, Ordre: {etat.ordre}, Couleur: {etat.couleur})")
                        
                except Exception as e:
                    print(f"❌ ERREUR lors de la vérification de l'état '{etat_data['libelle']}': {str(e)}")
                    self._log(f"Erreur lors de la vérification de l'état '{etat_data['libelle']}': {str(e)}", "error")
            
            print(f"📊 === RÉSUMÉ INITIALISATION ===")
            print(f"✅ États existants: {existing_count}")
            print(f"🆕 Nouveaux états créés: {created_count}")
            print(f"📋 Total traité: {existing_count + created_count}")
            
            if created_count > 0:
                message = f"Initialisation terminée: {created_count} nouveaux états créés"
                print(f"🎉 {message}")
                self._log(message)
            else:
                message = "Tous les états de base existent déjà"
                print(f"ℹ️ {message}")
                self._log(message)
            
            print(f"🏗️ === FIN INITIALISATION DES ÉTATS ===\n")
                
        except Exception as e:
            error_msg = f"Erreur lors de l'initialisation des états: {str(e)}"
            print(f"💥 {error_msg}")
            self._log(error_msg, "error")
            print(f"🏗️ === FIN INITIALISATION DES ÉTATS (AVEC ERREUR) ===\n")

    def _create_etat_commande(self, commande, status_libelle, operateur=None):
        """Crée un état de commande avec le libellé donné"""
        try:
            from commande.models import EnumEtatCmd, EtatCommande
            from django.utils import timezone
            from django.db import connection
            
            self._log(f"🏗️ === CRÉATION ÉTAT COMMANDE ===")
            self._log(f"🎯 Commande: {commande.num_cmd} (ID YZ: {commande.id_yz})")
            self._log(f"🏷️ Statut demandé: '{status_libelle}'")
            self._log(f"👤 Opérateur: {operateur.nom_complet if operateur else 'Aucun'}")
            
            # Terminer l'état actuel s'il existe
            etat_actuel = commande.etat_actuel
            if etat_actuel:
                self._log(f"🔄 Terminaison état actuel '{etat_actuel.enum_etat.libelle}' pour commande {commande.num_cmd}")
                etat_actuel.terminer_etat(operateur)
                self._log(f"✅ État actuel terminé avec succès")
            else:
                self._log(f"ℹ️ Aucun état actuel pour commande {commande.num_cmd}")
            
            # Récupérer l'énumération d'état (elle doit maintenant exister)
            try:
                enum_etat = EnumEtatCmd.objects.get(libelle=status_libelle)
                self._log(f"✅ EnumEtatCmd trouvé: {status_libelle} (ID: {enum_etat.id})")
            except EnumEtatCmd.DoesNotExist:
                # Si l'état n'existe toujours pas, le créer avec des valeurs par défaut
                self._log(f"⚠️ EnumEtatCmd non trouvé pour '{status_libelle}', création en cours...")
                enum_etat = EnumEtatCmd.objects.create(
                    libelle=status_libelle,
                    ordre=999,
                    couleur='#6B7280'
                )
                self._log(f"🆕 EnumEtatCmd créé: {status_libelle} (ID: {enum_etat.id})")
            
            # Créer le nouvel état de commande
            try:
                self._log(f"🏗️ Création de l'EtatCommande...")
                nouvel_etat = EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=enum_etat,
                    date_debut=timezone.now(),
                    operateur=operateur,
                    commentaire=f"État défini lors de la synchronisation depuis Google Sheets"
                )
                
                self._log(f"✅ EtatCommande créé avec succès!")
                self._log(f"   📋 ID: {nouvel_etat.id}")
                self._log(f"   📋 Commande: {nouvel_etat.commande.num_cmd}")
                self._log(f"   📋 État: {nouvel_etat.enum_etat.libelle}")
                self._log(f"   📋 Date début: {nouvel_etat.date_debut}")
                self._log(f"   📋 Opérateur: {nouvel_etat.operateur.nom_complet if nouvel_etat.operateur else 'Aucun'}")
                
                # FORCER LA VÉRIFICATION ET L'INDEXATION
                self._log(f"🔄 === VÉRIFICATION ET INDEXATION ===")
                
                # 1. Forcer la synchronisation de la base de données
                connection.commit()
                self._log(f"✅ Transaction commit forcé")
                
                # 2. Rafraîchir la commande depuis la base
                commande.refresh_from_db()
                self._log(f"✅ Commande rafraîchie depuis la base")
                
                # 3. Vérifier que l'état actuel est bien mis à jour
                etat_actuel_apres = commande.etat_actuel
                if etat_actuel_apres:
                    self._log(f"✅ Vérification réussie: État actuel après création: '{etat_actuel_apres.enum_etat.libelle}'")
                    self._log(f"   📋 ID état: {etat_actuel_apres.id}")
                    self._log(f"   📋 Date début: {etat_actuel_apres.date_debut}")
                    self._log(f"   📋 Date fin: {etat_actuel_apres.date_fin}")
                else:
                    self._log(f"❌ PROBLÈME: Aucun état actuel après création!", "error")
                    
                    # 4. Essayer de récupérer l'état créé manuellement
                    self._log(f"🔍 Tentative de récupération manuelle...")
                    etat_test = EtatCommande.objects.filter(commande=commande).order_by('-date_debut').first()
                    if etat_test:
                        self._log(f"🔍 État trouvé manuellement: {etat_test.enum_etat.libelle} (ID: {etat_test.id})", "error")
                        self._log(f"   📋 Date début: {etat_test.date_debut}")
                        self._log(f"   📋 Date fin: {etat_test.date_fin}")
                        
                        # 5. Vérifier la relation dans la base
                        self._log(f"🔍 Vérification de la relation dans la base...")
                        from django.db import connection
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT c.id_yz, c.num_cmd, ec.id, ec.enum_etat_id, eec.libelle
                                FROM commande_commande c
                                LEFT JOIN commande_etatcommande ec ON c.id = ec.commande_id
                                LEFT JOIN commande_enumetatcmd eec ON ec.enum_etat_id = eec.id
                                WHERE c.id_yz = %s
                                ORDER BY ec.date_debut DESC
                            """, [commande.id_yz])
                            rows = cursor.fetchall()
                            
                        if rows:
                            self._log(f"🔍 Données brutes de la base: {rows}", "error")
                        else:
                            self._log(f"🔍 Aucune donnée trouvée dans la base!", "error")
                    else:
                        self._log(f"🔍 Aucun état trouvé pour la commande {commande.num_cmd}", "error")
                
                # 6. Vérification finale
                self._log(f"🔄 === VÉRIFICATION FINALE ===")
                commande_finale = Commande.objects.get(id_yz=commande.id_yz)
                etat_final = commande_finale.etat_actuel
                
                if etat_final:
                    self._log(f"🎉 SUCCÈS: État final vérifié: '{etat_final.enum_etat.libelle}'")
                    self._log(f"🎉 === ÉTAT CRÉÉ AVEC SUCCÈS ===\n")
                    return True
                else:
                    self._log(f"❌ ÉCHEC: Aucun état final trouvé!", "error")
                    self._log(f"❌ === ÉCHEC CRÉATION ÉTAT ===\n")
                    return False
                
            except Exception as create_error:
                error_msg = f"❌ Erreur lors de la création d'EtatCommande pour {commande.num_cmd}: {str(create_error)}"
                self._log(error_msg, "error")
                return False
            
        except Exception as e:
            error_msg = f"Erreur lors de la création de l'état '{status_libelle}' pour commande {commande.num_cmd}: {str(e)}"
            self._log(error_msg, "error")
            self.errors.append(error_msg)
            return False
    
    def sync(self):
        """Synchronise les données depuis Google Sheets"""
        print(f"🚀 === DÉBUT SYNCHRONISATION GOOGLE SHEETS ===")
        print(f"⏰ Heure de début: {timezone.now()}")
        print(f"👤 Déclenché par: {self.triggered_by}")
        print(f"🔧 Configuration: {self.sheet_config.name if hasattr(self.sheet_config, 'name') else 'Config inconnue'}")
        
        # Marquer le début de la synchronisation
        self.start_time = timezone.now()
        self.execution_details['started_at'] = self.start_time.isoformat()
        
        # S'assurer que tous les états de base existent
        print(f"🏗️ === INITIALISATION DES ÉTATS ===")
        self._log("Initialisation des états de commande...")
        self._ensure_enum_etats_exist()
        
        print(f"🔐 === AUTHENTIFICATION ===")
        client = self.authenticate()
        if not client:
            print(f"❌ Échec de l'authentification")
            self.end_time = timezone.now()
            self._log_sync('error')
            return False
        print(f"✅ Authentification réussie")
            
        print(f"📊 === RÉCUPÉRATION FEUILLE ===")
        worksheet = self.get_sheet(client)
        if not worksheet:
            print(f"❌ Échec de récupération de la feuille")
            self.end_time = timezone.now()
            self._log_sync('error')
            return False
        print(f"✅ Feuille récupérée: {worksheet.title}")
            
        try:
            # Enregistrer les informations de la feuille
            print(f"📋 === INFORMATIONS FEUILLE ===")
            self.sheet_title = worksheet.spreadsheet.title
            self.execution_details['spreadsheet_title'] = worksheet.spreadsheet.title
            self.execution_details['worksheet_name'] = worksheet.title
            print(f"📊 Feuille: {worksheet.spreadsheet.title}")
            print(f"📋 Onglet: {worksheet.title}")
            
            # Récupérer toutes les données
            print(f"📥 === RÉCUPÉRATION DONNÉES ===")
            print(f"⏳ Récupération de toutes les données...")
            all_data = worksheet.get_all_values()
            print(f"✅ Données récupérées")
            
            if not all_data:
                error_msg = "❌ Aucune donnée trouvée dans la feuille"
                print(error_msg)
                self.errors.append("Aucune donnée trouvée dans la feuille")
                self.end_time = timezone.now()
                self._log_sync('error')
                return False
                
            # Extraire les en-têtes et les données
            headers = all_data[0]
            rows = all_data[1:]
            
            print(f"📊 === ANALYSE DONNÉES ===")
            print(f"📋 En-têtes détectés ({len(headers)} colonnes): {headers}")
            print(f"📊 Nombre total de lignes: {len(all_data)}")
            print(f"📊 Lignes de données: {len(rows)}")
            print(f"📊 Ligne d'en-têtes: 1")
            
            # Afficher les premiers en-têtes pour vérification
            if rows:
                print(f"🔍 Première ligne de données: {dict(zip(headers, rows[0]))}")
                if len(rows) > 1:
                    print(f"🔍 Deuxième ligne de données: {dict(zip(headers, rows[1]))}")
            
            # Enregistrer les statistiques
            self.total_rows = len(all_data)
            self.execution_details['headers'] = headers
            self.execution_details['total_rows'] = len(all_data)
            self.execution_details['data_rows'] = len(rows)
            
            print(f"🚀 === DÉBUT TRAITEMENT LIGNES ===")
            print(f"📈 Total lignes à traiter: {len(rows)}")
            
            # Traiter chaque ligne
            for i, row in enumerate(rows, 2):  # Commencer à 2 car la ligne 1 contient les en-têtes
                print(f"\n📝 === TRAITEMENT LIGNE {i} ===")
                
                # Vérifier si la ligne est vide
                if not any(cell.strip() for cell in row if cell):
                    print(f"⚠️ Ligne {i} ignorée: ligne complètement vide")
                    self._log(f"Ligne {i} ignorée : ligne complètement vide")
                    self.skipped_rows += 1
                    continue
                    
                if len(row) == len(headers):  # Vérifier que la ligne a le bon nombre de colonnes
                    print(f"✅ Ligne {i} valide: {len(row)} colonnes vs {len(headers)} en-têtes")
                    print(f"🔍 Aperçu: {dict(zip(headers[:3], row[:3]))}...")
                    
                    success = self.process_row(row, headers)
                    if success:
                        print(f"✅ Ligne {i} traitée avec succès")
                        self._log(f"Ligne {i} traitée avec succès")
                        self.processed_rows += 1
                    else:
                        print(f"❌ Échec traitement ligne {i}")
                        self._log(f"Échec traitement ligne {i}")
                        self.skipped_rows += 1
                else:
                    error_msg = f"❌ Ligne {i} ignorée: nombre de colonnes incorrect ({len(row)} vs {len(headers)})"
                    print(error_msg)
                    self._log(error_msg, "error")
                    self.skipped_rows += 1
            
            # Marquer la fin de la synchronisation
            self.end_time = timezone.now()
            
            # Calculer les statistiques finales détaillées
            duration = (self.end_time - self.start_time).total_seconds()
            self.execution_details.update({
                'finished_at': self.end_time.isoformat(),
                'duration_seconds': duration,
                'processed_rows': self.processed_rows,
                'skipped_rows': self.skipped_rows,
                'records_imported': self.records_imported,
                'success_rate': (self.processed_rows / len(rows) * 100) if rows else 0,
                'errors_count': len(self.errors),
                
                # Nouvelles statistiques détaillées
                'new_orders_created': self.new_orders_created,
                'existing_orders_updated': self.existing_orders_updated,
                'existing_orders_skipped': self.existing_orders_skipped,
                'duplicate_orders_found': self.duplicate_orders_found,
                'insertion_avoided_count': self.duplicate_orders_found,  # Nombre d'insertions évitées
                'protected_orders_count': self.protected_orders_count,  # Nombre de commandes protégées
            })
            
            # Message de notification détaillé
            notification_parts = []
            
            # Cas spécial : Aucune nouvelle commande mais des commandes existantes détectées
            if self.new_orders_created == 0 and self.duplicate_orders_found > 0:
                notification_parts.append(f"❌ Aucune nouvelle commande trouvée")
                notification_parts.append(f"📋 {self.duplicate_orders_found} commandes existantes détectées dans la feuille")
            elif self.new_orders_created > 0:
                notification_parts.append(f"✅ {self.new_orders_created} nouvelles commandes créées")
            
            # Ajouts des autres types d'actions
            if self.existing_orders_updated > 0:
                notification_parts.append(f"🔄 {self.existing_orders_updated} commandes existantes mises à jour")
            if self.existing_orders_skipped > 0:
                notification_parts.append(f"➖ {self.existing_orders_skipped} commandes existantes inchangées")
            if self.protected_orders_count > 0:
                notification_parts.append(f"🛡️ {self.protected_orders_count} commandes protégées contre la régression d'état")
            
            # Message par défaut si rien ne s'est passé
            if not notification_parts:
                notification_parts.append("⚠️ Aucune donnée valide trouvée")
            
            self.execution_details['sync_summary'] = " | ".join(notification_parts)
            
            self._log(f"Résumé synchronisation: {self.execution_details['sync_summary']}")
            
            # Déterminer le statut final
            if self.errors:
                status = 'partial' if self.records_imported > 0 else 'error'
            else:
                status = 'success'
                
            self._log_sync(status)
            return status == 'success' or status == 'partial'
            
        except Exception as e:
            self.end_time = timezone.now()
            self.errors.append(f"Erreur de synchronisation: {str(e)}")
            self._log_sync('error')
            return False
    
    def _log_sync(self, status):
        """Enregistre un log de synchronisation avec statistiques détaillées"""
        SyncLog.objects.create(
            status=status,
            records_imported=self.records_imported,
            errors='\n'.join(self.errors) if self.errors else None,
            sheet_config=self.sheet_config,
            triggered_by=self.triggered_by,
            
            # Champs détaillés existants
            start_time=self.start_time,
            end_time=self.end_time,
            total_rows=self.total_rows,
            processed_rows=self.processed_rows,
            skipped_rows=self.skipped_rows,
            sheet_title=self.sheet_title,
            execution_details=self.execution_details,
            
            # Nouvelles statistiques détaillées
            new_orders_created=self.new_orders_created,
            existing_orders_updated=self.existing_orders_updated,
            existing_orders_skipped=self.existing_orders_skipped,
            duplicate_orders_found=self.duplicate_orders_found,
            protected_orders_count=self.protected_orders_count,
        )

# --- Configuration for Google Sheets API ---
# In a production setting, use environment variables or Django settings for credentials.
# For simplicity, assuming 'service_account.json' is available in the project root.
def get_gc_client():
    try:
        # Assumes service_account.json is in the working directory or specified via GOOGLE_APPLICATION_CREDENTIALS
        return gspread.service_account()
    except Exception as e:
        raise Exception(f"Failed to initialize gspread client. Ensure 'service_account.json' is correctly configured: {e}")

# Helper to parse product string
def parse_product_string(product_str):
    # Example format: "ESP HOM YZ650 - 42/أسود أبيض / noir blanc"
    # We need: product_name, size, color
    product_name = None
    size = None
    color = None

    if ' - ' in product_str:
        parts = product_str.split(' - ', 1) # Split only on the first occurrence
        product_name = parts[0].strip()
        details_part = parts[1].strip()

        if '/' in details_part:
            size_and_color_parts = details_part.split('/', 1) # Split only on the first '/'
            size = size_and_color_parts[0].strip()
            if len(size_and_color_parts) > 1:
                color = size_and_color_parts[1].strip()
                # Further clean color to remove redundant language part if present
                if ' / ' in color:
                    color = color.split(' / ')[0].strip() # Take the first language part
        else:
            # If no '/', maybe the whole detail part is the size or color
            size = details_part # Or handle as a generic descriptor if not strictly size/color
    else:
        # If no ' - ', the whole string is the product name
        product_name = product_str.strip()

    return product_name, size, color

def sync_google_sheet_data(config_id):
    config = GoogleSheetConfig.objects.get(id=config_id)
    sync_log = SyncLog.objects.create(config=config, status='PENDING', start_time=timezone.now())

    try:
        gc = get_gc_client()
        spreadsheet = gc.open_by_url(config.sheet_url)
        worksheet = spreadsheet.worksheet(config.worksheet_name)
        data = worksheet.get_all_records() # Get data as list of dictionaries

        processed_rows = 0
        successful_imports = 0
        failed_imports = 0
        logs = []

        for row_data in data:
            with transaction.atomic():
                try:
                    # Map CSV headers to model fields (case-sensitive from CSV)
                    numero_commande = row_data.get('N° Commande')
                    statut_csv = row_data.get('Statut')
                    operateur_name = row_data.get('Opérateur')
                    client_full_name = row_data.get('Client') # e.g., "Housni", "نعيمة أماسو"
                    client_tel_raw = row_data.get('Téléphone', '')
                    client_tel = GoogleSheetSync.clean_phone_number(client_tel_raw)
                    adresse = row_data.get('Adresse')
                    ville_name = row_data.get('Ville')
                    produit_str = row_data.get('Produit')
                    quantite = row_data.get('Quantité')
                    prix = row_data.get('Prix')
                    date_creation_str = row_data.get('Date Création')
                    motifs = row_data.get('Motifs')

                    if not numero_commande:
                        raise ValueError("Skipping row: 'N° Commande' is missing.")
                    
                    # Vérifier que le statut est présent (obligatoire)
                    if not statut_csv or not statut_csv.strip():
                        raise ValueError(f"Skipping row: 'Statut' is missing for order '{numero_commande}'. Status is mandatory.")
                    
                    # 1. Create or get Client
                    # Client name from CSV is often just a full name. We need nom and prenom.
                    # Simple heuristic: last word is nom, rest is prenom.
                    client_nom_parts = client_full_name.split() if client_full_name else []
                    client_nom = client_nom_parts[-1] if client_nom_parts else ''
                    client_prenom = ' '.join(client_nom_parts[:-1]) if len(client_nom_parts) > 1 else client_full_name # Fallback if only one word

                    client, created_client = Client.objects.get_or_create(
                        numero_tel=client_tel,
                        defaults={
                            'nom': client_nom,
                            'prenom': client_prenom,
                            'adresse': adresse, # Use address from CSV
                            # 'email': None, # Not in CSV
                        }
                    )
                    if created_client:
                        logs.append(f"Created new client: {client.get_full_name()} ({client.numero_tel}) for order {numero_commande}")

                    # 2. Get Operateur (assuming Operateur exists in your DB)
                    operateur_obj = None
                    if operateur_name:
                        try:
                            # Use exact match for operator name
                            operateur_obj = Operateur.objects.get(nom_complet__iexact=operateur_name)
                        except Operateur.DoesNotExist:
                            logs.append(f"Operator '{operateur_name}' not found for order '{numero_commande}'. Skipping operator assignment.")
                        except Operateur.MultipleObjectsReturned:
                             logs.append(f"Multiple operators found for '{operateur_name}'. Skipping operator assignment for order '{numero_commande}'.")


                    # 3. Get Ville (assuming Ville exists in your DB)
                    ville_obj = None
                    if ville_name:
                        try:
                            # Use exact match for city name
                            ville_obj = Ville.objects.get(nom__iexact=ville_name)
                        except Ville.DoesNotExist:
                            logs.append(f"City '{ville_name}' not found for order '{numero_commande}'. Storing city name directly.")
                            pass # We will store ville_name directly in Commande if obj not found
                        except Ville.MultipleObjectsReturned:
                            logs.append(f"Multiple cities found for '{ville_name}'. Storing city name directly for order '{numero_commande}'.")
                            pass # Store city name directly

                    # 4. Parse Date Creation
                    date_cmd = timezone.now() # Default to now if parsing fails
                    try:
                        # Attempt to parse multiple date formats present in the CSV
                        # YYYY-MM-DD HH:MM:SS
                        if len(date_creation_str) == 19 and date_creation_str[4] == '-' and date_creation_str[13] == ':':
                            date_cmd = datetime.strptime(date_creation_str, '%Y-%m-%d %H:%M:%S')
                        # YYYY-MM-DD
                        elif len(date_creation_str) == 10 and date_creation_str[4] == '-':
                            date_cmd = datetime.strptime(date_creation_str, '%Y-%m-%d')
                        # DD/MM/YYYY (or MM/DD/YYYY, try DD/MM first) - "27/04/2025"
                        elif '/' in date_creation_str:
                            try:
                                date_cmd = datetime.strptime(date_creation_str, '%d/%m/%Y')
                            except ValueError:
                                date_cmd = datetime.strptime(date_creation_str, '%m/%d/%Y') # Try MM/DD/YYYY as fallback
                        
                        date_cmd = timezone.make_aware(date_cmd) # Make it timezone aware
                    except (ValueError, TypeError) as e:
                        logs.append(f"Could not parse date '{date_creation_str}' for order '{numero_commande}': {e}. Using current time.")
                        date_cmd = timezone.now()


                    # 5. Create or Update Commande
                    commande, created_commande = Commande.objects.update_or_create(
                        num_cmd=numero_commande,
                        defaults={
                            'date_cmd': date_cmd,
                            'total_cmd': float(prix) if prix else 0.0,
                            'adresse': adresse,
                            'client': client,
                            'ville_init': ville_name, # Storing name, not object, based on CSV
                            'produit_init': produit_str, # Store raw product string
                            'origine': 'GSheet',
                        }
                    )
                    if created_commande:
                        logs.append(f"Successfully created order: {commande.numero_commande}")
                        
                        # SUPPRIMÉ : Création du panier vide - un panier doit toujours contenir des articles
                        # Le panier sera créé plus tard quand des articles seront ajoutés à la commande
                        logs.append(f"Order created without cart - cart will be created when articles are added")
                    else:
                        logs.append(f"Successfully updated order: {commande.numero_commande}")

                    successful_imports += 1

                except Exception as e:
                    failed_imports += 1
                    logs.append(f"Error processing row for order '{row_data.get('N° Commande', 'N/A')}': {e}. Row data: {row_data}")
                    transaction.set_rollback(True) # Ensure rollback for this row

            processed_rows += 1

        sync_log.status = 'COMPLETED'
        sync_log.successful_imports = successful_imports
        sync_log.failed_imports = failed_imports
        sync_log.log_messages = "\\n".join(logs)
        sync_log.end_time = timezone.now()
        sync_log.save()
        return True, "Synchronization completed."

    except Exception as e:
        sync_log.status = 'FAILED'
        sync_log.log_messages = f"Synchronization failed unexpectedly: {e}\\n" + "\\n".join(logs)
        sync_log.end_time = timezone.now()
        sync_log.save()
        return False, f"Synchronization failed unexpectedly: {e}"
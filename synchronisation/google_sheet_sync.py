import os
import gspread
from google.oauth2.service_account import Credentials
from django.conf import settings
from django.utils import timezone
from client.models import Client
from commande.models import Commande, Panier, EtatCommande, EnumEtatCmd
from article.models import Article
from parametre.models import Operateur, Ville, Region
from synchronisation.models import SyncLog, GoogleSheetConfig
import pandas as pd
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Q

class GoogleSheetSync:
    """Classe pour gérer la synchronisation avec Google Sheets"""
    
    def __init__(self, sheet_config, triggered_by="admin"):
        self.sheet_config = sheet_config
        self.triggered_by = triggered_by
        self.records_imported = 0
        self.errors = []
        
    def authenticate(self):
        """Authentification avec l'API Google Sheets"""
        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
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
    
    def parse_product(self, product_str):
        """Parse le format de produit et retourne les composants"""
        try:
            # Format attendu: "ESP HOM YZ650 - 42/أسود أبيض / noir blanc"
            parts = product_str.split(' - ')
            if len(parts) != 2:
                return None
            
            product_code = parts[0].strip()
            details = parts[1].split('/')
            if len(details) != 3:
                return None
            
            size = details[0].strip()
            color_ar = details[1].strip()
            color_fr = details[2].strip()
            
            return {
                'product_code': product_code,
                'size': size,
                'color_ar': color_ar,
                'color_fr': color_fr
            }
        except Exception as e:
            self.errors.append(f"Erreur de parsing du produit: {str(e)}")
            return None
    
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
    
    def process_row(self, row_data, headers):
        """Traite une ligne de données et crée une nouvelle commande uniquement si elle n'existe pas"""
        try:
            # Créer un dictionnaire avec les données de la ligne
            data = dict(zip(headers, row_data))
            
            # Vérifier si la commande existe déjà - essayer différentes variantes de clés
            order_number = data.get('N° Commande') or data.get('Numéro') or data.get('N°Commande') or data.get('Numero')
            if not order_number:
                self.errors.append(f"Ligne sans numéro de commande: {data}")
                return False
            
            # Vérifier si la commande existe déjà
            if Commande.objects.filter(num_cmd=order_number).exists():
                # La commande existe déjà, on l'ignore
                return True
            
            # Récupérer ou créer le client
            client_phone = data.get('Téléphone', '')
            client_nom_prenom = data.get('Client', '').split(' ', 1) # Tente de séparer nom et prénom
            client_nom = client_nom_prenom[0] if client_nom_prenom else ''
            client_prenom = client_nom_prenom[1] if len(client_nom_prenom) > 1 else ''
            
            client_obj, created = Client.objects.get_or_create(
                numero_tel=client_phone,
                defaults={'nom': client_nom, 'prenom': client_prenom, 'adresse': data.get('Adresse', '')}
            )
            # Mettre à jour les infos client si la fiche n'est pas nouvelle et des données sont dispo
            if not created:
                if client_nom and client_obj.nom != client_nom: # Mettre à jour seulement si différent et non vide
                    client_obj.nom = client_nom
                if client_prenom and client_obj.prenom != client_prenom: # Mettre à jour seulement si différent et non vide
                    client_obj.prenom = client_prenom
                if data.get('Adresse') and client_obj.adresse != data.get('Adresse', ''):
                    client_obj.adresse = data.get('Adresse', '')
                client_obj.save()

            # Récupérer ou créer la ville
            ville_nom = data.get('Ville', '')
            if ville_nom:
                # Créer ou récupérer la région par défaut si elle n'existe pas
                default_region, created_region = Region.objects.get_or_create(nom_region='Non spécifiée')
                
                ville_obj, created_ville = Ville.objects.get_or_create(
                    nom=ville_nom,
                    defaults={
                        'frais_livraison': 0.0,
                        'frequence_livraison': 'Quotidienne',
                        'region': default_region
                    }
                )
            else:
                ville_obj = None

            # Gérer le prix de manière sécurisée
            try:
                total_cmd_price = float(data.get('Prix', 0)) or float(data.get('Total', 0))
            except (ValueError, TypeError):
                total_cmd_price = 0.0

            # Créer une nouvelle commande en utilisant le même numéro vérifié
            commande = Commande.objects.create(
                num_cmd=order_number,  # Numéro externe du fichier Google Sheets
                date_cmd=self._parse_date(data.get('Date', '')),
                total_cmd=total_cmd_price,
                adresse=data.get('Adresse', ''),
                client=client_obj,
                ville=ville_obj,
                produit_init=data.get('Produit', ''),
                # L'ID YZ sera généré automatiquement par la méthode save() du modèle (1, 2, 3, ...)
            )
            print(f"Commande créée avec ID YZ: {commande.id_yz} et numéro externe: {commande.num_cmd}")
            # Parser le produit et créer l'article de commande et le panier
            product_str = data.get('Produit', '')
            product_info = self.parse_product(product_str)
            if product_info:
                # Tenter de trouver l'article existant ou le créer si non trouvé
                article_obj, created = Article.objects.get_or_create(
                    reference=product_info['product_code'],
                    defaults={
                        'nom': product_info['product_code'], # Utilise le code comme nom par défaut
                        'description': f"Taille: {product_info['size']}, Couleur (AR): {product_info['color_ar']}, Couleur (FR): {product_info['color_fr']}",
                        'prix_unitaire': total_cmd_price,
                        'couleur': product_info['color_fr'],
                        'pointure': product_info['size'],
                        'categorie': 'Non spécifiée',
                        'qte_disponible': 0,
                    }
                )
                
                # Créer l'entrée dans le panier
                try:
                    quantite = int(data.get('Quantité', 1)) if data.get('Quantité') else 1
                    panier_obj = Panier.objects.create(
                        commande=commande,
                        article=article_obj,
                        quantite=quantite,
                        sous_total=total_cmd_price # Utilise le prix de la commande comme sous-total pour l'article unique
                    )
                    print(f"Panier créé automatiquement pour la commande ID YZ: {commande.id_yz} (Ext: {commande.num_cmd}) avec l'article {article_obj.reference}")
                except Exception as e:
                    self.errors.append(f"Erreur lors de la création du panier pour la commande ID YZ: {commande.id_yz} (Ext: {commande.num_cmd}): {str(e)}")
            else:
                # Si on ne peut pas parser le produit, créer une entrée générique
                try:
                    # Créer un article générique basé sur le produit initial
                    article_nom = product_str[:50] if product_str else "Article synchronisé"
                    article_ref = f"SYNC_{commande.id_yz}"  # Utiliser l'ID YZ pour la référence
                    
                    article_obj, created = Article.objects.get_or_create(
                        reference=article_ref,
                        defaults={
                            'nom': article_nom,
                            'description': f"Article synchronisé depuis Google Sheets: {product_str}",
                            'prix_unitaire': total_cmd_price,
                            'couleur': 'Non spécifiée',
                            'pointure': 'Unique',
                            'categorie': 'Non spécifiée',
                            'qte_disponible': 0,
                        }
                    )
                    
                    # Créer l'entrée dans le panier
                    quantite = int(data.get('Quantité', 1)) if data.get('Quantité') else 1
                    panier_obj = Panier.objects.create(
                        commande=commande,
                        article=article_obj,
                        quantite=quantite,
                        sous_total=total_cmd_price
                    )
                    print(f"Panier générique créé pour la commande ID YZ: {commande.id_yz} (Ext: {commande.num_cmd})")
                except Exception as e:
                    self.errors.append(f"Erreur lors de la création du panier générique pour la commande ID YZ: {commande.id_yz} (Ext: {commande.num_cmd}): {str(e)}")

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
            if status_from_sheet:
                status_libelle = self._map_status(status_from_sheet)
                self._create_etat_commande(commande, status_libelle, operateur_obj)
            else:
                # État par défaut si aucun statut n'est spécifié
                self._create_etat_commande(commande, 'En attente', operateur_obj)

            self.records_imported += 1
            return True
            
        except Exception as e:
            self.errors.append(f"Erreur lors du traitement de la ligne: {str(e)}")
            return False
    
    def _map_status(self, status):
        """Mappe les statuts du fichier aux libellés des états dans la base de données"""
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
        
        # Nettoyer le statut reçu
        cleaned_status = status.strip() if status else ''
        
        # Chercher dans le dictionnaire (recherche exacte puis insensible à la casse)
        if cleaned_status in status_map:
            return status_map[cleaned_status]
            
        # Recherche insensible à la casse
        for key, value in status_map.items():
            if key.lower() == cleaned_status.lower():
                return value
        
        # Si aucun statut ne correspond, retourner 'En attente'
        return 'En attente'

    def _create_etat_commande(self, commande, status_libelle, operateur=None):
        """Crée un état de commande avec le libellé donné"""
        try:
            from commande.models import EnumEtatCmd, EtatCommande
            from django.utils import timezone
            
            # Terminer l'état actuel s'il existe
            etat_actuel = commande.etat_actuel
            if etat_actuel:
                etat_actuel.terminer_etat(operateur)
            
            # Récupérer ou créer l'énumération d'état
            enum_etat, created = EnumEtatCmd.objects.get_or_create(
                libelle=status_libelle,
                defaults={
                    'ordre': 999,  # Ordre par défaut pour les nouveaux états
                    'couleur': '#6B7280'  # Couleur par défaut
                }
            )
            
            if created:
                self.errors.append(f"Nouvel état créé: {status_libelle}")
            
            # Créer le nouvel état de commande
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=enum_etat,
                date_debut=timezone.now(),
                operateur=operateur,
                commentaire=f"État défini lors de la synchronisation depuis Google Sheets"
            )
            
            return True
            
        except Exception as e:
            self.errors.append(f"Erreur lors de la création de l'état '{status_libelle}': {str(e)}")
            return False
    
    def sync(self):
        """Synchronise les données depuis Google Sheets"""
        client = self.authenticate()
        if not client:
            self._log_sync('error')
            return False
            
        worksheet = self.get_sheet(client)
        if not worksheet:
            self._log_sync('error')
            return False
            
        try:
            # Récupérer toutes les données
            all_data = worksheet.get_all_values()
            if not all_data:
                self.errors.append("Aucune donnée trouvée dans la feuille")
                self._log_sync('error')
                return False
                
            # Extraire les en-têtes et les données
            headers = all_data[0]
            rows = all_data[1:]
            
            # Traiter chaque ligne
            for i, row in enumerate(rows, 2):  # Commencer à 2 car la ligne 1 contient les en-têtes
                if len(row) == len(headers):  # Vérifier que la ligne a le bon nombre de colonnes
                    success = self.process_row(row, headers)
                else:
                    self.errors.append(f"Ligne {i} ignorée: nombre de colonnes incorrect ({len(row)} vs {len(headers)})")
            
            # Déterminer le statut final
            if self.errors:
                status = 'partial' if self.records_imported > 0 else 'error'
            else:
                status = 'success'
                
            self._log_sync(status)
            return status == 'success' or status == 'partial'
            
        except Exception as e:
            self.errors.append(f"Erreur de synchronisation: {str(e)}")
            self._log_sync('error')
            return False
    
    def _log_sync(self, status):
        """Enregistre un log de synchronisation"""
        SyncLog.objects.create(
            status=status,
            records_imported=self.records_imported,
            errors='\n'.join(self.errors) if self.errors else None,
            sheet_config=self.sheet_config,
            triggered_by=self.triggered_by
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
                    client_tel = str(row_data.get('Téléphone')).replace('-', '') # Clean phone number
                    adresse = row_data.get('Adresse')
                    ville_name = row_data.get('Ville')
                    produit_str = row_data.get('Produit')
                    quantite = row_data.get('Quantité')
                    prix = row_data.get('Prix')
                    date_creation_str = row_data.get('Date Création')
                    motifs = row_data.get('Motifs')

                    if not numero_commande:
                        raise ValueError("Skipping row: 'N° Commande' is missing.")
                    
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
                        numero_commande=numero_commande,
                        defaults={
                            'statut': statut_csv,
                            'operateur': operateur_obj,
                            'client': client,
                            'telephone': client_tel,
                            'adresse': adresse,
                            'ville': ville_name, # Storing name, not object, based on CSV
                            'produit': produit_str, # Store raw product string
                            'quantite': int(quantite) if quantite else 0, # Ensure integer
                            'prix': float(prix) if prix else 0.0, # Ensure float
                            'date_creation': date_cmd,
                            'motifs': motifs,
                        }
                    )
                    if created_commande:
                        logs.append(f"Successfully created order: {commande.numero_commande}")
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

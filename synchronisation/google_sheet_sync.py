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
    
    def parse_product(self, product_str):
        """Parse le format de produit et retourne les composants, en gérant plusieurs formats de manière robuste."""
        try:
            # Dictionnaire des couleurs connues pour une meilleure détection
            colors_fr = ['noir', 'blanc', 'beige', 'marron', 'bleu', 'rouge', 'vert', 'rose', 'gris', 
                         'bleu ciel', 'bleu marine', 'sablé', 'tabac', 'grenat', 'saumon']
            
            # Dictionnaire des catégories en fonction des préfixes de produits
            categories = {
                'SDL': 'Sandale',
                'CHAUSS': 'Chaussure',
                'ESCA': 'Escarpin',
                'ESPA': 'Espadrille',
                'MULE': 'Mule',
                'BOTT': 'Botte',
                'BASK': 'Basket',
                'BAL': 'Ballerine'
            }
            
            # Nettoyage de la chaîne
            s = product_str.strip()
            s = re.sub(r'عرض.*درهم|قطعتين.*درهم', '', s, flags=re.IGNORECASE).strip()
            s = re.sub(r'\s*TK\s*', ' ', s, flags=re.IGNORECASE).strip()
            s = s.replace('--', '').strip()
            
            # Extraction initiale des parties
            parts = []
            for delimiter in ['/', '-']:
                if delimiter in s:
                    parts.extend([p.strip() for p in s.split(delimiter) if p.strip()])
                    break
            
            # Si aucun délimiteur n'a été trouvé, on traite la chaîne entière
            if not parts:
                parts = [s]
            
            # Initialisation des variables
            size = 'N/A'
            color_fr = 'N/A'
            color_ar = 'N/A'
            product_parts = []
            category = 'Non spécifiée'
            
            # Première passe : identification des parties évidentes
            for part in parts:
                # Détection de la taille
                if re.match(r'^\d{2}$', part) or part.upper() in ['S', 'M', 'L', 'XL', 'XXL']:
                    size = part
                    continue
                
                # Détection de la couleur arabe (contient uniquement des caractères arabes)
                if re.match(r'^[\u0600-\u06FF\s]+$', part):
                    color_ar = part
                    continue
                
                # Détection de la couleur française (correspond à une couleur connue)
                part_lower = part.lower()
                if part_lower in colors_fr:
                    color_fr = part_lower
                    continue
                
                # Si on arrive ici, c'est une partie du nom du produit
                product_parts.append(part)
            
            # Construction du nom du produit
            product_code = ' '.join(product_parts)
            
            # Deuxième passe : recherche dans le nom du produit si certains éléments sont manquants
            if size == 'N/A':
                size_match = re.search(r'\b(\d{2}|[SMLX]{1,3})\b', product_code)
                if size_match:
                    size = size_match.group(1)
            
            # Recherche de couleurs dans le nom du produit
            if color_fr == 'N/A':
                # Recherche des couleurs connues dans le nom du produit
                for color in colors_fr:
                    if re.search(r'\b' + color + r'\b', product_code.lower(), re.IGNORECASE):
                        color_fr = color
                        break
                
                # Cas spéciaux pour les couleurs
                if color_fr == 'N/A':
                    # Vérifier si une couleur est mentionnée dans le nom du produit
                    color_words = re.findall(r'\b[a-zA-Z]+\b', product_code.lower())
                    for word in color_words:
                        # Si le mot n'est pas un préfixe connu et n'est pas un mot commun
                        if (word not in ['fem', 'hom', 'yz', 'sdl', 'esca', 'espa', 'mule', 'chauss', 'bott', 'bask', 'bal'] and 
                            len(word) > 2 and not re.match(r'^[yz]\d+$', word.lower())):
                            color_fr = word
                            break
            
            # Détermination de la catégorie
            for prefix, cat in categories.items():
                if product_code.upper().startswith(prefix) or any(part.upper().startswith(prefix) for part in parts):
                    category = cat
                    break
            
            # Si FEM ou HOM est dans le nom, c'est probablement une chaussure pour femme ou homme
            if 'FEM' in product_code.upper():
                if category == 'Non spécifiée':
                    category = 'Chaussures Femme'
                else:
                    category += ' Femme'
            elif 'HOM' in product_code.upper():
                if category == 'Non spécifiée':
                    category = 'Chaussures Homme'
                else:
                    category += ' Homme'
            
            # Nettoyage final du nom du produit
            product_code = re.sub(r'\s{2,}', ' ', product_code).strip()
            
            return {
                'product_code': product_code[:50],
                'size': size,
                'color_ar': color_ar,
                'color_fr': color_fr,
                'category': category
            }
            
        except Exception as e:
            self.errors.append(f"Erreur de parsing du produit '{product_str}': {str(e)}")
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
            
            # Vérifier si la commande existe déjà - essayer différentes variantes de clés
            order_number = data.get('N° Commande') or data.get('Numéro') or data.get('N°Commande') or data.get('Numero')
            if not order_number or not order_number.strip():
                self._log(f"Ligne rejetée : numéro de commande manquant ou vide", "error")
                return False
            
            self._log(f"Vérification commande {order_number}")
            
            # Vérifier si la commande existe déjà
            existing_commande = Commande.objects.filter(num_cmd=order_number).first()
            if existing_commande:
                # Commande existe déjà - pas d'insertion
                self._log(f"Commande {order_number} existe déjà (ID YZ: {existing_commande.id_yz}) - IGNORÉE")
                self.duplicate_orders_found += 1
                
                # Vérifier si une mise à jour est nécessaire
                should_update = self._should_update_command(existing_commande, data)
                if should_update:
                    self._log(f"Mise à jour détectée pour commande existante {order_number}")
                    success = self._update_existing_command(existing_commande, data, headers)
                    if success:
                        self.existing_orders_updated += 1
                    return success
                else:
                    # Aucun changement nécessaire
                    self._log(f"Commande {order_number} inchangée - aucune action requise")
                    self.existing_orders_skipped += 1
                    return True
            
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
            print(f"➕ Création NOUVELLE commande {order_number}")
            commande = Commande.objects.create(
                num_cmd=order_number,
                date_cmd=self._parse_date(data.get('Date', '')),
                total_cmd=total_cmd_price,
                adresse=data.get('Adresse', ''),
                client=client_obj,
                ville=None,
                ville_init=data.get('Ville', '').strip(),
                produit_init=data.get('Produit', ''),
                origine='GSheet',
                last_sync_date=timezone.now() # Définir la date de dernière synchronisation
            )
            self._log(f"✅ NOUVELLE commande créée avec ID YZ: {commande.id_yz} et numéro externe: {commande.num_cmd}", "info")
            self.new_orders_created += 1

            # Parser le produit et créer l'article de commande et le panier
            product_str = data.get('Produit', '').strip()
            product_info = self.parse_product(product_str)
            article_obj = None

            try:
                if product_info:
                    # Tronquer la référence si elle est trop longue
                    reference = product_info['product_code']
                    if len(reference) > 50:
                        reference = reference[:50]

                    article_obj, created = Article.objects.get_or_create(
                        reference=reference,
                        defaults={
                            'nom': product_info['product_code'],
                            'description': f"Taille: {product_info['size']}, Couleur (FR): {product_info['color_fr']}, Couleur (AR): {product_info['color_ar']}",
                            'prix_unitaire': total_cmd_price,
                            'couleur': product_info['color_fr'],
                            'pointure': product_info['size'],
                            'categorie': product_info.get('category', 'Non spécifiée'),
                            'qte_disponible': 1, # Default à 1 pour la disponibilité
                        }
                    )
                
                elif product_str:
                    # Si le formatage du produit n'est pas standard, utiliser le produit brut comme référence
                    article_ref = product_str[:50] # Truncate to 50
                    article_nom = product_str[:200]
                    
                    article_obj, created = Article.objects.get_or_create(
                        reference=article_ref,
                        defaults={
                            'nom': article_nom,
                            'description': "Article synchronisé (format non standard)",
                            'prix_unitaire': total_cmd_price,
                            'couleur': 'N/A',
                            'pointure': 'N/A',
                            'categorie': 'Non spécifiée',
                            'qte_disponible': 0,
                        }
                    )
                    self._log(f"Article trouvé/créé avec référence brute: {article_ref}")

                else:
                    # Cas où le produit est vide: créer un article générique
                    article_nom = f"Article manquant #{commande.id_yz}"
                    article_ref = f"SYNC_MISSING_{commande.id_yz}"
                    
                    article_obj, created = Article.objects.get_or_create(
                        reference=article_ref,
                        defaults={
                            'nom': article_nom,
                            'description': "Aucun produit spécifié dans la source de données.",
                            'prix_unitaire': total_cmd_price,
                            'couleur': 'N/A',
                            'pointure': 'N/A',
                            'categorie': 'Non spécifiée',
                            'qte_disponible': 0,
                        }
                    )
                    self.warnings.append(f"Aucun produit spécifié pour la commande {commande.num_cmd}, article générique créé.")

                # Créer l'entrée dans le panier si un article a été trouvé ou créé
                if article_obj:
                    quantite = int(data.get('Quantité', 1)) if data.get('Quantité') else 1
                    Panier.objects.create(
                        commande=commande,
                        article=article_obj,
                        quantite=quantite,
                        sous_total=total_cmd_price  # Utilise le prix de la commande comme sous-total pour l'article unique
                    )
                    self._log(f"Panier créé pour la commande ID YZ: {commande.id_yz} (Ext: {commande.num_cmd}) avec l'article {article_obj.nom}")

            except Exception as e:
                self.errors.append(f"Erreur lors de la création de l'article/panier pour la commande ID YZ: {commande.id_yz} (Ext: {commande.num_cmd}): {str(e)}")

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
                if status_libelle:  # Seulement si un statut valide a été mappé
                    self._create_etat_commande(commande, status_libelle, operateur_obj)
                else:
                    # Si le statut n'a pas pu être mappé, utiliser l'état par défaut pour les nouvelles commandes
                    self._create_etat_commande(commande, 'En attente', operateur_obj)
            else:
                # État par défaut si aucun statut n'est spécifié
                self._create_etat_commande(commande, 'En attente', operateur_obj)

            self.records_imported += 1
            return True
            
        except Exception as e:
            self.errors.append(f"Erreur lors du traitement de la ligne: {str(e)}")
            return False
    
    def _should_update_command(self, existing_commande, data):
        """Détermine si une commande existante doit être mise à jour"""
        # Vérifier si le statut a changé
        current_status = existing_commande.etat_actuel.enum_etat.libelle if existing_commande.etat_actuel else 'En attente'
        new_status_raw = self._map_status(data.get('Statut', ''))
        
        # Si aucun statut valide n'a été mappé, ne pas changer l'état
        if new_status_raw is None:
            new_status = current_status  # Garder le statut actuel
        else:
            new_status = new_status_raw
        
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
            changes_made = []
            
            print(f"🔄 Mise à jour en arrière-plan pour commande existante {existing_commande.num_cmd}")
            
            # Mettre à jour le prix si nécessaire
            try:
                new_price = float(data.get('Prix', 0)) or float(data.get('Total', 0))
                if abs(float(existing_commande.total_cmd) - new_price) > 0.01:
                    old_price = existing_commande.total_cmd
                    existing_commande.total_cmd = new_price
                    changes_made.append(f"Prix: {old_price} → {new_price}")
                    updated = True
            except (ValueError, TypeError):
                pass
            
            # Mettre à jour l'adresse si nécessaire
            new_address = data.get('Adresse', '')
            if new_address and existing_commande.adresse != new_address:
                old_address = existing_commande.adresse
                existing_commande.adresse = new_address
                changes_made.append(f"Adresse: '{old_address}' → '{new_address}'")
                updated = True
            
            # Mettre à jour la ville_init si nécessaire
            new_ville_nom = data.get('Ville', '').strip()
            if new_ville_nom and existing_commande.ville_init != new_ville_nom:
                old_ville_init = existing_commande.ville_init
                existing_commande.ville_init = new_ville_nom
                changes_made.append(f"Ville: '{old_ville_init}' → '{new_ville_nom}'")
                updated = True
            
            # Sauvegarder les changements de la commande
            if updated:
                existing_commande.last_sync_date = timezone.now() # Mettre à jour la date de dernière synchronisation
                existing_commande.save()
                print(f"📝 Commande mise à jour: ID YZ {existing_commande.id_yz} - Changements: {', '.join(changes_made)}")
            
            # Mettre à jour le statut si nécessaire
            new_status_raw = self._map_status(data.get('Statut', ''))
            if new_status_raw is not None:  # Seulement si un statut valide a été mappé
                current_status = existing_commande.etat_actuel.enum_etat.libelle if existing_commande.etat_actuel else 'En attente'
                
                # PROTECTION CONTRE LA RÉGRESSION D'ÉTATS
                # Si la commande a déjà un état avancé, ne pas la réinitialiser à un état basique
                if self._is_advanced_status(current_status) and self._is_basic_status(new_status_raw):
                    self._log(f"Protection activée lors de la mise à jour: Commande {existing_commande.num_cmd} garde l'état avancé '{current_status}' au lieu de régresser vers '{new_status_raw}'")
                    self.protected_orders_count += 1  # Incrémenter le compteur de protection
                    new_status_raw = current_status  # Garder le statut actuel
                
                if current_status != new_status_raw:
                    # Récupérer l'opérateur si spécifié
                    operateur_obj = None
                    operator_name = data.get('Opérateur', '')
                    if operator_name:
                        try:
                            operateur_obj = Operateur.objects.get(nom_complet__iexact=operator_name)
                        except Operateur.DoesNotExist:
                            self.errors.append(f"Opérateur non trouvé: {operator_name}")
                    
                    # Créer le nouvel état
                    self._create_etat_commande(existing_commande, new_status_raw, operateur_obj)
                    changes_made.append(f"Statut: '{current_status}' → '{new_status_raw}'")
                    print(f"📊 État mis à jour pour commande existante ID YZ {existing_commande.id_yz}: {current_status} → {new_status_raw}")
                else:
                    self._log(f"Statut inchangé pour commande {existing_commande.num_cmd}: {current_status}")
            else:
                self._log(f"Aucun statut valide trouvé pour commande {existing_commande.num_cmd} - état conservé")
            
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
                    print(f"👤 Client mis à jour: {client_obj.get_full_name()} - {', '.join(client_changes)}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Erreur lors de la mise à jour de la commande existante {existing_commande.num_cmd}: {str(e)}")
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
        
        # Si le statut est vide ou null, retourner None pour indiquer qu'aucun changement n'est nécessaire
        if not cleaned_status:
            return None
        
        # Chercher dans le dictionnaire (recherche exacte puis insensible à la casse)
        if cleaned_status in status_map:
            return status_map[cleaned_status]
            
        # Recherche insensible à la casse
        for key, value in status_map.items():
            if key.lower() == cleaned_status.lower():
                return value
        
        # Si aucun statut ne correspond, retourner None au lieu de 'En attente'
        # Cela évite de forcer un état par défaut qui pourrait régresser une commande
        self._log(f"Statut non reconnu: '{cleaned_status}' - aucun changement d'état appliqué")
        return None

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
        # Marquer le début de la synchronisation
        self.start_time = timezone.now()
        self.execution_details['started_at'] = self.start_time.isoformat()
        
        client = self.authenticate()
        if not client:
            self.end_time = timezone.now()
            self._log_sync('error')
            return False
            
        worksheet = self.get_sheet(client)
        if not worksheet:
            self.end_time = timezone.now()
            self._log_sync('error')
            return False
            
        try:
            # Enregistrer les informations de la feuille
            self.sheet_title = worksheet.spreadsheet.title
            self.execution_details['spreadsheet_title'] = worksheet.spreadsheet.title
            self.execution_details['worksheet_name'] = worksheet.title
            
            # Récupérer toutes les données
            all_data = worksheet.get_all_values()
            if not all_data:
                self.errors.append("Aucune donnée trouvée dans la feuille")
                self.end_time = timezone.now()
                self._log_sync('error')
                return False
                
            # Extraire les en-têtes et les données
            headers = all_data[0]
            rows = all_data[1:]
            
            # Enregistrer les statistiques
            self.total_rows = len(all_data)
            self.execution_details['headers'] = headers
            self.execution_details['total_rows'] = len(all_data)
            self.execution_details['data_rows'] = len(rows)
            
            self._log(f"Synchronisation démarrée - Total lignes à traiter : {len(rows)}")
            self._log(f"En-têtes détectés : {headers}")
            
            # Traiter chaque ligne
            for i, row in enumerate(rows, 2):  # Commencer à 2 car la ligne 1 contient les en-têtes
                # Vérifier si la ligne est vide
                if not any(cell.strip() for cell in row if cell):
                    self._log(f"Ligne {i} ignorée : ligne complètement vide")
                    self.skipped_rows += 1
                    continue
                    
                if len(row) == len(headers):  # Vérifier que la ligne a le bon nombre de colonnes
                    self._log(f"Traitement ligne {i} : {dict(zip(headers[:3], row[:3]))}...")  # Afficher les 3 premiers champs
                    success = self.process_row(row, headers)
                    if success:
                        self._log(f"Ligne {i} traitée avec succès")
                        self.processed_rows += 1
                    else:
                        self._log(f"Échec traitement ligne {i}")
                        self.skipped_rows += 1
                else:
                    error_msg = f"Ligne {i} ignorée: nombre de colonnes incorrect ({len(row)} vs {len(headers)})"
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
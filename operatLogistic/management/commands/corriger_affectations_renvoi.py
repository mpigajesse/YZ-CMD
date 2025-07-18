from django.core.management.base import BaseCommand
from django.db import transaction
from parametre.models import Operateur
from commande.models import Commande, EtatCommande
from django.db.models import Count, Q


class Command(BaseCommand):
    help = 'Corrige automatiquement l\'affectation des commandes renvoyées en préparation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les corrections qui seraient effectuées sans les appliquer',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("🔍 Recherche des commandes renvoyées en préparation...")
        
        # Trouver toutes les commandes renvoyées en préparation
        commandes_renvoyees = Commande.objects.filter(
            etats__enum_etat__libelle='En préparation',
            etats__date_fin__isnull=True
        ).distinct()
        
        self.stdout.write(f"📋 {commandes_renvoyees.count()} commandes renvoyées trouvées")
        
        corrections_effectuees = 0
        erreurs = 0
        
        for commande in commandes_renvoyees:
            try:
                # Trouver l'état actuel
                etat_actuel = commande.etats.filter(
                    enum_etat__libelle='En préparation', 
                    date_fin__isnull=True
                ).first()
                
                if not etat_actuel:
                    continue
                    
                # Chercher l'opérateur original qui avait préparé
                etat_preparee_original = commande.etats.filter(
                    enum_etat__libelle='Préparée',
                    date_fin__isnull=False
                ).order_by('-date_fin').first()
                
                operateur_cible = None
                
                if etat_preparee_original and etat_preparee_original.operateur:
                    if (etat_preparee_original.operateur.type_operateur == 'PREPARATION' and 
                        etat_preparee_original.operateur.actif):
                        operateur_cible = etat_preparee_original.operateur
                        self.stdout.write(f"  ✅ Opérateur original trouvé pour commande {commande.id_yz}: {operateur_cible.nom_complet}")
                
                # Si pas d'opérateur original, prendre le moins chargé
                if not operateur_cible:
                    operateurs_preparation = Operateur.objects.filter(
                        type_operateur='PREPARATION',
                        actif=True
                    ).order_by('id')
                    
                    if operateurs_preparation.exists():
                        operateur_cible = operateurs_preparation.annotate(
                            commandes_en_cours=Count('etats_modifies', filter=Q(
                                etats_modifies__enum_etat__libelle__in=['À imprimer', 'En préparation'],
                                etats_modifies__date_fin__isnull=True
                            ))
                        ).order_by('commandes_en_cours', 'id').first()
                        
                        self.stdout.write(f"  ⚠️  Affectation au moins chargé pour commande {commande.id_yz}: {operateur_cible.nom_complet} ({operateur_cible.commandes_en_cours} commandes)")
                    else:
                        self.stdout.write(f"  ❌ Aucun opérateur de préparation disponible pour commande {commande.id_yz}")
                        erreurs += 1
                        continue
                
                # Vérifier si une correction est nécessaire
                if etat_actuel.operateur != operateur_cible:
                    if dry_run:
                        self.stdout.write(
                            f"  🔧 [DRY-RUN] Commande {commande.id_yz}: "
                            f"{etat_actuel.operateur} → {operateur_cible.nom_complet}"
                        )
                    else:
                        with transaction.atomic():
                            ancien_operateur = etat_actuel.operateur
                            etat_actuel.operateur = operateur_cible
                            etat_actuel.save()
                            corrections_effectuees += 1
                            self.stdout.write(
                                f"  ✅ Commande {commande.id_yz}: "
                                f"{ancien_operateur} → {operateur_cible.nom_complet}"
                            )
                else:
                    self.stdout.write(f"  ✅ Commande {commande.id_yz}: affectation correcte ({etat_actuel.operateur})")
                    
            except Exception as e:
                self.stdout.write(f"  ❌ Erreur pour commande {commande.id_yz}: {e}")
                erreurs += 1
        
        # Résumé
        self.stdout.write("\n" + "="*50)
        if dry_run:
            self.stdout.write(f"🔍 DRY-RUN: {corrections_effectuees} corrections seraient effectuées")
        else:
            self.stdout.write(f"✅ {corrections_effectuees} corrections effectuées")
        
        if erreurs > 0:
            self.stdout.write(f"❌ {erreurs} erreurs rencontrées")
        
        self.stdout.write("="*50) 
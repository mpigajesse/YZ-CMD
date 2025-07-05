from django.core.management.base import BaseCommand
from django.utils import timezone
from article.models import Promotion, Article

class Command(BaseCommand):
    help = 'Force l\'application des promotions actives aux articles concernés'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Afficher les changements sans les appliquer'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Afficher plus de détails'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        now = timezone.now()
        
        # Statistiques
        stats = {
            'promotions_traitees': 0,
            'articles_mis_a_jour': 0,
            'promotions_activees': 0,
            'promotions_desactivees': 0
        }
        
        self.stdout.write(f"{'=' * 60}")
        self.stdout.write(self.style.SUCCESS("FORCER L'APPLICATION DES PROMOTIONS"))
        self.stdout.write(f"{'=' * 60}")
        self.stdout.write(f"Mode: {'DRY RUN (simulation)' if dry_run else 'EXECUTION RÉELLE'}")
        self.stdout.write(f"Date/Heure: {now.strftime('%d/%m/%Y %H:%M:%S')}")
        self.stdout.write("")
        
        # Récupérer toutes les promotions
        all_promotions = Promotion.objects.all().order_by('date_debut')
        
        self.stdout.write(f"Total des promotions à analyser: {all_promotions.count()}")
        self.stdout.write("")
        
        for promotion in all_promotions:
            stats['promotions_traitees'] += 1
            
            # Vérifier l'état de la promotion
            should_be_active = promotion.date_debut <= now <= promotion.date_fin
            is_currently_active = promotion.active
            
            if verbose:
                self.stdout.write(f"📋 Promotion: {promotion.nom}")
                self.stdout.write(f"   Période: {promotion.date_debut.strftime('%d/%m/%Y %H:%M')} → {promotion.date_fin.strftime('%d/%m/%Y %H:%M')}")
                self.stdout.write(f"   Réduction: {promotion.pourcentage_reduction}%")
                self.stdout.write(f"   Articles: {promotion.articles.count()}")
                self.stdout.write(f"   État DB: {'Actif' if is_currently_active else 'Inactif'}")
                self.stdout.write(f"   État attendu: {'Actif' if should_be_active else 'Inactif'}")
            
            # Cas 1: La promotion devrait être active mais ne l'est pas
            if should_be_active and not is_currently_active:
                if not dry_run:
                    promotion.activer_promotion()
                stats['promotions_activees'] += 1
                stats['articles_mis_a_jour'] += promotion.articles.count()
                
                self.stdout.write(self.style.WARNING(f"🔄 Activation de '{promotion.nom}' ({promotion.articles.count()} articles)"))
                
                if verbose and not dry_run:
                    for article in promotion.articles.all():
                        economie = article.prix_unitaire - article.prix_actuel
                        self.stdout.write(f"   ✅ {article.nom} - {article.couleur} - {article.pointure}: "
                                        f"{article.prix_unitaire}DH → {article.prix_actuel}DH (économie: {economie}DH)")
            
            # Cas 2: La promotion devrait être inactive mais est active
            elif not should_be_active and is_currently_active:
                if not dry_run:
                    promotion.desactiver_promotion()
                stats['promotions_desactivees'] += 1
                stats['articles_mis_a_jour'] += promotion.articles.count()
                
                if now > promotion.date_fin:
                    self.stdout.write(self.style.ERROR(f"⏰ Désactivation de '{promotion.nom}' (expirée le {promotion.date_fin.strftime('%d/%m/%Y')})"))
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Désactivation de '{promotion.nom}' (future, commence le {promotion.date_debut.strftime('%d/%m/%Y')})"))
                
                if verbose and not dry_run:
                    for article in promotion.articles.all():
                        self.stdout.write(f"   🔄 {article.nom} - {article.couleur} - {article.pointure}: "
                                        f"prix remis à {article.prix_unitaire}DH")
            
            # Cas 3: La promotion est dans le bon état mais vérifier les prix des articles
            elif should_be_active and is_currently_active:
                articles_a_corriger = []
                for article in promotion.articles.all():
                    # Calculer le prix attendu
                    reduction = article.prix_unitaire * (promotion.pourcentage_reduction / 100)
                    prix_attendu = article.prix_unitaire - reduction
                    
                    # Vérifier si le prix actuel correspond
                    if abs(article.prix_actuel - prix_attendu) > 0.01:  # Tolérance de 1 centime
                        articles_a_corriger.append(article)
                
                if articles_a_corriger:
                    self.stdout.write(self.style.WARNING(f"🔧 Correction des prix pour '{promotion.nom}' ({len(articles_a_corriger)} articles)"))
                    stats['articles_mis_a_jour'] += len(articles_a_corriger)
                    
                    if not dry_run:
                        for article in articles_a_corriger:
                            article.appliquer_promotion(promotion)
                    
                    if verbose:
                        for article in articles_a_corriger:
                            reduction = article.prix_unitaire * (promotion.pourcentage_reduction / 100)
                            prix_attendu = article.prix_unitaire - reduction
                            self.stdout.write(f"   💰 {article.nom} - {article.couleur} - {article.pointure}: "
                                            f"{article.prix_actuel}DH → {prix_attendu}DH")
                elif verbose:
                    self.stdout.write(self.style.SUCCESS(f"✅ '{promotion.nom}' est correctement appliquée"))
            
            else:
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f"✅ '{promotion.nom}' est dans le bon état"))
            
            if verbose:
                self.stdout.write("")
        
        # Vérifier les articles qui pourraient avoir des prix incorrects
        self.stdout.write("🔍 Vérification des articles sans promotion active...")
        articles_sans_promo = Article.objects.filter(actif=True)
        articles_corriges = 0
        
        for article in articles_sans_promo:
            if not article.has_promo_active and article.prix_actuel != article.prix_unitaire:
                if not dry_run:
                    article.prix_actuel = article.prix_unitaire
                    article.save(update_fields=['prix_actuel'])
                articles_corriges += 1
                
                if verbose:
                    self.stdout.write(f"   🔄 {article.nom} - {article.couleur} - {article.pointure}: "
                                    f"prix remis à {article.prix_unitaire}DH")
        
        if articles_corriges > 0:
            self.stdout.write(self.style.WARNING(f"🔧 {articles_corriges} articles sans promotion corrigés"))
            stats['articles_mis_a_jour'] += articles_corriges
        
        # Résumé final
        self.stdout.write("")
        self.stdout.write(f"{'=' * 60}")
        self.stdout.write(self.style.SUCCESS("RÉSUMÉ DE L'OPÉRATION"))
        self.stdout.write(f"{'=' * 60}")
        self.stdout.write(f"Promotions traitées: {stats['promotions_traitees']}")
        self.stdout.write(f"Promotions activées: {stats['promotions_activees']}")
        self.stdout.write(f"Promotions désactivées: {stats['promotions_desactivees']}")
        self.stdout.write(f"Articles mis à jour: {stats['articles_mis_a_jour']}")
        
        if dry_run:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("⚠️  SIMULATION TERMINÉE - Aucun changement appliqué"))
            self.stdout.write("Pour appliquer les changements, exécutez la commande sans --dry-run")
        else:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("✅ OPÉRATION TERMINÉE AVEC SUCCÈS"))
        
        self.stdout.write(f"{'=' * 60}") 
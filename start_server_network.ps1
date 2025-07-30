# Script PowerShell pour démarrer YZ-CMD sur le réseau local

Write-Host "=========================================" -ForegroundColor Green
Write-Host "   YZ-CMD - Serveur Réseau Local" -ForegroundColor Green  
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Configuration réseau :" -ForegroundColor Yellow
Write-Host "- Localhost : http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "- Réseau local : http://192.168.216.128:8000" -ForegroundColor Cyan
Write-Host ""

# Vérifier si l'environnement virtuel existe
if (Test-Path "env\Scripts\Activate.ps1") {
    Write-Host "Activation de l'environnement virtuel..." -ForegroundColor Yellow
    & "env\Scripts\Activate.ps1"
} else {
    Write-Host "ERREUR: Environnement virtuel non trouvé!" -ForegroundColor Red
    Write-Host "Assurez-vous que le dossier 'env' existe." -ForegroundColor Red
    pause
    exit
}

Write-Host ""
Write-Host "Vérification des migrations..." -ForegroundColor Yellow
python manage.py migrate

Write-Host ""
Write-Host "Démarrage du serveur sur le réseau..." -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT :" -ForegroundColor Red
Write-Host "- Assurez-vous que le port 8000 n'est pas bloqué par le pare-feu" -ForegroundColor White
Write-Host "- L'application sera accessible depuis d'autres appareils du réseau" -ForegroundColor White
Write-Host "- Utilisez Ctrl+C pour arrêter le serveur" -ForegroundColor White
Write-Host ""

# Démarrer le serveur
python manage.py runserver 0.0.0.0:8000 
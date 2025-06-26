@echo off
echo =========================================
echo   YZ-CMD - Serveur Reseau Local
echo =========================================
echo.
echo Configuration reseau :
echo - Localhost : http://127.0.0.1:8000
echo - Reseau local : http://192.168.216.128:8000
echo.
echo Activation de l'environnement virtuel...
call env\Scripts\activate
echo.
echo Verification des migrations...
python manage.py migrate
echo.
echo Demarrage du serveur sur le reseau...
echo.
echo IMPORTANT : 
echo - Assurez-vous que le port 8000 n'est pas bloque par le pare-feu
echo - L'application sera accessible depuis d'autres appareils du reseau
echo.
python manage.py runserver 0.0.0.0:8000
pause 
from django import template
from django.utils.safestring import mark_safe
import base64
from io import BytesIO

register = template.Library()

@register.filter
def barcode_image(reference):
    """
    Génère une image de QR code à partir d'une référence.
    Retourne une chaîne base64 de l'image PNG.
    """
    if not reference:
        return ""
    
    try:
        # Import ici pour éviter les erreurs si la bibliothèque n'est pas installée
        import qrcode
        
        # Créer le QR code
        qr = qrcode.QRCode(
            version=1,               # Version 1 (21x21 modules)
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # Niveau de correction d'erreur bas
            box_size=10,             # Taille de chaque module (pixel)
            border=4,                # Bordure autour du QR code
        )
        
        # Ajouter les données
        qr.add_data(str(reference))
        qr.make(fit=True)
        
        # Créer l'image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Créer un buffer pour l'image
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        
        # Convertir en base64
        buffer.seek(0)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return qr_base64
        
    except ImportError:
        # Si la bibliothèque qrcode n'est pas installée
        print("Erreur: La bibliothèque qrcode n'est pas installée")
        return ""
    except Exception as e:
        # En cas d'erreur, retourner une chaîne vide
        print(f"Erreur lors de la génération du QR code pour {reference}: {e}")
        return ""

@register.filter
def barcode_image_url(reference):
    """
    Génère une URL d'image de QR code à partir d'une référence.
    Retourne une URL data:image/png;base64,...
    """
    qr_base64 = barcode_image(reference)
    if qr_base64:
        return f"data:image/png;base64,{qr_base64}"
    return ""

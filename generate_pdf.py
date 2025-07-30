#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de génération PDF pour la documentation YZ-CMD
Convertit projetModel.md en PDF avec mise en forme professionnelle
COD$uite Team - Version 2.0
"""

import markdown2
import os
from datetime import datetime

def generate_pdf():
    """Génère un PDF à partir du fichier projetModel.md"""
    
    # Lecture du fichier Markdown
    try:
        with open('projetModel.md', 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        print("✅ Fichier projetModel.md lu avec succès")
    except FileNotFoundError:
        print("❌ Erreur: Fichier projetModel.md non trouvé")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la lecture: {e}")
        return False

    # Conversion Markdown vers HTML
    try:
        html_content = markdown2.markdown(
            markdown_content, 
            extras=[
                'tables', 
                'fenced-code-blocks', 
                'header-ids',
                'toc',
                'strike',
                'task_list'
            ]
        )
        print("✅ Conversion Markdown → HTML réussie")
    except Exception as e:
        print(f"❌ Erreur lors de la conversion MD→HTML: {e}")
        return False

    # CSS pour la mise en forme professionnelle
    css_style = """
    <style>
        @page {
            size: A4;
            margin: 2.5cm 2cm;
            @top-center {
                content: "Documentation YZ-CMD - COD$uite Team";
                font-size: 10px;
                color: #666;
                font-family: 'Segoe UI', sans-serif;
            }
            @bottom-center {
                content: "Page " counter(page);
                font-size: 10px;
                color: #666;
                font-family: 'Segoe UI', sans-serif;
            }
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            font-size: 11px;
        }
        
        h1 {
            color: #2563eb;
            border-bottom: 3px solid #2563eb;
            padding-bottom: 10px;
            page-break-before: always;
            font-size: 24px;
            margin-top: 0;
        }
        
        h1:first-child {
            page-break-before: avoid;
            margin-top: 20px;
        }
        
        h2 {
            color: #1e40af;
            border-bottom: 2px solid #93c5fd;
            padding-bottom: 5px;
            margin-top: 30px;
            font-size: 18px;
        }
        
        h3 {
            color: #1e3a8a;
            margin-top: 25px;
            font-size: 16px;
        }
        
        h4 {
            color: #1e40af;
            margin-top: 20px;
            font-size: 14px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 10px;
            page-break-inside: avoid;
        }
        
        th, td {
            border: 1px solid #d1d5db;
            padding: 6px 8px;
            text-align: left;
            vertical-align: top;
        }
        
        th {
            background-color: #f3f4f6;
            font-weight: bold;
            color: #374151;
        }
        
        tr:nth-child(even) {
            background-color: #f9fafb;
        }
        
        code {
            background-color: #f1f5f9;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 10px;
            color: #1e40af;
        }
        
        pre {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 5px;
            padding: 12px;
            overflow-x: auto;
            font-size: 10px;
            page-break-inside: avoid;
        }
        
        blockquote {
            border-left: 4px solid #3b82f6;
            margin: 15px 0;
            padding-left: 15px;
            color: #4b5563;
            font-style: italic;
        }
        
        ul, ol {
            margin: 10px 0;
            padding-left: 20px;
        }
        
        li {
            margin: 3px 0;
        }
        
        .warning {
            background-color: #fef3c7;
            border: 1px solid #f59e0b;
            border-radius: 5px;
            padding: 10px;
            margin: 15px 0;
            page-break-inside: avoid;
        }
        
        .info {
            background-color: #dbeafe;
            border: 1px solid #3b82f6;
            border-radius: 5px;
            padding: 10px;
            margin: 15px 0;
            page-break-inside: avoid;
        }
        
        .cover-page {
            text-align: center;
            page-break-after: always;
            margin-top: 100px;
        }
        
        .cover-title {
            font-size: 32px;
            color: #2563eb;
            margin-bottom: 20px;
            font-weight: bold;
        }
        
        .cover-subtitle {
            font-size: 18px;
            color: #1e40af;
            margin-bottom: 40px;
        }
        
        .cover-info {
            font-size: 14px;
            color: #6b7280;
            margin-top: 60px;
        }
    </style>
    """

    # Construction du HTML complet avec page de couverture
    current_date = datetime.now().strftime("%d/%m/%Y à %H:%M")
    
    full_html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Documentation YZ-CMD - COD$uite Team</title>
        {css_style}
    </head>
    <body>
        <div class="cover-page">
            <div class="cover-title">Documentation YZ-CMD</div>
            <div class="cover-subtitle">Système de Gestion de Commandes</div>
            <div class="cover-info">
                <p><strong>COD$uite Team</strong></p>
                <p>Version 2.0</p>
                <p>Généré le {current_date}</p>
            </div>
        </div>
        
        {html_content}
    </body>
    </html>
    """

    # Tentative avec WeasyPrint
    try:
        from weasyprint import HTML, CSS
        
        output_filename = f"Documentation_YZ-CMD_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Génération du PDF avec WeasyPrint
        HTML(string=full_html).write_pdf(
            output_filename,
            stylesheets=[CSS(string=css_style)]
        )
        
        print(f"✅ PDF généré avec succès: {output_filename}")
        print(f"📄 Taille du fichier: {os.path.getsize(output_filename) / 1024:.1f} KB")
        return True
        
    except ImportError:
        print("❌ WeasyPrint non disponible, tentative avec une méthode alternative...")
        return generate_html_alternative(full_html)
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération PDF avec WeasyPrint: {e}")
        return generate_html_alternative(full_html)

def generate_html_alternative(html_content):
    """Génère un fichier HTML si la génération PDF échoue"""
    try:
        output_filename = f"Documentation_YZ-CMD_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Fichier HTML généré: {output_filename}")
        print("💡 Vous pouvez ouvrir ce fichier dans votre navigateur et l'imprimer en PDF")
        print("💡 Ou utiliser 'Ctrl+P' → 'Enregistrer au format PDF'")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération HTML: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Génération du PDF de la documentation YZ-CMD...")
    print("📋 COD$uite Team - Version 2.0")
    print("=" * 60)
    
    success = generate_pdf()
    
    print("=" * 60)
    if success:
        print("✅ Génération terminée avec succès!")
        print("📄 Documentation prête à être utilisée")
    else:
        print("❌ Échec de la génération")
        print("💡 Vérifiez les dépendances ou utilisez la version HTML") 
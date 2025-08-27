import requests

def analyze_variantes_content():
    url = "http://127.0.0.1:8000/article/variantes/"
    try:
        response = requests.get(url, timeout=10)
        content = response.text
        
        print(f"Status: {response.status_code}")
        print(f"Longueur: {len(content)} caractères")
        print()
        
        # Vérifier les mots-clés
        keywords = ['variante', 'couleur', 'pointure', 'article', 'prix']
        for keyword in keywords:
            count = content.lower().count(keyword)
            print(f"'{keyword}': {count} occurrences")
        
        print()
        print("=== PREMIERS 1000 CARACTÈRES ===")
        print(content[:1000])
        
        print()
        print("=== DERNIERS 1000 CARACTÈRES ===")
        print(content[-1000:])
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    analyze_variantes_content()


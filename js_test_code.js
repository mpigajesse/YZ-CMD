
// Code JavaScript pour tester les codes-barres
// Copier ce code dans la console du navigateur

function testJsBarcode() {
    const references = ["BOT-FEM-YZ3010-Standard-37", "MULE-FEM-YZ1121-Beige-36", "BOT-FEM-YZ3010-Standard-40", "TEST-123-ABC", "PRODUCT-REF-001", "SHOES-MEN-42-BLACK", "BAG-WOMEN-LEATHER-BROWN"];
    const results = [];
    
    references.forEach((ref, index) => {
        console.log(`\n🧪 Test ${index + 1}/${references.length}: ${ref}`);
        
        try {
            const canvas = document.createElement('canvas');
            canvas.width = 400;
            canvas.height = 120;
            
            JsBarcode(canvas, ref, {
                format: "CODE128",
                width: 3,
                height: 80,
                displayValue: true,
                fontSize: 14,
                margin: 15,
                background: "#ffffff",
                lineColor: "#000000",
                fontOptions: "bold",
                textMargin: 8,
                valid: function(valid) {
                    console.log(`  ✅ Code128 valide: ${valid}`);
                    results.push({
                        reference: ref,
                        valid: valid,
                        success: true
                    });
                }
            });
            
            console.log(`  ✅ Code128 généré avec succès`);
            
        } catch (error) {
            console.error(`  ❌ Erreur: ${error.message}`);
            results.push({
                reference: ref,
                valid: false,
                success: false,
                error: error.message
            });
        }
    });
    
    console.log('\n📊 RÉSUMÉ:');
    const successCount = results.filter(r => r.success).length;
    const validCount = results.filter(r => r.valid).length;
    console.log(`  Succès: ${successCount}/${results.length}`);
    console.log(`  Valides: ${validCount}/${results.length}`);
    
    return results;
}

// Exécuter le test
const testResults = testJsBarcode();

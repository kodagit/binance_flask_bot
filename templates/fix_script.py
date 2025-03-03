with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Düzeltme 1: Syntax hatasını düzelt
content = content.replace('updateData();\n};', 'updateData();\n});')

# Düzeltme 2: changeSymbol fonksiyonunu ekle
change_symbol_function = '''</script>

<script>
// Sembol değiştirme fonksiyonu
function changeSymbol(symbol) {
    document.getElementById("symbol").value = symbol;
    // Grafiği güncelle
    if (window.tradingViewWidget) {
        // Widget'ı yeniden oluştur
        const container = document.getElementById("chart");
        container.innerHTML = "";
        
        window.tradingViewWidget = new TradingView.widget({
            "width": "100%",
            "height": "400",
            "symbol": "BINANCE:" + symbol,
            "interval": document.getElementById("interval").value,
            "timezone": "Europe/Istanbul",
            "theme": "dark",
            "style": "1",
            "locale": "tr",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "hide_side_toolbar": false,
            "allow_symbol_change": true,
            "container_id": "chart",
            "autosize": true
        });
    }
    // Verileri güncelle
    updateData();
}
</script>
{% endblock %}'''

content = content.replace('</script>\n{% endblock %}', change_symbol_function)

with open('index.html.fixed', 'w', encoding='utf-8') as f:
    f.write(content)

print('Dosya düzeltildi.')

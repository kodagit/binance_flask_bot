// Sayfa yüklendiğinde çalışacak
document.addEventListener('DOMContentLoaded', function() {
    // Varsayılan değerler
    if (!document.getElementById('symbol').value) {
        document.getElementById('symbol').value = "BTCUSDT";
    }
    
    if (!document.getElementById('interval').value) {
        document.getElementById('interval').value = "1h";
    }
    
    // Grafik oluştur
    initTradingViewWidget(document.getElementById('symbol').value, document.getElementById('interval').value);
    
    // İlk verileri yükle
    updateData();
    
    // Hesap bilgilerini güncelle
    updateAccountInfo();
    setInterval(updateAccountInfo, 30000);
});

// TradingView widget'ını başlat
function initTradingViewWidget(symbol, interval) {
    try {
        // Sembol formatını kontrol et ve düzelt
        let formattedSymbol = symbol;
        if (!formattedSymbol.includes(':')) {
            formattedSymbol = "BINANCE:" + formattedSymbol;
        }
        
        // Geçersiz sembol kontrolü
        if (formattedSymbol === "BINANCE:undefined" || formattedSymbol === "BINANCE:null") {
            formattedSymbol = "BINANCE:BTCUSDT";
            console.warn("Geçersiz sembol, varsayılan BTCUSDT kullanılıyor");
        }
        
        // Interval kontrolü
        if (!interval || interval === "undefined" || interval === "null") {
            interval = "1h";
            console.warn("Geçersiz interval, varsayılan 1h kullanılıyor");
        }
        
        console.log("Grafik yükleniyor:", formattedSymbol, interval);
        
        // Önceki widget'ı temizle
        if (window.tradingViewWidget) {
            try {
                delete window.tradingViewWidget;
            } catch (e) {
                console.warn("Önceki widget temizlenirken hata:", e);
            }
        }
        
        const container = document.getElementById('chart');
        container.innerHTML = '';
        
        // Yeni widget oluştur
        window.tradingViewWidget = new TradingView.widget({
            "width": "100%",
            "height": 400,
            "symbol": formattedSymbol,
            "interval": interval,
            "timezone": "Europe/Istanbul",
            "theme": "dark",
            "style": "1",
            "locale": "tr",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "hide_side_toolbar": false,
            "allow_symbol_change": true,
            "container_id": "chart",
            "autosize": true,
            "hide_top_toolbar": false,
            "save_image": false,
            "details": true,
            "hotlist": true,
            "calendar": true,
            "studies": [
                "RSI@tv-basicstudies",
                "MASimple@tv-basicstudies"
            ]
        });
    } catch (error) {
        console.error("Grafik oluşturulurken hata:", error);
        document.getElementById('chart').innerHTML = `
            <div class="alert alert-danger">
                <strong>Grafik yüklenemedi!</strong><br>
                Lütfen sayfayı yenileyin veya farklı bir sembol seçin.<br>
                <small>Hata: ${error.message}</small>
            </div>
        `;
    }
}

// Sembol değiştirme fonksiyonu
function changeSymbol(symbol) {
    try {
        if (!symbol || symbol === "undefined" || symbol === "null") {
            symbol = "BTCUSDT";
            console.warn("Geçersiz sembol, varsayılan BTCUSDT kullanılıyor");
        }
        
        document.getElementById('symbol').value = symbol;
        
        // Grafiği güncelle
        initTradingViewWidget(symbol, document.getElementById('interval').value);
        
        // Verileri güncelle
        updateData();
        
        // Botu durdur
        fetch('/api/bot/stop', {
            method: 'POST'
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Sunucu yanıt vermedi');
        })
        .then(data => {
            if (data && data.success) {
                botRunning = false;
                document.getElementById('start-bot-btn').classList.remove('btn-danger');
                document.getElementById('start-bot-btn').classList.add('btn-success');
                document.getElementById('start-bot-btn').innerHTML = '<i class="bi bi-play-fill"></i> Botu Başlat';
                document.getElementById('bot-status').classList.remove('bg-success');
                document.getElementById('bot-status').classList.add('bg-secondary');
                document.getElementById('bot-status').textContent = 'Durdu';
            } else {
                console.warn('Bot durdurulamadı:', data ? data.error : 'Bilinmeyen hata');
            }
        })
        .catch(error => {
            console.error('Bot durdurulurken hata:', error);
        });
    } catch (error) {
        console.error("Sembol değiştirme hatası:", error);
        alert("Sembol değiştirme sırasında bir hata oluştu: " + error.message);
    }
}

// Sembol veya interval değiştiğinde güncelle
document.getElementById('symbol').addEventListener('change', function() {
    const symbol = this.value;
    initTradingViewWidget(symbol, document.getElementById('interval').value);
    updateData();
});

document.getElementById('interval').addEventListener('change', function() {
    const interval = this.value;
    initTradingViewWidget(document.getElementById('symbol').value, interval);
    updateData();
});

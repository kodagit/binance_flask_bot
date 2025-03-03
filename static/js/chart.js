// Lightweight Charts kütüphanesi için yardımcı fonksiyonlar
let chart = null;
let candleSeries = null;

// Lightweight Chart oluşturma fonksiyonu
function createLightweightChart() {
    try {
        console.log("Lightweight Chart oluşturuluyor...");
        
        // Mevcut chart'ı temizle
        const container = document.getElementById('tradingview-widget-container');
        container.innerHTML = '';
        
        // Sembol ve interval değerlerini al
        let symbol = document.getElementById('symbol').value;
        const interval = document.getElementById('interval').value;
        
        // Geçersiz sembol kontrolü
        let cleanSymbol = symbol;
        if (!symbol || symbol === "undefined" || symbol === "null") {
            cleanSymbol = "BTCUSDT";
            document.getElementById('symbol').value = "BTCUSDT";
            console.warn("Geçersiz sembol, varsayılan BTCUSDT kullanılıyor");
        }
        
        console.log("Chart yükleniyor:", cleanSymbol, interval);
        
        // Yükleniyor göstergesi
        container.innerHTML = `
            <div class="d-flex justify-content-center align-items-center" style="height: 400px;">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Yükleniyor...</span>
                </div>
                <span class="ms-2">Grafik yükleniyor...</span>
            </div>
        `;
        
        // Chart oluştur
        chart = LightweightCharts.createChart(container, {
            width: container.clientWidth,
            height: 400,
            layout: {
                backgroundColor: '#131722',
                textColor: '#d1d4dc',
            },
            grid: {
                vertLines: {
                    color: 'rgba(42, 46, 57, 0.5)',
                },
                horzLines: {
                    color: 'rgba(42, 46, 57, 0.5)',
                },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            priceScale: {
                borderColor: 'rgba(197, 203, 206, 0.8)',
            },
            timeScale: {
                borderColor: 'rgba(197, 203, 206, 0.8)',
                timeVisible: true,
            },
        });
        
        // Mum serisi oluştur
        candleSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderDownColor: '#ef5350',
            borderUpColor: '#26a69a',
            wickDownColor: '#ef5350',
            wickUpColor: '#26a69a',
        });
        
        // Verileri yükle
        fetchCandleData(cleanSymbol, interval);
        
        // Pencere boyutu değiştiğinde grafiği yeniden boyutlandır
        window.addEventListener('resize', () => {
            if (chart) {
                chart.applyOptions({
                    width: container.clientWidth
                });
            }
        });
        
        console.log("Lightweight Chart oluşturuldu");
    } catch (error) {
        console.error("Chart hatası:", error);
        
        // Hata mesajını göster
        const container = document.getElementById('tradingview-widget-container');
        container.innerHTML = `
            <div class="alert alert-danger">
                <strong>Grafik yüklenemedi!</strong><br>
                Lütfen sayfayı yenileyin veya farklı bir sembol seçin.<br>
                <small>Hata: ${error.message}</small>
            </div>
        `;
    }
}

// Mum verilerini çek
async function fetchCandleData(symbol, interval) {
    try {
        const response = await fetch('/api/klines', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                interval: interval
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Verileri formatlama
        const candleData = data.map(d => ({
            time: d[0] / 1000,
            open: parseFloat(d[1]),
            high: parseFloat(d[2]),
            low: parseFloat(d[3]),
            close: parseFloat(d[4])
        }));
        
        // Verileri grafiğe ekle
        if (candleSeries) {
            candleSeries.setData(candleData);
        }
        
    } catch (error) {
        console.error('Mum verileri alınırken hata:', error);
        
        // Hata mesajını göster
        const container = document.getElementById('tradingview-widget-container');
        container.innerHTML = `
            <div class="alert alert-danger">
                <strong>Veri yüklenemedi!</strong><br>
                Lütfen sayfayı yenileyin veya farklı bir sembol seçin.<br>
                <small>Hata: ${error.message}</small>
            </div>
        `;
    }
}

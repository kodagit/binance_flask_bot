# Binance Futures Bot

Bu proje, Binance vadeli işlem platformunda otomatik alım satım yapmak, stratejileri test etmek ve piyasa analizi yapmak için geliştirilmiş bir Flask web uygulamasıdır.

## Özellikler

- Canlı fiyat grafikleri ve teknik göstergeler
- Strateji analizi ve sinyal üretimi
- Backtest aracı ile stratejileri test etme
- Hesap bilgilerini görüntüleme
- Açık pozisyonları takip etme
- Emir verme ve iptal etme

## Kurulum

1. Gerekli paketleri yükleyin:

```bash
pip install -r requirements.txt
```

2. `.env` dosyasını düzenleyin ve Binance API anahtarlarınızı ekleyin:

```
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
SECRET_KEY=your_flask_secret_key
```

3. Uygulamayı başlatın:

```bash
python app.py
```

Veya daha kolay bir şekilde başlatmak için:

```
start_bot.bat
```
dosyasına çift tıklayın.

4. Tarayıcınızda `http://localhost:5000` adresine gidin.

## Stratejiler

Şu anda uygulama aşağıdaki stratejiyi desteklemektedir:

- **MACD + EMA**: MACD, EMA ve RSI göstergelerini kullanarak alım satım sinyalleri üretir.

Yeni stratejiler eklemek için `strategies.py` dosyasını düzenleyebilirsiniz.

## Backtest

Backtest aracı, geçmiş veriler üzerinde stratejilerinizi test etmenizi sağlar. Aşağıdaki parametreleri ayarlayabilirsiniz:

- Sembol (örn. BTCUSDT)
- Zaman aralığı (1m, 5m, 15m, 1h, 4h, 1d, vb.)
- Başlangıç bakiyesi
- Pozisyon büyüklüğü
- Kaldıraç

## Güvenlik

- API anahtarlarınızı güvenli bir şekilde saklayın.
- Para çekme izni olmayan API anahtarları kullanın.
- Mümkünse IP kısıtlaması ekleyin.

## Masaüstü Kısayolu Oluşturma

Uygulamayı daha kolay başlatmak için masaüstüne bir kısayol oluşturabilirsiniz:

1. `create_desktop_shortcut.bat` dosyasına çift tıklayın.
2. Masaüstünüzde "Binance Trading Bot" kısayolu oluşturulacaktır.
3. Bu kısayola tıklayarak uygulamayı doğrudan başlatabilirsiniz.

## Sorumluluk Reddi

Bu uygulama eğitim amaçlıdır ve finansal tavsiye niteliği taşımaz. Kripto para piyasaları yüksek risk içerir. Kendi araştırmınızı yapın ve sadece kaybetmeyi göze alabileceğiniz miktarda yatırım yapın.

## Lisans

MIT

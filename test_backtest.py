import logging
logging.basicConfig(level=logging.DEBUG)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtest import Backtester
from strategies import StrategyManager

# Test verisi oluştur
def create_test_data(rows=500):
    dates = pd.date_range(start='2023-01-01', periods=rows, freq='1h')
    np.random.seed(42)  # Tekrarlanabilir sonuçlar için
    
    # Fiyat verisi oluştur - gerçekçi bir trend oluşturalım
    close = np.zeros(rows)
    close[0] = 50000  # Başlangıç fiyatı
    
    # Trend ve volatilite ekle
    for i in range(1, rows):
        # Trend bileşeni
        trend = np.sin(i/100) * 5000  # Sinüs dalgası trend
        
        # Rastgele bileşen
        random_component = np.random.normal(0, 500)
        
        # Yeni fiyat
        close[i] = close[i-1] + trend/100 + random_component
        
        # Fiyatın negatif olmamasını sağla
        if close[i] < 1000:
            close[i] = 1000
    
    high = close * (1 + np.random.random(rows) * 0.02)
    low = close * (1 - np.random.random(rows) * 0.02)
    open_price = close * (1 + (np.random.random(rows) * 0.04 - 0.02))
    volume = np.random.normal(1000, 200, rows).astype(int)
    
    # DataFrame oluştur
    df = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    return df

# Test verisi oluştur
print("Test verisi oluşturuluyor...")
df = create_test_data(500)
print(f"Test verisi oluşturuldu: {len(df)} satır")

# Backtest çalıştır
print("\nBacktest başlatılıyor...")
strategy_manager = StrategyManager()
backtester = Backtester(strategy_manager)

# Tüm stratejileri test et
for strategy_name in strategy_manager.strategies.keys():
    print(f"\n{strategy_name} stratejisi test ediliyor...")
    result = backtester.run(
        df=df,
        strategy_name=strategy_name,
        symbol="TEST/USDT",
        interval="1h"
    )
    
    if result:
        print(f"Strateji: {strategy_name}")
        print(f"Başlangıç bakiyesi: {result['initial_balance']}")
        print(f"Son bakiye: {result['final_balance']}")
        print(f"Kar/Zarar: {result['profit_loss']} ({result['profit_loss_percent']:.2f}%)")
        print(f"Toplam işlem: {len(result['trades'])}")
        print(f"Kazanan işlem: {result['win_count']}")
        print(f"Kaybeden işlem: {result['loss_count']}")
        print(f"Kazanma oranı: {result['win_rate']:.2f}%")
        
        # İlk 5 işlemi göster
        if result['trades']:
            print("\nİlk 5 işlem:")
            for i, trade in enumerate(result['trades'][:5]):
                print(f"{i+1}. {trade['type']} @ {trade['price']}, Çıkış: {trade['exit_price']}, Kar: {trade['profit']}")
    else:
        print(f"Backtest başarısız oldu: {strategy_name}")

print("\nTest tamamlandı.")

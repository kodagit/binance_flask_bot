import logging
logging.basicConfig(level=logging.DEBUG)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtest import Backtester
from strategies import StrategyManager
from binance_client import BinanceClient

# Binance client oluştur (API anahtarları olmadan)
client = BinanceClient(None, None, testnet=True)

# Test verisi al
df = client.get_historical_klines('BTCUSDT', '1h', limit=500)
print(f"Test verisi alındı: {len(df)} satır")

# Strateji yöneticisi oluştur
strategy_manager = StrategyManager()

# Backtest çalıştır
backtester = Backtester(strategy_manager)

# Tüm stratejileri test et
for strategy_name in strategy_manager.strategies.keys():
    print(f"\n{strategy_name} stratejisi test ediliyor...")
    result = backtester.run(
        df=df,
        strategy_name=strategy_name,
        symbol="BTCUSDT",
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

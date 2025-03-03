import logging
logging.basicConfig(level=logging.DEBUG)

import pandas as pd
from datetime import datetime
from backtest import Backtester
from strategies import StrategyManager
from binance_client import BinanceClient
import os

# API anahtarlarını al
api_key = os.getenv('BINANCE_TEST_API_KEY')
api_secret = os.getenv('BINANCE_TEST_API_SECRET')

print(f"API Anahtarları: {'Var' if api_key and api_secret else 'Yok'}")

# Binance client oluştur
client = BinanceClient(api_key, api_secret, testnet=True)

# Test verisi al
symbol = "BTCUSDT"
interval = "1h"
limit = 200

print(f"\nVeri alınıyor: {symbol} {interval} {limit} mum...")
df = client.get_historical_klines(symbol, interval, limit=limit)
print(f"Veri alındı: {len(df)} satır")

# Strateji yöneticisi oluştur
strategy_manager = StrategyManager()
print(f"\nYüklenen stratejiler: {list(strategy_manager.strategies.keys())}")

# Backtest çalıştır
backtester = Backtester(strategy_manager)

# Always_Signal stratejisini test et
strategy_name = "Always_Signal"
print(f"\n{strategy_name} stratejisi test ediliyor...")

result = backtester.run(
    df=df,
    strategy_name=strategy_name,
    symbol=symbol,
    interval=interval
)

if result:
    print(f"\nStrateji: {strategy_name}")
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

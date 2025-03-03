import logging
logging.basicConfig(level=logging.DEBUG)

import pandas as pd
from five_stage_approval_strategy import FiveStageApprovalStrategy
from binance_client import BinanceClient
import os
from datetime import datetime

# Binance client oluştur
client = BinanceClient(None, None, testnet=True)

# Veri al
df = client.get_historical_klines('BTCUSDT', '1h', limit=200)
print(f"Veri alındı: {len(df)} satır")

# Strateji oluştur
strategy = FiveStageApprovalStrategy()

# Stratejiyi çalıştır
signal, confidence, metrics = strategy.analyze(df)

# Sonuçları yazdır
print(f"Sinyal: {signal}")
print(f"Güven: {confidence}")

# Aşama sonuçlarını yazdır
stage_results = metrics.get("stage_results", {})
for stage, result in stage_results.items():
    print(f"{stage}: {result['passed']}")
    if 'details' in result:
        for key, value in result['details'].items():
            print(f"  {key}: {value}")

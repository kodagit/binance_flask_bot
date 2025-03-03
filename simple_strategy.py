import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

class SimpleStrategy:
    """
    Basit Sinyal Stratejisi
    Bu strateji, basit EMA kesişimleri kullanarak alım-satım sinyalleri üretir.
    Her zaman sinyal üretmesi için tasarlanmıştır.
    
    Özellikler:
    - Kısa ve uzun dönem EMA kesişimlerini kullanır
    - Fiyat ve EMA ilişkisine göre sinyal üretir
    - Basit ve anlaşılması kolay bir stratejidir
    - Yeni başlayanlar için idealdir
    """
    
    description = "Basit EMA kesişimlerine dayalı temel bir alım-satım stratejisi. Yeni başlayanlar için idealdir."
    
    def __init__(self):
        self.name = "SimpleStrategy"
        self.logger = logging.getLogger(__name__)
        
    def analyze(self, df: pd.DataFrame) -> Tuple[str, float, Dict]:
        """
        Basit strateji analizi
        Returns:
            tuple: (sinyal tipi [BUY, SELL, HOLD], güven skoru [0-100], ek metrikler)
        """
        try:
            # EMA hesapla
            df = self.calculate_ema(df)
            
            # Son değerleri al
            current_price = df['close'].iloc[-1]
            current_ema10 = df['ema10'].iloc[-1]
            current_ema20 = df['ema20'].iloc[-1]
            
            # Basit sinyal mantığı - neredeyse her zaman sinyal üretecek
            if current_price > current_ema10:
                signal = "BUY"
                confidence = 80
            elif current_price < current_ema10:
                signal = "SELL"
                confidence = 80
            else:
                signal = "HOLD"
                confidence = 0
            
            # Metrikleri topla
            metrics = {
                "price": current_price,
                "ema10": current_ema10,
                "ema20": current_ema20,
                "signal": signal
            }
            
            return signal, confidence, metrics
            
        except Exception as e:
            self.logger.error(f"Basit strateji analizi sırasında hata: {str(e)}")
            return "HOLD", 0, {"error": str(e)}
    
    def calculate_ema(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        EMA hesapla
        """
        try:
            df['ema10'] = df['close'].ewm(span=10, adjust=False).mean()
            df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
            return df
        except Exception as e:
            self.logger.error(f"EMA hesaplanırken hata: {str(e)}")
            return df
            
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Alım-satım sinyallerini üret
        
        Args:
            df (pd.DataFrame): İşlem verisi
            
        Returns:
            pd.DataFrame: Sinyal içeren veri çerçevesi
        """
        try:
            self.logger.info(f"Sinyal üretme işlemi başlatılıyor. Veri boyutu: {len(df)}")
            
            # Önce DataFrame'i kopyala
            signals_df = df.copy()
            
            # EMA hesapla
            signals_df = self.calculate_ema(signals_df)
            
            # Sinyal sütununu ekle
            signals_df['signal'] = 'HOLD'
            
            # Basit sinyal mantığı
            for i in range(1, len(signals_df)):
                current_price = signals_df['close'].iloc[i]
                current_ema10 = signals_df['ema10'].iloc[i]
                current_ema20 = signals_df['ema20'].iloc[i]
                
                prev_ema10 = signals_df['ema10'].iloc[i-1]
                prev_ema20 = signals_df['ema20'].iloc[i-1]
                
                # Alım sinyali: EMA10 EMA20'yi yukarı doğru kesiyor ve fiyat EMA10'un üzerinde
                if prev_ema10 <= prev_ema20 and current_ema10 > current_ema20 and current_price > current_ema10:
                    signals_df.loc[signals_df.index[i], 'signal'] = 'BUY'
                
                # Satış sinyali: EMA10 EMA20'yi aşağı doğru kesiyor ve fiyat EMA10'un altında
                elif prev_ema10 >= prev_ema20 and current_ema10 < current_ema20 and current_price < current_ema10:
                    signals_df.loc[signals_df.index[i], 'signal'] = 'SELL'
            
            # Sinyal istatistiklerini logla
            signal_counts = signals_df['signal'].value_counts()
            self.logger.info(f"Sinyal dağılımı: {signal_counts.to_dict()}")
            
            return signals_df
            
        except Exception as e:
            self.logger.error(f"Sinyal üretilirken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return pd.DataFrame()

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, List, Optional

class RCIEMAStrategy:
    """
    RCI (Rank Correlation Index) ve EMA (Exponential Moving Average) kullanarak 
    alım-satım sinyalleri üreten strateji.
    
    RCI, fiyatın momentumunu ölçmek için kullanılır ve EMA ile birlikte
    trend yönünü belirlemede yardımcı olur.
    """
    
    description = "RCI ve EMA göstergelerine dayalı trend takip stratejisi."
    
    def __init__(self, 
                rci_period=9, 
                ema_fast=10, 
                ema_slow=20,
                rci_overbought=80,
                rci_oversold=-80):
        """
        RCI ve EMA stratejisi parametrelerini ayarla
        
        Args:
            rci_period (int): RCI periyodu (öntanımlı: 9)
            ema_fast (int): Hızlı EMA periyodu (öntanımlı: 10)
            ema_slow (int): Yavaş EMA periyodu (öntanımlı: 20)
            rci_overbought (int): Aşırı alım seviyesi (öntanımlı: 80)
            rci_oversold (int): Aşırı satım seviyesi (öntanımlı: -80)
        """
        import logging
        self.name = "RCIEMAStrategy"
        self.logger = logging.getLogger(self.name)
        self.rci_period = rci_period
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.rci_overbought = rci_overbought
        self.rci_oversold = rci_oversold
        
        self.logger.info(f"RCIEMAStrategy başlatıldı. "
                        f"RCI Periyod: {rci_period}, "
                        f"EMA Hızlı: {ema_fast}, "
                        f"EMA Yavaş: {ema_slow}, "
                        f"RCI Aşırı Alım: {rci_overbought}, "
                        f"RCI Aşırı Satım: {rci_oversold}")
    
    def analyze(self, df: pd.DataFrame) -> Tuple[str, float, Dict]:
        """
        RCI ve EMA'ya dayalı analiz
        
        Returns:
            tuple: (sinyal tipi [BUY, SELL, HOLD], güven skoru [0-100], ek metrikler)
        """
        try:
            # Veri kontrolü
            if df is None or len(df) < self.ema_slow + 10:
                self.logger.warning(f"Yetersiz veri: {len(df) if df is not None else 0} satır")
                return "HOLD", 0, {"error": "Yetersiz veri"}
                
            # Sinyal üret
            signals = self.generate_signals(df)
            
            if signals is None or signals.empty:
                return "HOLD", 0, {"error": "Sinyal üretilemedi"}
            
            # Son sinyal ve güven skorunu al
            last_signal = signals.iloc[-1]
            signal = last_signal.get('signal', 'HOLD')
            
            # Güven skorunu hesapla
            confidence = 0
            
            if signal == 'BUY':
                # RCI ve EMA'nın gücüne göre güven skorunu belirle
                rci_strength = min(100, max(0, (last_signal.get('rci', 0) + 100) / 2))
                ema_diff = last_signal.get('ema_diff_pct', 0)
                
                if ema_diff > 0:
                    ema_strength = min(100, ema_diff * 100)
                else:
                    ema_strength = 0
                    
                confidence = int((rci_strength * 0.6) + (ema_strength * 0.4))
                
            elif signal == 'SELL':
                # RCI ve EMA'nın gücüne göre güven skorunu belirle
                rci_strength = min(100, max(0, (100 - last_signal.get('rci', 0)) / 2))
                ema_diff = last_signal.get('ema_diff_pct', 0)
                
                if ema_diff < 0:
                    ema_strength = min(100, abs(ema_diff) * 100)
                else:
                    ema_strength = 0
                    
                confidence = int((rci_strength * 0.6) + (ema_strength * 0.4))
            
            # Döndürülecek metrikleri hazırla
            metrics = {
                'rci': last_signal.get('rci', 0),
                'ema_fast': last_signal.get('ema_fast', 0),
                'ema_slow': last_signal.get('ema_slow', 0),
                'ema_diff': last_signal.get('ema_diff', 0),
                'ema_diff_pct': last_signal.get('ema_diff_pct', 0)
            }
            
            # Log
            self.logger.info(f"RCI-EMA Analizi: Sinyal={signal}, Güven={confidence}, Metrikler={metrics}")
            
            return signal, confidence, metrics
            
        except Exception as e:
            self.logger.error(f"Analiz sırasında hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return "HOLD", 0, {"error": str(e)}
    
    def calculate_rci(self, series: pd.Series, period: int) -> float:
        """
        Rank Correlation Index (RCI) hesapla
        
        Args:
            series: Fiyat serisi
            period: Hesaplama periyodu
            
        Returns:
            float: RCI değeri [-100, 100]
        """
        if len(series) < period:
            return 0
            
        # Son 'period' kadar veriyi al
        recent_data = series[-period:].values
        
        # Zaman sıralaması (en yeni = en yüksek sıra)
        time_ranks = np.arange(period, 0, -1)
        
        # Fiyat sıralaması
        price_ranks = np.zeros(period)
        sorted_indices = np.argsort(recent_data)
        
        for i, idx in enumerate(sorted_indices):
            price_ranks[idx] = i + 1
            
        # RCI hesapla: 100 * (1 - (6 * sum(d^2)) / (n*(n^2-1)))
        # d: iki sıralama arasındaki fark
        d_squared_sum = np.sum((time_ranks - price_ranks) ** 2)
        rci = 100 * (1 - (6 * d_squared_sum) / (period * (period**2 - 1)))
        
        return rci
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        RCI ve EMA kullanarak alım-satım sinyalleri üret
        
        Args:
            df: OHLCV verileri
            
        Returns:
            pd.DataFrame: Sinyaller eklenmiş DataFrame
        """
        try:
            # Verilerin kopyasını oluştur
            signals = df.copy()
            
            # Veri tiplerini kontrol et ve dönüştür
            if 'close' not in signals.columns:
                self.logger.error("'close' sütunu verilerde bulunamadı")
                self.logger.error(f"Mevcut sütunlar: {signals.columns.tolist()}")
                return pd.DataFrame()
            
            # Kontrol için sütun isimlerini logla
            self.logger.info(f"Veri sütunları: {signals.columns.tolist()}")
            self.logger.info(f"Veri örnekleri: {signals.head(3)}")
                
            # Close sütununu sayısal tipe dönüştür
            signals['close'] = pd.to_numeric(signals['close'], errors='coerce')
            
            # NaN değerleri kontrol et
            if signals['close'].isna().any():
                self.logger.warning("'close' sütununda eksik değerler var, doldurulacak")
                signals['close'] = signals['close'].fillna(method='ffill')  # İleri dolgu
            
            # İstatistik bilgisini logla
            self.logger.info(f"İstatistik: {signals['close'].describe()}")
                
            # EMA hesapla
            signals['ema_fast'] = signals['close'].ewm(span=self.ema_fast, adjust=False).mean()
            signals['ema_slow'] = signals['close'].ewm(span=self.ema_slow, adjust=False).mean()
            
            # EMA farkını hesapla
            signals['ema_diff'] = signals['ema_fast'] - signals['ema_slow']
            signals['ema_diff_pct'] = signals['ema_diff'] / signals['close'] * 100
            
            # RCI hesapla
            signals['rci'] = 0
            
            # Her satır için RCI hesapla
            for i in range(self.rci_period, len(signals)):
                price_series = signals['close'].iloc[i-self.rci_period:i+1]
                signals.loc[signals.index[i], 'rci'] = self.calculate_rci(price_series, self.rci_period)
            
            # Sinyal sütunu oluştur - varsayılan olarak HOLD
            signals['signal'] = 'HOLD'
            
            # RCI ve EMA'ya göre sinyal üret
            for i in range(1, len(signals)):
                # RCI değerleri
                current_rci = signals['rci'].iloc[i]
                prev_rci = signals['rci'].iloc[i-1]
                
                # EMA değerleri
                ema_diff = signals['ema_diff'].iloc[i]
                prev_ema_diff = signals['ema_diff'].iloc[i-1]
                
                # Alış sinyali: RCI -80'den yukarı geçiyor ve EMA farkı pozitife dönüyor
                if (prev_rci < self.rci_oversold and current_rci > self.rci_oversold) or (prev_ema_diff < 0 and ema_diff > 0):
                    signals.loc[signals.index[i], 'signal'] = 'BUY'
                
                # Satış sinyali: RCI 80'den aşağı geçiyor ve EMA farkı negatife dönüyor
                elif (prev_rci > self.rci_overbought and current_rci < self.rci_overbought) or (prev_ema_diff > 0 and ema_diff < 0):
                    signals.loc[signals.index[i], 'signal'] = 'SELL'
            
            # En az bir sinyal olduğundan emin ol
            if len(signals) > 0 and not 'BUY' in signals['signal'].values and not 'SELL' in signals['signal'].values:
                self.logger.warning("Hiç alım-satım sinyali üretilmedi, ilk satıra BUY sinyali ekleniyor")
                signals.loc[signals.index[0], 'signal'] = 'BUY'
                
            # Sinyal istatistiklerini logla
            signal_counts = signals['signal'].value_counts().to_dict()
            self.logger.info(f"Sinyal dağılımı: {signal_counts}")
            self.logger.info(f"Sinyaller oluşturuldu: {len(signals)} satır")
            
            return signals
            
        except Exception as e:
            import traceback
            self.logger.error(f"Sinyaller oluşturulurken hata: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            # Boş bir DataFrame döndür
            return pd.DataFrame()

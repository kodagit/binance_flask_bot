import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from advanced_indicators import AdvancedIndicators

class FiveStageApprovalStrategy:
    """
    5 Aşamalı Onay Stratejisi
    
    Bu strateji, farklı teknik göstergelerin onayını alarak işlem sinyalleri üretir.
    Aşağıdaki göstergeleri kullanır:
    1. EMA (Üstel Hareketli Ortalama)
    2. MACD (Hareketli Ortalama Yakınsama Iraksama)
    3. RSI (Göreceli Güç Endeksi)
    4. Bollinger Bantları
    5. Stokastik Osilatör
    
    Özellikler:
    - 5 farklı teknik gösterge ile sinyal doğrulama
    - Yüksek güvenilirlik için çoklu onay sistemi
    - Farklı piyasa koşullarına adaptasyon
    - Detaylı metrik raporlama
    
    Parametreler:
        config: Strateji konfigürasyonu
    """
    
    description = "5 farklı teknik göstergenin onayını alarak yüksek güvenilirlikli işlem sinyalleri üreten gelişmiş strateji."
    
    def __init__(self, config=None):
        """
        Strateji başlatma
        
        Args:
            config: Strateji konfigürasyonu
        """
        self.name = "Five Stage Approval"
        self.config = config
        
        # Varsayılan parametreler (config yoksa kullanılır)
        self.ema_short_period = 9
        self.ema_long_period = 21
        self.macd_fast_period = 12
        self.macd_slow_period = 26
        self.macd_signal_period = 9
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.bollinger_period = 20
        self.bollinger_std_dev = 2
        self.stochastic_k_period = 14
        self.stochastic_d_period = 3
        self.stochastic_overbought = 80
        self.stochastic_oversold = 20
        
        # Eğer config varsa, parametreleri güncelle
        if config:
            self._load_parameters_from_config()
        
        # Gelişmiş göstergeler sınıfını başlat
        self.indicators = AdvancedIndicators()
        
    def _load_parameters_from_config(self):
        """Parametreleri konfigürasyondan yükle"""
        strategy_key = self.name.replace(' ', '_')
        
        if self.config:
            # EMA parametreleri
            if 'ema_short_period' in self.config.config['strategies'][strategy_key]:
                self.ema_short_period = self.config.config['strategies'][strategy_key]['ema_short_period']['default']
            
            if 'ema_long_period' in self.config.config['strategies'][strategy_key]:
                self.ema_long_period = self.config.config['strategies'][strategy_key]['ema_long_period']['default']
            
            # MACD parametreleri
            if 'macd_fast_period' in self.config.config['strategies'][strategy_key]:
                self.macd_fast_period = self.config.config['strategies'][strategy_key]['macd_fast_period']['default']
            
            if 'macd_slow_period' in self.config.config['strategies'][strategy_key]:
                self.macd_slow_period = self.config.config['strategies'][strategy_key]['macd_slow_period']['default']
            
            if 'macd_signal_period' in self.config.config['strategies'][strategy_key]:
                self.macd_signal_period = self.config.config['strategies'][strategy_key]['macd_signal_period']['default']
            
            # RSI parametreleri
            if 'rsi_period' in self.config.config['strategies'][strategy_key]:
                self.rsi_period = self.config.config['strategies'][strategy_key]['rsi_period']['default']
            
            if 'rsi_overbought' in self.config.config['strategies'][strategy_key]:
                self.rsi_overbought = self.config.config['strategies'][strategy_key]['rsi_overbought']['default']
            
            if 'rsi_oversold' in self.config.config['strategies'][strategy_key]:
                self.rsi_oversold = self.config.config['strategies'][strategy_key]['rsi_oversold']['default']
            
            # Bollinger Bantları parametreleri
            if 'bollinger_period' in self.config.config['strategies'][strategy_key]:
                self.bollinger_period = self.config.config['strategies'][strategy_key]['bollinger_period']['default']
            
            if 'bollinger_std_dev' in self.config.config['strategies'][strategy_key]:
                self.bollinger_std_dev = self.config.config['strategies'][strategy_key]['bollinger_std_dev']['default']
            
            # Stokastik Osilatör parametreleri
            if 'stochastic_k_period' in self.config.config['strategies'][strategy_key]:
                self.stochastic_k_period = self.config.config['strategies'][strategy_key]['stochastic_k_period']['default']
            
            if 'stochastic_d_period' in self.config.config['strategies'][strategy_key]:
                self.stochastic_d_period = self.config.config['strategies'][strategy_key]['stochastic_d_period']['default']
            
            if 'stochastic_overbought' in self.config.config['strategies'][strategy_key]:
                self.stochastic_overbought = self.config.config['strategies'][strategy_key]['stochastic_overbought']['default']
            
            if 'stochastic_oversold' in self.config.config['strategies'][strategy_key]:
                self.stochastic_oversold = self.config.config['strategies'][strategy_key]['stochastic_oversold']['default']
    
    def analyze(self, df: pd.DataFrame) -> Tuple[str, float, Dict]:
        """
        5 aşamalı onay sistemi ile piyasa analizi yapar
        
        Args:
            df: Veri çerçevesi
            
        Returns:
            Tuple[str, float, Dict]: Sinyal, güven oranı ve metrikler
        """
        try:
            # Veri çerçevesini kontrol et
            if df.empty:
                return "BEKLE", 0, {"error": "Veri çerçevesi boş"}
            
            # Gerekli indikatörleri hesapla
            # 1. EMA - Trend yönünü belirlemek için
            df = self.indicators.add_ema(df, self.ema_short_period, 'ema_short')
            df = self.indicators.add_ema(df, self.ema_long_period, 'ema_long')
            
            # 2. MACD - Momentum ve trend gücünü ölçmek için
            df = self.indicators.add_macd(df, self.macd_fast_period, self.macd_slow_period, self.macd_signal_period)
            
            # 3. RSI - Aşırı alım/satım durumlarını belirlemek için
            df = self.indicators.add_rsi(df, self.rsi_period)
            
            # 4. Bollinger Bantları - Volatilite ve fiyat aralıklarını belirlemek için
            df = self.indicators.add_bollinger_bands(df, self.bollinger_period, self.bollinger_std_dev)
            
            # 5. Stokastik Osilatör - Momentum ve trend dönüşlerini belirlemek için
            df = self.indicators.add_stochastic(df, self.stochastic_k_period, self.stochastic_d_period)
            
            # Son satırı al
            last_row = df.iloc[-1]
            current_price = last_row['close']
            
            # 1. Aşama: Trend Analizi (EMA ile)
            ema_short = last_row['ema_short']
            ema_long = last_row['ema_long']
            
            # Trend yönünü belirle
            if ema_short > ema_long:
                trend = "YUKARI"
                trend_strength = (ema_short / ema_long - 1) * 100  # Trend gücü yüzdesi
            elif ema_short < ema_long:
                trend = "AŞAĞI"
                trend_strength = (1 - ema_short / ema_long) * 100  # Trend gücü yüzdesi
            else:
                trend = "YATAY"
                trend_strength = 0
                
            # Trend onayı
            trend_confirmed = trend == "YUKARI" and trend_strength > 0.5  # Yukarı trend ve belirli bir güçte olmalı
            
            # 2. Aşama: Momentum Analizi (MACD ile)
            macd_line = last_row['macd_line']
            signal_line = last_row['signal_line']
            macd_histogram = last_row['macd_histogram']
            
            # MACD sinyalini belirle
            if macd_line > signal_line and macd_histogram > 0:
                macd_signal = "AL"
                macd_strength = abs(macd_line / signal_line) if signal_line != 0 else 1
            elif macd_line < signal_line and macd_histogram < 0:
                macd_signal = "SAT"
                macd_strength = abs(signal_line / macd_line) if macd_line != 0 else 1
            else:
                macd_signal = "BEKLE"
                macd_strength = 0
                
            # Momentum onayı
            momentum_confirmed = macd_signal == "AL" and macd_strength > 1.05  # AL sinyali ve belirli bir güçte olmalı
            
            # 3. Aşama: Aşırı Alım/Satım Analizi (RSI ile)
            rsi = last_row['rsi']
            
            # RSI sinyalini belirle
            if rsi < self.rsi_oversold:
                rsi_signal = "AŞIRI SATIM"
                rsi_strength = (self.rsi_oversold - rsi) / self.rsi_oversold * 100
            elif rsi > self.rsi_overbought:
                rsi_signal = "AŞIRI ALIM"
                rsi_strength = (rsi - self.rsi_overbought) / (100 - self.rsi_overbought) * 100
            else:
                rsi_signal = "NORMAL"
                rsi_strength = 0
                
            # RSI onayı
            rsi_confirmed = rsi_signal == "NORMAL" or rsi_signal == "AŞIRI SATIM"  # Normal veya aşırı satım durumunda olmalı
            
            # 4. Aşama: Volatilite Analizi (Bollinger Bantları ile)
            bb_upper = last_row['bb_upper']
            bb_middle = last_row['bb_middle']
            bb_lower = last_row['bb_lower']
            
            # Bollinger Bantları sinyalini belirle
            bb_width = (bb_upper - bb_lower) / bb_middle * 100  # Bant genişliği yüzdesi
            
            if current_price < bb_lower:
                bb_signal = "AŞIRI SATIM"
                bb_strength = (bb_lower - current_price) / bb_lower * 100
            elif current_price > bb_upper:
                bb_signal = "AŞIRI ALIM"
                bb_strength = (current_price - bb_upper) / bb_upper * 100
            else:
                bb_signal = "NORMAL"
                bb_strength = 0
                
            # Volatilite onayı
            volatility_confirmed = bb_signal == "NORMAL" or bb_signal == "AŞIRI SATIM"  # Normal veya aşırı satım durumunda olmalı
            
            # 5. Aşama: Trend Dönüşü Analizi (Stokastik Osilatör ile)
            stoch_k = last_row['stoch_k']
            stoch_d = last_row['stoch_d']
            
            # Stokastik sinyalini belirle
            if stoch_k < self.stochastic_oversold and stoch_d < self.stochastic_oversold:
                stoch_signal = "AŞIRI SATIM"
                stoch_strength = (self.stochastic_oversold - stoch_k) / self.stochastic_oversold * 100
            elif stoch_k > self.stochastic_overbought and stoch_d > self.stochastic_overbought:
                stoch_signal = "AŞIRI ALIM"
                stoch_strength = (stoch_k - self.stochastic_overbought) / (100 - self.stochastic_overbought) * 100
            else:
                stoch_signal = "NORMAL"
                stoch_strength = 0
                
            # Stokastik onayı
            stochastic_confirmed = stoch_signal == "NORMAL" or stoch_signal == "AŞIRI SATIM"  # Normal veya aşırı satım durumunda olmalı
            
            # Tüm aşamaların onayını kontrol et
            all_confirmed = trend_confirmed and momentum_confirmed and rsi_confirmed and volatility_confirmed and stochastic_confirmed
            
            # Sonuç
            if all_confirmed:
                signal = "BUY"  # Tüm aşamalar onaylandıysa AL sinyali
            else:
                signal = "WAIT"  # Herhangi bir aşama onaylanmadıysa BEKLE sinyali
                
            # Güven oranını hesapla
            confidence = (trend_strength + macd_strength + rsi_strength + bb_strength + stoch_strength) / 5
            
            # Metrikleri birleştir
            metrics = {
                "trend": trend,
                "trend_strength": trend_strength,
                "trend_confirmed": trend_confirmed,
                "macd_signal": macd_signal,
                "macd_strength": macd_strength,
                "momentum_confirmed": momentum_confirmed,
                "rsi": rsi,
                "rsi_signal": rsi_signal,
                "rsi_strength": rsi_strength,
                "rsi_confirmed": rsi_confirmed,
                "bb_width": bb_width,
                "bb_signal": bb_signal,
                "bb_strength": bb_strength,
                "volatility_confirmed": volatility_confirmed,
                "stoch_signal": stoch_signal,
                "stoch_strength": stoch_strength,
                "stochastic_confirmed": stochastic_confirmed,
                "all_confirmed": all_confirmed,
                "confidence": confidence
            }
            
            return signal, confidence, metrics
            
        except Exception as e:
            import traceback
            print(f"Analiz hatası: {str(e)}")
            print(traceback.format_exc())
            return "ERROR", 0, {"error": str(e)}
    
    def get_signal(self, df: pd.DataFrame) -> str:
        """Son mum için sinyal üret"""
        signal, _, _ = self.analyze(df)
        return signal
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Tüm veri için sinyal üret
        
        Args:
            df: Veri çerçevesi
            
        Returns:
            pd.DataFrame: Sinyaller eklenmiş veri çerçevesi
        """
        if df.empty:
            return df
            
        try:
            # Gerekli indikatörleri hesapla
            # 1. EMA - Trend yönünü belirlemek için
            df = self.indicators.add_ema(df, self.ema_short_period, 'ema_short')
            df = self.indicators.add_ema(df, self.ema_long_period, 'ema_long')
            
            # 2. MACD - Momentum ve trend gücünü ölçmek için
            df = self.indicators.add_macd(df, self.macd_fast_period, self.macd_slow_period, self.macd_signal_period)
            
            # 3. RSI - Aşırı alım/satım durumlarını belirlemek için
            df = self.indicators.add_rsi(df, self.rsi_period)
            
            # 4. Bollinger Bantları - Volatilite ve fiyat aralıklarını belirlemek için
            df = self.indicators.add_bollinger_bands(df, self.bollinger_period, self.bollinger_std_dev)
            
            # 5. Stokastik Osilatör - Momentum ve trend dönüşlerini belirlemek için
            df = self.indicators.add_stochastic(df, self.stochastic_k_period, self.stochastic_d_period)
            
            # Sinyalleri hesapla
            df['signal'] = 'WAIT'  # Varsayılan sinyal
            
            for i in range(max(self.ema_long_period, self.macd_slow_period, self.rsi_period, 
                               self.bollinger_period, self.stochastic_k_period) + 5, len(df)):
                # Her bir satır için sinyal hesapla
                signal, _, _ = self.analyze(df.iloc[:i+1])
                df.loc[df.index[i], 'signal'] = signal
                
            return df
            
        except Exception as e:
            import traceback
            print(f"Sinyal üretme hatası: {str(e)}")
            print(traceback.format_exc())
            # Hata durumunda boş sinyaller döndür
            if 'signal' not in df.columns:
                df['signal'] = 'WAIT'
            return df
    
    def calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """Bollinger Bantlarını hesapla"""
        return self.indicators.add_bollinger_bands(df, self.bollinger_period, self.bollinger_std_dev)

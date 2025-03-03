import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from advanced_indicators import AdvancedIndicators

class AdvancedStrategy:
    """
    Gelişmiş strateji sınıfı.
    Bu sınıf, trend belirleme ve sinyal onaylama mekanizması ile çalışır.
    
    Özellikler:
    - Çoklu teknik gösterge kullanımı (EMA, RSI, MACD, Stokastik RSI, ATR)
    - Trend belirleme ve doğrulama
    - Sinyal gücü hesaplama
    - Adaptif risk yönetimi
    - Gelişmiş filtreleme mekanizmaları
    """
    
    description = "Çoklu teknik göstergeleri kullanan gelişmiş bir alım-satım stratejisi. Trend belirleme ve sinyal doğrulama mekanizmaları içerir."
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(__name__)
        self.indicators = AdvancedIndicators()
        
        # Varsayılan parametreler
        self.ema_short = 50
        self.ema_long = 200
        self.rsi_period = 14
        self.rsi_oversold = 40
        self.rsi_overbought = 60
        self.atr_period = 14
        self.atr_multiplier = 1.5
        self.stoch_rsi_period = 14
        self.stoch_rsi_k = 3
        self.stoch_rsi_d = 3
        self.stoch_rsi_oversold = 20
        self.stoch_rsi_overbought = 80
        self.supertrend_period = 10
        self.supertrend_multiplier = 3
        
    def analyze(self, df: pd.DataFrame) -> Tuple[str, float, Dict]:
        """
        Fiyat verilerini analiz et ve sinyal üret
        Returns:
            tuple: (sinyal tipi [BUY, SELL, HOLD], güven skoru [0-100], ek metrikler)
        """
        try:
            # Tüm indikatörleri hesapla
            df = self.indicators.calculate_all(df)
            
            # Son değerleri al
            current_price = df['close'].iloc[-1]
            current_ema50 = df['ema50'].iloc[-1]
            current_ema200 = df['ema200'].iloc[-1]
            current_rsi = df['rsi'].iloc[-1]
            current_stoch_rsi_k = df['stoch_rsi_k'].iloc[-1]
            current_stoch_rsi_d = df['stoch_rsi_d'].iloc[-1]
            current_macd = df['macd'].iloc[-1]
            current_macd_signal = df['macd_signal'].iloc[-1]
            current_macd_hist = df['macd_hist'].iloc[-1]
            current_atr = df['atr'].iloc[-1]
            current_supertrend = df['supertrend'].iloc[-1]
            current_supertrend_dir = df['supertrend_direction'].iloc[-1]
            
            # Ichimoku değerleri
            current_tenkan = df['tenkan_sen'].iloc[-1]
            current_kijun = df['kijun_sen'].iloc[-1]
            current_senkou_a = df['senkou_span_a'].iloc[-1]
            current_senkou_b = df['senkou_span_b'].iloc[-1]
            
            # 1. Trend Yönünü Belirle
            trend_signals = []
            
            # EMA Trend
            if current_ema50 > current_ema200 and current_price > current_ema50:
                trend_signals.append(1)  # Yükseliş trendi
            elif current_ema50 < current_ema200 and current_price < current_ema50:
                trend_signals.append(-1)  # Düşüş trendi
            else:
                trend_signals.append(0)  # Belirsiz trend
            
            # Ichimoku Trend
            if current_price > current_senkou_a and current_price > current_senkou_b:
                trend_signals.append(1)  # Yükseliş trendi
            elif current_price < current_senkou_a and current_price < current_senkou_b:
                trend_signals.append(-1)  # Düşüş trendi
            else:
                trend_signals.append(0)  # Belirsiz trend
            
            # Supertrend
            trend_signals.append(current_supertrend_dir)
            
            # Genel trend yönünü belirle
            trend_score = sum(trend_signals)
            
            if trend_score >= 2:
                trend = "BULLISH"
            elif trend_score <= -2:
                trend = "BEARISH"
            else:
                trend = "NEUTRAL"
            
            # 2. Giriş Sinyallerini Doğrula
            signal_strength = 0
            signal = "HOLD"
            
            # MACD Kesişimi
            prev_macd = df['macd'].iloc[-2]
            prev_signal = df['macd_signal'].iloc[-2]
            
            macd_cross_up = prev_macd < prev_signal and current_macd > current_macd_signal
            macd_cross_down = prev_macd > prev_signal and current_macd < current_macd_signal
            
            # RSI Kontrolü
            rsi_buy_zone = current_rsi > 50 and current_rsi < self.rsi_overbought
            rsi_sell_zone = current_rsi < 50 and current_rsi > self.rsi_oversold
            
            # Stochastic RSI Kontrolü
            stoch_rsi_buy = current_stoch_rsi_k > current_stoch_rsi_d and current_stoch_rsi_k < self.stoch_rsi_overbought
            stoch_rsi_sell = current_stoch_rsi_k < current_stoch_rsi_d and current_stoch_rsi_k > self.stoch_rsi_oversold
            
            # Volatilite Kontrolü (ATR)
            sufficient_volatility = current_atr > (current_price * 0.005)  # Fiyatın en az %0.5'i kadar volatilite
            
            # 3. Sinyal Üret
            confidence = 0
            
            # LONG Sinyali
            if trend == "BULLISH" and macd_cross_up and rsi_buy_zone and stoch_rsi_buy and sufficient_volatility:
                signal = "BUY"
                # Güven skorunu hesapla
                confidence = 50 + (current_rsi - 50) * 1.5 + abs(current_macd_hist/current_atr * 20)
                confidence = min(100, confidence)
            
            # SHORT Sinyali
            elif trend == "BEARISH" and macd_cross_down and rsi_sell_zone and stoch_rsi_sell and sufficient_volatility:
                signal = "SELL"
                # Güven skorunu hesapla
                confidence = 50 + (50 - current_rsi) * 1.5 + abs(current_macd_hist/current_atr * 20)
                confidence = min(100, confidence)
            
            # 4. Stop Loss ve Take Profit Seviyeleri
            stop_loss = 0
            take_profit = 0
            
            if signal == "BUY":
                # ATR bazlı stop loss
                stop_loss = current_price - (current_atr * self.atr_multiplier)
                # Supertrend bazlı stop loss (daha sıkı olan seçilir)
                supertrend_sl = current_supertrend
                stop_loss = max(stop_loss, supertrend_sl)
                
                # Take profit seviyeleri
                take_profit_1 = current_price + (current_price - stop_loss) * 1.0  # 1:1 risk-ödül
                take_profit_2 = current_price + (current_price - stop_loss) * 1.5  # 1.5:1 risk-ödül
                take_profit_3 = current_price + (current_price - stop_loss) * 2.0  # 2:1 risk-ödül
                
                take_profit = take_profit_3  # En yüksek hedef
                
            elif signal == "SELL":
                # ATR bazlı stop loss
                stop_loss = current_price + (current_atr * self.atr_multiplier)
                # Supertrend bazlı stop loss (daha sıkı olan seçilir)
                supertrend_sl = current_supertrend
                stop_loss = min(stop_loss, supertrend_sl)
                
                # Take profit seviyeleri
                take_profit_1 = current_price - (stop_loss - current_price) * 1.0  # 1:1 risk-ödül
                take_profit_2 = current_price - (stop_loss - current_price) * 1.5  # 1.5:1 risk-ödül
                take_profit_3 = current_price - (stop_loss - current_price) * 2.0  # 2:1 risk-ödül
                
                take_profit = take_profit_3  # En yüksek hedef
            
            # 5. Sonuçları döndür
            metrics = {
                "trend": trend,
                "trend_score": trend_score,
                "price": current_price,
                "ema50": current_ema50,
                "ema200": current_ema200,
                "rsi": current_rsi,
                "stoch_rsi_k": current_stoch_rsi_k,
                "stoch_rsi_d": current_stoch_rsi_d,
                "macd": current_macd,
                "macd_signal": current_macd_signal,
                "macd_hist": current_macd_hist,
                "atr": current_atr,
                "supertrend": current_supertrend,
                "supertrend_direction": current_supertrend_dir,
                "ichimoku_tenkan": current_tenkan,
                "ichimoku_kijun": current_kijun,
                "ichimoku_senkou_a": current_senkou_a,
                "ichimoku_senkou_b": current_senkou_b,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "take_profit_1": take_profit_1 if signal != "HOLD" else 0,
                "take_profit_2": take_profit_2 if signal != "HOLD" else 0,
                "take_profit_3": take_profit_3 if signal != "HOLD" else 0,
                "risk_reward_ratio": abs((take_profit - current_price) / (current_price - stop_loss)) if signal != "HOLD" and stop_loss != current_price else 0
            }
            
            return signal, confidence, metrics
            
        except Exception as e:
            self.logger.error(f"Gelişmiş strateji analizi sırasında hata: {str(e)}")
            return "HOLD", 0, {}

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Backtest için sinyaller üretir
        
        Args:
            df (pd.DataFrame): OHLCV verileri içeren dataframe
            
        Returns:
            pd.DataFrame: Sinyallerin eklendiği dataframe
        """
        self.logger.info(f"AdvancedStrategy.generate_signals çağrıldı, veri şekli: {df.shape}")
        
        if df.empty:
            self.logger.warning("Boş dataframe, sinyal üretilemedi")
            return df
            
        try:
            # Gerekli sütunları kontrol et
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col.lower() in df.columns for col in required_columns):
                self.logger.error(f"Veri gereken sütunları içermiyor. Mevcut sütunlar: {df.columns}")
                # Gerekli sütunlar yoksa, Pandas görünümünü kapat ve aynı veriyi döndür
                return df
            
            # İndikatörleri hesapla
            df = self.indicators.calculate_all(df)
            
            # Sinyalleri oluştur
            df['signal'] = 0  # 0: bekle, 1: al, -1: sat
            
            # EMA çapraz geçişleri
            df['ema_cross'] = 0
            df.loc[df['ema_50'] > df['ema_200'], 'ema_cross'] = 1  # Altın çapraz (bullish)
            df.loc[df['ema_50'] < df['ema_200'], 'ema_cross'] = -1  # Ölüm çaprazı (bearish)
            
            # RSI filtresi
            df['rsi_signal'] = 0
            df.loc[df['rsi_14'] < self.rsi_oversold, 'rsi_signal'] = 1  # Aşırı satım
            df.loc[df['rsi_14'] > self.rsi_overbought, 'rsi_signal'] = -1  # Aşırı alım
            
            # Supertrend sinyali (varsa)
            if 'supertrend' in df.columns:
                df['st_signal'] = 0
                df.loc[df['supertrend'] < df['close'], 'st_signal'] = 1  # Bullish
                df.loc[df['supertrend'] > df['close'], 'st_signal'] = -1  # Bearish
            
            # Sinyalleri birleştir
            # Alım sinyali: EMA altın çapraz + RSI aşırı satım + (varsa) Supertrend yukarı
            buy_signals = (df['ema_cross'] == 1) & (df['rsi_signal'] == 1)
            if 'supertrend' in df.columns:
                buy_signals = buy_signals & (df['st_signal'] == 1)
            
            # Satım sinyali: EMA ölüm çaprazı + RSI aşırı alım + (varsa) Supertrend aşağı
            sell_signals = (df['ema_cross'] == -1) & (df['rsi_signal'] == -1)
            if 'supertrend' in df.columns:
                sell_signals = sell_signals & (df['st_signal'] == -1)
            
            # Sinyalleri işaretle
            df.loc[buy_signals, 'signal'] = 1
            df.loc[sell_signals, 'signal'] = -1
            
            # Gereksiz sütunları temizle
            columns_to_keep = required_columns + ['signal']
            df = df[columns_to_keep]
            
            return df
            
        except Exception as e:
            self.logger.error(f"Sinyal üretilirken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return df


class TrimLossStrategy(AdvancedStrategy):
    """
    Trim Loss stratejisi.
    Bu strateji, kademeli kar alma ve zarar kesme mekanizması kullanır.
    
    Özellikler:
    - Kademeli kar alma seviyeleri
    - Dinamik zarar kesme
    - Trailing stop kullanımı
    - Risk yönetimi optimizasyonu
    """
    
    description = "Kademeli kar alma ve dinamik zarar kesme mekanizması kullanan risk yönetimi odaklı strateji."
    
    def __init__(self):
        super().__init__("Trim_Loss")
        
        # Trim Loss parametreleri
        self.take_profit_levels = [0.03, 0.04, 0.05]  # %3, %4, %5 kar hedefleri
        self.position_size_per_level = [0.3, 0.3, 0.4]  # Her seviyede pozisyonun ne kadarını kapat
        self.trailing_stop_activation = 0.02  # %2 kar sonrası trailing stop aktifleştir
        self.trailing_stop_distance = 0.01  # Fiyattan %1 uzaklıkta trailing stop
        
    def calculate_exit_strategy(self, entry_price, current_price, position_type):
        """
        Çıkış stratejisini hesapla
        """
        exits = []
        
        if position_type == "BUY":
            # Kar hedefleri
            for i, level in enumerate(self.take_profit_levels):
                target_price = entry_price * (1 + level)
                exits.append({
                    "type": "TAKE_PROFIT",
                    "price": target_price,
                    "size": self.position_size_per_level[i],
                    "activated": current_price >= target_price
                })
            
            # Trailing stop
            trailing_activation_price = entry_price * (1 + self.trailing_stop_activation)
            trailing_stop_price = current_price * (1 - self.trailing_stop_distance)
            
            exits.append({
                "type": "TRAILING_STOP",
                "activation_price": trailing_activation_price,
                "current_stop": trailing_stop_price,
                "activated": current_price >= trailing_activation_price
            })
            
        elif position_type == "SELL":
            # Kar hedefleri
            for i, level in enumerate(self.take_profit_levels):
                target_price = entry_price * (1 - level)
                exits.append({
                    "type": "TAKE_PROFIT",
                    "price": target_price,
                    "size": self.position_size_per_level[i],
                    "activated": current_price <= target_price
                })
            
            # Trailing stop
            trailing_activation_price = entry_price * (1 - self.trailing_stop_activation)
            trailing_stop_price = current_price * (1 + self.trailing_stop_distance)
            
            exits.append({
                "type": "TRAILING_STOP",
                "activation_price": trailing_activation_price,
                "current_stop": trailing_stop_price,
                "activated": current_price <= trailing_activation_price
            })
        
        return exits

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Backtest için sinyaller üretir
        
        Args:
            df (pd.DataFrame): OHLCV verileri içeren dataframe
            
        Returns:
            pd.DataFrame: Sinyallerin eklendiği dataframe
        """
        self.logger.info(f"TrimLossStrategy.generate_signals çağrıldı, veri şekli: {df.shape}")
        
        if df.empty:
            self.logger.warning("Boş dataframe, sinyal üretilemedi")
            return df
            
        try:
            # Gereken sütunları kontrol et
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col.lower() in df.columns for col in required_columns):
                self.logger.error(f"Veri gereken sütunları içermiyor. Mevcut sütunlar: {df.columns}")
                return df
            
            # Ana strateji sinyallerini al
            df = super().generate_signals(df)
            
            # Eğer super() sinyalleri üretmediyse, temel sinyaller oluştur
            if 'signal' not in df.columns:
                df['signal'] = 0
                
                # Basit sinyaller oluşturalım (örneğin)
                df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
                df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
                
                # EMA kesişimleri
                df.loc[df['ema_20'] > df['ema_50'], 'signal'] = 1  # Alım sinyali
                df.loc[df['ema_20'] < df['ema_50'], 'signal'] = -1  # Satım sinyali
            
            # Trim Loss stratejisine özgü iyileştirmeler ekle
            # (Bu bir örnek olarak tutuldu, gerçek bir uygulama daha komplex olabilir)
            
            return df
            
        except Exception as e:
            self.logger.error(f"TrimLossStrategy sinyal üretiminde hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return df


class MultiTimeframeStrategy(AdvancedStrategy):
    """
    Çoklu zaman dilimi stratejisi.
    Farklı zaman dilimlerindeki verileri kullanarak sinyal üretir.
    
    Özellikler:
    - Farklı zaman dilimlerinde analiz (1s, 5d, 15d, 1h, 4h, 1g)
    - Zaman dilimleri arası trend doğrulama
    - Ağırlıklı sinyal hesaplama
    - Yüksek güvenilirlik için çoklu onay sistemi
    """
    
    description = "Farklı zaman dilimlerindeki verileri analiz ederek yüksek güvenilirlikli sinyaller üreten gelişmiş strateji."
    
    def __init__(self):
        self.name = "Multi_Timeframe"
        self.logger = logging.getLogger(__name__)
        self.indicators = AdvancedIndicators()
        
    def analyze(self, df: pd.DataFrame) -> Tuple[str, float, Dict]:
        """
        Tek zaman dilimi için analiz
        """
        try:
            # İndikatörleri hesapla
            df = self.indicators.calculate_all(df)
            
            # Son satırı al
            last_row = df.iloc[-1]
            
            # Sinyal gücünü hesapla
            signal_strength = 0
            
            # EMA sinyalleri
            if last_row['ema_50'] > last_row['ema_200']:
                signal_strength += 20
            else:
                signal_strength -= 20
                
            # RSI sinyalleri 
            if last_row['rsi_14'] > 50:
                signal_strength += 10
            else:
                signal_strength -= 10
                
            # MACD sinyalleri (varsa)
            if 'macd' in last_row and 'macd_signal' in last_row:
                if last_row['macd'] > last_row['macd_signal']:
                    signal_strength += 15
                else:
                    signal_strength -= 15
            
            # Sinyal kararı
            if signal_strength > 30:
                signal = "BUY"
                confidence = min(100, abs(signal_strength))
            elif signal_strength < -30:
                signal = "SELL"
                confidence = min(100, abs(signal_strength))
            else:
                signal = "HOLD"
                confidence = 0
                
            # Ek metrikler
            metrics = {
                "signal_strength": signal_strength,
                "ema_status": "bullish" if last_row['ema_50'] > last_row['ema_200'] else "bearish",
                "rsi_value": last_row['rsi_14']
            }
            
            return signal, confidence, metrics
            
        except Exception as e:
            self.logger.error(f"MultiTimeframe analizi sırasında hata: {str(e)}")
            return "HOLD", 0, {"error": str(e)}
            
    def analyze_multi_timeframe(self, df_dict: Dict[str, pd.DataFrame]) -> Tuple[str, float, Dict]:
        """
        Farklı zaman dilimlerindeki verileri analiz et
        df_dict: {"1h": df_1h, "4h": df_4h, "1d": df_1d}
        """
        try:
            # Her zaman dilimi için sinyal hesapla
            signals = {}
            confidences = {}
            metrics = {}
            
            for timeframe, df in df_dict.items():
                signal, confidence, metric = self.analyze(df)
                signals[timeframe] = signal
                confidences[timeframe] = confidence
                metrics[timeframe] = metric
            
            # Ağırlıklar (daha uzun zaman dilimleri daha önemli)
            weights = {
                "1m": 0.05,
                "5m": 0.1,
                "15m": 0.15,
                "1h": 0.2,
                "4h": 0.25,
                "1d": 0.25
            }
            
            # Mevcut zaman dilimlerine göre ağırlıkları normalize et
            total_weight = sum(weights[tf] for tf in df_dict.keys() if tf in weights)
            if total_weight > 0:
                normalized_weights = {tf: weights[tf]/total_weight for tf in df_dict.keys() if tf in weights}
            else:
                # Eşit ağırlık ver
                normalized_weights = {tf: 1.0/len(df_dict) for tf in df_dict.keys()}
            
            # Ağırlıklı sinyal skoru hesapla
            signal_score = 0
            for timeframe, signal in signals.items():
                if timeframe in normalized_weights:
                    if signal == "BUY":
                        signal_score += normalized_weights[timeframe] * confidences[timeframe]
                    elif signal == "SELL":
                        signal_score -= normalized_weights[timeframe] * confidences[timeframe]
            
            # Final sinyal kararı
            if signal_score > 30:
                final_signal = "BUY"
                final_confidence = min(100, abs(signal_score))
            elif signal_score < -30:
                final_signal = "SELL"
                final_confidence = min(100, abs(signal_score))
            else:
                final_signal = "HOLD"
                final_confidence = 0
                
            # Sonuç metrikleri
            final_metrics = {
                "signal_score": signal_score,
                "timeframe_signals": signals,
                "timeframe_confidences": confidences,
                "normalized_weights": normalized_weights
            }
            
            return final_signal, final_confidence, final_metrics
            
        except Exception as e:
            self.logger.error(f"Çoklu zaman dilimi analizi sırasında hata: {str(e)}")
            return "HOLD", 0, {"error": str(e)}
            
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Backtest için sinyaller üretir. Bu strateji normalde çoklu zaman dilimi kullanır,
        ancak backtest için tek zaman dilimindeki veriyi kullanıyoruz.
        
        Args:
            df (pd.DataFrame): OHLCV verileri içeren dataframe
            
        Returns:
            pd.DataFrame: Sinyallerin eklendiği dataframe
        """
        self.logger.info(f"MultiTimeframeStrategy.generate_signals çağrıldı, veri şekli: {df.shape}")
        
        if df.empty:
            self.logger.warning("Boş dataframe, sinyal üretilemedi")
            return df
            
        try:
            # Gereken sütunları kontrol et
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col.lower() in df.columns for col in required_columns):
                self.logger.error(f"Veri gereken sütunları içermiyor. Mevcut sütunlar: {df.columns}")
                return df
            
            # İndikatörleri hesapla
            df = self.indicators.calculate_all(df)
            
            # Başlangıçta sinyal sütunu ekle
            df['signal'] = 0  # 0: bekle, 1: al, -1: sat
            
            # Birden fazla indikatör kombinasyonu 
            # EMA sinyalleri
            ema_signal = ((df['ema_50'] > df['ema_200'])).astype(int) * 2 - 1  # 1: al, -1: sat
            
            # RSI sinyalleri 
            rsi_signal = np.zeros(len(df))
            rsi_signal[df['rsi_14'] > 60] = -1  # Aşırı alım
            rsi_signal[df['rsi_14'] < 40] = 1   # Aşırı satım
            
            # Stochastic RSI sinyalleri (varsa)
            stoch_rsi_signal = np.zeros(len(df))
            if 'stoch_rsi_k' in df.columns and 'stoch_rsi_d' in df.columns:
                stoch_rsi_signal[(df['stoch_rsi_k'] > df['stoch_rsi_d']) & (df['stoch_rsi_k'] < 80)] = 1
                stoch_rsi_signal[(df['stoch_rsi_k'] < df['stoch_rsi_d']) & (df['stoch_rsi_k'] > 20)] = -1
            
            # MACD sinyalleri (varsa)
            macd_signal = np.zeros(len(df))
            if 'macd' in df.columns and 'macd_signal' in df.columns:
                macd_signal[df['macd'] > df['macd_signal']] = 1
                macd_signal[df['macd'] < df['macd_signal']] = -1
            
            # Sinyalleri birleştir (ağırlıklı toplam)
            combined_signal = 0.3 * ema_signal + 0.2 * rsi_signal + 0.25 * stoch_rsi_signal + 0.25 * macd_signal
            
            # Final sinyal kararı
            df.loc[combined_signal >= 0.5, 'signal'] = 1    # Alım sinyali
            df.loc[combined_signal <= -0.5, 'signal'] = -1  # Satım sinyali
            
            # Gereksiz sütunları temizle
            columns_to_keep = required_columns + ['signal']
            df = df[columns_to_keep]
            
            return df
            
        except Exception as e:
            self.logger.error(f"MultiTimeframeStrategy sinyal üretiminde hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return df

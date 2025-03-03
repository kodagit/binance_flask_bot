import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

# Strateji yöneticisini import et
from strategy_manager import StrategyManager

# Strateji yöneticisi instance'ı oluştur
strategy_manager = StrategyManager()

class Strategy:
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(__name__)

    def analyze(self, df: pd.DataFrame) -> Tuple[str, float, Dict]:
        """
        Fiyat verilerini analiz et ve sinyal üret
        Returns:
            tuple: (sinyal tipi [BUY, SELL, HOLD], güven skoru [0-100], ek metrikler)
        """
        pass

class MACDEMAStrategy(Strategy):
    def __init__(self):
        super().__init__("MACD_EMA")
        # Strateji parametreleri
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.ema_period = 200
        self.rsi_period = 14
        self.rsi_oversold = 40
        self.rsi_overbought = 60
        
    def analyze(self, df: pd.DataFrame) -> Tuple[str, float, Dict]:
        try:
            # MACD hesapla
            df = self.calculate_macd(df)
            macd_line = df['macd']
            signal_line = df['macd_signal']
            hist = df['macd_hist']
            
            # EMA hesapla
            df = self.calculate_ema(df)
            
            # RSI hesapla
            df = self.calculate_rsi(df)
            
            # ATR hesapla
            df = self.calculate_atr(df)
            
            # Son değerleri al
            current_price = df['close'].iloc[-1]
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_hist = hist.iloc[-1]
            current_ema50 = df['ema50'].iloc[-1]
            current_ema200 = df['ema200'].iloc[-1]
            current_rsi = df['rsi'].iloc[-1]
            current_atr = df['atr'].iloc[-1]
            
            # Trend yönünü belirle
            trend = "BULLISH" if current_price > current_ema200 else "BEARISH"
            
            # MACD kesişimi kontrol et
            prev_macd = macd_line.iloc[-2]
            prev_signal = signal_line.iloc[-2]
            
            macd_cross_up = prev_macd < prev_signal and current_macd > current_signal
            macd_cross_down = prev_macd > prev_signal and current_macd < current_signal
            
            # Sinyal hesapla
            signal = "HOLD"
            confidence = 0
            
            # LONG sinyali
            if trend == "BULLISH" and macd_cross_up and current_rsi > self.rsi_oversold:
                signal = "BUY"
                confidence = min(100, 50 + (current_rsi - self.rsi_oversold) + abs(current_hist/current_atr * 50))
            
            # SHORT sinyali
            elif trend == "BEARISH" and macd_cross_down and current_rsi < self.rsi_overbought:
                signal = "SELL"
                confidence = min(100, 50 + (self.rsi_overbought - current_rsi) + abs(current_hist/current_atr * 50))
            
            metrics = {
                "trend": trend,
                "macd": current_macd,
                "signal": current_signal,
                "histogram": current_hist,
                "rsi": current_rsi,
                "atr": current_atr,
                "ema50": current_ema50,
                "ema200": current_ema200,
                "price": current_price
            }
            
            return signal, confidence, metrics
            
        except Exception as e:
            self.logger.error(f"Strateji analizi sırasında hata: {str(e)}")
            return "HOLD", 0, {}
    
    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """MACD hesapla"""
        exp1 = df['close'].ewm(span=self.macd_fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=self.macd_slow, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=self.macd_signal, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        return df
    
    def calculate_ema(self, df: pd.DataFrame) -> pd.DataFrame:
        """EMA hesapla"""
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema200'] = df['close'].ewm(span=self.ema_period, adjust=False).mean()
        return df
    
    def calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """RSI hesapla"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        return df
    
    def calculate_atr(self, df: pd.DataFrame, period=14) -> pd.DataFrame:
        """ATR hesapla"""
        df = df.copy()
        df['tr0'] = abs(df['high'] - df['low'])
        df['tr1'] = abs(df['high'] - df['close'].shift())
        df['tr2'] = abs(df['low'] - df['close'].shift())
        df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
        df['atr'] = df['tr'].rolling(window=period).mean()
        return df
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Tüm veri için sinyal üret
        
        Args:
            df (pd.DataFrame): Fiyat verileri
            
        Returns:
            pd.DataFrame: Sinyal sütunu eklenmiş veri
        """
        self.logger.info(f"MACD_EMA stratejisi sinyaller üretiliyor: {len(df)} satır")
        
        try:
            # Veri kopyası oluştur
            result_df = df.copy()
            
            # Sinyal sütunu oluştur
            result_df['signal'] = 'HOLD'
            
            # Tüm mumlar için analiz yap
            for i in range(len(result_df)):
                try:
                    if i < 30:  # İlk 30 mum için yeterli veri yok
                        result_df.iloc[i, result_df.columns.get_loc('signal')] = 'HOLD'
                        continue
                        
                    # Her mum için veri dilimi oluştur
                    temp_df = df.iloc[:i+1].copy()
                    
                    # Analiz et
                    signal, _, _ = self.analyze(temp_df)
                    
                    # Sinyali kaydet
                    result_df.iloc[i, result_df.columns.get_loc('signal')] = signal
                except Exception as e:
                    self.logger.error(f"Satır {i} için sinyal üretilirken hata: {str(e)}")
                    result_df.iloc[i, result_df.columns.get_loc('signal')] = 'HOLD'
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"MACD_EMA sinyaller üretilirken hata: {str(e)}")
            # Hata durumunda orijinal veriyi döndür
            if 'signal' not in df.columns:
                df = df.copy()
                df['signal'] = 'HOLD'
            return df

class VolatilityStrategy(Strategy):
    def __init__(self):
        super().__init__("Volatility")
        # Strateji parametreleri
        self.bb_period = 20
        self.bb_std = 2.0
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.min_volatility = 1.5
        
    def analyze(self, df: pd.DataFrame) -> Tuple[str, float, Dict]:
        try:
            # Bollinger Bands hesapla
            df = self.calculate_bollinger_bands(df)
            
            # RSI hesapla
            df = self.calculate_rsi(df)
            
            # Volatilite hesapla
            df = self.calculate_volatility(df)
            
            # Hacim ortalaması hesapla
            df = self.calculate_volume_average(df)
            
            # Son değerleri al
            current_price = df['close'].iloc[-1]
            current_rsi = df['rsi'].iloc[-1]
            current_upper_band = df['upper_band'].iloc[-1]
            current_lower_band = df['lower_band'].iloc[-1]
            current_volatility = df['volatility'].iloc[-1]
            avg_volatility = df['avg_volatility'].iloc[-1]
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['avg_volume'].iloc[-1]
            
            # Volatilite kontrolü
            high_volatility = current_volatility > (avg_volatility * self.min_volatility)
            high_volume = current_volume > avg_volume
            
            # Sinyal hesapla
            signal = "HOLD"
            confidence = 0
            
            # LONG sinyali
            if current_price < current_lower_band and current_rsi < self.rsi_oversold and high_volatility and high_volume:
                signal = "BUY"
                confidence = min(100, 50 + (self.rsi_oversold - current_rsi) + (current_volatility / avg_volatility * 20))
            
            # SHORT sinyali
            elif current_price > current_upper_band and current_rsi > self.rsi_overbought and high_volatility and high_volume:
                signal = "SELL"
                confidence = min(100, 50 + (current_rsi - self.rsi_overbought) + (current_volatility / avg_volatility * 20))
            
            metrics = {
                "price": current_price,
                "rsi": current_rsi,
                "upper_band": current_upper_band,
                "lower_band": current_lower_band,
                "volatility": current_volatility,
                "avg_volatility": avg_volatility,
                "volume": current_volume,
                "avg_volume": avg_volume,
                "high_volatility": high_volatility,
                "high_volume": high_volume
            }
            
            return signal, confidence, metrics
            
        except Exception as e:
            self.logger.error(f"Strateji analizi sırasında hata: {str(e)}")
            return "HOLD", 0, {}
    
    def calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """Bollinger Bands hesapla"""
        df['middle_band'] = df['close'].rolling(window=self.bb_period).mean()
        df['std'] = df['close'].rolling(window=self.bb_period).std()
        df['upper_band'] = df['middle_band'] + (df['std'] * self.bb_std)
        df['lower_band'] = df['middle_band'] - (df['std'] * self.bb_std)
        return df
    
    def calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """RSI hesapla"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        return df
    
    def calculate_volatility(self, df: pd.DataFrame) -> pd.DataFrame:
        """Volatilite hesapla (True Range'in yüzdesi olarak)"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        df['volatility'] = (true_range / df['close']) * 100
        df['avg_volatility'] = df['volatility'].rolling(window=24).mean()
        return df
    
    def calculate_volume_average(self, df: pd.DataFrame) -> pd.DataFrame:
        """Hacim ortalaması hesapla"""
        df['avg_volume'] = df['volume'].rolling(window=24).mean()
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Tüm veri için sinyal üret
        
        Args:
            df (pd.DataFrame): Fiyat verileri
            
        Returns:
            pd.DataFrame: Sinyal sütunu eklenmiş veri
        """
        self.logger.info(f"Volatility stratejisi sinyaller üretiliyor: {len(df)} satır")
        
        try:
            # Veri kopyası oluştur
            result_df = df.copy()
            
            # Sinyal sütunu oluştur
            result_df['signal'] = 'HOLD'
            
            # Tüm mumlar için analiz yap
            for i in range(len(result_df)):
                try:
                    if i < 30:  # İlk 30 mum için yeterli veri yok
                        result_df.iloc[i, result_df.columns.get_loc('signal')] = 'HOLD'
                        continue
                        
                    # Her mum için veri dilimi oluştur
                    temp_df = df.iloc[:i+1].copy()
                    
                    # Analiz et
                    signal, _, _ = self.analyze(temp_df)
                    
                    # Sinyali kaydet
                    result_df.iloc[i, result_df.columns.get_loc('signal')] = signal
                except Exception as e:
                    self.logger.error(f"Satır {i} için sinyal üretilirken hata: {str(e)}")
                    result_df.iloc[i, result_df.columns.get_loc('signal')] = 'HOLD'
            
            # Sinyal dağılımını logla
            signal_counts = result_df['signal'].value_counts()
            self.logger.info(f"Sinyal dağılımı: {signal_counts.to_dict()}")
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"Volatility sinyaller üretilirken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            # Hata durumunda orijinal veriyi döndür
            if 'signal' not in df.columns:
                df = df.copy()
                df['signal'] = 'HOLD'
            return df

class TrendFollowStrategy(Strategy):
    def __init__(self):
        super().__init__("Trend_Follow")
        # Strateji parametreleri
        self.short_ema = 9
        self.medium_ema = 21
        self.long_ema = 50
        self.adx_period = 14
        self.min_trend_strength = 25
        
    def analyze(self, df: pd.DataFrame) -> Tuple[str, float, Dict]:
        try:
            # EMA hesapla
            df = self.calculate_ema(df)
            
            # ADX hesapla
            df = self.calculate_adx(df)
            
            # Hacim değişimi hesapla
            df = self.calculate_volume_change(df)
            
            # Son değerleri al
            current_price = df['close'].iloc[-1]
            short_ema = df['short_ema'].iloc[-1]
            medium_ema = df['medium_ema'].iloc[-1]
            long_ema = df['long_ema'].iloc[-1]
            adx = df['adx'].iloc[-1]
            volume_change = df['volume_change'].iloc[-1]
            
            # Son 3 mumun rengini kontrol et
            green_candles = sum(1 for i in range(1, 4) if df['close'].iloc[-i] > df['open'].iloc[-i])
            red_candles = 3 - green_candles
            
            # Trend kontrolü
            strong_uptrend = short_ema > medium_ema > long_ema
            strong_downtrend = short_ema < medium_ema < long_ema
            strong_trend = adx > self.min_trend_strength
            increasing_volume = volume_change > 0
            
            # Sinyal hesapla
            signal = "HOLD"
            confidence = 0
            
            # LONG sinyali
            if strong_uptrend and strong_trend and green_candles >= 2 and increasing_volume:
                signal = "BUY"
                confidence = min(100, 50 + (adx - self.min_trend_strength) / 2 + green_candles * 10)
            
            # SHORT sinyali
            elif strong_downtrend and strong_trend and red_candles >= 2 and increasing_volume:
                signal = "SELL"
                confidence = min(100, 50 + (adx - self.min_trend_strength) / 2 + red_candles * 10)
            
            metrics = {
                "price": current_price,
                "short_ema": short_ema,
                "medium_ema": medium_ema,
                "long_ema": long_ema,
                "adx": adx,
                "volume_change": volume_change,
                "green_candles": green_candles,
                "red_candles": red_candles,
                "strong_uptrend": strong_uptrend,
                "strong_downtrend": strong_downtrend,
                "strong_trend": strong_trend
            }
            
            return signal, confidence, metrics
            
        except Exception as e:
            self.logger.error(f"Strateji analizi sırasında hata: {str(e)}")
            return "HOLD", 0, {}
    
    def calculate_ema(self, df: pd.DataFrame) -> pd.DataFrame:
        """EMA hesapla"""
        df['short_ema'] = df['close'].ewm(span=self.short_ema, adjust=False).mean()
        df['medium_ema'] = df['close'].ewm(span=self.medium_ema, adjust=False).mean()
        df['long_ema'] = df['close'].ewm(span=self.long_ema, adjust=False).mean()
        return df
    
    def calculate_adx(self, df: pd.DataFrame) -> pd.DataFrame:
        """ADX hesapla"""
        # True Range hesapla
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        # Directional Movement hesapla
        plus_dm = df['high'].diff()
        minus_dm = df['low'].diff().mul(-1)
        
        plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > minus_dm), 0)
        minus_dm = minus_dm.where((minus_dm > 0) & (minus_dm > plus_dm), 0)
        
        # Smoothed TR ve DM hesapla
        tr_period = true_range.rolling(window=self.adx_period).sum()
        plus_di_period = plus_dm.rolling(window=self.adx_period).sum()
        minus_di_period = minus_dm.rolling(window=self.adx_period).sum()
        
        # +DI ve -DI hesapla
        plus_di = 100 * (plus_di_period / tr_period)
        minus_di = 100 * (minus_di_period / tr_period)
        
        # DX hesapla
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        
        # ADX hesapla
        df['adx'] = dx.rolling(window=self.adx_period).mean()
        
        return df
    
    def calculate_volume_change(self, df: pd.DataFrame) -> pd.DataFrame:
        """Hacim değişimi hesapla"""
        df['volume_change'] = df['volume'].pct_change(3)
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Tüm veri için sinyal üret
        
        Args:
            df (pd.DataFrame): Fiyat verileri
            
        Returns:
            pd.DataFrame: Sinyal sütunu eklenmiş veri
        """
        self.logger.info(f"TrendFollow stratejisi sinyaller üretiliyor: {len(df)} satır")
        
        try:
            # Veri kopyası oluştur
            result_df = df.copy()
            
            # Sinyal sütunu oluştur
            result_df['signal'] = 'HOLD'
            
            # Tüm mumlar için analiz yap
            for i in range(len(result_df)):
                try:
                    if i < 30:  # İlk 30 mum için yeterli veri yok
                        result_df.iloc[i, result_df.columns.get_loc('signal')] = 'HOLD'
                        continue
                        
                    # Her mum için veri dilimi oluştur
                    temp_df = df.iloc[:i+1].copy()
                    
                    # Analiz et
                    signal, _, _ = self.analyze(temp_df)
                    
                    # Sinyali kaydet
                    result_df.iloc[i, result_df.columns.get_loc('signal')] = signal
                except Exception as e:
                    self.logger.error(f"Satır {i} için sinyal üretilirken hata: {str(e)}")
                    result_df.iloc[i, result_df.columns.get_loc('signal')] = 'HOLD'
            
            # Sinyal dağılımını logla
            signal_counts = result_df['signal'].value_counts()
            self.logger.info(f"Sinyal dağılımı: {signal_counts.to_dict()}")
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"TrendFollow sinyaller üretilirken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            # Hata durumunda orijinal veriyi döndür
            if 'signal' not in df.columns:
                df = df.copy()
                df['signal'] = 'HOLD'
            return df

class StrategyManager:
    """
    Strateji yöneticisi
    """
    def __init__(self):
        self.strategies = {}
        self.logger = logging.getLogger(__name__)
        
    def register_strategy(self, name, strategy_class):
        """
        Strateji kaydet
        """
        self.strategies[name] = strategy_class
        self.logger.info(f"Strateji kaydedildi: {name}")
        
    def get_strategy(self, strategy_name):
        """
        Strateji adına göre strateji nesnesi döndür
        """
        if strategy_name in self.strategies:
            try:
                strategy = self.strategies[strategy_name]()
                self.logger.info(f"Strateji alındı: {strategy_name}")
                return strategy
            except Exception as e:
                self.logger.error(f"Strateji oluşturulurken hata: {strategy_name} - {str(e)}")
                return None
        else:
            self.logger.error(f"Strateji bulunamadı: {strategy_name}")
            return None
            
    def get_all_strategies(self):
        """
        Tüm strateji adlarını döndür
        """
        return list(self.strategies.keys())
        
    def analyze_all(self, df):
        """
        Tüm stratejileri çalıştır ve sonuçları döndür
        """
        results = []
        for name, strategy_class in self.strategies.items():
            try:
                strategy = strategy_class()
                signal, confidence, metrics = strategy.analyze(df)
                results.append((name, signal, confidence, metrics))
            except Exception as e:
                self.logger.error(f"Strateji analizi sırasında hata: {name} - {str(e)}")
                results.append((name, "HOLD", 0, {"error": str(e)}))
        return results

# Strateji yöneticisi oluştur
strategy_manager = StrategyManager()

# Stratejileri kaydet
strategy_manager.register_strategy("MACD_EMA", MACDEMAStrategy)
strategy_manager.register_strategy("Volatility", VolatilityStrategy)
strategy_manager.register_strategy("Trend_Follow", TrendFollowStrategy)

# Always Signal stratejisini import et ve kaydet
try:
    from always_signal_strategy import AlwaysSignalStrategy
    strategy_manager.register_strategy("Always_Signal", AlwaysSignalStrategy)
    strategy_manager.logger.info("Always Signal stratejisi kaydedildi")
except Exception as e:
    strategy_manager.logger.error(f"Always Signal stratejisi kaydedilirken hata: {str(e)}")
    import traceback
    strategy_manager.logger.error(traceback.format_exc())

# Five Stage Approval stratejisini import et ve kaydet
try:
    from five_stage_approval_strategy import FiveStageApprovalStrategy
    strategy_manager.register_strategy("Five_Stage_Approval", FiveStageApprovalStrategy)
    strategy_manager.logger.info("Five Stage Approval stratejisi kaydedildi")
except Exception as e:
    strategy_manager.logger.error(f"Five Stage Approval stratejisi kaydedilirken hata: {str(e)}")
    import traceback
    strategy_manager.logger.error(traceback.format_exc())

import pandas as pd
import numpy as np
import logging

class AdvancedIndicators:
    """
    Gelişmiş teknik indikatörler sınıfı.
    Bu sınıf, stratejilerde kullanılabilecek çeşitli teknik indikatörleri hesaplar.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Tüm indikatörleri hesapla ve DataFrame'e ekle
        """
        try:
            df = self.calculate_ema(df)
            df = self.calculate_macd(df)
            df = self.calculate_rsi(df)
            df = self.calculate_stoch_rsi(df)
            df = self.calculate_atr(df)
            df = self.calculate_supertrend(df)
            df = self.calculate_ichimoku(df)
            return df
        except Exception as e:
            self.logger.error(f"İndikatörler hesaplanırken hata: {str(e)}")
            return df
    
    def calculate_ema(self, df: pd.DataFrame, periods=[20, 50, 200]) -> pd.DataFrame:
        """
        Exponential Moving Average (EMA) hesapla
        """
        try:
            for period in periods:
                df[f'ema{period}'] = df['close'].ewm(span=period, adjust=False).mean()
            return df
        except Exception as e:
            self.logger.error(f"EMA hesaplanırken hata: {str(e)}")
            return df
    
    def calculate_macd(self, df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
        """
        Moving Average Convergence Divergence (MACD) hesapla
        """
        try:
            df['macd_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
            df['macd_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
            df['macd'] = df['macd_fast'] - df['macd_slow']
            df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            return df
        except Exception as e:
            self.logger.error(f"MACD hesaplanırken hata: {str(e)}")
            return df
    
    def calculate_rsi(self, df: pd.DataFrame, period=14) -> pd.DataFrame:
        """
        Relative Strength Index (RSI) hesapla
        """
        try:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            rs = avg_gain / avg_loss
            df['rsi'] = 100 - (100 / (1 + rs))
            return df
        except Exception as e:
            self.logger.error(f"RSI hesaplanırken hata: {str(e)}")
            return df
    
    def calculate_stoch_rsi(self, df: pd.DataFrame, period=14, k_period=3, d_period=3) -> pd.DataFrame:
        """
        Stochastic RSI hesapla
        """
        try:
            # Önce RSI hesapla
            if 'rsi' not in df.columns:
                df = self.calculate_rsi(df, period)
            
            # Stochastic RSI hesapla
            min_rsi = df['rsi'].rolling(window=period).min()
            max_rsi = df['rsi'].rolling(window=period).max()
            
            df['stoch_rsi'] = ((df['rsi'] - min_rsi) / (max_rsi - min_rsi)) * 100
            df['stoch_rsi_k'] = df['stoch_rsi'].rolling(window=k_period).mean()
            df['stoch_rsi_d'] = df['stoch_rsi_k'].rolling(window=d_period).mean()
            return df
        except Exception as e:
            self.logger.error(f"Stochastic RSI hesaplanırken hata: {str(e)}")
            return df
    
    def calculate_atr(self, df: pd.DataFrame, period=14) -> pd.DataFrame:
        """
        Average True Range (ATR) hesapla
        """
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
            df['atr'] = tr.rolling(window=period).mean()
            return df
        except Exception as e:
            self.logger.error(f"ATR hesaplanırken hata: {str(e)}")
            return df
    
    def calculate_supertrend(self, df: pd.DataFrame, period=10, multiplier=3) -> pd.DataFrame:
        """
        Supertrend indikatörü hesapla
        """
        try:
            # Önce ATR hesapla
            if 'atr' not in df.columns:
                df = self.calculate_atr(df, period)
            
            hl2 = (df['high'] + df['low']) / 2
            
            # Üst ve alt bantları hesapla
            df['upperband'] = hl2 + (multiplier * df['atr'])
            df['lowerband'] = hl2 - (multiplier * df['atr'])
            
            # Supertrend hesapla
            df['supertrend'] = 0.0
            df['supertrend_direction'] = 0  # 1: yukarı trend, -1: aşağı trend
            
            for i in range(period, len(df)):
                curr_close = df['close'].iloc[i]
                prev_close = df['close'].iloc[i-1]
                curr_upper = df['upperband'].iloc[i]
                curr_lower = df['lowerband'].iloc[i]
                prev_upper = df['upperband'].iloc[i-1]
                prev_lower = df['lowerband'].iloc[i-1]
                
                # Önceki Supertrend değerini al
                prev_supertrend = df['supertrend'].iloc[i-1]
                prev_direction = df['supertrend_direction'].iloc[i-1]
                
                # Supertrend yönünü güncelle
                if prev_supertrend == prev_upper:
                    if curr_close > curr_upper:
                        curr_direction = 1  # Yukarı trend
                        curr_supertrend = curr_lower
                    else:
                        curr_direction = -1  # Aşağı trend
                        curr_supertrend = curr_upper
                else:
                    if curr_close < curr_lower:
                        curr_direction = -1  # Aşağı trend
                        curr_supertrend = curr_upper
                    else:
                        curr_direction = 1  # Yukarı trend
                        curr_supertrend = curr_lower
                
                df.at[df.index[i], 'supertrend'] = curr_supertrend
                df.at[df.index[i], 'supertrend_direction'] = curr_direction
            
            return df
        except Exception as e:
            self.logger.error(f"Supertrend hesaplanırken hata: {str(e)}")
            return df
    
    def calculate_ichimoku(self, df: pd.DataFrame, tenkan_period=9, kijun_period=26, senkou_period=52, displacement=26) -> pd.DataFrame:
        """
        Ichimoku Cloud indikatörü hesapla
        """
        try:
            # Tenkan-sen (Conversion Line)
            tenkan_high = df['high'].rolling(window=tenkan_period).max()
            tenkan_low = df['low'].rolling(window=tenkan_period).min()
            df['tenkan_sen'] = (tenkan_high + tenkan_low) / 2
            
            # Kijun-sen (Base Line)
            kijun_high = df['high'].rolling(window=kijun_period).max()
            kijun_low = df['low'].rolling(window=kijun_period).min()
            df['kijun_sen'] = (kijun_high + kijun_low) / 2
            
            # Senkou Span A (Leading Span A)
            df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(displacement)
            
            # Senkou Span B (Leading Span B)
            senkou_high = df['high'].rolling(window=senkou_period).max()
            senkou_low = df['low'].rolling(window=senkou_period).min()
            df['senkou_span_b'] = ((senkou_high + senkou_low) / 2).shift(displacement)
            
            # Chikou Span (Lagging Span)
            df['chikou_span'] = df['close'].shift(-displacement)
            
            return df
        except Exception as e:
            self.logger.error(f"Ichimoku hesaplanırken hata: {str(e)}")
            return df
    
    def add_ema(self, df: pd.DataFrame, period: int, column_name: str = None) -> pd.DataFrame:
        """
        Belirli bir periyot için EMA hesapla ve DataFrame'e ekle
        
        Args:
            df: Veri çerçevesi
            period: EMA periyodu
            column_name: Sütun adı (None ise 'ema{period}' kullanılır)
            
        Returns:
            pd.DataFrame: EMA eklenmiş veri çerçevesi
        """
        try:
            col_name = column_name if column_name else f'ema{period}'
            df[col_name] = df['close'].ewm(span=period, adjust=False).mean()
            return df
        except Exception as e:
            print(f"EMA hesaplanırken hata: {str(e)}")
            return df
    
    def add_macd(self, df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
        """
        MACD hesapla ve DataFrame'e ekle
        
        Args:
            df: Veri çerçevesi
            fast_period: Hızlı EMA periyodu
            slow_period: Yavaş EMA periyodu
            signal_period: Sinyal periyodu
            
        Returns:
            pd.DataFrame: MACD eklenmiş veri çerçevesi
        """
        try:
            fast_ema = df['close'].ewm(span=fast_period, adjust=False).mean()
            slow_ema = df['close'].ewm(span=slow_period, adjust=False).mean()
            df['macd_line'] = fast_ema - slow_ema
            df['signal_line'] = df['macd_line'].ewm(span=signal_period, adjust=False).mean()
            df['macd_histogram'] = df['macd_line'] - df['signal_line']
            return df
        except Exception as e:
            print(f"MACD hesaplanırken hata: {str(e)}")
            return df
    
    def add_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        RSI hesapla ve DataFrame'e ekle
        
        Args:
            df: Veri çerçevesi
            period: RSI periyodu
            
        Returns:
            pd.DataFrame: RSI eklenmiş veri çerçevesi
        """
        try:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            rs = avg_gain / avg_loss
            df['rsi'] = 100 - (100 / (1 + rs))
            return df
        except Exception as e:
            print(f"RSI hesaplanırken hata: {str(e)}")
            return df
    
    def add_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """
        Bollinger Bantları hesapla ve DataFrame'e ekle
        
        Args:
            df: Veri çerçevesi
            period: Periyot
            std_dev: Standart sapma çarpanı
            
        Returns:
            pd.DataFrame: Bollinger Bantları eklenmiş veri çerçevesi
        """
        try:
            df['bb_middle'] = df['close'].rolling(window=period).mean()
            df['bb_std'] = df['close'].rolling(window=period).std()
            df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * std_dev)
            df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * std_dev)
            return df
        except Exception as e:
            print(f"Bollinger Bantları hesaplanırken hata: {str(e)}")
            return df
    
    def add_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """
        Stokastik Osilatör hesapla ve DataFrame'e ekle
        
        Args:
            df: Veri çerçevesi
            k_period: K periyodu
            d_period: D periyodu
            
        Returns:
            pd.DataFrame: Stokastik Osilatör eklenmiş veri çerçevesi
        """
        try:
            low_min = df['low'].rolling(window=k_period).min()
            high_max = df['high'].rolling(window=k_period).max()
            
            df['stoch_k'] = 100 * ((df['close'] - low_min) / (high_max - low_min))
            df['stoch_d'] = df['stoch_k'].rolling(window=d_period).mean()
            return df
        except Exception as e:
            print(f"Stokastik Osilatör hesaplanırken hata: {str(e)}")
            return df

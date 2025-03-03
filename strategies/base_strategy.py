import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """
    Temel strateji sınıfı - tüm stratejilerin miras alması gereken sınıf
    """
    
    def __init__(self, params=None):
        """
        Strateji başlatma
        
        Args:
            params (dict, optional): Strateji parametreleri
        """
        self.name = "Base Strategy"
        self.description = "Temel strateji sınıfı"
        self.default_params = {}
        self.params = self.default_params.copy()
        
        # Parametreleri güncelle
        if params:
            self.params.update(params)
    
    @abstractmethod
    def generate_signals(self, df):
        """
        Veri setine göre alım/satım sinyalleri üret
        
        Args:
            df (pd.DataFrame): İşlenecek OHLCV verileri
            
        Returns:
            pd.DataFrame: Sinyalleri içeren DataFrame
        """
        pass
    
    def analyze(self, df):
        """
        Veri setini analiz et ve sinyal, güven skoru ve metrikleri döndür
        
        Args:
            df (pd.DataFrame): İşlenecek OHLCV verileri
            
        Returns:
            tuple: (sinyal, güven skoru, metrikler)
        """
        # Sinyalleri hesapla
        signals_df = self.generate_signals(df)
        
        # Son sinyal
        last_signal = signals_df['signal'].iloc[-1] if 'signal' in signals_df.columns else None
        
        # Güven skorunu hesapla (basit bir örnek)
        confidence = 80.0  # Varsayılan güven skoru
        
        # Metrikler
        metrics = {
            'last_close': df['close'].iloc[-1],
            'last_volume': df['volume'].iloc[-1],
            'signal_count': signals_df['signal'].value_counts().to_dict() if 'signal' in signals_df.columns else {}
        }
        
        return last_signal, confidence, metrics
    
    def get_parameters(self):
        """
        Strateji parametrelerini döndür
        
        Returns:
            dict: Strateji parametreleri
        """
        return self.params
    
    def set_parameters(self, params):
        """
        Strateji parametrelerini ayarla
        
        Args:
            params (dict): Yeni parametreler
        """
        self.params.update(params)
    
    def reset_parameters(self):
        """
        Strateji parametrelerini varsayılana sıfırla
        """
        self.params = self.default_params.copy()

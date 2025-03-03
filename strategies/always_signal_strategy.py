from .base_strategy import BaseStrategy
import pandas as pd
import numpy as np

class AlwaysSignalStrategy(BaseStrategy):
    """
    Her zaman sinyal üreten basit bir strateji.
    Test amaçlı kullanılabilir.
    """
    
    def __init__(self, signal_type='buy', **kwargs):
        """
        AlwaysSignalStrategy başlatıcı
        
        Args:
            signal_type (str, optional): Üretilecek sinyal tipi ('buy', 'sell' veya 'random'). Defaults to 'buy'.
        """
        super().__init__(**kwargs)
        self.signal_type = signal_type
        self.name = "AlwaysSignalStrategy"
        self.description = "Her zaman belirtilen tipte sinyal üreten basit bir strateji"
        
    def generate_signals(self, df):
        """
        Veri çerçevesine sinyal ekler
        
        Args:
            df (pandas.DataFrame): İşlem verileri
            
        Returns:
            pandas.DataFrame: Sinyaller eklenmiş veri çerçevesi
        """
        # Kopya oluştur
        signals = df.copy()
        
        # Sinyal kolonları oluştur
        signals['signal'] = 0
        signals['position'] = 0
        
        # Sinyal tipine göre değerleri ata
        if self.signal_type == 'buy':
            signals['signal'] = 1
        elif self.signal_type == 'sell':
            signals['signal'] = -1
        elif self.signal_type == 'random':
            signals['signal'] = np.random.choice([1, -1], size=len(signals))
        
        # Pozisyon hesapla
        signals['position'] = signals['signal'].cumsum()
        
        return signals
    
    @classmethod
    def get_parameters(cls):
        """
        Strateji parametrelerini döndürür
        
        Returns:
            dict: Parametre adları ve açıklamaları
        """
        return {
            'signal_type': {
                'type': 'select',
                'options': ['buy', 'sell', 'random'],
                'default': 'buy',
                'description': 'Üretilecek sinyal tipi'
            }
        }
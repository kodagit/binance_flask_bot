import logging
import os
import importlib
import inspect
from typing import Dict, List, Any, Optional
from strategy_config import StrategyConfig

logger = logging.getLogger(__name__)

class StrategyManager:
    """
    Strateji yöneticisi sınıfı
    """
    
    def __init__(self, strategies_dir="strategies"):
        """
        Strateji yöneticisini başlat
        
        Args:
            strategies_dir (str): Stratejilerin bulunduğu dizin
        """
        self.strategies_dir = strategies_dir
        self.strategies = {}
        self.config = StrategyConfig()
        self.logger = logging.getLogger('strategy_manager')
        self.load_strategies()
        
        # Eğer hiç strateji yüklenmediyse, varsayılan stratejileri ekle
        if not self.strategies:
            self.add_default_strategies()
        
    def load_strategies(self):
        """
        Tüm stratejileri yükle
        """
        try:
            self.logger.info("Stratejiler yükleniyor...")
            
            # Strateji dosyalarını bul
            strategy_files = self._find_strategy_files()
            self.logger.info(f"Bulunan strateji dosyaları: {strategy_files}")
            
            # Her strateji dosyasını yükle
            for file_name in strategy_files:
                try:
                    # Modül adını al
                    module_name = file_name.replace('.py', '')
                    
                    # Dosya strategies dizininde mi yoksa ana dizinde mi kontrol et
                    if os.path.exists(os.path.join(self.strategies_dir, file_name)):
                        # Strategies dizinindeki dosya
                        module_path = f"{self.strategies_dir}.{module_name}"
                    else:
                        # Ana dizindeki dosya
                        module_path = module_name
                    
                    # Modülü import et
                    module = importlib.import_module(module_path)
                    
                    # Modüldeki tüm sınıfları kontrol et
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # Strateji sınıflarını bul (adında "Strategy" geçenler)
                        if "Strategy" in name and name != "BaseStrategy":
                            # Strateji sınıfını kaydet
                            self.strategies[name] = obj
                            self.logger.info(f"Strateji yüklendi: {name}")
                            
                except Exception as e:
                    self.logger.error(f"Strateji yüklenirken hata: {module_name} - {str(e)}")
                    import traceback
                    self.logger.error(traceback.format_exc())
            
            self.logger.info(f"Toplam {len(self.strategies)} strateji yüklendi")
            
        except Exception as e:
            self.logger.error(f"Stratejiler yüklenirken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
    def _find_strategy_files(self) -> List[str]:
        """
        Strateji dosyalarını bul
        
        Returns:
            List[str]: Strateji dosyalarının listesi
        """
        strategy_files = []
        
        try:
            # Strategies dizinini kontrol et
            if not os.path.exists(self.strategies_dir):
                os.makedirs(self.strategies_dir)
                self.logger.info(f"Strategies dizini oluşturuldu: {self.strategies_dir}")
            
            # Strategies dizinindeki tüm .py dosyalarını bul
            for file_name in os.listdir(self.strategies_dir):
                if file_name.endswith('.py') and not file_name.startswith('__'):
                    strategy_files.append(file_name)
            
            # Ana dizindeki strateji dosyalarını da ekle
            main_dir_strategy_files = [
                "always_signal_strategy.py",
                "five_stage_approval_strategy.py",
                "simple_strategy.py",
                "advanced_strategy.py",
                "rci_ema_strategy.py",
                "debug_strategy.py"
            ]
            
            # Ana dizindeki strateji dosyalarını kontrol et ve ekle
            for file_name in main_dir_strategy_files:
                if os.path.exists(file_name):
                    strategy_files.append(file_name)
            
            # Eğer hiç dosya bulunamadıysa, varsayılan stratejileri ekle
            if not strategy_files:
                # Doğrudan belirli strateji dosyalarını ekle
                known_strategies = [
                    "always_signal_strategy.py",
                    "five_stage_approval_strategy.py"
                ]
                
                # Varsayılan stratejileri oluştur
                for strategy_file in known_strategies:
                    self._create_default_strategy_file(strategy_file)
                    strategy_files.append(strategy_file)
                    
            self.logger.info(f"Bulunan strateji dosyaları: {strategy_files}")
            
        except Exception as e:
            self.logger.error(f"Strateji dosyaları bulunurken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
        return strategy_files
    
    def _create_default_strategy_file(self, file_name: str):
        """
        Varsayılan strateji dosyasını oluştur
        
        Args:
            file_name (str): Oluşturulacak dosya adı
        """
        try:
            file_path = os.path.join(self.strategies_dir, file_name)
            
            # Dosya içeriğini belirle
            if file_name == "always_signal_strategy.py":
                content = """
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class AlwaysSignalStrategy(BaseStrategy):
    \"\"\"Her zaman sinyal üreten basit strateji\"\"\"
    
    def __init__(self, params=None):
        super().__init__(params)
        self.name = "Always Signal Strategy"
        self.description = "Her zaman BUY sinyali üreten basit test stratejisi"
        
    def generate_signals(self, df):
        \"\"\"
        Veri setine göre alım/satım sinyalleri üret
        
        Args:
            df (pd.DataFrame): İşlenecek OHLCV verileri
            
        Returns:
            pd.DataFrame: Sinyalleri içeren DataFrame
        \"\"\"
        # Kopya oluştur
        signals = df.copy()
        
        # Her zaman BUY sinyali ekle
        signals['signal'] = 'BUY'
        
        return signals
"""
            elif file_name == "five_stage_approval_strategy.py":
                content = """
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class FiveStageApprovalStrategy(BaseStrategy):
    \"\"\"5 aşamalı onay stratejisi\"\"\"
    
    def __init__(self, params=None):
        super().__init__(params)
        self.name = "Five Stage Approval Strategy"
        self.description = "5 farklı indikatörün onayına dayalı strateji"
        
        # Varsayılan parametreler
        self.default_params = {
            'ema_short': 9,
            'ema_medium': 21,
            'ema_long': 50,
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9
        }
        
        # Parametreleri ayarla
        self.params = self.default_params.copy()
        if params:
            self.params.update(params)
    
    def generate_signals(self, df):
        \"\"\"
        Veri setine göre alım/satım sinyalleri üret
        
        Args:
            df (pd.DataFrame): İşlenecek OHLCV verileri
            
        Returns:
            pd.DataFrame: Sinyalleri içeren DataFrame
        \"\"\"
        # Kopya oluştur
        signals = df.copy()
        
        # EMA hesapla
        signals[f'ema_{self.params["ema_short"]}'] = signals['close'].ewm(span=self.params['ema_short'], adjust=False).mean()
        signals[f'ema_{self.params["ema_medium"]}'] = signals['close'].ewm(span=self.params['ema_medium'], adjust=False).mean()
        signals[f'ema_{self.params["ema_long"]}'] = signals['close'].ewm(span=self.params['ema_long'], adjust=False).mean()
        
        # RSI hesapla
        delta = signals['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.params['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.params['rsi_period']).mean()
        rs = gain / loss
        signals['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD hesapla
        signals['macd_fast'] = signals['close'].ewm(span=self.params['macd_fast'], adjust=False).mean()
        signals['macd_slow'] = signals['close'].ewm(span=self.params['macd_slow'], adjust=False).mean()
        signals['macd'] = signals['macd_fast'] - signals['macd_slow']
        signals['macd_signal'] = signals['macd'].ewm(span=self.params['macd_signal'], adjust=False).mean()
        signals['macd_hist'] = signals['macd'] - signals['macd_signal']
        
        # Sinyalleri hesapla
        signals['signal'] = None
        
        # Alım sinyali koşulları
        buy_conditions = (
            (signals[f'ema_{self.params["ema_short"]}'] > signals[f'ema_{self.params["ema_medium"]}']) &  # Kısa EMA orta EMA'nın üstünde
            (signals[f'ema_{self.params["ema_medium"]}'] > signals[f'ema_{self.params["ema_long"]}']) &   # Orta EMA uzun EMA'nın üstünde
            (signals['rsi'] > 50) &                                                                       # RSI 50'nin üstünde
            (signals['macd'] > signals['macd_signal']) &                                                  # MACD sinyal çizgisinin üstünde
            (signals['macd_hist'] > 0)                                                                    # MACD histogramı pozitif
        )
        
        # Satım sinyali koşulları
        sell_conditions = (
            (signals[f'ema_{self.params["ema_short"]}'] < signals[f'ema_{self.params["ema_medium"]}']) &  # Kısa EMA orta EMA'nın altında
            (signals[f'ema_{self.params["ema_medium"]}'] < signals[f'ema_{self.params["ema_long"]}']) &   # Orta EMA uzun EMA'nın altında
            (signals['rsi'] < 50) &                                                                       # RSI 50'nin altında
            (signals['macd'] < signals['macd_signal']) &                                                  # MACD sinyal çizgisinin altında
            (signals['macd_hist'] < 0)                                                                    # MACD histogramı negatif
        )
        
        # Sinyalleri uygula
        signals.loc[buy_conditions, 'signal'] = 'BUY'
        signals.loc[sell_conditions, 'signal'] = 'SELL'
        
        return signals
"""
            
            # Dosyayı oluştur
            with open(file_path, 'w') as f:
                f.write(content)
                
            self.logger.info(f"Varsayılan strateji dosyası oluşturuldu: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Varsayılan strateji dosyası oluşturulurken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
    def get_strategy(self, strategy_name: str) -> Any:
        """
        Strateji sınıfını al
        
        Args:
            strategy_name (str): Strateji adı
            
        Returns:
            Any: Strateji sınıfı instance'ı
        """
        try:
            # Strateji adını düzelt (boşlukları kaldır, ilk harfi büyük yap)
            strategy_name = strategy_name.replace(" ", "")
            if "Strategy" not in strategy_name:
                strategy_name = f"{strategy_name}Strategy"
            
            # Strateji sınıfını bul
            for name, strategy_class in self.strategies.items():
                if name.lower() == strategy_name.lower():
                    self.logger.info(f"Strateji bulundu: {name}")
                    return strategy_class()
                
            # Strateji bulunamadı
            self.logger.error(f"Strateji bulunamadı: {strategy_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"Strateji alınırken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
            
    def get_strategy_class(self, strategy_name):
        """
        Belirli bir strateji sınıfını döndür
        
        Args:
            strategy_name (str): Strateji adı
            
        Returns:
            class: Strateji sınıfı
        """
        if strategy_name in self.strategies:
            return self.strategies[strategy_name]
        return None

    def get_strategy_names(self) -> List[str]:
        """
        Tüm strateji isimlerini döndür
        
        Returns:
            List[str]: Strateji isimleri listesi
        """
        try:
            # Stratejilerin yüklendiğinden emin ol
            if not self.strategies:
                self.load_strategies()
                
            # Eğer hala strateji yoksa, varsayılan stratejileri ekle
            if not self.strategies:
                self.add_default_strategies()
                
            # Strateji isimlerini döndür
            return list(self.strategies.keys())
        except Exception as e:
            self.logger.error(f"Strateji isimleri alınırken hata: {str(e)}")
            return []
    
    def get_strategy_parameters(self, strategy_name: str) -> Dict:
        """
        Get parameters for a specific strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Dictionary containing strategy parameters
        """
        try:
            # Convert strategy name to key if needed
            strategy_key = strategy_name
            
            # Get parameters from config
            params = self.config.get_strategy_parameters(strategy_key)
            
            # Add description if available
            if params:
                strategy_class = self.get_strategy_class(strategy_name)
                if strategy_class:
                    if hasattr(strategy_class, 'description'):
                        params['description'] = strategy_class.description
                    elif hasattr(strategy_class, '__doc__') and strategy_class.__doc__:
                        params['description'] = strategy_class.__doc__.strip()
                    else:
                        params['description'] = f"{strategy_name} strategy"
            
            return params
        except Exception as e:
            self.logger.error(f"Error getting parameters for strategy {strategy_name}: {e}")
            return None

    def save_strategy_parameters(self, strategy_name: str, parameters: Dict) -> bool:
        """
        Save parameters for a specific strategy.
        
        Args:
            strategy_name: Name of the strategy
            parameters: Dictionary of parameter values to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert strategy name to key if needed
            strategy_key = strategy_name
            
            # Update each parameter
            success = True
            for param_name, param_value in parameters.items():
                result = self.config.update_strategy_parameter(strategy_key, param_name, param_value)
                if not result:
                    success = False
                    self.logger.warning(f"Failed to update parameter {param_name} for strategy {strategy_name}")
            
            return success
        except Exception as e:
            self.logger.error(f"Error saving parameters for strategy {strategy_name}: {e}")
            return False

    def reset_strategy_parameters(self, strategy_name: str) -> bool:
        """
        Reset parameters for a specific strategy to default values.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert strategy name to key if needed
            strategy_key = strategy_name
            
            # Reset parameters
            result = self.config.reset_strategy_parameters(strategy_key)
            
            return result
        except Exception as e:
            self.logger.error(f"Error resetting parameters for strategy {strategy_name}: {e}")
            return False

    def add_default_strategies(self):
        """
        Varsayılan stratejileri ekle
        """
        try:
            # AlwaysSignalStrategy ekle
            if "AlwaysSignalStrategy" not in self.strategies:
                from strategies.always_signal_strategy import AlwaysSignalStrategy
                self.strategies["AlwaysSignalStrategy"] = AlwaysSignalStrategy
                self.logger.info("Always Signal stratejisi kaydedildi")
                
                # Varsayılan parametreleri ekle
                self.config.set_strategy_parameters("AlwaysSignalStrategy", {
                    "signal_type": {
                        "type": "select",
                        "options": ["BUY", "SELL", "NONE"],
                        "default": "BUY",
                        "description": "Üretilecek sinyal tipi"
                    },
                    "confidence": {
                        "type": "number",
                        "min": 0,
                        "max": 100,
                        "default": 80,
                        "description": "Sinyal güven skoru"
                    }
                })
            
            # FiveStageApprovalStrategy ekle
            if "FiveStageApprovalStrategy" not in self.strategies:
                from strategies.five_stage_approval_strategy import FiveStageApprovalStrategy
                self.strategies["FiveStageApprovalStrategy"] = FiveStageApprovalStrategy
                self.logger.info("Five Stage Approval stratejisi kaydedildi")
                
                # Varsayılan parametreleri ekle
                self.config.set_strategy_parameters("FiveStageApprovalStrategy", {
                    "ema_short": {
                        "type": "number",
                        "min": 3,
                        "max": 50,
                        "default": 9,
                        "description": "Kısa EMA periyodu"
                    },
                    "ema_medium": {
                        "type": "number",
                        "min": 10,
                        "max": 100,
                        "default": 21,
                        "description": "Orta EMA periyodu"
                    },
                    "ema_long": {
                        "type": "number",
                        "min": 20,
                        "max": 200,
                        "default": 50,
                        "description": "Uzun EMA periyodu"
                    },
                    "rsi_period": {
                        "type": "number",
                        "min": 3,
                        "max": 30,
                        "default": 14,
                        "description": "RSI periyodu"
                    },
                    "rsi_overbought": {
                        "type": "number",
                        "min": 50,
                        "max": 100,
                        "default": 70,
                        "description": "RSI aşırı alım seviyesi"
                    },
                    "rsi_oversold": {
                        "type": "number",
                        "min": 0,
                        "max": 50,
                        "default": 30,
                        "description": "RSI aşırı satım seviyesi"
                    },
                    "macd_fast": {
                        "type": "number",
                        "min": 3,
                        "max": 50,
                        "default": 12,
                        "description": "MACD hızlı periyodu"
                    },
                    "macd_slow": {
                        "type": "number",
                        "min": 10,
                        "max": 100,
                        "default": 26,
                        "description": "MACD yavaş periyodu"
                    },
                    "macd_signal": {
                        "type": "number",
                        "min": 3,
                        "max": 30,
                        "default": 9,
                        "description": "MACD sinyal periyodu"
                    }
                })
                
        except Exception as e:
            self.logger.error(f"Varsayılan stratejiler eklenirken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

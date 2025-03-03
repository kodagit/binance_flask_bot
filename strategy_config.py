import json
import os
import logging
from typing import Dict, Any, List, Optional
import copy

logger = logging.getLogger(__name__)

class StrategyConfig:
    """
    Strateji yapılandırma sınıfı
    """
    
    def __init__(self, config_file='config.json'):
        """
        Strateji yapılandırmasını başlat
        
        Args:
            config_file (str): Yapılandırma dosyası yolu
        """
        self.config_file = config_file
        self.config = None
        self.logger = logging.getLogger('strategy_config')
        
        # Yapılandırmayı yükle veya oluştur
        self._load_or_create_config()
    
    def _load_or_create_config(self) -> None:
        """
        Yapılandırma dosyasını yükle veya oluştur
        
        Returns:
            None
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                # Varsayılan yapılandırma
                default_config = self._create_default_config()
                self._save_config(default_config)
                self.config = default_config
        except Exception as e:
            self.logger.error(f"Yapılandırma yüklenirken hata: {str(e)}")
            self.config = self._create_default_config()
    
    def _save_config(self, config: Dict) -> bool:
        """
        Yapılandırmayı dosyaya kaydet
        
        Args:
            config: Kaydedilecek yapılandırma
            
        Returns:
            bool: Başarılı ise True, değilse False
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Yapılandırma kaydedilirken hata: {str(e)}")
            return False
    
    def _create_default_config(self) -> Dict:
        """
        Varsayılan yapılandırmayı oluştur
        
        Returns:
            Dict: Varsayılan yapılandırma
        """
        return {
            "strategies": {
                "AlwaysSignalStrategy": {
                    "description": "Her zaman sinyal üreten test stratejisi",
                    "parameters": {
                        "signal_frequency": {
                            "type": "int",
                            "default": 2,
                            "min": 1,
                            "max": 10,
                            "description": "Kaç mumda bir sinyal üretileceği"
                        }
                    }
                },
                "FiveStageApprovalStrategy": {
                    "description": "5 aşamalı onay sistemi ile işlem stratejisi",
                    "parameters": {
                        "ema_short": {
                            "type": "int",
                            "default": 9,
                            "min": 5,
                            "max": 50,
                            "description": "Kısa EMA periyodu"
                        },
                        "ema_medium": {
                            "type": "int",
                            "default": 21,
                            "min": 10,
                            "max": 100,
                            "description": "Orta EMA periyodu"
                        },
                        "ema_long": {
                            "type": "int",
                            "default": 50,
                            "min": 20,
                            "max": 200,
                            "description": "Uzun EMA periyodu"
                        },
                        "rsi_period": {
                            "type": "int",
                            "default": 14,
                            "min": 5,
                            "max": 30,
                            "description": "RSI periyodu"
                        },
                        "rsi_overbought": {
                            "type": "int",
                            "default": 70,
                            "min": 50,
                            "max": 90,
                            "description": "RSI aşırı alım seviyesi"
                        },
                        "rsi_oversold": {
                            "type": "int",
                            "default": 30,
                            "min": 10,
                            "max": 50,
                            "description": "RSI aşırı satım seviyesi"
                        },
                        "macd_fast": {
                            "type": "int",
                            "default": 12,
                            "min": 5,
                            "max": 50,
                            "description": "MACD hızlı periyodu"
                        },
                        "macd_slow": {
                            "type": "int",
                            "default": 26,
                            "min": 10,
                            "max": 100,
                            "description": "MACD yavaş periyodu"
                        },
                        "macd_signal": {
                            "type": "int",
                            "default": 9,
                            "min": 5,
                            "max": 30,
                            "description": "MACD sinyal periyodu"
                        }
                    }
                },
                "SimpleStrategy": {
                    "description": "Basit EMA kesişim stratejisi",
                    "parameters": {
                        "ema_short_period": {
                            "type": "int",
                            "default": 10,
                            "min": 5,
                            "max": 50,
                            "description": "Kısa EMA periyodu"
                        },
                        "ema_long_period": {
                            "type": "int",
                            "default": 20,
                            "min": 10,
                            "max": 100,
                            "description": "Uzun EMA periyodu"
                        }
                    }
                },
                "AdvancedStrategy": {
                    "description": "Gelişmiş çoklu indikatör stratejisi",
                    "parameters": {
                        "ema_short": {
                            "type": "int",
                            "default": 50,
                            "min": 10,
                            "max": 100,
                            "description": "Kısa EMA periyodu"
                        },
                        "ema_long": {
                            "type": "int",
                            "default": 200,
                            "min": 50,
                            "max": 300,
                            "description": "Uzun EMA periyodu"
                        },
                        "rsi_period": {
                            "type": "int",
                            "default": 14,
                            "min": 5,
                            "max": 30,
                            "description": "RSI periyodu"
                        },
                        "rsi_oversold": {
                            "type": "int",
                            "default": 40,
                            "min": 20,
                            "max": 50,
                            "description": "RSI aşırı satım seviyesi"
                        },
                        "rsi_overbought": {
                            "type": "int",
                            "default": 60,
                            "min": 50,
                            "max": 80,
                            "description": "RSI aşırı alım seviyesi"
                        },
                        "atr_period": {
                            "type": "int",
                            "default": 14,
                            "min": 5,
                            "max": 30,
                            "description": "ATR periyodu"
                        },
                        "atr_multiplier": {
                            "type": "float",
                            "default": 1.5,
                            "min": 0.5,
                            "max": 5.0,
                            "description": "ATR çarpanı"
                        },
                        "stoch_rsi_period": {
                            "type": "int",
                            "default": 14,
                            "min": 5,
                            "max": 30,
                            "description": "Stochastic RSI periyodu"
                        },
                        "stoch_rsi_k": {
                            "type": "int",
                            "default": 3,
                            "min": 1,
                            "max": 10,
                            "description": "Stochastic RSI K periyodu"
                        },
                        "stoch_rsi_d": {
                            "type": "int",
                            "default": 3,
                            "min": 1,
                            "max": 10,
                            "description": "Stochastic RSI D periyodu"
                        },
                        "stoch_rsi_oversold": {
                            "type": "int",
                            "default": 20,
                            "min": 5,
                            "max": 40,
                            "description": "Stochastic RSI aşırı satım seviyesi"
                        },
                        "stoch_rsi_overbought": {
                            "type": "int",
                            "default": 80,
                            "min": 60,
                            "max": 95,
                            "description": "Stochastic RSI aşırı alım seviyesi"
                        },
                        "supertrend_period": {
                            "type": "int",
                            "default": 10,
                            "min": 5,
                            "max": 30,
                            "description": "Supertrend periyodu"
                        },
                        "supertrend_multiplier": {
                            "type": "float",
                            "default": 3.0,
                            "min": 1.0,
                            "max": 10.0,
                            "description": "Supertrend çarpanı"
                        }
                    }
                },
                "TrimLossStrategy": {
                    "description": "Kademeli kar alma ve zarar kesme stratejisi",
                    "parameters": {
                        "take_profit_level_1": {
                            "type": "float",
                            "default": 0.03,
                            "min": 0.01,
                            "max": 0.1,
                            "description": "1. Kar alma seviyesi (%)"
                        },
                        "take_profit_level_2": {
                            "type": "float",
                            "default": 0.04,
                            "min": 0.01,
                            "max": 0.15,
                            "description": "2. Kar alma seviyesi (%)"
                        },
                        "take_profit_level_3": {
                            "type": "float",
                            "default": 0.05,
                            "min": 0.01,
                            "max": 0.2,
                            "description": "3. Kar alma seviyesi (%)"
                        },
                        "position_size_level_1": {
                            "type": "float",
                            "default": 0.3,
                            "min": 0.1,
                            "max": 0.5,
                            "description": "1. Seviyede kapatılacak pozisyon oranı"
                        },
                        "position_size_level_2": {
                            "type": "float",
                            "default": 0.3,
                            "min": 0.1,
                            "max": 0.5,
                            "description": "2. Seviyede kapatılacak pozisyon oranı"
                        },
                        "position_size_level_3": {
                            "type": "float",
                            "default": 0.4,
                            "min": 0.1,
                            "max": 0.5,
                            "description": "3. Seviyede kapatılacak pozisyon oranı"
                        },
                        "trailing_stop_activation": {
                            "type": "float",
                            "default": 0.02,
                            "min": 0.005,
                            "max": 0.1,
                            "description": "Trailing stop aktifleşme seviyesi (%)"
                        },
                        "trailing_stop_distance": {
                            "type": "float",
                            "default": 0.01,
                            "min": 0.005,
                            "max": 0.05,
                            "description": "Trailing stop mesafesi (%)"
                        }
                    }
                },
                "MultiTimeframeStrategy": {
                    "description": "Çoklu zaman dilimi stratejisi",
                    "parameters": {
                        "short_timeframe_weight": {
                            "type": "float",
                            "default": 0.3,
                            "min": 0.1,
                            "max": 0.5,
                            "description": "Kısa zaman dilimi ağırlığı"
                        },
                        "medium_timeframe_weight": {
                            "type": "float",
                            "default": 0.3,
                            "min": 0.1,
                            "max": 0.5,
                            "description": "Orta zaman dilimi ağırlığı"
                        },
                        "long_timeframe_weight": {
                            "type": "float",
                            "default": 0.4,
                            "min": 0.1,
                            "max": 0.5,
                            "description": "Uzun zaman dilimi ağırlığı"
                        },
                        "confidence_threshold": {
                            "type": "float",
                            "default": 70.0,
                            "min": 50.0,
                            "max": 90.0,
                            "description": "Sinyal üretme güven eşiği"
                        }
                    }
                }
            }
        }
    
    def get_strategy_parameters(self, strategy_name):
        """
        Get parameters for a specific strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Dictionary containing strategy parameters or None if not found
        """
        try:
            if not self.config or 'strategies' not in self.config:
                self.logger.error("Configuration file is invalid or not loaded")
                return None
            
            if strategy_name not in self.config['strategies']:
                self.logger.warning(f"Strategy {strategy_name} not found in configuration")
                return None
            
            # Check if parameters exist
            if 'parameters' not in self.config['strategies'][strategy_name]:
                self.logger.warning(f"No parameters found for strategy {strategy_name}")
                return {'parameters': {}}
            
            # Return a copy to prevent modification of the original
            return {'parameters': copy.deepcopy(self.config['strategies'][strategy_name]['parameters'])}
        
        except Exception as e:
            self.logger.error(f"Error getting parameters for strategy {strategy_name}: {e}")
            return None

    def update_strategy_parameter(self, strategy_name, parameter_name, value):
        """
        Update a specific parameter for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            parameter_name: Name of the parameter to update
            value: New value for the parameter
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.config or 'strategies' not in self.config:
                self.logger.error("Configuration file is invalid or not loaded")
                return False
            
            if strategy_name not in self.config['strategies']:
                self.logger.warning(f"Strategy {strategy_name} not found in configuration")
                return False
            
            # Check if parameters exist
            if 'parameters' not in self.config['strategies'][strategy_name]:
                self.logger.warning(f"No parameters found for strategy {strategy_name}")
                return False
            
            if parameter_name not in self.config['strategies'][strategy_name]['parameters']:
                self.logger.warning(f"Parameter {parameter_name} not found for strategy {strategy_name}")
                return False
            
            # Update the parameter
            self.config['strategies'][strategy_name]['parameters'][parameter_name]['default'] = value
            
            # Save the configuration
            self._save_config(self.config)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error updating parameter {parameter_name} for strategy {strategy_name}: {e}")
            return False

    def reset_strategy_parameters(self, strategy_name):
        """
        Reset all parameters for a strategy to their default values.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.config or 'strategies' not in self.config:
                self.logger.error("Configuration file is invalid or not loaded")
                return False
            
            if strategy_name not in self.config['strategies']:
                self.logger.warning(f"Strategy {strategy_name} not found in configuration")
                return False
            
            # Load the default configuration
            default_config = self.load_default_config()
            
            if not default_config or 'strategies' not in default_config:
                self.logger.error("Default configuration file is invalid or not loaded")
                return False
            
            if strategy_name not in default_config['strategies']:
                self.logger.warning(f"Strategy {strategy_name} not found in default configuration")
                return False
            
            # Reset to default values
            if 'parameters' in default_config['strategies'][strategy_name]:
                if 'parameters' not in self.config['strategies'][strategy_name]:
                    self.config['strategies'][strategy_name]['parameters'] = {}
                
                self.config['strategies'][strategy_name]['parameters'] = copy.deepcopy(
                    default_config['strategies'][strategy_name]['parameters']
                )
                
                # Save the configuration
                self._save_config(self.config)
                
                return True
            else:
                self.logger.warning(f"No parameters found in default configuration for strategy {strategy_name}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error resetting parameters for strategy {strategy_name}: {e}")
            return False

    def load_default_config(self):
        """
        Load the default configuration from the template file.
        
        Returns:
            Default configuration dictionary or None if failed
        """
        try:
            default_config_path = os.path.join(os.path.dirname(self.config_file), 'config_template.json')
            
            if not os.path.exists(default_config_path):
                logger.error(f"Default configuration file not found: {default_config_path}")
                return None
            
            with open(default_config_path, 'r') as f:
                default_config = json.load(f)
            
            return default_config
        
        except Exception as e:
            logger.error(f"Error loading default configuration: {e}")
            return None
    
    def get_all_strategies(self) -> List[str]:
        """
        Tüm strateji adlarını al
        
        Returns:
            List[str]: Strateji adları listesi
        """
        try:
            return list(self.config["strategies"].keys())
        except Exception as e:
            logger.error(f"Stratejiler alınırken hata: {str(e)}")
            return []
    
    def add_strategy(self, strategy_name: str, description: str, parameters: Dict) -> bool:
        """
        Yeni strateji ekle
        
        Args:
            strategy_name: Strateji adı
            description: Strateji açıklaması
            parameters: Strateji parametreleri
            
        Returns:
            bool: Başarılı ise True, değilse False
        """
        try:
            if strategy_name not in self.config["strategies"]:
                self.config["strategies"][strategy_name] = {
                    "description": description,
                    "parameters": parameters
                }
                return self._save_config(self.config)
            else:
                logger.warning(f"Strateji zaten mevcut: {strategy_name}")
                return False
        except Exception as e:
            logger.error(f"Strateji eklenirken hata: {str(e)}")
            return False
    
    def remove_strategy(self, strategy_name: str) -> bool:
        """
        Stratejiyi kaldır
        
        Args:
            strategy_name: Strateji adı
            
        Returns:
            bool: Başarılı ise True, değilse False
        """
        try:
            if strategy_name in self.config["strategies"]:
                del self.config["strategies"][strategy_name]
                return self._save_config(self.config)
            else:
                logger.warning(f"Strateji bulunamadı: {strategy_name}")
                return False
        except Exception as e:
            logger.error(f"Strateji kaldırılırken hata: {str(e)}")
            return False
    
    def set_strategy_parameters(self, strategy_name: str, parameters: Dict) -> bool:
        """
        Strateji parametrelerini ayarla
        
        Args:
            strategy_name: Strateji adı
            parameters: Parametre ayarları
            
        Returns:
            bool: Başarılı ise True, değilse False
        """
        try:
            # Strateji adını düzelt (boşlukları alt çizgi ile değiştir)
            strategy_key = strategy_name.replace(' ', '_')
            
            # Eğer strateji yoksa, yeni bir giriş oluştur
            if strategy_key not in self.config['strategies']:
                self.config['strategies'][strategy_key] = {
                    "description": f"{strategy_name} stratejisi",
                    "parameters": {}
                }
            
            # Parametreleri güncelle
            self.config['strategies'][strategy_key]['parameters'] = parameters
            
            # Yapılandırmayı kaydet
            return self._save_config(self.config)
            
        except Exception as e:
            logger.error(f"Strateji parametreleri ayarlanırken hata: {str(e)}")
            return False

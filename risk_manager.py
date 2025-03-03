import logging
import json
import os
from typing import Dict, Optional

class RiskManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'risk_settings.json')
        
        # Varsayılan risk ayarları
        self.default_settings = {
            'max_position_size_percent': 5.0,
            'max_open_positions': 3,
            'max_daily_loss_percent': 5.0,
            'trailing_stop_percent': 2.0,
            'take_profit_percent': 5.0,
            'stop_loss_percent': 3.0,
            'enable_trailing_stop': True,
            'enable_stop_loss': True,
            'enable_take_profit': True,
            'max_risk_per_trade_percent': 1.0,
            'enable_risk_management': True
        }
        
        # Ayarları yükle
        self.settings = self.default_settings.copy()
        try:
            self.load_settings()
        except Exception as e:
            self.logger.error(f"Risk ayarları yüklenirken hata: {str(e)}")
    
    def load_settings(self) -> Dict:
        """Risk ayarlarını yükle"""
        try:
            # Data dizini yoksa oluştur
            data_dir = os.path.dirname(self.settings_file)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
                self.logger.info(f"Data dizini oluşturuldu: {data_dir}")
            
            # Dosya yoksa varsayılan ayarları kullan
            if not os.path.exists(self.settings_file):
                self.logger.info(f"Risk ayarları dosyası bulunamadı, varsayılan ayarlar kullanılıyor")
                return self.default_settings.copy()
            
            # Dosyayı oku
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            
            # Eksik ayarları varsayılanlarla tamamla
            for key, value in self.default_settings.items():
                if key not in settings:
                    settings[key] = value
            
            self.settings = settings
            self.logger.info(f"Risk ayarları başarıyla yüklendi")
            return settings
        
        except Exception as e:
            self.logger.error(f"Risk ayarları yüklenirken hata: {str(e)}")
            return self.default_settings.copy()
    
    def save_settings(self, settings: Dict) -> bool:
        """Risk ayarlarını kaydet"""
        try:
            # Data dizini yoksa oluştur
            data_dir = os.path.dirname(self.settings_file)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # Ayarları kaydet
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            self.settings = settings
            self.logger.info(f"Risk ayarları başarıyla kaydedildi")
            return True
        
        except Exception as e:
            self.logger.error(f"Risk ayarları kaydedilirken hata: {str(e)}")
            return False
    
    def update_settings(self, new_settings: Dict) -> bool:
        """Risk ayarlarını güncelle"""
        try:
            # Mevcut ayarları al
            current_settings = self.settings.copy()
            
            # Yeni ayarları ekle/güncelle
            for key, value in new_settings.items():
                if key in self.default_settings:
                    current_settings[key] = value
            
            # Ayarları kaydet
            return self.save_settings(current_settings)
        
        except Exception as e:
            self.logger.error(f"Risk ayarları güncellenirken hata: {str(e)}")
            return False
    
    def get_settings(self) -> Dict:
        """Risk ayarlarını al"""
        try:
            return self.settings.copy()
        except Exception as e:
            self.logger.error(f"Risk ayarları alınırken hata: {str(e)}")
            return self.default_settings.copy()
    
    def calculate_position_size(self, account_balance: float, current_price: float, symbol: str) -> float:
        """Pozisyon büyüklüğünü hesapla"""
        try:
            max_position_size_percent = self.settings.get('max_position_size_percent', 5.0)
            position_size = account_balance * (max_position_size_percent / 100)
            return position_size
        except Exception as e:
            self.logger.error(f"Pozisyon büyüklüğü hesaplanırken hata: {str(e)}")
            return account_balance * 0.05
    
    def calculate_stop_loss(self, entry_price: float, position_type: str) -> Optional[float]:
        """Stop loss fiyatını hesapla"""
        try:
            stop_loss_percent = self.settings.get('stop_loss_percent', 3.0)
            
            if position_type.upper() == 'LONG':
                stop_loss_price = entry_price * (1 - stop_loss_percent / 100)
            else:  # SHORT
                stop_loss_price = entry_price * (1 + stop_loss_percent / 100)
            
            return stop_loss_price
        except Exception as e:
            self.logger.error(f"Stop loss hesaplanırken hata: {str(e)}")
            return None
    
    def calculate_take_profit(self, entry_price: float, position_type: str) -> Optional[float]:
        """Take profit fiyatını hesapla"""
        try:
            take_profit_percent = self.settings.get('take_profit_percent', 5.0)
            
            if position_type.upper() == 'LONG':
                take_profit_price = entry_price * (1 + take_profit_percent / 100)
            else:  # SHORT
                take_profit_price = entry_price * (1 - take_profit_percent / 100)
            
            return take_profit_price
        except Exception as e:
            self.logger.error(f"Take profit hesaplanırken hata: {str(e)}")
            return None

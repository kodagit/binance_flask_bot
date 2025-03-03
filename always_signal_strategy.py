import pandas as pd
import numpy as np
import logging

class AlwaysSignalStrategy:
    """
    Her zaman sinyal üreten basit bir strateji.
    Kapanış fiyatı çift sayı ise BUY, tek sayı ise SELL sinyali üretir.
    Backtest sistemini test etmek için kullanılır.
    """
    
    def __init__(self, config=None):
        self.name = "Always_Signal"
        self.description = "Her zaman sinyal üreten test stratejisi"
        self.logger = logging.getLogger(__name__)
        
        # Varsayılan parametreler
        self.signal_frequency = 2  # Her kaç mumda bir sinyal üretileceği
        
        # Eğer yapılandırma varsa, parametreleri güncelle
        if config:
            self._load_parameters_from_config(config)
    
    def _load_parameters_from_config(self, config):
        """
        Yapılandırma dosyasından parametreleri yükle
        """
        if 'signal_frequency' in config:
            self.signal_frequency = config['signal_frequency']
            
    def analyze(self, df):
        """
        Veriyi analiz et ve sinyal üret
        
        Args:
            df (pd.DataFrame): Fiyat verileri
            
        Returns:
            pd.DataFrame: Sinyal sütunu eklenmiş veri
        """
        try:
            self.logger.info(f"Always Signal stratejisi analiz ediliyor: {len(df)} satır")
            
            if df.empty:
                self.logger.error("Veri yok veya boş")
                return df
                
            # Veri kopyası oluştur
            result_df = df.copy()
            
            # Sinyal sütunu oluştur
            result_df['signal'] = 'HOLD'  # Varsayılan olarak HOLD
            
            # Her satır için sinyal üret
            for i in range(len(result_df)):
                # Kapanış fiyatını al
                try:
                    close_price = float(result_df.iloc[i]['close'])
                    
                    # Timestamp değerini al (eğer yoksa indeksi kullan)
                    if 'timestamp' in result_df.columns:
                        timestamp = result_df.iloc[i]['timestamp']
                    elif isinstance(result_df.index[i], pd.Timestamp):
                        timestamp = int(result_df.index[i].timestamp() * 1000)
                    else:
                        timestamp = i * 1000  # Varsayılan değer
                    
                    # Timestamp'i kullanarak daha deterministik bir sinyal üret
                    # Bu şekilde tarih aralığı değiştiğinde farklı sayıda sinyal üretilecek
                    timestamp_int = int(timestamp / 1000)
                    
                    # Her 2 mumdan birinde sinyal üret (daha sık sinyal)
                    if i % self.signal_frequency == 0:
                        # Timestamp'in son basamağı çift ise BUY, tek ise SELL
                        if timestamp_int % 2 == 0:
                            result_df.iloc[i, result_df.columns.get_loc('signal')] = 'BUY'
                        else:
                            result_df.iloc[i, result_df.columns.get_loc('signal')] = 'SELL'
                    else:
                        result_df.iloc[i, result_df.columns.get_loc('signal')] = 'HOLD'
                        
                except (ValueError, TypeError, KeyError) as e:
                    self.logger.error(f"Fiyat dönüşümünde hata: {str(e)}")
                    result_df.iloc[i, result_df.columns.get_loc('signal')] = 'HOLD'
            
            # Sinyal dağılımını logla
            signal_counts = result_df['signal'].value_counts()
            self.logger.info(f"Sinyal dağılımı: {signal_counts.to_dict()}")
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"Always Signal stratejisi analiz edilirken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            # Hata durumunda orijinal veriyi döndür
            if 'signal' not in df.columns:
                df = df.copy()
                df['signal'] = 'HOLD'
            return df
            
    def get_signal(self, df):
        """
        Son mum için sinyal üret
        
        Args:
            df (pd.DataFrame): Fiyat verileri
            
        Returns:
            str: Sinyal (BUY, SELL, HOLD)
        """
        try:
            if df.empty:
                return "HOLD"
                
            # Son mum için sinyal üret
            try:
                close_price = float(df.iloc[-1]['close'])
                price_int = int(close_price)
                
                # Çift sayı ise BUY, tek sayı ise SELL
                if price_int % 2 == 0:
                    return "BUY"
                else:
                    return "SELL"
            except (ValueError, TypeError, KeyError, IndexError) as e:
                self.logger.error(f"Sinyal üretirken hata: {str(e)}")
                return "HOLD"
                
        except Exception as e:
            self.logger.error(f"Always Signal stratejisi sinyal üretirken hata: {str(e)}")
            return "HOLD"
            
    def generate_signals(self, df):
        """
        Tüm veri için sinyal üret (Backtest için)
        
        Args:
            df (pd.DataFrame): Fiyat verileri
            
        Returns:
            pd.DataFrame: Sinyal sütunu eklenmiş veri
        """
        self.logger.info(f"Always Signal stratejisi sinyaller üretiliyor: {len(df)} satır")
        
        try:
            # Veri kopyası oluştur
            result_df = df.copy()
            
            # Sinyal sütunu oluştur
            result_df['signal'] = 'HOLD'  # Varsayılan olarak HOLD
            
            # Timestamp sütunu oluştur (eğer yoksa)
            if 'timestamp' not in result_df.columns and not isinstance(result_df.index[0], pd.Timestamp):
                result_df['timestamp'] = [i * 1000 for i in range(len(result_df))]
            
            # Veri aralığını logla
            self.logger.info(f"Veri aralığı: {result_df.index[0]} - {result_df.index[-1]}")
            
            # Her 2 mumdan birinde sinyal üret (daha fazla sinyal)
            for i in range(len(result_df)):
                try:
                    # Timestamp değerini al
                    if 'timestamp' in result_df.columns:
                        timestamp = result_df.iloc[i]['timestamp']
                    elif isinstance(result_df.index[i], pd.Timestamp):
                        timestamp = int(result_df.index[i].timestamp() * 1000)
                    else:
                        timestamp = i * 1000
                    
                    # Her 2 mumdan birinde sinyal üret (daha fazla sinyal)
                    if i % self.signal_frequency == 0:
                        # Timestamp'in son basamağı çift ise BUY, tek ise SELL
                        if (timestamp // 1000) % 2 == 0:
                            result_df.iloc[i, result_df.columns.get_loc('signal')] = 'BUY'
                        else:
                            result_df.iloc[i, result_df.columns.get_loc('signal')] = 'SELL'
                    else:
                        result_df.iloc[i, result_df.columns.get_loc('signal')] = 'HOLD'
                
                except Exception as e:
                    self.logger.error(f"Satır {i} için sinyal üretilirken hata: {str(e)}")
                    result_df.iloc[i, result_df.columns.get_loc('signal')] = 'HOLD'
            
            # Sinyal dağılımını logla
            signal_counts = result_df['signal'].value_counts()
            self.logger.info(f"Sinyal dağılımı: {signal_counts.to_dict()}")
            
            # BUY ve SELL sinyallerinin sayısını kontrol et
            buy_sell_count = result_df['signal'].isin(['BUY', 'SELL']).sum()
            self.logger.info(f"Toplam BUY/SELL sinyali: {buy_sell_count}")
            
            return result_df
        
        except Exception as e:
            self.logger.error(f"Always Signal sinyaller üretilirken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            # Hata durumunda orijinal veriyi döndür
            if 'signal' not in df.columns:
                df = df.copy()
                df['signal'] = 'HOLD'
            return df

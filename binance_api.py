import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from binance.client import Client
from dotenv import load_dotenv

# Logging
logger = logging.getLogger('binance_api')

class BinanceAPI:
    """Binance API işlemleri için sınıf"""
    
    def __init__(self):
        """Binance API istemcisini oluştur"""
        # .env dosyasından API anahtarlarını al
        load_dotenv()
        
        # TestNet mi yoksa Live mı kontrol et
        testnet = os.getenv('TESTNET', 'false').lower() == 'true'
        
        if testnet:
            api_key = os.getenv('BINANCE_TEST_API_KEY')
            api_secret = os.getenv('BINANCE_TEST_API_SECRET')
            logger.info("Binance TEST modu aktif")
        else:
            api_key = os.getenv('BINANCE_LIVE_API_KEY')
            api_secret = os.getenv('BINANCE_LIVE_API_SECRET')
            logger.info("Binance LIVE modu aktif")
        
        # Anahtarları kontrol et
        if not api_key or not api_secret:
            logger.error("Binance API anahtarları bulunamadı. .env dosyasını kontrol edin.")
            raise ValueError("Binance API anahtarları bulunamadı. .env dosyasını kontrol edin.")
            
        # İstemciyi oluştur
        try:
            self.client = Client(api_key, api_secret, testnet=testnet)
            logger.info("Binance API istemcisi başarıyla oluşturuldu")
            
            # API bağlantısını test et
            test_time = self.client.get_server_time()
            if test_time:
                logger.info(f"Binance API bağlantısı test edildi. Sunucu zamanı: {datetime.fromtimestamp(test_time['serverTime']/1000)}")
            
        except Exception as e:
            logger.error(f"Binance API istemcisi oluşturulurken hata: {str(e)}")
            raise e
        
    def get_historical_klines(self, symbol, interval, start_date, end_date=None):
        """
        Belirtilen tarih aralığındaki kline verilerini alır
        
        Args:
            symbol (str): İşlem çifti (örn. BTCUSDT)
            interval (str): Zaman aralığı (örn. 1h, 4h, 1d)
            start_date (datetime): Başlangıç tarihi
            end_date (datetime, optional): Bitiş tarihi. None ise şu anki zaman kullanılır.
            
        Returns:
            pd.DataFrame: OHLCV verileri içeren DataFrame
        """
        try:
            # Bitiş tarihi belirtilmemişse şu anki zamanı kullan
            if end_date is None:
                end_date = datetime.now()
                
            # Datetime nesneleri milisaniyeye çevir
            start_timestamp = int(start_date.timestamp() * 1000)
            end_timestamp = int(end_date.timestamp() * 1000)
            
            logger.info(f"Veri alınıyor: {symbol} {interval} {start_date} - {end_date}")
            logger.info(f"Zaman damgaları: {start_timestamp} - {end_timestamp}")
            
            # Binance API'sinden veri al
            try:
                klines = self.client.get_historical_klines(
                    symbol=symbol,
                    interval=interval,
                    start_str=start_timestamp,
                    end_str=end_timestamp
                )
                logger.info(f"Alınan veri miktarı: {len(klines)} kayıt")
            except Exception as api_error:
                logger.error(f"Binance API'sinden veri alınırken hata: {str(api_error)}")
                if "Invalid symbol" in str(api_error):
                    logger.error(f"Geçersiz sembol: {symbol}")
                elif "Invalid interval" in str(api_error):
                    logger.error(f"Geçersiz zaman aralığı: {interval}")
                else:
                    logger.error(f"API hatası detayı: {repr(api_error)}")
                raise api_error
            
            # Veri boş ise boş DataFrame dön
            if not klines:
                logger.warning(f"Belirtilen tarih aralığında veri bulunamadı: {symbol} {interval}")
                logger.warning(f"Zaman aralığı (ms): {start_timestamp} - {end_timestamp}")
                logger.warning(f"Zaman aralığı (insan okunaklı): {start_date.strftime('%Y-%m-%d %H:%M:%S')} - {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
                return pd.DataFrame()
                
            # Veriyi DataFrame'e dönüştür
            df = pd.DataFrame(
                klines,
                columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ]
            )
            
            # Veri dönüşümlerini yap
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Sayısal sütunları dönüştür
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)
            
            logger.info(f"Veri alındı: {len(df)} satır, ilk tarih: {df.index[0].strftime('%Y-%m-%d %H:%M:%S')}, son tarih: {df.index[-1].strftime('%Y-%m-%d %H:%M:%S')}")
            
            return df
            
        except Exception as e:
            logger.error(f"Veri alınırken genel hata: {str(e)}")
            logger.error(f"Hata tipi: {type(e).__name__}")
            import traceback
            logger.error(f"Hata detayı:\n{traceback.format_exc()}")
            raise e
            
    def get_exchange_info(self, symbol=None):
        """
        Borsa bilgilerini al
        
        Args:
            symbol (str, optional): İşlem çifti. None ise tüm semboller için bilgi alınır.
            
        Returns:
            dict: Borsa bilgileri
        """
        try:
            if symbol:
                return self.client.get_exchange_info(symbol=symbol)
            else:
                return self.client.get_exchange_info()
        except Exception as e:
            logger.error(f"Borsa bilgileri alınırken hata: {str(e)}")
            raise e
            
    def get_symbol_info(self, symbol):
        """
        Sembol bilgilerini al
        
        Args:
            symbol (str): İşlem çifti (örn. BTCUSDT)
            
        Returns:
            dict: Sembol bilgileri
        """
        try:
            return self.client.get_symbol_info(symbol=symbol)
        except Exception as e:
            logger.error(f"Sembol bilgileri alınırken hata: {str(e)}")
            raise e

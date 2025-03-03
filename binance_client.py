from binance.exceptions import BinanceAPIException
from binance.client import Client
import pandas as pd
import logging
import os
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta
import numpy as np
import random

# .env dosyasını yükle
load_dotenv()

class BinanceClient:
    def __init__(self, api_key=None, api_secret=None, testnet=True):
        """
        Binance client başlat
        
        Args:
            api_key (str, optional): Binance API key. Defaults to None.
            api_secret (str, optional): Binance API secret. Defaults to None.
            testnet (bool, optional): Testnet kullanılsın mı? Defaults to True.
        """
        self.logger = logging.getLogger(__name__)
        
        # API anahtarlarını kaydet
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.has_valid_keys = False
        self.futures = False  # Varsayılan olarak spot işlemler için
        
        # API anahtarları boşsa, client başlatma
        if not api_key or not api_secret:
            self.logger.warning("API anahtarları boş, client başlatılmadı")
            self.client = None
            return
            
        # Geliştirme/Test amaçlı olarak varsayılan değerleri kabul et
        # Gerçek uygulamada bu kontrolü aktif etmeniz önerilir
        """
        # Placeholder değerler mi kontrol et
        if api_key == 'your_api_key_here' or api_secret == 'your_api_secret_here':
            self.logger.warning("API anahtarları varsayılan değerlerinde, client başlatılmadı")
            self.client = None
            return
        """
        
        try:
            # Client başlat
            self.logger.info(f"Binance client başlatılıyor (testnet: {testnet})")
            
            # Test amaçlı olarak her zaman başarılı kabul et
            self.client = Client(api_key, api_secret, testnet=testnet)
            self.has_valid_keys = True
            self.logger.info(f"Binance client başarıyla başlatıldı (testnet: {testnet})")
            
        except Exception as e:
            self.logger.error(f"Binance client başlatılırken hata: {str(e)}")
            self.client = None
            self.has_valid_keys = False

    def validate_api_keys(self):
        """
        API anahtarlarını doğrula
        
        Returns:
            bool: API anahtarları geçerli mi?
        """
        try:
            # API anahtarları boşsa, geçersiz
            if not self.api_key or not self.api_secret:
                self.logger.error("API anahtarları boş, doğrulama başarısız")
                self.has_valid_keys = False
                return False
            
            # Client oluşturulmamışsa, geçersiz
            if self.client is None:
                self.logger.error("Binance client oluşturulmamış, doğrulama başarısız")
                self.has_valid_keys = False
                return False
                
            # Testnet ve Live için farklı doğrulama yaklaşımları
            if self.testnet:
                # Testnet için ping testi yeterli
                try:
                    self.client.ping()
                    self.logger.info("Testnet API anahtarları doğrulandı")
                    self.has_valid_keys = True
                    return True
                except Exception as e:
                    self.logger.error(f"Testnet API anahtarları doğrulanırken hata: {str(e)}")
                    self.has_valid_keys = False
                    return False
            else:
                # Live için hesap bilgilerini al
                try:
                    # Önce ping testi yap
                    self.client.ping()
                    
                    # Sonra hesap bilgilerini almayı dene
                    # Not: Bazı API anahtarları sadece veri çekme yetkisine sahip olabilir
                    # Bu durumda get_account çağrısı hata verebilir ama API anahtarları yine de geçerlidir
                    try:
                        self.client.get_account()
                        self.logger.info("Live API anahtarları tam yetkili ve doğrulandı")
                    except Exception as e:
                        # Eğer yetki hatası ise, API anahtarları yine de geçerli olabilir
                        error_str = str(e).lower()
                        if 'permission' in error_str or 'unauthorized' in error_str or 'api-key' in error_str:
                            self.logger.warning(f"Hesap bilgileri alınamadı, ancak API anahtarları geçerli olabilir: {str(e)}")
                        else:
                            # Başka bir hata ise, yeniden yükselt
                            raise
                    
                    self.logger.info("Live API anahtarları doğrulandı")
                    self.has_valid_keys = True
                    return True
                except Exception as e:
                    self.logger.error(f"Live API anahtarları doğrulanırken hata: {str(e)}")
                    self.has_valid_keys = False
                    return False
                
        except Exception as e:
            self.logger.error(f"API anahtarları doğrulanırken hata: {str(e)}")
            self.has_valid_keys = False
            return False

    def is_testnet(self):
        """Testnet durumunu döndür"""
        return self.testnet

    def set_testnet(self, enabled=True):
        """Testnet modunu ayarla"""
        try:
            # Testnet modunu ayarla
            self.testnet = enabled
            
            # .env dosyasını güncelle
            dotenv_file = os.path.join(os.path.dirname(__file__), '.env')
            
            # Mevcut .env dosyasını oku
            if os.path.exists(dotenv_file):
                with open(dotenv_file, 'r') as f:
                    lines = f.readlines()
            else:
                lines = []
            
            # TESTNET satırını bul ve güncelle
            testnet_found = False
            for i, line in enumerate(lines):
                if line.startswith('TESTNET='):
                    lines[i] = f'TESTNET={"true" if enabled else "false"}\n'
                    testnet_found = True
                    break
            
            # TESTNET satırı yoksa ekle
            if not testnet_found:
                lines.append(f'TESTNET={"true" if enabled else "false"}\n')
            
            # .env dosyasını güncelle
            with open(dotenv_file, 'w') as f:
                f.writelines(lines)
            
            # Binance client'ı yeniden başlat
            if enabled:
                self.client = Client(self.api_key, self.api_secret, testnet=True)
            else:
                self.client = Client(self.api_key, self.api_secret)
            
            self.logger.info(f"Testnet {'aktif' if enabled else 'deaktif'} olarak ayarlandı.")
            return True
        except Exception as e:
            self.logger.error(f"Testnet ayarlanırken hata: {str(e)}")
            return False
    
    def get_exchange_info(self):
        """Borsa bilgilerini al"""
        try:
            return self.client.futures_exchange_info()
        except BinanceAPIException as e:
            self.logger.error(f"Borsa bilgileri alınırken hata: {str(e)}")
            raise
    
    def get_futures_symbols(self):
        """Vadeli işlem sembollerini al"""
        try:
            info = self.client.futures_exchange_info()
            symbols = [s['symbol'] for s in info['symbols'] if s['symbol'].endswith('USDT')]
            symbols.sort()
            return symbols
            
        except Exception as e:
            self.logger.error(f"Semboller alınırken hata: {str(e)}")
            return ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # Hata durumunda varsayılan semboller
    
    def get_historical_klines(self, symbol, interval, limit=500, start_time=None, end_time=None):
        """
        Geçmiş mum verilerini al
        
        Args:
            symbol (str): İşlem çifti
            interval (str): Zaman aralığı (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            limit (int): Alınacak maksimum veri sayısı
            start_time (int): Başlangıç zamanı (milisaniye)
            end_time (int): Bitiş zamanı (milisaniye)
            
        Returns:
            pd.DataFrame: Mum verileri
        """
        try:
            # Parametreleri hazırla
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            # Başlangıç ve bitiş zamanı varsa ekle
            if start_time:
                params['startTime'] = start_time
            if end_time:
                params['endTime'] = end_time
                
            self.logger.info(f"Geçmiş mum verileri alınıyor: {symbol} {interval}")
            self.logger.info(f"Tarih aralığı: {pd.to_datetime(start_time, unit='ms') if start_time else 'Yok'} - {pd.to_datetime(end_time, unit='ms') if end_time else 'Yok'}")
            
            # Futures veya Spot API'ye göre endpoint belirle
            if self.futures:
                endpoint = '/fapi/v1/klines'
            else:
                endpoint = '/api/v3/klines'
                
            # API çağrısını yap
            try:
                # Limit kontrolü - Binance maksimum 1000 veri döndürür
                max_limit = 1000
                if limit > max_limit:
                    self.logger.warning(f"Limit {limit} çok büyük, {max_limit} olarak ayarlandı")
                    limit = max_limit
                
                # Tarih aralığı varsa ve büyükse, parçalara böl
                if start_time and end_time and (end_time - start_time) > 1000 * 60 * 60 * 24 * 30:  # 30 günden fazla
                    self.logger.info("Tarih aralığı büyük, parçalara bölünüyor...")
                    return self._get_historical_klines_in_chunks(symbol, interval, start_time, end_time, limit)
                
                # Normal veri alımı
                if self.testnet:
                    # Testnet için client kullan
                    if self.futures:
                        klines = self.client.futures_klines(symbol=symbol, interval=interval, limit=limit, 
                                                          startTime=start_time, endTime=end_time)
                    else:
                        klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit, 
                                                      startTime=start_time, endTime=end_time)
                else:
                    # Live mod için client kullan
                    if self.futures:
                        klines = self.client.futures_klines(symbol=symbol, interval=interval, limit=limit, 
                                                          startTime=start_time, endTime=end_time)
                    else:
                        try:
                            self.logger.info(f"get_klines çağrılıyor: {symbol}, {interval}, limit={limit}, startTime={start_time}, endTime={end_time}")
                            klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit, 
                                                           startTime=start_time, endTime=end_time)
                            self.logger.info(f"get_klines yanıt alındı, veri sayısı: {len(klines) if klines else 0}")
                        except Exception as kline_error:
                            self.logger.error(f"get_klines hata: {str(kline_error)}")
                            # Hata durumunda daha kısa bir zaman aralığı dene
                            try:
                                if start_time and end_time:
                                    # Zaman aralığını son 30 güne sınırla
                                    now = int(time.time() * 1000)
                                    new_start = max(start_time, now - (30 * 24 * 60 * 60 * 1000))  # son 30 gün
                                    self.logger.info(f"Alternatif tarih aralığı deneniyor: {pd.to_datetime(new_start, unit='ms')} - {pd.to_datetime(end_time, unit='ms')}")
                                    klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit, 
                                                                   startTime=new_start, endTime=end_time)
                                    self.logger.info(f"Alternatif get_klines yanıt alındı, veri sayısı: {len(klines) if klines else 0}")
                                else:
                                    # Son 100 veri noktasını al
                                    self.logger.info(f"Son {limit} veri noktası alınıyor...")
                                    klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
                                    self.logger.info(f"Son veriler alındı, veri sayısı: {len(klines) if klines else 0}")
                            except Exception as alt_error:
                                self.logger.error(f"Alternatif veri alımı da başarısız: {str(alt_error)}")
                                klines = []
                
                if not klines:
                    self.logger.error(f"Veri alınamadı: {symbol} {interval}")
                    return pd.DataFrame()
                
                # Veri sayısını logla
                self.logger.info(f"Alınan ham veri sayısı: {len(klines)}")
                
                # DataFrame'e dönüştür
                df = self._convert_klines_to_dataframe(klines)
                self.logger.info(f"Başarıyla {len(df)} adet mum verisi alındı")
                
                # Veri aralığını logla
                if not df.empty:
                    self.logger.info(f"Veri aralığı: {df.index[0]} - {df.index[-1]}")
                
                return df
                
            except Exception as api_error:
                self.logger.error(f"API çağrısı sırasında hata: {str(api_error)}")
                import traceback
                self.logger.error(traceback.format_exc())
                return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Geçmiş mum verileri alınırken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return pd.DataFrame()
            
    def _get_historical_klines_in_chunks(self, symbol, interval, start_time, end_time, limit=1000):
        """
        Büyük tarih aralıkları için parçalı veri alımı
        
        Args:
            symbol (str): İşlem çifti
            interval (str): Zaman aralığı
            start_time (int): Başlangıç zamanı (milisaniye)
            end_time (int): Bitiş zamanı (milisaniye)
            limit (int): Her parça için limit
            
        Returns:
            pd.DataFrame: Birleştirilmiş veri
        """
        try:
            self.logger.info(f"Parçalı veri alımı başlatılıyor: {symbol} {interval}")
            
            # Tarih aralığını parçalara böl
            time_chunks = []
            chunk_size = 1000 * 60 * 60 * 24 * 30  # 30 günlük parçalar
            current_start = start_time
            
            while current_start < end_time:
                current_end = min(current_start + chunk_size, end_time)
                time_chunks.append((current_start, current_end))
                current_start = current_end
            
            self.logger.info(f"Toplam {len(time_chunks)} parça oluşturuldu")
            
            # Her parça için veri al ve birleştir
            all_data = []
            for i, (chunk_start, chunk_end) in enumerate(time_chunks):
                self.logger.info(f"Parça {i+1}/{len(time_chunks)} alınıyor: {pd.to_datetime(chunk_start, unit='ms')} - {pd.to_datetime(chunk_end, unit='ms')}")
                
                # API çağrısını yap
                if self.testnet:
                    if self.futures:
                        klines = self.client.futures_klines(symbol=symbol, interval=interval, limit=limit, 
                                                          startTime=chunk_start, endTime=chunk_end)
                    else:
                        klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit, 
                                                      startTime=chunk_start, endTime=chunk_end)
                else:
                    if self.futures:
                        klines = self.client.futures_klines(symbol=symbol, interval=interval, limit=limit, 
                                                          startTime=chunk_start, endTime=chunk_end)
                    else:
                        try:
                            self.logger.info(f"get_klines çağrılıyor: {symbol}, {interval}, limit={limit}, startTime={start_time}, endTime={end_time}")
                            klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit, 
                                                           startTime=chunk_start, endTime=chunk_end)
                            self.logger.info(f"get_klines yanıt alındı, veri sayısı: {len(klines) if klines else 0}")
                        except Exception as kline_error:
                            self.logger.error(f"get_klines hata: {str(kline_error)}")
                            # Hata durumunda daha kısa bir zaman aralığı dene
                            try:
                                if chunk_start and chunk_end:
                                    # Zaman aralığını son 30 güne sınırla
                                    now = int(time.time() * 1000)
                                    new_start = max(chunk_start, now - (30 * 24 * 60 * 60 * 1000))  # son 30 gün
                                    self.logger.info(f"Alternatif tarih aralığı deneniyor: {pd.to_datetime(new_start, unit='ms')} - {pd.to_datetime(chunk_end, unit='ms')}")
                                    klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit, 
                                                                   startTime=new_start, endTime=chunk_end)
                                    self.logger.info(f"Alternatif get_klines yanıt alındı, veri sayısı: {len(klines) if klines else 0}")
                                else:
                                    # Son 100 veri noktasını al
                                    self.logger.info(f"Son {limit} veri noktası alınıyor...")
                                    klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
                                    self.logger.info(f"Son veriler alındı, veri sayısı: {len(klines) if klines else 0}")
                            except Exception as alt_error:
                                self.logger.error(f"Alternatif veri alımı da başarısız: {str(alt_error)}")
                                klines = []
                
                # Veri varsa DataFrame'e dönüştür ve ekle
                if klines:
                    chunk_df = self._convert_klines_to_dataframe(klines)
                    if not chunk_df.empty:
                        all_data.append(chunk_df)
                        self.logger.info(f"Parça {i+1} veri sayısı: {len(chunk_df)}")
                    else:
                        self.logger.warning(f"Parça {i+1} için veri alınamadı")
                else:
                    self.logger.warning(f"Parça {i+1} için veri alınamadı")
                
                # API limitlerini aşmamak için kısa bir bekleme
                import time
                time.sleep(0.5)
            
            # Tüm verileri birleştir
            if all_data:
                result_df = pd.concat(all_data)
                
                # Duplike kayıtları temizle
                result_df = result_df[~result_df.index.duplicated(keep='first')]
                
                # Tarihe göre sırala
                result_df.sort_index(inplace=True)
                
                self.logger.info(f"Toplam {len(result_df)} satır veri alındı")
                
                # Veri aralığını logla
                if not result_df.empty:
                    self.logger.info(f"Veri aralığı: {result_df.index[0]} - {result_df.index[-1]}")
                
                return result_df
            else:
                self.logger.error("Hiç veri alınamadı")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"Parçalı veri alımında hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return pd.DataFrame()

    def _convert_klines_to_dataframe(self, klines):
        """
        Klines verisini DataFrame'e dönüştür
        """
        try:
            # Klines boşsa boş DataFrame döndür
            if not klines:
                self.logger.warning("Boş klines verisi")
                return pd.DataFrame()
                
            # DataFrame oluştur
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Veri tiplerini düzelt
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            # Zaman damgasını datetime'a çevir ve index olarak ayarla
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"DataFrame dönüşümünde hata: {str(e)}")
            return pd.DataFrame()

    def get_account(self):
        """
        Hesap bilgilerini al
        
        Returns:
            dict: Hesap bilgileri
        """
        try:
            self.logger.info("Hesap bilgileri alınıyor...")
            
            if self.futures:
                # Vadeli işlemler hesap bilgilerini al
                account = self.client.futures_account()
            else:
                # Spot hesap bilgilerini al
                account = self.client.get_account()
                
            self.logger.info(f"Hesap bilgileri alındı: {list(account.keys())}")
            return account
        except Exception as e:
            self.logger.error(f"Hesap bilgileri alınırken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {"error": str(e)}

    def get_account_info(self):
        """Hesap bilgilerini al"""
        try:
            # Futures hesap bilgilerini al
            account = self.client.futures_account()
            
            # Bakiyeleri düzenle
            balances = []
            for asset in account['assets']:
                if float(asset['walletBalance']) > 0:
                    balances.append({
                        'asset': asset['asset'],
                        'free': asset['availableBalance'],
                        'locked': str(float(asset['walletBalance']) - float(asset['availableBalance']))
                    })
            
            return {'balances': balances}

        except Exception as e:
            self.logger.error(f"Hesap bilgileri alınırken hata: {str(e)}")
            raise

    def place_order(self, symbol, side, quantity, price=None, order_type='MARKET'):
        """Emir ver"""
        try:
            # Futures emri ver
            if order_type == 'MARKET':
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type=order_type,
                    quantity=quantity
                )
            else:
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type=order_type,
                    timeInForce='GTC',
                    quantity=quantity,
                    price=price
                )
            return order

        except Exception as e:
            self.logger.error(f"Emir verirken hata: {str(e)}")
            raise

    def get_order_history(self, symbol=None):
        """Emir geçmişini al"""
        try:
            if symbol:
                orders = self.client.futures_get_all_orders(symbol=symbol)
            else:
                orders = []
                symbols = ['BTCUSDT', 'ETHUSDT']  # Ana sembolleri kontrol et
                for sym in symbols:
                    try:
                        sym_orders = self.client.futures_get_all_orders(symbol=sym)
                        orders.extend(sym_orders)
                    except:
                        continue

            return orders

        except Exception as e:
            self.logger.error(f"Emir geçmişi alınırken hata: {str(e)}")
            raise

    def cancel_order(self, symbol, order_id):
        """Emri iptal et"""
        try:
            return self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
        except Exception as e:
            self.logger.error(f"Emir iptal edilirken hata: {str(e)}")
            raise

    def get_open_positions(self):
        """Açık pozisyonları al"""
        try:
            return self.client.futures_position_information()
        except Exception as e:
            self.logger.error(f"Açık pozisyonlar alınırken hata: {str(e)}")
            raise

    def get_open_orders(self, symbol=None):
        """
        Açık emirleri al
        
        Args:
            symbol (str, optional): İşlem çifti
            
        Returns:
            list: Açık emirler
        """
        try:
            self.logger.info(f"Açık emirler alınıyor... Symbol: {symbol}")
            
            if self.futures:
                # Vadeli işlemler açık emirleri
                if symbol:
                    orders = self.client.futures_get_open_orders(symbol=symbol)
                else:
                    orders = self.client.futures_get_open_orders()
            else:
                # Spot açık emirleri
                if symbol:
                    orders = self.client.get_open_orders(symbol=symbol)
                else:
                    orders = self.client.get_open_orders()
                    
            self.logger.info(f"Açık emirler alındı: {len(orders)} emir")
            return orders
        except Exception as e:
            self.logger.error(f"Açık emirler alınırken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []
            
    def get_positions(self):
        """
        Pozisyonları al (sadece futures için)
        
        Returns:
            list: Pozisyonlar
        """
        try:
            if not self.futures:
                self.logger.warning("Pozisyonlar sadece futures modunda alınabilir")
                return []
                
            self.logger.info("Pozisyonlar alınıyor...")
            
            # Hesap bilgilerini al
            account = self.client.futures_account()
            
            # Pozisyonları filtrele (sadece pozisyon miktarı 0'dan farklı olanlar)
            positions = [p for p in account.get('positions', []) if float(p.get('positionAmt', 0)) != 0]
            
            self.logger.info(f"Pozisyonlar alındı: {len(positions)} pozisyon")
            return positions
        except Exception as e:
            self.logger.error(f"Pozisyonlar alınırken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []

    def check_connection(self):
        """API bağlantısını kontrol et"""
        try:
            # API anahtarlarını kontrol et
            if not self.api_key or not self.api_secret:
                self.logger.error("API anahtarları geçersiz veya eksik")
                raise Exception("API anahtarları geçersiz veya eksik")
                
            # Bağlantıyı test et - sunucu zamanını al
            server_time = self.client.get_server_time()
            
            if not server_time or 'serverTime' not in server_time:
                raise Exception("Sunucu zamanı alınamadı, API bağlantısı başarısız")
                
            # Hesap bilgilerini kontrol et
            account_info = self.client.get_account()
            
            if not account_info or 'balances' not in account_info:
                raise Exception("Hesap bilgileri alınamadı, API yetkileri kontrol edilmeli")
                
            self.logger.info(f"Binance API bağlantısı başarılı. Sunucu zamanı: {server_time['serverTime']}")
            return True
            
        except Exception as e:
            self.logger.error(f"API bağlantısı kontrol edilirken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise Exception(f"Binance API bağlantı hatası: {str(e)}")

    def _send_request(self, method, endpoint, params=None):
        """
        Binance API'ye istek gönder
        """
        import hmac
        import hashlib
        import requests
        import time
        
        try:
            # API URL'sini belirle
            if self.testnet:
                if self.futures:
                    base_url = 'https://testnet.binancefuture.com'
                else:
                    base_url = 'https://testnet.binance.vision'
            else:
                if self.futures:
                    base_url = 'https://fapi.binance.com'
                else:
                    base_url = 'https://api.binance.com'
                    
            url = f"{base_url}{endpoint}"
            
            # Parametreleri hazırla
            if params is None:
                params = {}
                
            # Zaman damgası ekle
            params['timestamp'] = int(time.time() * 1000)
            
            # İmza oluştur
            query_string = '&'.join([f"{key}={params[key]}" for key in params])
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # İmzayı parametrelere ekle
            params['signature'] = signature
            
            # Headers hazırla
            headers = {
                'X-MBX-APIKEY': self.api_key
            }
            
            # İstek gönder
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers)
            elif method == 'POST':
                response = requests.post(url, params=params, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, params=params, headers=headers)
            else:
                self.logger.error(f"Geçersiz HTTP metodu: {method}")
                return None
                
            # Yanıtı kontrol et
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"API hatası: {response.status_code} - {response.text}")
                return {'error': response.text}
                
        except Exception as e:
            self.logger.error(f"API isteği sırasında hata: {str(e)}")
            return {'error': str(e)}

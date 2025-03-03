from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import pandas as pd
import numpy as np
import logging
import json
import os
import time
from datetime import datetime, timedelta
import traceback
from binance_client import BinanceClient
from strategy_manager import StrategyManager
from risk_manager import RiskManager

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask uygulamasını oluştur
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'gizli_anahtar_123')

# Strateji yöneticisini oluştur
strategy_manager = StrategyManager()

# Risk yöneticisini oluştur
risk_manager = RiskManager()

# API anahtarlarını al
api_key = os.environ.get('BINANCE_LIVE_API_KEY', '')
api_secret = os.environ.get('BINANCE_LIVE_API_SECRET', '')
testnet = os.environ.get('TESTNET', 'true').lower() == 'true'

# Binance istemcilerini oluştur
binance_client_live = None
binance_client_test = None

def get_binance_client(testnet=True):
    """
    Binance istemcisini döndür
    
    Args:
        testnet (bool, optional): Testnet kullanılacak mı? Defaults to True.
        
    Returns:
        BinanceClient: Binance istemcisi
    """
    global binance_client_test, binance_client_live
    
    if testnet:
        # Testnet API anahtarlarını al
        api_key = os.environ.get('BINANCE_TEST_API_KEY', '')
        api_secret = os.environ.get('BINANCE_TEST_API_SECRET', '')
        logger.info(f"Testnet API anahtarları kullanılıyor: {api_key[:5]}...")
    else:
        # Live API anahtarlarını al
        api_key = os.environ.get('BINANCE_LIVE_API_KEY', '')
        api_secret = os.environ.get('BINANCE_LIVE_API_SECRET', '')
        logger.info(f"Live API anahtarları kullanılıyor: {api_key[:5]}...")
    
    # API anahtarları boşsa, None döndür
    if not api_key or not api_secret:
        logger.error("API anahtarları eksik, Binance client oluşturulamadı")
        return None
    
    if testnet:
        if binance_client_test is None or binance_client_test.client is None:
            logger.warning("Test Binance client mevcut değil, yeniden oluşturuluyor...")
            try:
                binance_client_test = BinanceClient(api_key=api_key, api_secret=api_secret, testnet=True)
                if binance_client_test.client is None:
                    logger.error("Test Binance client oluşturulamadı")
                    return None
            except Exception as e:
                logger.error(f"Test Binance client yeniden oluşturulurken hata: {str(e)}")
                return None
        return binance_client_test
    else:
        if binance_client_live is None or binance_client_live.client is None:
            logger.warning("Live Binance client mevcut değil, yeniden oluşturuluyor...")
            try:
                binance_client_live = BinanceClient(api_key=api_key, api_secret=api_secret, testnet=False)
                if binance_client_live.client is None:
                    logger.error("Live Binance client oluşturulamadı")
                    return None
            except Exception as e:
                logger.error(f"Live Binance client yeniden oluşturulurken hata: {str(e)}")
                return None
        return binance_client_live

# Ana sayfa
@app.route('/')
def index():
    """Ana sayfa"""
    # Testnet durumunu al
    testnet = os.environ.get('TESTNET', 'true').lower() == 'true'
    
    # Sembol listesini al
    try:
        client = get_binance_client(testnet)
        if client is None or client.client is None:
            return render_template('error.html', 
                error="API anahtarları eksik veya geçersiz. Lütfen API anahtarlarınızı kontrol edin.",
                details="Sistem çalışabilmek için geçerli Binance API anahtarlarına ihtiyaç duyar.")
            
        symbols = client.client.get_exchange_info()['symbols']
        symbols = [s['symbol'] for s in symbols if s['symbol'].endswith('USDT')]
        
        if not symbols:
            return render_template('error.html', 
                error="Sembol listesi alınamadı.",
                details="Binance API'den sembol listesi alınamadı. Lütfen API anahtarlarınızı kontrol edin.")
    except Exception as e:
        logger.error(f"Sembol listesi alınırken hata: {str(e)}")
        return render_template('error.html', 
            error="Binance API'ye erişim hatası", 
            details=str(e))
    
    # Zaman dilimleri
    intervals = [
        ("1m", "1 Dakika"),
        ("5m", "5 Dakika"),
        ("15m", "15 Dakika"),
        ("30m", "30 Dakika"),
        ("1h", "1 Saat"),
        ("4h", "4 Saat"),
        ("1d", "1 Gün"),
        ("1w", "1 Hafta")
    ]
    
    # Favori semboller
    favorite_symbols = []
    
    # Stratejileri al
    strategies = strategy_manager.get_strategy_names()
    
    return render_template(
        'index.html', 
        symbols=symbols, 
        intervals=intervals, 
        favorite_symbols=favorite_symbols,
        strategies=strategies,
        testnet=testnet
    )

@app.route('/api/backtest/run', methods=['POST'])
def run_backtest():
    """Backtest çalıştır"""
    try:
        data = request.json
        
        # Parametreleri kontrol et
        symbol = data.get('symbol', 'BTCUSDT')
        interval = data.get('interval', '1h')
        strategy_name = data.get('strategy', 'SimpleStrategy')
        start_date_str = data.get('start_date', None)
        end_date_str = data.get('end_date', None)
        initial_balance = float(data.get('initial_balance', 1000))
        take_profit_pct = float(data.get('take_profit_pct', 0)) if data.get('take_profit_pct') else None
        stop_loss_pct = float(data.get('stop_loss_pct', 0)) if data.get('stop_loss_pct') else None
        trailing_stop_pct = float(data.get('trailing_stop_pct', 0)) if data.get('trailing_stop_pct') else None
        trailing_profit_pct = float(data.get('trailing_profit_pct', 0)) if data.get('trailing_profit_pct') else None
        risk_per_trade_pct = float(data.get('risk_per_trade_pct', 1))
        
        logger.info(f"Backtest isteği alındı: {symbol} {interval} {strategy_name}")
        logger.info(f"İşlem aralığı: {start_date_str} - {end_date_str}")
        
        # Tarih kontrolü
        if not start_date_str or not end_date_str:
            logger.error("Başlangıç veya bitiş tarihi belirtilmemiş")
            return jsonify({'error': 'Başlangıç ve bitiş tarihi gerekli'}), 400
            
        # Strateji yöneticisini al
        from strategy_manager import StrategyManager
        strategy_manager = StrategyManager()
        
        # Strateji sınıfını al
        try:
            logger.info(f"Strateji sınıfını alınıyor: {strategy_name}")
            strategy_class = strategy_manager.get_strategy_class(strategy_name)
            
            if not strategy_class:
                logger.error(f"Strateji bulunamadı: {strategy_name}")
                return jsonify({'error': f'Strateji bulunamadı: {strategy_name}'}), 404
                
            logger.info(f"Strateji sınıfı: {strategy_class.__name__}")
            
        except Exception as e:
            logger.error(f"Strateji alınırken hata: {str(e)}")
            return jsonify({'error': f'Strateji oluşturulamadı: {str(e)}'}), 500
            
        # Binance'dan veri al
        try:
            import pandas as pd
            from datetime import datetime
            
            # Tarihleri datetime'a çevir
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                
                # Tarih kontrolü
                if start_date > end_date:
                    logger.error("Başlangıç tarihi bitiş tarihinden sonra olamaz")
                    return jsonify({'error': 'Başlangıç tarihi bitiş tarihinden sonra olamaz'}), 400
                    
                current_date = datetime.now()
                if end_date > current_date:
                    logger.warning(f"Bitiş tarihi bugünden sonra: {end_date_str}, bugünün tarihine ayarlanıyor")
                    end_date = current_date
                    
                if (end_date - start_date).days > 365:
                    logger.warning("Tarih aralığı çok uzun (>365 gün), performans sorunları olabilir")
                
                logger.info(f"Veri talep aralığı: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
            except ValueError as date_error:
                logger.error(f"Tarih formatı hatası: {str(date_error)}")
                return jsonify({'error': f'Geçersiz tarih formatı: {str(date_error)}'}), 400
            
            logger.info(f"Veri alınıyor: {symbol} {interval} {start_date} - {end_date}")
            
            # Binance'dan veri al
            from binance_api import BinanceAPI
            binance_api = BinanceAPI()
            
            # Veriyi al
            try:
                df = binance_api.get_historical_klines(symbol, interval, start_date, end_date)
                
                if df is None or df.empty:
                    logger.error("Veri alınamadı veya boş")
                    return jsonify({
                        'error': 'Veri alınamadı veya belirtilen tarih aralığında veri yok',
                        'details': f"Symbol: {symbol}, Interval: {interval}, Date Range: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}. Lütfen farklı bir sembol, zaman dilimi veya tarih aralığı deneyin."
                    }), 400
            except Exception as api_error:
                logger.error(f"Veri alınırken API hatası: {str(api_error)}")
                error_msg = str(api_error)
                
                if "Invalid symbol" in error_msg:
                    return jsonify({'error': f'Geçersiz sembol: {symbol}. Lütfen geçerli bir sembol girin.'}), 400
                elif "Invalid interval" in error_msg:
                    return jsonify({'error': f'Geçersiz zaman aralığı: {interval}. Geçerli değerler: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M'}), 400
                else:
                    return jsonify({'error': f'Binance API hatası: {error_msg}'}), 500
                
            # Veri hakkında bilgi logla
            logger.info(f"Veri aralığı: {df.index[0]} - {df.index[-1]}")
            logger.info(f"Toplam veri sayısı: {len(df)}")
            logger.info(f"Veri sütunları: {df.columns.tolist()}")
            logger.info(f"İlk 3 satır: {df.head(3)}")
            
            # Strateji nesnesini oluştur
            if strategy_name == 'AdvancedStrategy':
                strategy = strategy_class('Advanced')  # AdvancedStrategy için 'name' parametresi gerekiyor
            else:
                strategy = strategy_class()
            logger.info(f"Strateji nesnesi oluşturuldu: {type(strategy)}")
            
            # Strateji metodlarını kontrol et
            if not hasattr(strategy, 'generate_signals'):
                logger.error(f"Strateji generate_signals metoduna sahip değil: {strategy_name}")
                return jsonify({'error': f'Strateji generate_signals metoduna sahip değil: {strategy_name}'}), 400
                
            # Sinyalleri hesapla
            logger.info(f"Sinyaller hesaplanıyor...")
            signals = strategy.generate_signals(df)
            
            if signals is None or signals.empty:
                logger.error("Strateji hiç sinyal üretmedi")
                return jsonify({'error': 'Strateji hiç sinyal üretmedi'}), 400
                
            logger.info(f"Sinyaller oluşturuldu: {len(signals)} satır")
            
            # Backtester kullan
            try:
                from new_backtest import Backtester
                backtester = Backtester(strategy_manager)
                
                # Backtest çalıştır
                logger.info(f"Backtest çalıştırılıyor...")
                result = backtester.run(df, strategy, symbol, interval, initial_balance, 
                                    take_profit_pct, stop_loss_pct, trailing_stop_pct, trailing_profit_pct,
                                    risk_per_trade_pct)
                
                if not result:
                    logger.error("Backtest sonuçları hesaplanamadı")
                    return jsonify({'error': 'Backtest sonuçları hesaplanamadı'}), 400
                    
                # İşlem listesini hazırla
                trades = []
                for trade in result.trades:
                    trades.append({
                        'entry_time': trade.entry_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(trade.entry_time, 'strftime') else str(trade.entry_time),
                        'entry_price': float(trade.entry_price),
                        'exit_time': trade.exit_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(trade.exit_time, 'strftime') else str(trade.exit_time) if trade.exit_time else None,
                        'exit_price': float(trade.exit_price) if trade.exit_price is not None else None,
                        'side': trade.side,
                        'pnl': float(trade.pnl),
                        'pnl_percent': float(trade.pnl_percent)
                    })
                
                # Equity curve'i hazırla
                equity_curve = []
                for time, value in result.equity_curve:
                    equity_curve.append({
                        'time': time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(time, 'strftime') else str(time),
                        'value': float(value)
                    })
                
                # Bakiye geçmişini hazırla
                balance_history = []
                for time, value in result.balance_history:
                    balance_history.append({
                        'time': time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(time, 'strftime') else str(time),
                        'value': float(value)
                    })
                
                # Sinyal istatistiklerini hazırla
                signal_stats = {
                    'buy_signals': len([signal for signal in signals['signal'] if signal == 1]),
                    'sell_signals': len([signal for signal in signals['signal'] if signal == -1]),
                    'neutral_signals': len([signal for signal in signals['signal'] if signal == 0])
                }
                
                # Sonuç
                backtest_result_data = {
                    'strategy': result.strategy,  # strategy_name yerine strategy
                    'symbol': result.symbol,
                    'interval': result.interval,
                    'initial_balance': result.initial_balance,
                    'final_balance': result.final_balance,
                    'profit_loss': result.total_profit_loss,  # profit_loss yerine total_profit_loss
                    'profit_loss_percent': result.total_profit_loss_pct,  # profit_loss_percent yerine total_profit_loss_pct
                    'win_count': result.winning_trades,  # win_count yerine winning_trades
                    'loss_count': result.losing_trades,  # loss_count yerine losing_trades
                    'win_rate': result.win_rate,
                    'max_drawdown': result.max_drawdown,
                    'take_profit_pct': result.take_profit_pct,
                    'stop_loss_pct': result.stop_loss_pct,
                    'trailing_stop_pct': result.trailing_stop_pct,
                    'trailing_profit_pct': result.trailing_profit_pct,
                    'risk_per_trade_pct': result.risk_per_trade_pct,
                    'equity_curve': result.equity_curve,
                    'trades': result.trades,
                    'signal_stats': result.signal_stats,  # Sinyal istatistikleri eklendi
                    'date_range': {
                        'start_date': start_date,
                        'end_date': end_date,
                        'data_points': len(df) if df is not None else 0
                    }
                }
                
                logger.info(f"Backtest tamamlandı: {result.total_trades} işlem, P/L: {result.total_profit_loss_pct:.2f}%")
                return jsonify(backtest_result_data)
                
            except Exception as e:
                import traceback
                error_msg = str(e)
                error_type = type(e).__name__
                error_traceback = traceback.format_exc()
                logger.error(f"Backtest çalıştırılırken hata: {error_type} - {error_msg}")
                logger.error(error_traceback)
                return jsonify({
                    'error': f'Backtest sonuçları alınamadı. Strateji çalıştırılamadı. Hata: {error_type} - {error_msg}',
                    'traceback': error_traceback
                }), 500
                
        except Exception as e:
            logger.error(f"Veri alınırken hata: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': f'Veri alınamadı: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Backtest çalıştırılırken genel hata: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Beklenmeyen hata: {str(e)}'}), 500

@app.route('/backtest')
def backtest():
    """Backtest sayfası"""
    # Testnet durumunu al
    testnet = os.environ.get('TESTNET', 'true').lower() == 'true'
    
    # Sembol listesini al
    try:
        client = get_binance_client(testnet)
        if client is None or client.client is None:
            return render_template('error.html', 
                error="API anahtarları eksik veya geçersiz. Lütfen API anahtarlarınızı kontrol edin.",
                details="Sistem çalışabilmek için geçerli Binance API anahtarlarına ihtiyaç duyar.")
            
        symbols = client.client.get_exchange_info()['symbols']
        symbols = [s['symbol'] for s in symbols if s['symbol'].endswith('USDT')]
        
        if not symbols:
            return render_template('error.html', 
                error="Sembol listesi alınamadı.",
                details="Binance API'den sembol listesi alınamadı. Lütfen API anahtarlarınızı kontrol edin.")
    except Exception as e:
        logger.error(f"Sembol listesi alınırken hata: {str(e)}")
        return render_template('error.html', 
            error="Binance API'ye erişim hatası", 
            details=str(e))
    
    # Zaman dilimleri
    intervals = [
        ("1m", "1 Dakika"),
        ("5m", "5 Dakika"),
        ("15m", "15 Dakika"),
        ("30m", "30 Dakika"),
        ("1h", "1 Saat"),
        ("4h", "4 Saat"),
        ("1d", "1 Gün"),
        ("1w", "1 Hafta")
    ]
    
    # Stratejileri al
    strategies = strategy_manager.get_strategy_names()
    
    return render_template(
        'backtest.html', 
        symbols=symbols, 
        intervals=intervals, 
        strategies=strategies,
        testnet=testnet
    )

@app.route('/advanced')
def advanced():
    """Gelişmiş analiz sayfası"""
    # Testnet durumunu al
    testnet = os.environ.get('TESTNET', 'true').lower() == 'true'
    
    # Sembol listesini al
    try:
        client = get_binance_client(testnet)
        if client is None or client.client is None:
            return render_template('error.html', 
                error="API anahtarları eksik veya geçersiz. Lütfen API anahtarlarınızı kontrol edin.",
                details="Sistem çalışabilmek için geçerli Binance API anahtarlarına ihtiyaç duyar.")
            
        symbols = client.client.get_exchange_info()['symbols']
        symbols = [s['symbol'] for s in symbols if s['symbol'].endswith('USDT')]
        
        if not symbols:
            return render_template('error.html', 
                error="Sembol listesi alınamadı.",
                details="Binance API'den sembol listesi alınamadı. Lütfen API anahtarlarınızı kontrol edin.")
    except Exception as e:
        logger.error(f"Sembol listesi alınırken hata: {str(e)}")
        return render_template('error.html', 
            error="Binance API'ye erişim hatası", 
            details=str(e))
    
    # Zaman dilimleri
    intervals = [
        ("1m", "1 Dakika"),
        ("5m", "5 Dakika"),
        ("15m", "15 Dakika"),
        ("30m", "30 Dakika"),
        ("1h", "1 Saat"),
        ("4h", "4 Saat"),
        ("1d", "1 Gün"),
        ("1w", "1 Hafta")
    ]
    
    # Stratejileri al
    strategies = strategy_manager.get_strategy_names()
    
    return render_template(
        'advanced.html', 
        symbols=symbols, 
        intervals=intervals, 
        strategies=strategies,
        testnet=testnet
    )

@app.route('/api/account', methods=['GET'])
def get_account():
    """Hesap bilgilerini al"""
    try:
        if not binance_client:
            logger.error("Binance client başlatılamadı")
            return jsonify({"error": "Binance client başlatılamadı"}), 500
            
        # Hesap bilgilerini al
        try:
            account = binance_client.get_account()
            logger.info(f"Hesap bilgileri alındı: {account.keys() if isinstance(account, dict) else 'Hesap bilgisi alınamadı'}")
            
            # Hesap bilgisi yoksa hata döndür
            if not account or not isinstance(account, dict):
                logger.error("Hesap bilgileri alınamadı")
                return jsonify({"error": "Hesap bilgileri alınamadı"}), 400
                
            # API anahtarları doğru mu kontrol et
            if 'code' in account and account['code'] < 0:
                logger.error(f"API hatası: {account.get('msg', 'Bilinmeyen hata')}")
                return jsonify({"error": f"API hatası: {account.get('msg', 'Bilinmeyen hata')}"}), 400
                
            # Bakiyeleri al
            balances = []
            if 'balances' in account:
                balances = account['balances']
            elif 'assets' in account:
                balances = account['assets']
            
            # Açık emirleri al
            open_orders = binance_client.get_open_orders()
            
            # Pozisyonları al
            positions = []
            try:
                if binance_client.futures:
                    positions = binance_client.get_positions()
            except Exception as pos_error:
                logger.error(f"Pozisyonlar alınırken hata: {str(pos_error)}")
            
            # Sonuçları döndür
            return jsonify({
                "balances": balances,
                "open_orders": open_orders,
                "positions": positions
            })
            
        except Exception as account_error:
            logger.error(f"Hesap bilgileri alınırken hata: {str(account_error)}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({"error": f"Hesap bilgileri alınırken hata: {str(account_error)}"}), 400
            
    except Exception as e:
        logger.error(f"Hesap bilgileri alınırken beklenmeyen hata: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Beklenmeyen hata: {str(e)}"}), 500

@app.route('/api/account_info', methods=['GET'])
def account_info():
    """Hesap bilgilerini al"""
    try:
        # Hem testnet hem de canlı hesap bilgilerini al
        account_data = {}
        
        # Testnet hesap bilgileri
        try:
            testnet_client = get_binance_client(testnet=True)
            if testnet_client:
                testnet_info = testnet_client.get_account()
                testnet_balances = [balance for balance in testnet_info.get('balances', []) 
                                  if float(balance.get('free', 0)) > 0 or float(balance.get('locked', 0)) > 0]
                account_data['testnet'] = {
                    'available': True,
                    'balances': testnet_balances,
                    'canTrade': True
                }
            else:
                account_data['testnet'] = {
                    'available': False,
                    'error': 'Testnet API anahtarları ayarlanmamış'
                }
        except Exception as testnet_error:
            logger.error(f"Testnet hesap bilgileri alınırken hata: {str(testnet_error)}")
            account_data['testnet'] = {
                'available': False,
                'error': str(testnet_error)
            }
        
        # Canlı hesap bilgileri
        try:
            live_client = get_binance_client(testnet=False)
            if live_client:
                live_info = live_client.get_account()
                live_balances = [balance for balance in live_info.get('balances', []) 
                               if float(balance.get('free', 0)) > 0 or float(balance.get('locked', 0)) > 0]
                account_data['live'] = {
                    'available': True,
                    'balances': live_balances,
                    'canTrade': True
                }
            else:
                account_data['live'] = {
                    'available': False,
                    'error': 'Canlı API anahtarları ayarlanmamış'
                }
        except Exception as live_error:
            logger.error(f"Canlı hesap bilgileri alınırken hata: {str(live_error)}")
            account_data['live'] = {
                'available': False,
                'error': str(live_error)
            }
        
        # Şu anki aktif mod
        account_data['current'] = os.getenv('TESTNET', 'false').lower() == 'true'
        
        return jsonify(account_data)
        
    except Exception as e:
        logger.error(f"Hesap bilgileri alınırken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/place_order', methods=['POST'])
def place_order():
    """Emir ver"""
    try:
        data = request.json
        symbol = data.get('symbol')
        side = data.get('side')
        order_type = data.get('order_type')
        quantity = float(data.get('quantity'))
        price = float(data.get('price')) if data.get('price') else None
        stop_price = float(data.get('stop_price')) if data.get('stop_price') else None
        leverage = int(data.get('leverage', 1))
        
        if not binance_client:
            return jsonify({"error": "Binance client başlatılamadı."}), 500
        
        # Emri ver
        order = binance_client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            leverage=leverage
        )
        
        return jsonify(order)
    except Exception as e:
        logger.error(f"Emir verilirken hata: {str(e)}")
        return str(e), 500

@app.route('/api/order_history', methods=['GET'])
def get_order_history():
    """Emir geçmişini al"""
    try:
        symbol = request.args.get('symbol')
        limit = int(request.args.get('limit', 50))
        
        if not binance_client:
            return jsonify({"error": "Binance client başlatılamadı."}), 500
        
        # Emir geçmişini al
        orders = binance_client.get_order_history(symbol=symbol, limit=limit)
        
        return jsonify(orders)
    except Exception as e:
        logger.error(f"Emir geçmişi alınırken hata: {str(e)}")
        return str(e), 500

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Ayarlar sayfası"""
    try:
        logger.info("Ayarlar sayfası yükleniyor...")
        
        if request.method == 'POST':
            # Ayarları kaydet
            live_api_key = request.form.get('live_api_key')
            live_api_secret = request.form.get('live_api_secret')
            test_api_key = request.form.get('test_api_key')
            test_api_secret = request.form.get('test_api_secret')
            testnet = request.form.get('testnet') == 'on'
            
            # .env dosyasına kaydet
            with open('.env', 'w') as f:
                f.write(f'BINANCE_LIVE_API_KEY={live_api_key}\n')
                f.write(f'BINANCE_LIVE_API_SECRET={live_api_secret}\n')
                f.write(f'BINANCE_TEST_API_KEY={test_api_key}\n')
                f.write(f'BINANCE_TEST_API_SECRET={test_api_secret}\n')
                f.write(f'TESTNET={"true" if testnet else "false"}\n')
            
            # Binance client'ı yeniden başlat
            try:
                global binance_client
                if testnet:
                    binance_client = get_binance_client(testnet)
                else:
                    binance_client = get_binance_client(testnet=False)
                flash('Ayarlar başarıyla kaydedildi', 'success')
            except Exception as e:
                flash(f'Binance client başlatılamadı: {str(e)}', 'error')
            
            return redirect(url_for('settings'))
        
        # Mevcut ayarları al
        live_api_key = os.getenv('BINANCE_LIVE_API_KEY', '')
        live_api_secret = os.getenv('BINANCE_LIVE_API_SECRET', '')
        test_api_key = os.getenv('BINANCE_TEST_API_KEY', '')
        test_api_secret = os.getenv('BINANCE_TEST_API_SECRET', '')
        testnet = os.getenv('TESTNET', 'false').lower() == 'true'
        
        logger.info("Ayarlar sayfası render ediliyor...")
        try:
            return render_template('settings.html',
                                live_api_key=live_api_key,
                                live_api_secret=live_api_secret,
                                test_api_key=test_api_key,
                                test_api_secret=test_api_secret,
                                testnet=testnet)
        except Exception as template_error:
            logger.error(f"Şablon render edilirken hata: {str(template_error)}")
            import traceback
            logger.error(traceback.format_exc())
            return f"Şablon hatası: {str(template_error)}", 500
    except Exception as e:
        logger.error(f"Ayarlar sayfası yüklenirken hata: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return str(e), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """API ayarlarını al veya güncelle"""
    try:
        if request.method == 'GET':
            # Ayarları .env dosyasından veya veritabanından al
            live_api_key = os.environ.get('BINANCE_LIVE_API_KEY', '')
            live_api_secret = os.environ.get('BINANCE_LIVE_API_SECRET', '')
            test_api_key = os.environ.get('BINANCE_TEST_API_KEY', '')
            test_api_secret = os.environ.get('BINANCE_TEST_API_SECRET', '')
            testnet = os.environ.get('TESTNET', 'true').lower() == 'true'
            
            return jsonify({
                'live_api_key': live_api_key,
                'live_api_secret': live_api_secret,
                'test_api_key': test_api_key,
                'test_api_secret': test_api_secret,
                'testnet': testnet
            })
        elif request.method == 'POST':
            data = request.json
            live_api_key = data.get('live_api_key', '')
            live_api_secret = data.get('live_api_secret', '')
            test_api_key = data.get('test_api_key', '')
            test_api_secret = data.get('test_api_secret', '')
            testnet = data.get('testnet', True)
            
            # Ayarları .env dosyasına kaydet
            with open('.env', 'w') as f:
                f.write(f'BINANCE_LIVE_API_KEY={live_api_key}\n')
                f.write(f'BINANCE_LIVE_API_SECRET={live_api_secret}\n')
                f.write(f'BINANCE_TEST_API_KEY={test_api_key}\n')
                f.write(f'BINANCE_TEST_API_SECRET={test_api_secret}\n')
                f.write(f'TESTNET={"true" if testnet else "false"}\n')
            
            # Çevre değişkenlerini güncelle
            os.environ['BINANCE_LIVE_API_KEY'] = live_api_key
            os.environ['BINANCE_LIVE_API_SECRET'] = live_api_secret
            os.environ['BINANCE_TEST_API_KEY'] = test_api_key
            os.environ['BINANCE_TEST_API_SECRET'] = test_api_secret
            os.environ['TESTNET'] = 'true' if testnet else 'false'
        
            # Aktif API anahtarlarını belirle
            if testnet:
                active_api_key = test_api_key
                active_api_secret = test_api_secret
            else:
                active_api_key = live_api_key
                active_api_secret = live_api_secret
            
            # Binance client'ı yeniden başlat
            global binance_client
            try:
                binance_client = get_binance_client(testnet=testnet)
                logger.info(f"Binance client başarıyla güncellendi. Testnet: {testnet}")
            except Exception as e:
                logger.error(f"Binance client güncellenirken hata: {str(e)}")
            
            return jsonify({'success': True, 'message': 'API ayarları güncellendi'})
    except Exception as e:
        logger.error(f"API ayarları işlenirken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_testnet', methods=['GET'])
def get_testnet():
    """Testnet durumunu al"""
    try:
        if not binance_client:
            return jsonify({'error': 'Binance client başlatılamadı'}), 500
            
        testnet = binance_client.testnet
        return jsonify({'testnet': testnet})
    except Exception as e:
        logger.error(f"Testnet durumu alınırken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Ayarlar API'leri
@app.route('/api/settings/favorites', methods=['POST'])
def update_favorites():
    try:
        data = request.json
        symbols = data.get('symbols', [])
        
        # Favori sembolleri kaydet
        with open('favorites.json', 'w') as f:
            json.dump(symbols, f)
        
        return jsonify({'success': True, 'message': 'Favori semboller güncellendi'})
    except Exception as e:
        logger.error(f"Favori semboller güncellenirken hata: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/risk', methods=['POST'])
def update_risk_settings():
    """Risk yönetimi ayarlarını güncelle"""
    try:
        if risk_manager is None:
            logger.error("Risk Manager başlatılamadı")
            return jsonify({'error': 'Risk Manager başlatılamadı'}), 500
            
        data = request.get_json()
        success = risk_manager.update_settings(data)
        
        if success:
            return jsonify({'success': True, 'message': 'Risk ayarları başarıyla güncellendi'})
        else:
            return jsonify({'success': False, 'message': 'Risk ayarları güncellenirken hata oluştu'}), 400
    except Exception as e:
        logger.error(f"Risk ayarları güncellenirken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/notifications', methods=['POST'])
def update_notification_settings():
    try:
        data = request.json
        telegram_token = data.get('telegram_token', '')
        telegram_chat_id = data.get('telegram_chat_id', '')
        notify_trades = data.get('notify_trades', False)
        notify_signals = data.get('notify_signals', False)
        
        # Bildirim ayarlarını kaydet
        with open('notification_settings.json', 'w') as f:
            json.dump({
                'telegram_token': telegram_token,
                'telegram_chat_id': telegram_chat_id,
                'notify_trades': notify_trades,
                'notify_signals': notify_signals
            }, f)
        
        return jsonify({'success': True, 'message': 'Bildirim ayarları güncellendi'})
    except Exception as e:
        logger.error(f"Bildirim ayarları güncellenirken hata: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    """Mevcut stratejileri listele"""
    try:
        # Strateji yöneticisinden stratejileri al
        strategies = list(strategy_manager.get_strategy_names())
        
        # Stratejileri alfabetik olarak sırala
        strategies.sort()
        
        logger.info(f"Mevcut stratejiler: {strategies}")
        return jsonify({'strategies': strategies})
    except Exception as e:
        logger.error(f"Stratejiler listelenirken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced_analyze', methods=['POST'])
def advanced_analyze():
    """Gelişmiş strateji analizi yap"""
    try:
        # Form verilerini al
        data = request.get_json()
        if not data:
            logger.error("Gelişmiş analiz için veri alınamadı")
            return jsonify({'error': 'Veri alınamadı'}), 400
            
        symbol = data.get('symbol', '')
        logger.info(f"Gelişmiş analiz yapılıyor: symbol={symbol}")
        
        # Zaman dilimleri
        timeframes = data.get('timeframes', ['1h'])
        logger.info(f"Seçilen zaman dilimleri: {timeframes}")
        
        # Tüm zaman dilimleri için veri al
        dataframes = {}
        for interval in timeframes:
            logger.info(f"{interval} için veri alınıyor...")
            try:
                df = get_binance_client(testnet=False).get_historical_klines(symbol, interval, limit=100)
                if df.empty:
                    logger.error(f"{interval} için veri alınamadı")
                    return jsonify({'error': f'{interval} için veri alınamadı'}), 400
                dataframes[interval] = df.copy()
                logger.info(f"{interval} için {len(df)} adet veri alındı")
            except Exception as interval_error:
                logger.error(f"{interval} için veri alınırken hata: {str(interval_error)}")
                return jsonify({'error': f'{interval} için veri alınırken hata: {str(interval_error)}'}), 400
        
        # Strateji adını al
        strategy_name = data.get('strategy', 'Advanced')
        logger.info(f"Seçilen strateji: {strategy_name}")
        
        # Strateji nesnesini al
        strategy = strategy_manager.get_strategy(strategy_name)
        
        if not strategy:
            logger.error(f"{strategy_name} stratejisi bulunamadı")
            return jsonify({'error': f'{strategy_name} stratejisi bulunamadı'}), 400
        
        logger.info(f"Strateji analizi başlatılıyor: {strategy_name}")
        
        # Çoklu zaman dilimi analizi
        if strategy_name == "Multi_Timeframe" and hasattr(strategy, 'analyze_multi_timeframe'):
            logger.info("Çoklu zaman dilimi analizi yapılıyor...")
            try:
                signal, confidence, metrics = strategy.analyze_multi_timeframe(dataframes)
                logger.info(f"Çoklu zaman dilimi analizi tamamlandı: {signal}, {confidence}")
            except Exception as multi_error:
                logger.error(f"Çoklu zaman dilimi analizi sırasında hata: {str(multi_error)}")
                import traceback
                logger.error(traceback.format_exc())
                return jsonify({'error': f'Çoklu zaman dilimi analizi hatası: {str(multi_error)}'}), 500
        else:
            # Tek zaman dilimi analizi (varsayılan olarak ilk zaman dilimini kullan)
            logger.info(f"Tek zaman dilimi analizi yapılıyor: {timeframes[0]}")
            try:
                primary_timeframe = timeframes[0]
                signal, confidence, metrics = strategy.analyze(dataframes[primary_timeframe])
                logger.info(f"Tek zaman dilimi analizi tamamlandı: {signal}, {confidence}")
            except Exception as single_error:
                logger.error(f"Tek zaman dilimi analizi sırasında hata: {str(single_error)}")
                import traceback
                logger.error(traceback.format_exc())
                return jsonify({'error': f'Tek zaman dilimi analizi hatası: {str(single_error)}'}), 500
        
        # JSON serileştirme hatalarını önlemek için metrikleri düzelt
        cleaned_metrics = {}
        for key, value in metrics.items():
            # Bool değerleri string'e çevir
            if isinstance(value, bool):
                cleaned_metrics[key] = str(value)
            # NumPy değerlerini Python değerlerine çevir
            elif isinstance(value, (np.int64, np.int32, np.float64, np.float32)):
                cleaned_metrics[key] = value.item()
            # Diğer değerleri olduğu gibi kullan
            else:
                cleaned_metrics[key] = value
        
        # Sonuçları döndür
        result = {
            'strategy': strategy_name,
            'symbol': symbol,
            'timeframes': timeframes,
            'signal': signal,
            'confidence': float(confidence) if isinstance(confidence, (np.int64, np.int32, np.float64, np.float32)) else confidence,
            'metrics': cleaned_metrics
        }
        
        logger.info(f"Gelişmiş analiz tamamlandı: {signal}, {confidence}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Gelişmiş analiz hatası: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk/settings', methods=['GET'])
def get_risk_settings():
    """Risk yönetimi ayarlarını al"""
    try:
        if risk_manager is None:
            logger.error("Risk Manager başlatılamadı")
            return jsonify({'error': 'Risk Manager başlatılamadı'}), 500
            
        settings = risk_manager.get_settings()
        if settings:
            return jsonify(settings)
        else:
            return jsonify(risk_manager.default_settings)
    except Exception as e:
        logger.error(f"Risk ayarları alınırken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk/calculate_position_size', methods=['POST'])
def calculate_position_size():
    """Pozisyon büyüklüğünü hesapla"""
    try:
        if risk_manager is None:
            logger.error("Risk Manager başlatılamadı")
            return jsonify({'error': 'Risk Manager başlatılamadı'}), 500
            
        data = request.get_json()
        account_balance = float(data.get('account_balance', 0))
        current_price = float(data.get('current_price', 0))
        symbol = data.get('symbol', 'BTCUSDT')
        
        if account_balance <= 0 or current_price <= 0:
            return jsonify({'error': 'Geçersiz bakiye veya fiyat değeri'}), 400
            
        position_size = risk_manager.calculate_position_size(account_balance, current_price, symbol)
        
        return jsonify({
            'position_size': position_size,
            'position_size_coins': position_size / current_price if current_price > 0 else 0
        })
    except Exception as e:
        logger.error(f"Pozisyon büyüklüğü hesaplanırken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk/calculate_stop_loss', methods=['POST'])
def calculate_stop_loss():
    """Stop loss fiyatını hesapla"""
    try:
        if risk_manager is None:
            logger.error("Risk Manager başlatılamadı")
            return jsonify({'error': 'Risk Manager başlatılamadı'}), 500
            
        data = request.get_json()
        entry_price = float(data.get('entry_price', 0))
        position_type = data.get('position_type', 'LONG')
        
        if entry_price <= 0:
            return jsonify({'error': 'Geçersiz giriş fiyatı'}), 400
            
        stop_loss = risk_manager.calculate_stop_loss(entry_price, position_type)
        
        return jsonify({'stop_loss': stop_loss})
    except Exception as e:
        logger.error(f"Stop loss hesaplanırken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk/calculate_take_profit', methods=['POST'])
def calculate_take_profit():
    """Take profit fiyatını hesapla"""
    try:
        if risk_manager is None:
            logger.error("Risk Manager başlatılamadı")
            return jsonify({'error': 'Risk Manager başlatılamadı'}), 500
            
        data = request.get_json()
        entry_price = float(data.get('entry_price', 0))
        position_type = data.get('position_type', 'LONG')
        
        if entry_price <= 0:
            return jsonify({'error': 'Geçersiz giriş fiyatı'}), 400
            
        take_profit = risk_manager.calculate_take_profit(entry_price, position_type)
        
        return jsonify({'take_profit': take_profit})
    except Exception as e:
        logger.error(f"Take profit hesaplanırken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test_connection', methods=['GET'])
def test_api_connection():
    """API bağlantısını test et"""
    try:
        logger.info("API bağlantısı testi başlatıldı")
        
        # Mevcut testnet durumunu al
        current_testnet = os.environ.get('TESTNET', 'true').lower() == 'true'
        
        # Sonuçları saklamak için sözlük
        results = {
            'current': current_testnet,
            'live': {'success': False, 'message': 'Test edilmedi'},
            'test': {'success': False, 'message': 'Test edilmedi'}
        }
        
        # Live API anahtarlarını test et
        live_api_key = os.environ.get('BINANCE_LIVE_API_KEY', '')
        live_api_secret = os.environ.get('BINANCE_LIVE_API_SECRET', '')
        
        if live_api_key and live_api_secret:
            try:
                # Live client oluştur
                live_client = get_binance_client(testnet=False)
                
                # API anahtarlarını doğrula
                if live_client and live_client.validate_api_keys():
                    logger.info("Live API anahtarları doğrulandı")
                    results['live'] = {'success': True, 'message': 'API anahtarları doğrulandı'}
                else:
                    logger.warning("Live API anahtarları doğrulanamadı")
                    results['live'] = {'success': False, 'message': 'API anahtarları doğrulanamadı'}
            except Exception as e:
                logger.error(f"Live API testi sırasında hata: {str(e)}")
                results['live'] = {'success': False, 'message': f'Hata: {str(e)}'}
        else:
            logger.warning("Live API anahtarları girilmemiş")
            results['live'] = {'success': False, 'message': 'API anahtarları girilmemiş'}
        
        # Testnet API anahtarlarını test et
        test_api_key = os.environ.get('BINANCE_TEST_API_KEY', '')
        test_api_secret = os.environ.get('BINANCE_TEST_API_SECRET', '')
        
        if test_api_key and test_api_secret:
            try:
                # Testnet client oluştur
                test_client = get_binance_client(testnet=True)
                
                # API anahtarlarını doğrula
                if test_client:
                    # Testnet için ping testi yeterli
                    try:
                        test_client.client.ping()
                        logger.info("Testnet API anahtarları doğrulandı")
                        results['test'] = {'success': True, 'message': 'API anahtarları doğrulandı'}
                    except Exception as ping_error:
                        logger.warning(f"Testnet API ping testi başarısız: {str(ping_error)}")
                        results['test'] = {'success': False, 'message': f'Ping testi başarısız: {str(ping_error)}'}
                else:
                    logger.warning("Testnet API anahtarları doğrulanamadı")
                    results['test'] = {'success': False, 'message': 'API anahtarları doğrulanamadı'}
            except Exception as e:
                logger.error(f"Testnet API testi sırasında hata: {str(e)}")
                results['test'] = {'success': False, 'message': f'Hata: {str(e)}'}
        else:
            logger.warning("Testnet API anahtarları girilmemiş")
            results['test'] = {'success': False, 'message': 'API anahtarları girilmemiş'}
        
        # Aktif modu belirle
        active = 'live'
        if testnet:
            active = 'testnet'
        if not live_api_key or not live_api_secret:
            active = 'none'
        
        logger.info(f"API bağlantısı testi tamamlandı: {results}")
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"API bağlantısı test edilirken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Botu başlat"""
    try:
        data = request.json
        symbol = data.get('symbol', 'BTCUSDT')
        interval = data.get('interval', '1h')
        strategy_name = data.get('strategy', 'MACD_EMA')
        
        # Bot zaten çalışıyorsa durdur
        if bot_status['running']:
            stop_bot()
        
        # Bot ayarlarını güncelle
        bot_status['symbol'] = symbol
        bot_status['interval'] = interval
        bot_status['strategy'] = strategy_name
        bot_status['stop_event'].clear()
        
        # Bot thread'ini başlat
        bot_status['thread'] = threading.Thread(target=bot_loop)
        bot_status['thread'].daemon = True
        bot_status['thread'].start()
        
        bot_status['running'] = True
        
        return jsonify({
            "success": True,
            "message": f"Bot başlatıldı: {symbol} {interval} {strategy_name}"
        })
    except Exception as e:
        logger.error(f"Bot başlatılırken hata: {str(e)}")
        return str(e), 500

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Botu durdur"""
    try:
        if bot_status['running']:
            # Thread'i durdur
            bot_status['stop_event'].set()
            
            # Thread'in sonlanmasını bekle (en fazla 5 saniye)
            if bot_status['thread']:
                bot_status['thread'].join(timeout=5)
            
            bot_status['running'] = False
            bot_status['thread'] = None
            
            return jsonify({
                "success": True,
                "message": "Bot durduruldu"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Bot zaten çalışmıyor"
            })
    except Exception as e:
        logger.error(f"Bot durdurulurken hata: {str(e)}")
        return str(e), 500

@app.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    """Bot durumunu al"""
    try:
        status_data = {
            "running": bot_status['running'],
            "symbol": bot_status['symbol'],
            "interval": bot_status['interval'],
            "strategy": bot_status['strategy'],
            "last_check": bot_status['last_check'].isoformat() if bot_status['last_check'] else None,
            "last_signal": bot_status['last_signal'],
        }
        
        return jsonify(status_data)
    except Exception as e:
        logger.error(f"Bot durumu alınırken hata: {str(e)}")
        return str(e), 500

@app.route('/api/settings/api', methods=['POST'])
def update_api_settings():
    """API ayarlarını güncelle"""
    try:
        data = request.json
        
        # API anahtarlarını al
        live_api_key = data.get('live_api_key', '')
        live_api_secret = data.get('live_api_secret', '')
        test_api_key = data.get('test_api_key', '')
        test_api_secret = data.get('test_api_secret', '')
        testnet = data.get('testnet', False)
        
        # .env dosyasını güncelle
        with open('.env', 'w') as f:
            f.write(f"BINANCE_LIVE_API_KEY={live_api_key}\n")
            f.write(f"BINANCE_LIVE_API_SECRET={live_api_secret}\n")
            f.write(f"BINANCE_TEST_API_KEY={test_api_key}\n")
            f.write(f"BINANCE_TEST_API_SECRET={test_api_secret}\n")
            f.write(f"TESTNET={'true' if testnet else 'false'}\n")
        
        # Çevre değişkenlerini güncelle
        os.environ['BINANCE_LIVE_API_KEY'] = live_api_key
        os.environ['BINANCE_LIVE_API_SECRET'] = live_api_secret
        os.environ['BINANCE_TEST_API_KEY'] = test_api_key
        os.environ['BINANCE_TEST_API_SECRET'] = test_api_secret
        os.environ['TESTNET'] = 'true' if testnet else 'false'
        
        # Aktif API anahtarlarını belirle
        if testnet:
            active_api_key = test_api_key
            active_api_secret = test_api_secret
        else:
            active_api_key = live_api_key
            active_api_secret = live_api_secret
            
        # Binance client'ı yeniden başlat
        global binance_client
        try:
            binance_client = get_binance_client(testnet=testnet)
            logger.info(f"Binance client başarıyla güncellendi. Testnet: {testnet}")
        except Exception as e:
            logger.error(f"Binance client güncellenirken hata: {str(e)}")
        
        return jsonify({'success': True, 'message': 'API ayarları güncellendi'})
    except Exception as e:
        logger.error(f"API ayarları işlenirken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/strategy_config')
def strategy_config_page():
    """
    Strategy configuration page.
    """
    try:
        # Get the list of available strategies
        strategies = strategy_manager.get_strategy_names()
        app.logger.info(f"Available strategies: {strategies}")
        
        # Get the parameters for each strategy
        strategy_params = {}
        for strategy in strategies:
            try:
                params = strategy_manager.get_strategy_parameters(strategy)
                app.logger.info(f"Parameters for {strategy}: {params}")
                strategy_params[strategy] = params
            except Exception as e:
                app.logger.error(f"Error getting parameters for strategy {strategy}: {e}")
        
        # Get testnet status
        testnet = os.environ.get('TESTNET', 'false').lower() == 'true'
        
        # Render the template with the strategy parameters
        return render_template('strategy_config_en.html', strategies=strategies, strategy_params=strategy_params, testnet=testnet)
    except Exception as e:
        app.logger.error(f"Error loading strategy configuration page: {e}")
        return render_template('error.html', error=str(e))

@app.route('/api/strategy/parameters', methods=['GET', 'POST'])
def strategy_parameters():
    """
    API endpoint for getting and setting strategy parameters.
    """
    try:
        if request.method == 'GET':
            # Get parameters for a specific strategy
            strategy = request.args.get('strategy')
            if not strategy:
                return jsonify({'error': 'Strategy name is required'}), 400
            
            app.logger.info(f"Getting parameters for strategy: {strategy}")
            
            # Get parameters from strategy manager
            try:
                params = strategy_manager.get_strategy_parameters(strategy)
                if params:
                    return jsonify(params)
                else:
                    return jsonify({'error': f'No parameters found for strategy: {strategy}'}), 404
            except Exception as e:
                app.logger.error(f"Error getting parameters for strategy {strategy}: {e}")
                return jsonify({'error': f'Error getting parameters: {str(e)}'}), 500
        
        elif request.method == 'POST':
            # Save parameters for a specific strategy
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            strategy = data.get('strategy')
            parameters = data.get('parameters')
            
            if not strategy:
                return jsonify({'error': 'Strategy name is required'}), 400
            
            if not parameters:
                return jsonify({'error': 'Parameters are required'}), 400
            
            app.logger.info(f"Saving parameters for strategy: {strategy}")
            app.logger.debug(f"Parameters: {parameters}")
            
            # Save parameters to strategy manager
            try:
                success = strategy_manager.save_strategy_parameters(strategy, parameters)
                if success:
                    return jsonify({'success': True, 'message': 'Parameters saved successfully'})
                else:
                    return jsonify({'error': 'Failed to save parameters'}), 500
            except Exception as e:
                app.logger.error(f"Error saving parameters for strategy {strategy}: {e}")
                return jsonify({'error': f'Error saving parameters: {str(e)}'}), 500
    
    except Exception as e:
        app.logger.error(f"Error in strategy parameters API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy/reset', methods=['POST'])
def reset_strategy_parameters():
    """
    API endpoint for resetting strategy parameters to default values.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        strategy = data.get('strategy')
        if not strategy:
            return jsonify({'error': 'Strategy name is required'}), 400
        
        app.logger.info(f"Resetting parameters for strategy: {strategy}")
        
        # Reset parameters to default values
        try:
            success = strategy_manager.reset_strategy_parameters(strategy)
            if success:
                return jsonify({'success': True, 'message': 'Parameters reset to default values'})
            else:
                return jsonify({'error': 'Failed to reset parameters'}), 500
        except Exception as e:
            app.logger.error(f"Error resetting parameters for strategy {strategy}: {e}")
            return jsonify({'error': f'Error resetting parameters: {str(e)}'}), 500
    
    except Exception as e:
        app.logger.error(f"Error in reset strategy parameters API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy/signals', methods=['POST'])
def get_strategy_signals():
    """Strateji sinyallerini al"""
    try:
        # Gelen veriyi al
        data = request.get_json()
        if not data:
            logger.error("Strateji sinyalleri için veri alınamadı")
            return jsonify({'error': 'Veri alınamadı'}), 400
            
        # Parametreleri al
        symbol = data.get('symbol', '')
        interval = data.get('interval', '1h')
        strategy_name = data.get('strategy', '')
        limit = int(data.get('limit', 100))
        
        # Parametreleri kontrol et
        if not symbol:
            logger.error("Sembol belirtilmedi")
            return jsonify({'error': 'Sembol belirtilmedi'}), 400
            
        if not strategy_name:
            logger.error("Strateji belirtilmedi")
            return jsonify({'error': 'Strateji belirtilmedi'}), 400
            
        # Testnet durumunu al
        testnet = os.environ.get('TESTNET', 'true').lower() == 'true'
        
        # Binance client oluştur
        client = get_binance_client(testnet)
        if client is None or client.client is None:
            logger.error("Binance client oluşturulamadı")
            return jsonify({'error': 'Binance API bağlantısı kurulamadı. API anahtarlarınızı kontrol edin.'}), 500
            
        # Veri al
        try:
            klines = client.client.get_klines(symbol=symbol, interval=interval, limit=limit)
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
        except Exception as e:
            logger.error(f"Veri alınırken hata: {str(e)}")
            return jsonify({'error': f'Veri alınamadı: {str(e)}'}), 500
            
        # Strateji oluştur
        try:
            strategy_class = strategy_manager.get_strategy(strategy_name)
            if strategy_class is None:
                logger.error(f"Strateji bulunamadı: {strategy_name}")
                return jsonify({'error': f'Strateji bulunamadı: {strategy_name}'}), 404
                
            strategy = strategy_class()
        except Exception as e:
            logger.error(f"Strateji oluşturulurken hata: {str(e)}")
            return jsonify({'error': f'Strateji oluşturulamadı: {str(e)}'}), 500
            
        # Sinyalleri oluştur
        try:
            signals = strategy.generate_signals(df)
        except Exception as e:
            logger.error(f"Sinyaller oluşturulurken hata: {str(e)}")
            return jsonify({'error': f'Sinyaller oluşturulamadı: {str(e)}'}), 500
            
        # Sonuçları hazırla
        result = []
        for i, row in signals.iterrows():
            result.append({
                'date': row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume'],
                'signal': row.get('signal', 0),
                'position': row.get('position', 0)
            })
            
        return jsonify({'data': result}), 200
        
    except Exception as e:
        logger.error(f"Strateji sinyalleri alınırken hata: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/check_keys', methods=['GET'])
def check_api_keys():
    """API anahtarlarını kontrol et"""
    try:
        # Testnet durumunu al
        testnet = os.environ.get('TESTNET', 'true').lower() == 'true'
        
        # Live API anahtarlarını al
        live_api_key = os.environ.get('BINANCE_LIVE_API_KEY', '')
        live_api_secret = os.environ.get('BINANCE_LIVE_API_SECRET', '')
        
        # Testnet API anahtarlarını al
        test_api_key = os.environ.get('BINANCE_TEST_API_KEY', '')
        test_api_secret = os.environ.get('BINANCE_TEST_API_SECRET', '')
        
        # Live API anahtarları boşsa, hata döndür
        if not live_api_key or not live_api_secret:
            logger.warning("Live API anahtarları boş veya eksik")
            live_status = False
            live_message = 'API anahtarları eksik'
        else:
            # Live API anahtarlarını kontrol et
            try:
                logger.info("Live API anahtarları kontrol ediliyor...")
                live_client = BinanceClient(api_key=live_api_key, api_secret=live_api_secret, testnet=False)
                live_status = live_client.validate_api_keys()
                if live_status:
                    live_message = 'API anahtarları doğrulandı'
                    logger.info("Live API anahtarları başarıyla doğrulandı")
                else:
                    logger.warning("Live API anahtarları doğrulanamadı")
                    live_message = 'API anahtarları doğrulanamadı'
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Live API anahtarları kontrol edilirken hata: {error_msg}")
                live_status = False
                live_message = f'Hata: {error_msg}'
        
        # Testnet API anahtarları boşsa, hata döndür
        if not test_api_key or not test_api_secret:
            logger.warning("Testnet API anahtarları boş veya eksik")
            test_status = False
            test_message = 'API anahtarları eksik'
        else:
            # Testnet API anahtarlarını kontrol et
            try:
                logger.info("Testnet API anahtarları kontrol ediliyor...")
                test_client = BinanceClient(api_key=test_api_key, api_secret=test_api_secret, testnet=True)
                test_status = test_client.validate_api_keys()
                if test_status:
                    test_message = 'API anahtarları doğrulandı'
                    logger.info("Testnet API anahtarları başarıyla doğrulandı")
                else:
                    logger.warning("Testnet API anahtarları doğrulanamadı")
                    test_message = 'API anahtarları doğrulanamadı'
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Testnet API anahtarları kontrol edilirken hata: {error_msg}")
                test_status = False
                test_message = f'Hata: {error_msg}'
        
        # Aktif modu belirle
        active = 'live'
        if testnet:
            active = 'testnet'
        
        if not live_status and not test_status:
            active = 'none'
        
        logger.info(f"API anahtarları kontrol sonucu - Live: {live_status}, Testnet: {test_status}, Aktif: {active}")
        
        return jsonify({
            'live': {
                'status': live_status,
                'message': live_message
            },
            'testnet': {
                'status': test_status,
                'message': test_message
            },
            'active': active
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"API anahtarları kontrol edilirken beklenmeyen hata: {error_msg}")
        return jsonify({'error': error_msg}), 500

@app.route('/settings')
def settings_page():
    """Ayarlar sayfası"""
    # Testnet durumunu al
    testnet = os.environ.get('TESTNET', 'true').lower() == 'true'
    
    # API anahtarlarını al
    live_api_key = os.environ.get('BINANCE_LIVE_API_KEY', '')
    live_api_secret = os.environ.get('BINANCE_LIVE_API_SECRET', '')
    
    # Testnet API anahtarlarını al (eğer ayrı olarak tanımlanmışsa)
    test_api_key = os.environ.get('BINANCE_TEST_API_KEY', live_api_key)
    test_api_secret = os.environ.get('BINANCE_TEST_API_SECRET', live_api_secret)
    
    # API anahtarlarını maskele (güvenlik için)
    masked_live_api_key = mask_api_key(live_api_key)
    masked_live_api_secret = mask_api_key(live_api_secret)
    masked_test_api_key = mask_api_key(test_api_key)
    masked_test_api_secret = mask_api_key(test_api_secret)
    
    return render_template(
        'settings.html',
        testnet=testnet,
        live_api_key=masked_live_api_key,
        live_api_secret=masked_live_api_secret,
        test_api_key=masked_test_api_key,
        test_api_secret=masked_test_api_secret
    )

def mask_api_key(key):
    """API anahtarını maskele"""
    if not key or len(key) < 8:
        return ''
    
    # İlk 4 ve son 4 karakteri göster, arasını maskele
    return key[:4] + '*' * (len(key) - 8) + key[-4:]

def bot_loop():
    """Bot döngüsü - sürekli olarak sinyalleri kontrol eder ve işlem yapar"""
    logger.info(f"Bot başlatıldı: {bot_status['symbol']} {bot_status['interval']} {bot_status['strategy']}")
    
    while not bot_status['stop_event'].is_set():
        try:
            # Verileri al
            df = binance_client.get_historical_klines(bot_status['symbol'], bot_status['interval'], limit=100)
            
            # Strateji analizi yap
            strategy = strategy_manager.get_strategy(bot_status['strategy'])
            signal, confidence, metrics = strategy.analyze(df)
            
            # Sonuçları kaydet
            bot_status['last_check'] = datetime.now()
            bot_status['last_signal'] = {
                'signal': signal,
                'confidence': confidence,
                'metrics': metrics
            }
            
            logger.info(f"Bot sinyal: {signal} ({confidence:.2f}%) - {bot_status['symbol']} {bot_status['interval']}")
            
            # Sinyal varsa ve güven skoru yüksekse işlem yap
            if signal in ['BUY', 'SELL'] and confidence > 75:
                # Hesap bilgilerini al
                account = binance_client.get_account()
                
                # İşlem büyüklüğünü hesapla (hesap bakiyesinin %5'i)
                balance = float(account.get('totalWalletBalance', 0))
                position_size = balance * 0.05
                
                # Emir ver
                side = "BUY" if signal == "BUY" else "SELL"
                
                # Gerçek emir vermek için aşağıdaki satırı aktif edin
                # binance_client.place_order(bot_status['symbol'], side, position_size)
                
                logger.info(f"Bot işlem sinyali: {side} {position_size} {bot_status['symbol']}")
            
            # Her kontrolden sonra bekle (interval'e göre ayarlanabilir)
            time.sleep(60)  # 1 dakika bekle
            
        except Exception as e:
            logger.error(f"Bot döngüsünde hata: {str(e)}")
            time.sleep(30)  # Hata durumunda 30 saniye bekle

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Tüm stratejileri çalıştır ve sinyallerini döndür"""
    try:
        # İstek verilerini al
        data = request.json
        if not data:
            logger.error("Analiz için veri gönderilmedi")
            return jsonify({'error': 'Veri gönderilmedi'}), 400
        
        symbol = data.get('symbol')
        interval = data.get('interval')
        
        if not symbol or not interval:
            logger.error(f"Geçersiz sembol veya interval: {symbol}, {interval}")
            return jsonify({'error': 'Sembol ve interval gerekli'}), 400
        
        logger.info(f"Analiz istendi: {symbol} {interval}")
        
        # Piyasa verilerini al
        try:
            market_data = get_binance_client(testnet=False).get_historical_klines(
                symbol=symbol,
                interval=interval,
                limit=200
            )
            
            if market_data.empty:
                logger.error(f"Yetersiz piyasa verisi: {len(market_data)} satır")
                return jsonify({'error': 'Yetersiz piyasa verisi'}), 400
                
            logger.info(f"Piyasa verisi alındı: {len(market_data)} satır")
            
            # DataFrame'e dönüştür
            df = pd.DataFrame(market_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Sayısal sütunları dönüştür
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)
            
            # Tüm stratejileri çalıştır ve sinyallerini al
            signals = {}
            strategies = strategy_manager.get_strategies()
            
            for strategy_name in strategies:
                try:
                    strategy_instance = strategy_manager.create_strategy_instance(strategy_name, df)
                    if strategy_instance:
                        signal = strategy_instance.generate_signal()
                        signals[strategy_name] = {
                            'signal': signal,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                    else:
                        logger.warning(f"Strateji örneği oluşturulamadı: {strategy_name}")
                        signals[strategy_name] = {
                            'signal': 'ERROR',
                            'error': 'Strateji örneği oluşturulamadı',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                except Exception as e:
                    logger.error(f"Strateji çalıştırılırken hata: {strategy_name} - {str(e)}")
                    signals[strategy_name] = {
                        'signal': 'ERROR',
                        'error': str(e),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
            
            logger.info(f"Analiz tamamlandı: {len(signals)} strateji")
            return jsonify(signals)
            
        except Exception as e:
            logger.error(f"Piyasa verisi alınırken hata: {str(e)}")
            return jsonify({'error': f'Piyasa verisi alınırken hata: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Analiz sırasında hata: {str(e)}")
        return jsonify({'error': f'Analiz sırasında hata: {str(e)}'}), 500

if __name__ == '__main__':
    try:
        # Türkçe karakter sorunlarını çözmek için
        import sys
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
        
        # Uygulama başlatma
        logger.info("Uygulama baslatiliyor...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Uygulama baslatilirken hata: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"Uygulama baslatilirken hata: {str(e)}")
        print("Detaylı hata bilgisi için log dosyasını kontrol edin.")

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import time
from typing import Dict, List, Tuple, Any, Optional
from strategy_manager import StrategyManager

class Trade:
    """
    Ticaret işlemlerini temsil eden sınıf
    """
    def __init__(self, entry_time, entry_price, position_size, position, 
                 exit_time=None, exit_price=None, profit_loss=0, 
                 profit_loss_pct=0, status="CLOSED"):
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.position_size = position_size
        self.position = position  # LONG veya SHORT
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.profit_loss = profit_loss
        self.profit_loss_pct = profit_loss_pct
        self.status = status  # OPEN veya CLOSED

class BacktestResult:
    """
    Backtest sonuçlarını saklamak için sınıf
    """
    def __init__(self, symbol=None, interval=None, strategy=None):
        self.symbol = symbol
        self.interval = interval
        self.strategy = strategy
        self.initial_balance = 0
        self.final_balance = 0
        self.total_profit_loss = 0
        self.total_profit_loss_pct = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.win_rate = 0
        self.total_trades = 0
        self.max_drawdown = 0
        self.max_drawdown_pct = 0
        self.equity_curve = []
        self.balance_history = []
        self.trades = []
        self.take_profit_pct = None
        self.stop_loss_pct = None
        self.trailing_stop_pct = None
        self.trailing_profit_pct = None
        self.risk_per_trade_pct = None
        self.signal_stats = {}

class Backtester:
    """
    Geliştirilmiş backtest sistemi
    """
    def __init__(self, strategy_manager=None):
        """
        Backtester sınıfını başlat
        
        Args:
            strategy_manager: Strateji yöneticisi
        """
        self.logger = logging.getLogger(__name__)
        self.strategy_manager = strategy_manager
        
    def run(self, df: pd.DataFrame, strategy, symbol: str, interval: str, 
            initial_balance: float = 1000.0, take_profit_pct: Optional[float] = None, 
            stop_loss_pct: Optional[float] = None, trailing_stop_pct: Optional[float] = None, 
            trailing_profit_pct: Optional[float] = None, risk_per_trade_pct: float = 1.0) -> BacktestResult:
        """
        Backtest çalıştır.
        
        Args:
            df (pd.DataFrame): Backtest edilecek veri (OHLCV)
            strategy: Strateji nesnesi veya sınıfı
            symbol (str): Sembol (örn. BTCUSDT)
            interval (str): Zaman aralığı (örn. 1h, 4h, 1d)
            initial_balance (float): Başlangıç bakiyesi
            take_profit_pct (float, optional): Kar alma yüzdesi
            stop_loss_pct (float, optional): Zarar durdurma yüzdesi
            trailing_stop_pct (float, optional): Takip eden zarar durdurma yüzdesi
            trailing_profit_pct (float, optional): Takip eden kar alma yüzdesi  
            risk_per_trade_pct (float): Her işlemde risk alınacak yüzde
            
        Returns:
            BacktestResult: Backtest sonuçları
        """
        # Başlangıç değerleri
        self.logger.info(f"Backtest başlatılıyor: {symbol} {interval}")
        self.logger.info(f"Başlangıç bakiyesi: {initial_balance}")
        
        # Strateji nesnesini oluştur (eğer bir sınıf ise)
        strategy_obj = None
        if isinstance(strategy, type):  # Eğer bir sınıf ise
            self.logger.info(f"Strateji bir sınıf: {strategy.__name__}")
            try:
                # Sınıfın init metodunu incele ve gerekli parametreleri sağla
                import inspect
                sig = inspect.signature(strategy.__init__)
                self.logger.info(f"Strateji init parametreleri: {sig.parameters}")
                
                # Farklı stratejilerin ihtiyaçlarına göre parametreler hazırla
                init_params = {}
                
                # name parametresi bekleniyor mu?
                if 'name' in sig.parameters:
                    if strategy.__name__ == 'AdvancedStrategy':
                        init_params['name'] = 'Advanced'
                    else:
                        init_params['name'] = strategy.__name__
                        
                self.logger.info(f"Strateji init parametreleri hazırlandı: {init_params}")
                
                # Strateji nesnesini oluştur
                strategy_obj = strategy(**init_params)
                self.logger.info(f"Strateji nesnesi oluşturuldu: {strategy_obj}")
            except Exception as e:
                self.logger.error(f"Strateji nesnesi oluşturulurken hata: {str(e)}")
                result = BacktestResult(symbol, interval, strategy.__name__)
                result.initial_balance = initial_balance
                return result
        else:  # Eğer zaten bir nesne ise
            self.logger.info(f"Strateji zaten bir nesne: {strategy}")
            strategy_obj = strategy
            
        # Strateji adını al
        if hasattr(strategy_obj, 'name') and isinstance(strategy_obj.name, str):
            strategy_name = strategy_obj.name
        else:
            strategy_name = strategy_obj.__class__.__name__
        
        # Sonuç nesnesi
        result = BacktestResult(symbol, interval, strategy_name)
        result.initial_balance = initial_balance
        
        # Veri kontrolü
        if df is None or df.empty:
            self.logger.error("Veri yok veya boş")
            return result
            
        # Sütun kontrolü
        required_columns = ['open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.logger.error(f"Eksik sütunlar: {missing_columns}")
            return result
            
        # Strateji kontrolü
        if strategy_obj is None:
            self.logger.error("Strateji nesnesi yok")
            return result
            
        # Strateji sinyallerini hesapla
        try:
            self.logger.info(f"Strateji sinyalleri hesaplanıyor: {strategy_name}")
            
            if not hasattr(strategy_obj, 'generate_signals'):
                self.logger.error("Strateji 'generate_signals' metoduna sahip değil")
                return result
                
            # Stratejiden sinyalleri al
            signals_df = strategy_obj.generate_signals(df)
            
            if signals_df is None or signals_df.empty:
                self.logger.error("Sinyal üretilemedi veya boş DataFrame döndü")
                return result
                
            if 'signal' not in signals_df.columns:
                self.logger.error("'signal' sütunu bulunamadı")
                self.logger.info(f"Mevcut sütunlar: {signals_df.columns.tolist()}")
                return result
                
            # Sinyal dağılımı
            signal_counts = signals_df['signal'].value_counts().to_dict()
            self.logger.info(f"Sinyal dağılımı: {signal_counts}")
            
            # Sinyal istatistiklerini ekle
            result.signal_stats = {}
            for signal_val, count in signal_counts.items():
                if isinstance(signal_val, (int, float)):
                    if signal_val == 1 or signal_val == 'BUY':
                        result.signal_stats['BUY'] = count
                    elif signal_val == -1 or signal_val == 'SELL':
                        result.signal_stats['SELL'] = count
                    elif signal_val == 0 or signal_val == 'HOLD':
                        result.signal_stats['HOLD'] = count
                    else:
                        result.signal_stats[f"SİNYAL_{signal_val}"] = count
                else:
                    result.signal_stats[str(signal_val)] = count
            
            # Backtest işlemi
            balance = initial_balance
            equity = initial_balance
            position = None  # LONG, SHORT veya None
            position_size = 0
            entry_price = 0
            entry_time = None
            
            trades = []  # Tüm işlemler
            equity_curve = []  # Equity eğrisi
            balance_history = []  # Bakiye geçmişi
            
            # Takip eden stop için değişkenler
            highest_price_since_entry = 0
            lowest_price_since_entry = float('inf')
            
            # Her zaman noktası için işlem kararları
            for i in range(1, len(signals_df)):
                # Güncel değerler
                current_time = signals_df.index[i]
                current_price = signals_df['close'].iloc[i]
                current_signal = signals_df['signal'].iloc[i]
                
                # Equity güncelle ve kaydet
                equity_curve.append((current_time, equity))
                balance_history.append((current_time, balance))
                
                # Açık pozisyonun kar/zarar durumu
                if position:
                    # Long pozisyon için kar/zarar
                    if position == "LONG":
                        unrealized_pnl = position_size * (current_price - entry_price) / entry_price
                        equity = balance + unrealized_pnl
                        
                        # Takip eden stop için en yüksek fiyatı güncelle
                        highest_price_since_entry = max(highest_price_since_entry, current_price)
                        
                        # Take profit kontrolü
                        take_profit_triggered = False
                        if take_profit_pct is not None:
                            take_profit_price = entry_price * (1 + take_profit_pct / 100)
                            if current_price >= take_profit_price:
                                take_profit_triggered = True
                                
                        # Stop loss kontrolü
                        stop_loss_triggered = False
                        if stop_loss_pct is not None:
                            stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
                            if current_price <= stop_loss_price:
                                stop_loss_triggered = True
                                
                        # Trailing stop kontrolü
                        trailing_stop_triggered = False
                        if trailing_stop_pct is not None:
                            trailing_stop_price = highest_price_since_entry * (1 - trailing_stop_pct / 100)
                            if current_price <= trailing_stop_price and current_price > entry_price:
                                trailing_stop_triggered = True
                                
                        # Pozisyonu kapat (take profit, stop loss, trailing stop veya SELL sinyali ile)
                        if take_profit_triggered or stop_loss_triggered or trailing_stop_triggered or current_signal == "SELL":
                            # Kar/zarar hesapla
                            profit_loss = position_size * (current_price - entry_price) / entry_price
                            new_balance = balance + profit_loss
                            profit_loss_pct = (current_price - entry_price) / entry_price * 100
                            
                            # İşlemi kaydet
                            trade = Trade(
                                entry_time=entry_time,
                                entry_price=entry_price,
                                position_size=position_size,
                                position=position,
                                exit_time=current_time,
                                exit_price=current_price,
                                profit_loss=profit_loss,
                                profit_loss_pct=profit_loss_pct
                            )
                            trades.append(trade)
                            
                            # Bakiyeyi güncelle
                            balance = new_balance
                            equity = balance
                            
                            # Pozisyonu sıfırla
                            position = None
                            position_size = 0
                            
                            # Log
                            self.logger.info(f"LONG pozisyon kapatıldı: {current_time}, Fiyat: {current_price}, P/L: {profit_loss:.2f} ({profit_loss_pct:.2f}%)")
                            
                    # Short pozisyon için kar/zarar (gelecekte eklenebilir)
                    # ...
                    
                # Yeni pozisyon açma
                if position is None:  # Açık pozisyon yoksa
                    if current_signal == "BUY":
                        # Risk bazlı pozisyon büyüklüğü
                        position_size = (balance * risk_per_trade_pct / 100)
                        entry_price = current_price
                        entry_time = current_time
                        position = "LONG"
                        
                        # Takip değişkenlerini sıfırla
                        highest_price_since_entry = current_price
                        lowest_price_since_entry = current_price
                        
                        self.logger.info(f"LONG pozisyon açıldı: {current_time}, Fiyat: {current_price}, Miktar: {position_size}")
                        
                    # SHORT pozisyonlar için (gelecekte eklenebilir)
                    # elif current_signal == "SELL":
                    #    ...
            
            # Sonuçları hazırla
            self.logger.info(f"Backtest tamamlandı: {len(trades)} işlem, Son bakiye: {balance:.2f}")
            
            # Son bakiyeyi kaydet
            result.final_balance = balance
            result.total_profit_loss = balance - initial_balance
            result.total_profit_loss_pct = (result.total_profit_loss / initial_balance) * 100
            
            # İşlem istatistikleri
            win_trades = [trade for trade in trades if trade.profit_loss > 0]
            loss_trades = [trade for trade in trades if trade.profit_loss <= 0]
            
            result.trades = trades
            result.winning_trades = len(win_trades)
            result.losing_trades = len(loss_trades)
            result.total_trades = len(trades)
            result.win_rate = (result.winning_trades / len(trades) * 100) if trades else 0
            
            # Equity eğrisi ve bakiye geçmişi
            result.equity_curve = equity_curve
            result.balance_history = balance_history
            
            # Maksimum drawdown hesapla
            if equity_curve:
                peak = initial_balance
                max_drawdown = 0
                
                for _, value in equity_curve:
                    if value > peak:
                        peak = value
                    drawdown = (peak - value) / peak * 100 if peak > 0 else 0
                    max_drawdown = max(max_drawdown, drawdown)
                
                result.max_drawdown = max_drawdown
                result.max_drawdown_pct = max_drawdown
            
            # Risk yönetimi parametreleri
            result.take_profit_pct = take_profit_pct
            result.stop_loss_pct = stop_loss_pct
            result.trailing_stop_pct = trailing_stop_pct
            result.trailing_profit_pct = trailing_profit_pct
            result.risk_per_trade_pct = risk_per_trade_pct
            
            return result
            
        except Exception as e:
            import traceback
            self.logger.error(f"Backtest çalıştırılırken hata: {str(e)}")
            self.logger.error(traceback.format_exc())
            return result

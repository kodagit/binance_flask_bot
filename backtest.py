import pandas as pd
import numpy as np
import logging
from datetime import datetime
import time
import json
from typing import Dict, List, Tuple, Any
from strategy_manager import StrategyManager

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
        self.sharpe_ratio = 0
        self.sortino_ratio = 0
        self.profit_factor = 0
        self.average_trade = 0
        self.average_win = 0
        self.average_loss = 0
        self.largest_win = 0
        self.largest_loss = 0
        self.average_hold_time = None
        self.total_fees = 0
        self.equity_curve = []
        self.balance_history = []
        self.trades = []
        self.take_profit_pct = None
        self.stop_loss_pct = None
        self.trailing_stop_pct = None
        self.trailing_profit_pct = None
        self.risk_per_trade_pct = None
        self.date_range = None

class Trade:
    def __init__(self, entry_time, entry_price, position_size, position, exit_time=None, exit_price=None, profit_loss=0, profit_loss_pct=0, status="CLOSED"):
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.position_size = position_size
        self.position = position  # LONG veya SHORT
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.profit_loss = profit_loss
        self.profit_loss_pct = profit_loss_pct
        self.status = status  # OPEN, CLOSED, CANCELLED

class Backtester:
    """Backtester sınıfı"""
    
    def __init__(self, strategy_manager=None):
        """Backtester'ı başlat"""
        self.logger = logging.getLogger(__name__)
        self.strategy_manager = strategy_manager
    
    def run(self, df, strategy, symbol, interval, initial_balance=1000.0, 
            take_profit_pct=None, stop_loss_pct=None, trailing_stop_pct=None, 
            trailing_profit_pct=None, risk_per_trade_pct=1):
        """
        Backtest çalıştır.
        
        Args:
            df (pd.DataFrame): Backtest edilecek veri
            strategy: Strateji nesnesi
            symbol (str): Sembol
            interval (str): Zaman aralığı
            initial_balance (float): Başlangıç bakiyesi
            take_profit_pct (float, optional): Kar alma yüzdesi
            stop_loss_pct (float, optional): Zarar durdurma yüzdesi
            trailing_stop_pct (float, optional): Trailing stop yüzdesi
            trailing_profit_pct (float, optional): Trailing profit yüzdesi
            risk_per_trade_pct (float, optional): Her işlemde risk alınacak yüzde
            
        Returns:
            BacktestResult: Backtest sonuçları
        """
        result = BacktestResult()
        
        # Veri kontrolü
        if df is None or df.empty:
            self.logger.error("Veri yok")
            return result
            
        self.logger.info(f"Backtest başlatılıyor: {symbol} {interval}")
        self.logger.info(f"Başlangıç bakiyesi: {initial_balance}")
        
        # Strateji kontrolü
        if strategy is None:
            self.logger.error("Strateji nesnesi yok")
            return result
            
        # Strateji tipini kontrol et
        self.logger.info(f"Strateji tipi: {type(strategy)}")
            
        # Sonuç nesnesi oluştur
        if hasattr(strategy, 'name') and isinstance(strategy.name, str):
            strategy_name = strategy.name
        else:
            strategy_name = strategy.__class__.__name__
            
        result = BacktestResult(symbol, interval, strategy_name)
        result.initial_balance = initial_balance
        
        self.logger.info(f"Strateji: {strategy_name}")
        
        try:
            # Veriyi analiz et ve sinyalleri al
            self.logger.info("Strateji sinyalleri hesaplanıyor...")
            
            if hasattr(strategy, 'generate_signals'):
                try:
                    # generate_signals metodunu çağır
                    df_signals = strategy.generate_signals(df)
                    self.logger.info(f"Sinyaller generate_signals metodu ile hesaplandı: {len(df_signals) if df_signals is not None else 0} satır")
                except Exception as e:
                    import traceback
                    self.logger.error(f"generate_signals metodu çağrılırken hata: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    return result
            else:
                self.logger.error("Strateji sınıfında generate_signals metodu bulunamadı")
                return result
                
            if df_signals is None or df_signals.empty:
                self.logger.error("Sinyal oluşturulamadı veya boş veri geldi")
                return result
                
            # Sinyalleri kontrol et
            if 'signal' not in df_signals.columns:
                self.logger.error("Sinyaller DataFrame'inde 'signal' sütunu yok")
                self.logger.info(f"Mevcut sütunlar: {df_signals.columns.tolist()}")
                return result
            
            # Sinyal dağılımını logla
            signal_counts = df_signals['signal'].value_counts().to_dict()
            self.logger.info(f"Sinyal dağılımı: {signal_counts}")
            
            # Backtest değişkenleri
            balance = initial_balance
            position = None  # LONG, SHORT veya None
            entry_time = None
            entry_price = None
            position_size = 0
            trades = []
            equity_curve = []
            balance_history = []
            
            # Trailing stop ve profit için değişkenler
            highest_price_since_entry = 0
            lowest_price_since_entry = float('inf')
            
            # Strateji için işlem kararları
            for i in range(1, len(df_signals)):
                current_time = df_signals.index[i]
                current_price = df_signals['close'].iloc[i]
                current_signal = df_signals['signal'].iloc[i] if 'signal' in df_signals.columns else None
                
                # Sinyal yoksa devam et
                if current_signal is None:
                    continue
                
                # Equity curve için mevcut değeri kaydet
                if position == 'LONG':
                    current_value = balance + position_size * (current_price / entry_price - 1)
                elif position == 'SHORT':
                    current_value = balance + position_size * (1 - current_price / entry_price)
                else:
                    current_value = balance
                
                equity_curve.append((current_time, current_value))
                balance_history.append((current_time, balance))
                
                # Pozisyon varsa, stop loss ve take profit kontrolleri
                if position == 'LONG':
                    # En yüksek fiyatı güncelle (trailing stop/profit için)
                    highest_price_since_entry = max(highest_price_since_entry, current_price)
                    
                    # Stop loss kontrolü
                    stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
                    if current_price <= stop_loss_price:
                        self.logger.info(f"Stop loss tetiklendi: {current_time}, Fiyat: {current_price}, Stop: {stop_loss_price}")
                        # Pozisyonu kapat
                        pnl = position_size * (current_price / entry_price - 1)
                        pnl_percent = (current_price / entry_price - 1) * 100
                        balance += pnl
                        
                        # Trade'i kaydet
                        trade = Trade(
                            entry_time=entry_time,
                            entry_price=entry_price,
                            position_size=position_size,
                            position=position,
                            exit_time=current_time,
                            exit_price=current_price,
                            profit_loss=pnl,
                            profit_loss_pct=pnl_percent
                        )
                        trades.append(trade)
                        
                        # Pozisyonu sıfırla
                        position = None
                        entry_price = 0
                        entry_time = None
                        position_size = 0
                        highest_price_since_entry = 0
                        lowest_price_since_entry = float('inf')
                        continue
                    
                    # Take profit kontrolü
                    take_profit_price = entry_price * (1 + take_profit_pct / 100)
                    if current_price >= take_profit_price:
                        self.logger.info(f"Take profit tetiklendi: {current_time}, Fiyat: {current_price}, TP: {take_profit_price}")
                        # Pozisyonu kapat
                        pnl = position_size * (current_price / entry_price - 1)
                        pnl_percent = (current_price / entry_price - 1) * 100
                        balance += pnl
                        
                        # Trade'i kaydet
                        trade = Trade(
                            entry_time=entry_time,
                            entry_price=entry_price,
                            position_size=position_size,
                            position=position,
                            exit_time=current_time,
                            exit_price=current_price,
                            profit_loss=pnl,
                            profit_loss_pct=pnl_percent
                        )
                        trades.append(trade)
                        
                        # Pozisyonu sıfırla
                        position = None
                        entry_price = 0
                        entry_time = None
                        position_size = 0
                        highest_price_since_entry = 0
                        lowest_price_since_entry = float('inf')
                        continue
                    
                    # Trailing stop kontrolü
                    if trailing_stop_pct is not None and trailing_stop_pct > 0:
                        trailing_stop_price = highest_price_since_entry * (1 - trailing_stop_pct / 100)
                        if current_price <= trailing_stop_price and current_price > entry_price:
                            self.logger.info(f"Trailing stop tetiklendi: {current_time}, Fiyat: {current_price}, Stop: {trailing_stop_price}")
                            # Pozisyonu kapat
                            pnl = position_size * (current_price / entry_price - 1)
                            pnl_percent = (current_price / entry_price - 1) * 100
                            balance += pnl
                            
                            # Trade'i kaydet
                            trade = Trade(
                                entry_time=entry_time,
                                entry_price=entry_price,
                                position_size=position_size,
                                position=position,
                                exit_time=current_time,
                                exit_price=current_price,
                                profit_loss=pnl,
                                profit_loss_pct=pnl_percent
                            )
                            trades.append(trade)
                            
                            # Pozisyonu sıfırla
                            position = None
                            entry_price = 0
                            entry_time = None
                            position_size = 0
                            highest_price_since_entry = 0
                            lowest_price_since_entry = float('inf')
                            continue
                    
                    # Trailing profit kontrolü
                    if trailing_profit_pct is not None and trailing_profit_pct > 0 and current_price >= take_profit_price:
                        trailing_profit_price = highest_price_since_entry * (1 - trailing_profit_pct / 100)
                        if current_price <= trailing_profit_price:
                            self.logger.info(f"Trailing profit tetiklendi: {current_time}, Fiyat: {current_price}, Profit: {trailing_profit_price}")
                            # Pozisyonu kapat
                            pnl = position_size * (current_price / entry_price - 1)
                            pnl_percent = (current_price / entry_price - 1) * 100
                            balance += pnl
                            
                            # Trade'i kaydet
                            trade = Trade(
                                entry_time=entry_time,
                                entry_price=entry_price,
                                position_size=position_size,
                                position=position,
                                exit_time=current_time,
                                exit_price=current_price,
                                profit_loss=pnl,
                                profit_loss_pct=pnl_percent
                            )
                            trades.append(trade)
                            
                            # Pozisyonu sıfırla
                            position = None
                            entry_price = 0
                            entry_time = None
                            position_size = 0
                            highest_price_since_entry = 0
                            lowest_price_since_entry = float('inf')
                            continue
                
                elif position == 'SHORT':
                    # En düşük fiyatı güncelle (trailing stop/profit için)
                    lowest_price_since_entry = min(lowest_price_since_entry, current_price)
                    
                    # Stop loss kontrolü
                    stop_loss_price = entry_price * (1 + stop_loss_pct / 100)
                    if current_price >= stop_loss_price:
                        self.logger.info(f"Stop loss tetiklendi: {current_time}, Fiyat: {current_price}, Stop: {stop_loss_price}")
                        # Pozisyonu kapat
                        pnl = position_size * (1 - current_price / entry_price)
                        pnl_percent = (1 - current_price / entry_price) * 100
                        balance += pnl
                        
                        # Trade'i kaydet
                        trade = Trade(
                            entry_time=entry_time,
                            entry_price=entry_price,
                            position_size=position_size,
                            position=position,
                            exit_time=current_time,
                            exit_price=current_price,
                            profit_loss=pnl,
                            profit_loss_pct=pnl_percent
                        )
                        trades.append(trade)
                        
                        # Pozisyonu sıfırla
                        position = None
                        entry_price = 0
                        entry_time = None
                        position_size = 0
                        highest_price_since_entry = 0
                        lowest_price_since_entry = float('inf')
                        continue
                    
                    # Take profit kontrolü
                    take_profit_price = entry_price * (1 - take_profit_pct / 100)
                    if current_price <= take_profit_price:
                        self.logger.info(f"Take profit tetiklendi: {current_time}, Fiyat: {current_price}, TP: {take_profit_price}")
                        # Pozisyonu kapat
                        pnl = position_size * (1 - current_price / entry_price)
                        pnl_percent = (1 - current_price / entry_price) * 100
                        balance += pnl
                        
                        # Trade'i kaydet
                        trade = Trade(
                            entry_time=entry_time,
                            entry_price=entry_price,
                            position_size=position_size,
                            position=position,
                            exit_time=current_time,
                            exit_price=current_price,
                            profit_loss=pnl,
                            profit_loss_pct=pnl_percent
                        )
                        trades.append(trade)
                        
                        # Pozisyonu sıfırla
                        position = None
                        entry_price = 0
                        entry_time = None
                        position_size = 0
                        highest_price_since_entry = 0
                        lowest_price_since_entry = float('inf')
                        continue
                    
                    # Trailing stop kontrolü
                    if trailing_stop_pct is not None and trailing_stop_pct > 0:
                        trailing_stop_price = lowest_price_since_entry * (1 + trailing_stop_pct / 100)
                        if current_price >= trailing_stop_price and current_price < entry_price:
                            self.logger.info(f"Trailing stop tetiklendi: {current_time}, Fiyat: {current_price}, Stop: {trailing_stop_price}")
                            # Pozisyonu kapat
                            pnl = position_size * (1 - current_price / entry_price)
                            pnl_percent = (1 - current_price / entry_price) * 100
                            balance += pnl
                            
                            # Trade'i kaydet
                            trade = Trade(
                                entry_time=entry_time,
                                entry_price=entry_price,
                                position_size=position_size,
                                position=position,
                                exit_time=current_time,
                                exit_price=current_price,
                                profit_loss=pnl,
                                profit_loss_pct=pnl_percent
                            )
                            trades.append(trade)
                            
                            # Pozisyonu sıfırla
                            position = None
                            entry_price = 0
                            entry_time = None
                            position_size = 0
                            highest_price_since_entry = 0
                            lowest_price_since_entry = float('inf')
                            continue
                    
                    # Trailing profit kontrolü
                    if trailing_profit_pct is not None and trailing_profit_pct > 0 and current_price <= take_profit_price:
                        trailing_profit_price = lowest_price_since_entry * (1 + trailing_profit_pct / 100)
                        if current_price >= trailing_profit_price:
                            self.logger.info(f"Trailing profit tetiklendi: {current_time}, Fiyat: {current_price}, Profit: {trailing_profit_price}")
                            # Pozisyonu kapat
                            pnl = position_size * (1 - current_price / entry_price)
                            pnl_percent = (1 - current_price / entry_price) * 100
                            balance += pnl
                            
                            # Trade'i kaydet
                            trade = Trade(
                                entry_time=entry_time,
                                entry_price=entry_price,
                                position_size=position_size,
                                position=position,
                                exit_time=current_time,
                                exit_price=current_price,
                                profit_loss=pnl,
                                profit_loss_pct=pnl_percent
                            )
                            trades.append(trade)
                            
                            # Pozisyonu sıfırla
                            position = None
                            entry_price = 0
                            entry_time = None
                            position_size = 0
                            highest_price_since_entry = 0
                            lowest_price_since_entry = float('inf')
                            continue
                
                # Pozisyon yoksa ve sinyal varsa gir
                if position is None:
                    if current_signal == "BUY":
                        # Pozisyon büyüklüğünü hesapla
                        position_size = balance * risk_per_trade_pct / 100
                        
                        # Pozisyon oluştur
                        position = "LONG"
                        entry_price = current_price
                        entry_time = current_time
                        highest_price_since_entry = current_price
                        
                        self.logger.info(f"LONG pozisyon oluşturuldu: {entry_time}, Fiyat: {entry_price}")
                    
                    elif current_signal == "SELL":
                        # Pozisyon büyüklüğünü hesapla
                        position_size = balance * risk_per_trade_pct / 100
                        
                        # Pozisyon oluştur
                        position = "SHORT"
                        entry_price = current_price
                        entry_time = current_time
                        lowest_price_since_entry = current_price
                        
                        self.logger.info(f"SHORT pozisyon oluşturuldu: {entry_time}, Fiyat: {entry_price}")
                
                # Pozisyon varsa ve ters sinyal varsa çık
                elif position is not None and ((position == "LONG" and current_signal == "SELL") or (position == "SHORT" and current_signal == "BUY")):
                    # PnL hesapla
                    if position == "LONG":
                        pnl = position_size * (current_price / entry_price - 1)
                        pnl_percent = (current_price / entry_price - 1) * 100
                    else:  # SHORT
                        pnl = position_size * (1 - current_price / entry_price)
                        pnl_percent = (1 - current_price / entry_price) * 100
                    
                    # Pozisyonu kapat
                    balance += pnl
                    
                    # Trade'i kaydet
                    trade = Trade(
                        entry_time=entry_time,
                        entry_price=entry_price,
                        position_size=position_size,
                        position=position,
                        exit_time=current_time,
                        exit_price=current_price,
                        profit_loss=pnl,
                        profit_loss_pct=pnl_percent
                    )
                    trades.append(trade)
                    
                    # Pozisyonu sıfırla
                    position = None
                    entry_price = 0
                    entry_time = None
                    position_size = 0
                    highest_price_since_entry = 0
                    lowest_price_since_entry = float('inf')
            
            # Sonuçları hazırla
            result.final_balance = balance
            result.total_profit_loss = balance - initial_balance
            result.total_profit_loss_pct = (result.total_profit_loss / initial_balance) * 100
            
            # İşlem istatistiklerini hesapla
            win_trades = [trade for trade in trades if trade.profit_loss > 0]
            loss_trades = [trade for trade in trades if trade.profit_loss <= 0]
            
            result.trades = trades
            result.winning_trades = len(win_trades)
            result.losing_trades = len(loss_trades)
            result.total_trades = len(trades)
            result.win_rate = (result.winning_trades / len(trades) * 100) if trades else 0
            
            # Equity eğrisini düzenle
            result.equity_curve = [(time, value) for time, value in equity_curve]
            result.balance_history = [(time, value) for time, value in balance_history]
            
            # Maksimum düşüşü hesapla
            if equity_curve:
                peak = 0
                max_drawdown = 0
                
                for _, value in equity_curve:
                    if value > peak:
                        peak = value
                    drawdown = (peak - value) / peak * 100
                    max_drawdown = max(max_drawdown, drawdown)
                
                result.max_drawdown = max_drawdown
                result.max_drawdown_pct = max_drawdown
            
            result.take_profit_pct = take_profit_pct
            result.stop_loss_pct = stop_loss_pct
            result.trailing_stop_pct = trailing_stop_pct
            result.trailing_profit_pct = trailing_profit_pct
            result.risk_per_trade_pct = risk_per_trade_pct
            
            return result
            
        except Exception as e:
            self.logger.error(f"Backtest çalıştırılırken hata: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return BacktestResult(symbol, interval, strategy.name)

    def run_backtest(self, df: pd.DataFrame, symbol: str, timeframe: str, 
                    initial_balance: float = 10000, position_size_percent: float = 60,
                    leverage: int = 10, strategy_name: str = "Five_Stage_Approval",
                    take_profit_pct: float = 10.0, stop_loss_pct: float = 5.0,
                    trailing_stop_pct: float = None, trailing_profit_pct: float = None):
        """
        Backtest çalıştır
        
        Args:
            df (pd.DataFrame): Fiyat verileri
            symbol (str): İşlem çifti
            timeframe (str): Zaman aralığı
            initial_balance (float, optional): Başlangıç bakiyesi
            position_size_percent (float, optional): Pozisyon büyüklüğü yüzdesi
            leverage (int, optional): Kaldıraç
            strategy_name (str, optional): Strateji adı
            take_profit_pct (float, optional): Kar alma yüzdesi
            stop_loss_pct (float, optional): Zarar durdurma yüzdesi
            trailing_stop_pct (float, optional): Takip eden stop yüzdesi (None ise devre dışı)
            trailing_profit_pct (float, optional): Takip eden kar alma yüzdesi (None ise devre dışı)
            
        Returns:
            BacktestResult: Backtest sonuçları
        """
        # Sonuç nesnesi oluştur
        result = BacktestResult(symbol, timeframe, strategy_name)
        result.initial_balance = initial_balance
        
        # Strateji sınıfını al
        strategy_class = self.strategy_manager.get_strategy(strategy_name)
        if not strategy_class:
            self.logger.error(f"Strateji bulunamadı: {strategy_name}")
            return result
        
        # Strateji örneği oluştur
        strategy = strategy_class()
        
        # Veriyi analiz et
        df_signals = strategy.generate_signals(df)
        
        if df_signals is None or len(df_signals) == 0:
            self.logger.error("Analiz sonucu boş")
            return result
        
        # Backtest çalıştır
        return self.run(df_signals, strategy, symbol, timeframe, initial_balance, 
                        take_profit_pct, stop_loss_pct, trailing_stop_pct, trailing_profit_pct, position_size_percent)

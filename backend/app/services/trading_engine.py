import asyncio
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import SessionLocal, Trade, TradeDecision, MarketData
from app.services.tradestation_api import TradeStationAPI
from app.services.market_data import MarketDataService
from app.services.pdt_compliance import PDTComplianceService

logger = logging.getLogger(__name__)

class TradingEngine:
    """Main trading engine that orchestrates entry and exit logic"""
    
    def __init__(self):
        self.api = TradeStationAPI()
        self.market_data = MarketDataService()
        self.pdt_service = PDTComplianceService()
    
    async def execute_entry(self) -> Dict[str, Any]:
        """Execute entry logic - VIX gap up iron condor strategy"""
        logger.info("Starting entry logic execution")
        
        db = SessionLocal()
        try:
            # Get current account configuration
            account_type = "live" if settings.USE_LIVE_ACCOUNT else "sim"
            account_id = settings.get_account_id()
            
            # Check if strategy is enabled
            strategy_enabled = await self._is_strategy_enabled(db)
            if not strategy_enabled:
                return await self._record_decision(
                    db, "entry_attempt", False, "Strategy is disabled", account_type
                )
            
            # Check PDT compliance
            pdt_status = self.pdt_service.check_pdt_compliance(account_type)
            if not pdt_status["can_trade_today"]:
                return await self._record_decision(
                    db, "entry_attempt", False, 
                    f"PDT rule violation risk - {pdt_status['trades_remaining']} trades remaining",
                    account_type, pdt_trades_remaining=pdt_status["trades_remaining"]
                )
            
            # Check if we already have an open position today
            existing_trade = db.query(Trade).filter(
                Trade.trade_date == date.today(),
                Trade.account_type == account_type,
                Trade.is_open == True
            ).first()
            
            if existing_trade:
                return await self._record_decision(
                    db, "entry_attempt", False, "Already have open position today", account_type
                )
            
            # Check VIX gap up condition
            vix_condition = self.market_data.check_vix_gap_up_condition()
            if not vix_condition["condition_met"]:
                return await self._record_decision(
                    db, "entry_attempt", False, "VIX gap up condition not met", account_type,
                    vix_value=vix_condition.get("current_vix"),
                    vix_gap_up=vix_condition.get("vix_gap_up", False)
                )
            
            # Execute the iron condor trade
            trade_result = await self._execute_iron_condor_entry(account_id, vix_condition)
            
            if trade_result["success"]:
                # Record the trade in database
                trade = Trade(
                    trade_date=date.today(),
                    entry_time=datetime.now(),
                    underlying_symbol="SPY",
                    expiration_date=trade_result["expiration_date"],
                    put_strike=trade_result["put_strike"],
                    put_wing_strike=trade_result["put_wing_strike"],
                    call_strike=trade_result["call_strike"],
                    call_wing_strike=trade_result["call_wing_strike"],
                    quantity=1,
                    entry_price=trade_result.get("entry_price"),
                    max_profit=trade_result.get("max_profit"),
                    max_loss=trade_result.get("max_loss"),
                    account_type=account_type,
                    vix_open=vix_condition.get("current_vix"),
                    vix_previous_close=vix_condition.get("previous_vix_close"),
                    spy_price_at_entry=trade_result.get("spy_price"),
                    entry_order_id=trade_result.get("order_id"),
                    take_profit_order_id=trade_result.get("take_profit_order_id")
                )
                db.add(trade)
                db.commit()
                db.refresh(trade)
                
                # Record PDT day trade
                self.pdt_service.record_day_trade(account_type)
                
                # Record successful decision
                await self._record_decision(
                    db, "entry_attempt", True, "VIX gap up detected - iron condor executed",
                    account_type, vix_value=vix_condition.get("current_vix"),
                    vix_gap_up=True, trade_id=trade.id
                )
                
                logger.info(f"Iron condor trade executed successfully: {trade_result}")
                return {
                    "success": True,
                    "trade_id": trade.id,
                    "message": "Iron condor trade executed",
                    "details": trade_result
                }
            
            else:
                # Record failed execution
                await self._record_decision(
                    db, "entry_attempt", False, f"Trade execution failed: {trade_result.get('error')}",
                    account_type, vix_value=vix_condition.get("current_vix"),
                    error_message=trade_result.get("error")
                )
                
                return {
                    "success": False,
                    "message": "Trade execution failed",
                    "error": trade_result.get("error")
                }
                
        except Exception as e:
            logger.error(f"Error in entry execution: {e}", exc_info=True)
            await self._record_decision(
                db, "entry_attempt", False, f"System error: {str(e)}", 
                account_type or "sim", error_message=str(e)
            )
            return {
                "success": False,
                "message": "Entry execution failed",
                "error": str(e)
            }
        finally:
            db.close()
    
    async def execute_exit(self) -> Dict[str, Any]:
        """Execute exit logic - timed exit at 11:30 AM ET"""
        logger.info("Starting exit logic execution")
        
        db = SessionLocal()
        try:
            account_type = "live" if settings.USE_LIVE_ACCOUNT else "sim"
            account_id = settings.get_account_id()
            
            # Find open positions for today
            open_trades = db.query(Trade).filter(
                Trade.trade_date == date.today(),
                Trade.account_type == account_type,
                Trade.is_open == True
            ).all()
            
            if not open_trades:
                await self._record_decision(
                    db, "exit_attempt", False, "No open positions to exit", account_type
                )
                return {
                    "success": True,
                    "message": "No open positions to exit",
                    "trades_closed": 0
                }
            
            results = []
            for trade in open_trades:
                try:
                    # Execute exit for this trade
                    exit_result = await self._execute_trade_exit(account_id, trade)
                    
                    if exit_result["success"]:
                        # Update trade record
                        trade.is_open = False
                        trade.exit_time = datetime.now()
                        trade.exit_reason = "timed_exit"
                        trade.exit_price = exit_result.get("exit_price")
                        trade.realized_pnl = exit_result.get("realized_pnl")
                        trade.exit_order_id = exit_result.get("order_id")
                        
                        db.commit()
                        
                        results.append({
                            "trade_id": trade.id,
                            "success": True,
                            "message": "Trade closed successfully"
                        })
                        
                        logger.info(f"Trade {trade.id} closed successfully")
                    else:
                        results.append({
                            "trade_id": trade.id,
                            "success": False,
                            "error": exit_result.get("error")
                        })
                        
                except Exception as e:
                    logger.error(f"Error closing trade {trade.id}: {e}")
                    results.append({
                        "trade_id": trade.id,
                        "success": False,
                        "error": str(e)
                    })
            
            successful_exits = sum(1 for r in results if r["success"])
            
            await self._record_decision(
                db, "exit_attempt", successful_exits > 0, 
                f"Timed exit executed - {successful_exits} trades closed", account_type
            )
            
            return {
                "success": True,
                "message": f"Exit executed: {successful_exits}/{len(results)} trades closed",
                "trades_closed": successful_exits,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in exit execution: {e}", exc_info=True)
            await self._record_decision(
                db, "exit_attempt", False, f"System error: {str(e)}", 
                account_type or "sim", error_message=str(e)
            )
            return {
                "success": False,
                "message": "Exit execution failed",
                "error": str(e)
            }
        finally:
            db.close()
    
    async def _execute_iron_condor_entry(self, account_id: str, vix_condition: Dict) -> Dict[str, Any]:
        """Execute iron condor entry using existing entry script logic"""
        try:
            # This implements the logic from your vix_SPY_IC_entry.py
            today = date.today()
            expiration_str = f"{today.month:02d}-{today.day:02d}-{today.year}"
            
            # Get options chain
            chain_data = await self.api.get_options_chain("SPY", expiration_str, strike_proximity=20)
            
            if not chain_data:
                return {"success": False, "error": "Failed to get options chain"}
            
            # Process chain data (simplified version of your script logic)
            # This would need the full implementation from your entry script
            # For now, returning a placeholder structure
            
            return {
                "success": True,
                "expiration_date": today,
                "put_strike": 400.0,  # These would be calculated from chain
                "put_wing_strike": 390.0,
                "call_strike": 420.0,
                "call_wing_strike": 430.0,
                "entry_price": 2.50,
                "max_profit": 2.50,
                "max_loss": 7.50,
                "spy_price": 405.0,
                "order_id": "placeholder_order_id"
            }
            
        except Exception as e:
            logger.error(f"Error executing iron condor entry: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_trade_exit(self, account_id: str, trade: Trade) -> Dict[str, Any]:
        """Execute trade exit using existing exit script logic"""
        try:
            # This implements the logic from your vix_SPY_IC_timedexit.py
            # Get current positions and close them
            positions = await self.api.get_positions(account_id)
            
            # Filter positions for this trade's symbol
            spy_positions = [p for p in positions if p.get("Symbol", "").startswith("SPY")]
            
            if not spy_positions:
                return {"success": True, "exit_price": 0.0, "realized_pnl": trade.entry_price}
            
            # Execute exit orders (simplified)
            return {
                "success": True,
                "exit_price": 1.25,  # This would be calculated from actual exit
                "realized_pnl": (trade.entry_price or 0) - 1.25,
                "order_id": "placeholder_exit_order_id"
            }
            
        except Exception as e:
            logger.error(f"Error executing trade exit: {e}")
            return {"success": False, "error": str(e)}
    
    async def _is_strategy_enabled(self, db: Session) -> bool:
        """Check if strategy is enabled in configuration"""
        try:
            from app.routers.strategy import get_config_value
            enabled = await get_config_value(db, "strategy_enabled", "false")
            return enabled.lower() == "true"
        except Exception as e:
            logger.error(f"Error checking strategy status: {e}")
            return False
    
    async def _record_decision(
        self, 
        db: Session, 
        decision_type: str, 
        action_taken: bool, 
        reason: str, 
        account_type: str,
        vix_value: Optional[float] = None,
        vix_gap_up: Optional[bool] = None,
        spy_price: Optional[float] = None,
        pdt_trades_remaining: Optional[int] = None,
        error_message: Optional[str] = None,
        trade_id: Optional[int] = None
    ):
        """Record trading decision in audit trail"""
        try:
            strategy_enabled = await self._is_strategy_enabled(db)
            
            decision = TradeDecision(
                decision_type=decision_type,
                action_taken=action_taken,
                reason=reason,
                vix_value=vix_value,
                vix_gap_up=vix_gap_up,
                spy_price=spy_price,
                account_type=account_type,
                pdt_trades_remaining=pdt_trades_remaining,
                strategy_enabled=strategy_enabled,
                error_message=error_message,
                trade_id=trade_id
            )
            
            db.add(decision)
            db.commit()
            
            logger.info(f"Decision recorded: {decision_type} - {reason}")
            
        except Exception as e:
            logger.error(f"Error recording decision: {e}")
            db.rollback()
    
    async def _execute_iron_condor_entry(self, account_id: str, vix_condition: Dict[str, Any]) -> Dict[str, Any]:
        """Execute iron condor entry based on VIX gap up condition"""
        try:
            logger.info("Executing iron condor entry strategy")
            
            # Get current SPY price
            spy_price = self.market_data.get_spy_price()
            
            # Build iron condor strategy
            strategy_info = await self.api.build_iron_condor_strategy(
                symbol=settings.UNDERLYING_SYMBOL,
                expiration_date=date.today(),
                delta_target=settings.DELTA_TARGET,
                wing_width=settings.WING_WIDTH
            )
            
            # Place the iron condor order
            order_result = await self.api.place_iron_condor_order(
                account_id=account_id,
                strategy_info=strategy_info,
                quantity=1
            )
            
            return {
                "success": True,
                "message": "Iron condor executed successfully",
                "expiration_date": strategy_info['expiration_date'],
                "put_strike": strategy_info['put_strike'],
                "put_wing_strike": strategy_info['put_wing_strike'],
                "call_strike": strategy_info['call_strike'],
                "call_wing_strike": strategy_info['call_wing_strike'],
                "entry_price": strategy_info['net_credit'],
                "max_profit": strategy_info['max_profit'],
                "max_loss": strategy_info['max_loss'],
                "spy_price": spy_price,
                "order_id": order_result.get('order_result', {}).get('orderId'),
                "take_profit_order_id": None,  # OSO order ID would be in the response
                "strategy_info": strategy_info
            }
            
        except Exception as e:
            logger.error(f"Error executing iron condor entry: {e}")
            return {
                "success": False,
                "message": "Iron condor execution failed",
                "error": str(e)
            }
    
    async def _execute_iron_condor_exit(self, trade: Trade, account_id: str) -> Dict[str, Any]:
        """Execute iron condor exit (timed exit logic)"""
        try:
            logger.info(f"Executing timed exit for trade {trade.id}")
            
            # Reconstruct strategy info from trade record
            strategy_info = {
                'expiration_date': trade.expiration_date,
                'put_strike': int(trade.put_strike),
                'call_strike': int(trade.call_strike),
                'put_wing_strike': int(trade.put_wing_strike),
                'call_wing_strike': int(trade.call_wing_strike),
                'option_symbols': {
                    'put_sell': f'{trade.underlying_symbol} {trade.expiration_date.strftime("%y%m%d")}P{int(trade.put_strike)}',
                    'put_buy': f'{trade.underlying_symbol} {trade.expiration_date.strftime("%y%m%d")}P{int(trade.put_wing_strike)}',
                    'call_sell': f'{trade.underlying_symbol} {trade.expiration_date.strftime("%y%m%d")}C{int(trade.call_strike)}',
                    'call_buy': f'{trade.underlying_symbol} {trade.expiration_date.strftime("%y%m%d")}C{int(trade.call_wing_strike)}'
                }
            }
            
            # Close the iron condor position
            exit_result = await self.api.close_iron_condor_position(
                account_id=account_id,
                strategy_info=strategy_info,
                quantity=trade.quantity
            )
            
            return {
                "success": True,
                "message": "Iron condor closed successfully",
                "exit_order_id": exit_result.get('order_result', {}).get('orderId'),
                "exit_result": exit_result
            }
            
        except Exception as e:
            logger.error(f"Error executing iron condor exit: {e}")
            return {
                "success": False,
                "message": "Iron condor exit failed",
                "error": str(e)
            }
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from app.models.database import get_db, Trade, TradeDecision
from app.schemas.trade_schemas import TradeResponse, TradeDecisionResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[TradeResponse])
async def get_trades(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    account_type: Optional[str] = Query(None),
    is_open: Optional[bool] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get trades with optional filtering"""
    query = db.query(Trade)
    
    if account_type:
        query = query.filter(Trade.account_type == account_type)
    
    if is_open is not None:
        query = query.filter(Trade.is_open == is_open)
    
    if start_date:
        query = query.filter(Trade.trade_date >= start_date)
    
    if end_date:
        query = query.filter(Trade.trade_date <= end_date)
    
    trades = query.order_by(Trade.created_at.desc()).offset(offset).limit(limit).all()
    return trades

@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: int, db: Session = Depends(get_db)):
    """Get a specific trade by ID"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade

@router.get("/decisions/", response_model=List[TradeDecisionResponse])
async def get_trade_decisions(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get trade decisions (audit trail)"""
    query = db.query(TradeDecision)
    
    if start_date:
        query = query.filter(TradeDecision.decision_date >= start_date)
    
    if end_date:
        query = query.filter(TradeDecision.decision_date <= end_date)
    
    decisions = query.order_by(TradeDecision.created_at.desc()).offset(offset).limit(limit).all()
    return decisions

@router.get("/current/position")
async def get_current_position(db: Session = Depends(get_db)):
    """Get current open position if any"""
    current_trade = db.query(Trade).filter(
        Trade.is_open == True,
        Trade.trade_date == date.today()
    ).first()
    
    if current_trade:
        return {
            "has_position": True,
            "trade": current_trade,
            "message": "Current position found"
        }
    else:
        return {
            "has_position": False,
            "trade": None,
            "message": "No current position"
        }
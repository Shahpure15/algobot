# src/utils/exceptions.py
class TradingBotException(Exception):
    """Base exception for trading bot"""
    pass

class ExchangeError(TradingBotException):
    """Exchange-related errors"""
    pass

class AuthenticationError(ExchangeError):
    """Authentication errors"""
    pass

class WebSocketError(TradingBotException):
    """WebSocket connection errors"""
    pass

class RiskManagementError(TradingBotException):
    """Risk management errors"""
    pass

class DataError(TradingBotException):
    """Data-related errors"""
    pass

class ModelError(TradingBotException):
    """ML model errors"""
    pass

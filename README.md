# AlgoBot - Delta Exchange Trading Bot

A sophisticated algorithmic trading bot for Delta Exchange focused on crypto futures trading.

## Features

- 🚀 **Delta Exchange Integration**: Full API integration with authentication
- 📊 **Technical Analysis**: 20+ technical indicators (RSI, MACD, EMA, etc.)
- 🤖 **Machine Learning**: AI-powered trading signals
- ⚠️ **Risk Management**: Comprehensive risk controls and position sizing
- 📈 **Real-time Trading**: WebSocket-based live data processing
- 🐳 **Docker Support**: Containerized deployment
- 📱 **Monitoring**: Grafana dashboards and metrics
- 🔒 **Security**: Secure API key management

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd AlgoBot
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Delta Exchange credentials
nano .env
```

**Required Configuration:**
```bash
DELTA_API_KEY=your_api_key_here
DELTA_API_SECRET=your_api_secret_here
DELTA_TESTNET=true  # Start with testnet
```

### 3. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# For development
pip install -r requirements.dev.txt
```

### 4. Test Connection

```bash
# Test your Delta Exchange connection
python scripts/test_connection.py
```

### 5. Run the Bot

```bash
# Run directly
python src/main.py

# Or with Docker
docker-compose up -d
```

## Delta Exchange Setup

### 1. Create Delta Exchange Account

1. Go to [Delta Exchange](https://www.delta.exchange)
2. Create an account
3. Complete KYC verification
4. **Start with Testnet**: [Testnet](https://testnet.delta.exchange)

### 2. Generate API Keys

1. Login to your Delta Exchange account
2. Go to **Account Settings** → **API Management**
3. Create new API key with permissions:
   - ✅ Read Account
   - ✅ Place Orders
   - ✅ Cancel Orders
   - ✅ View Positions
4. **Important**: Save your API secret securely (it's shown only once)

### 3. Configure Bot

Update your `.env` file:

```bash
# Your Delta Exchange API credentials
DELTA_API_KEY=your_actual_api_key
DELTA_API_SECRET=your_actual_api_secret

# Start with testnet for safety
DELTA_TESTNET=true

# Trading configuration
TRADING_SYMBOL=BTCUSDT_PERP
POSITION_SIZE=0.01
RISK_PER_TRADE=0.02
```

## Testing Your Setup

### 1. Connection Test

```bash
python scripts/test_connection.py
```

This will verify:
- ✅ API credentials are working
- ✅ Account balance can be retrieved
- ✅ Trading symbol exists
- ✅ Historical data access

### 2. Paper Trading Test

The test script includes a paper trading simulation that can place and immediately cancel orders on testnet.

### 3. Monitor Logs

```bash
# View real-time logs
tail -f data/logs/bot.log

# Or with Docker
docker-compose logs -f algobot
```

## Configuration

### Trading Parameters

```bash
# Position sizing
POSITION_SIZE=0.01          # Base position size
MAX_POSITION_SIZE=0.1       # Maximum position size
RISK_PER_TRADE=0.02         # 2% risk per trade

# Risk management
MAX_DAILY_LOSS=0.05         # 5% max daily loss
STOP_LOSS_PCT=0.02          # 2% stop loss
TAKE_PROFIT_PCT=0.04        # 4% take profit
MAX_OPEN_POSITIONS=3        # Max simultaneous positions

# ML parameters
MIN_CONFIDENCE=0.65         # Minimum signal confidence
LOOKBACK_PERIOD=200         # Historical data lookback
```

### Supported Symbols

Common Delta Exchange symbols:
- `BTCUSDT_PERP` - Bitcoin Perpetual
- `ETHUSDT_PERP` - Ethereum Perpetual
- `ADAUSDT_PERP` - Cardano Perpetual
- `SOLUSDT_PERP` - Solana Perpetual

## Docker Deployment

### 1. Build and Run

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f algobot

# Stop services
docker-compose down
```

### 2. Services Included

- **AlgoBot**: Main trading bot
- **PostgreSQL**: Database for trade history
- **Redis**: Caching and session management
- **Grafana**: Monitoring dashboards (port 3000)
- **Prometheus**: Metrics collection (port 9090)

### 3. Monitoring

- **Grafana**: http://localhost:3000 (admin/admin123)
- **Bot Logs**: `docker-compose logs -f algobot`
- **Health Check**: http://localhost:8000/health

## Architecture

```
src/
├── main.py                 # Entry point
├── core/
│   ├── bot.py             # Main trading bot
│   ├── strategy.py        # Trading strategy
│   └── risk_manager.py    # Risk management
├── exchanges/
│   └── delta/
│       ├── auth.py        # Delta Exchange authentication
│       ├── clients.py     # API client
│       └── websocket.py   # WebSocket client
├── data/
│   └── indicators.py      # Technical indicators
├── ml/
│   └── predictor.py       # ML prediction model
└── utils/
    ├── logger.py          # Logging utilities
    └── exceptions.py      # Custom exceptions
```

## Safety Features

### 1. Risk Controls

- **Position Sizing**: Automatic calculation based on risk tolerance
- **Stop Loss**: Automatic stop loss orders
- **Daily Loss Limit**: Bot stops if daily loss exceeds limit
- **Maximum Positions**: Limits number of open positions
- **Circuit Breaker**: Emergency stop functionality

### 2. Testing

- **Testnet Support**: Full testnet integration
- **Paper Trading**: Simulate trades without real money
- **Connection Tests**: Verify API connectivity
- **Dry Run Mode**: Test strategies without placing orders

### 3. Monitoring

- **Real-time Logs**: Comprehensive logging
- **Health Checks**: Automated health monitoring
- **Performance Metrics**: Track bot performance
- **Alerts**: Email/SMS notifications for important events

## Troubleshooting

### Common Issues

1. **API Key Errors**
   ```bash
   # Check if API keys are set
   echo $DELTA_API_KEY
   
   # Verify API permissions in Delta Exchange
   ```

2. **Connection Issues**
   ```bash
   # Test connection
   python scripts/test_connection.py
   
   # Check network connectivity
   ping api.delta.exchange
   ```

3. **Symbol Not Found**
   ```bash
   # List available symbols
   python scripts/list_symbols.py
   
   # Update TRADING_SYMBOL in .env
   ```

4. **Insufficient Balance**
   ```bash
   # Check account balance
   python scripts/check_balance.py
   
   # Reduce POSITION_SIZE in .env
   ```

### Logs and Debugging

```bash
# View recent logs
tail -100 data/logs/bot.log

# Debug mode
DEBUG=true python src/main.py

# Check bot status
python scripts/bot_status.py
```

## Important Notes

⚠️ **SAFETY FIRST**:
- Always start with testnet
- Use small position sizes initially
- Monitor the bot closely
- Never risk more than you can afford to lose

⚠️ **TESTNET vs MAINNET**:
- Testnet: `DELTA_TESTNET=true`
- Mainnet: `DELTA_TESTNET=false`
- Switch only when confident

⚠️ **API SECURITY**:
- Never share your API keys
- Use environment variables
- Regenerate keys if compromised
- Use IP whitelisting if available

## Support

For issues and questions:
1. Check the logs first
2. Run the connection test
3. Review the configuration
4. Check Delta Exchange API status

## License

MIT License - see LICENSE file for details.

---

**Disclaimer**: This software is for educational and research purposes. Trading cryptocurrencies involves risk of financial loss. Always test thoroughly before using real money.

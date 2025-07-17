# AlgoBot: Cryptocurrency Trading Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A full-stack application for algorithmic cryptocurrency trading that integrates with Delta Exchange API. This platform allows users to execute trades, manage positions, and analyze trading performance through a clean web interface.

## Features

- 🔐 **Secure Delta Exchange Integration** - Connect safely with API credentials
- 💰 **Real-time Account Balance** - View your account balances across all assets
- 📊 **Advanced Order Types** - Place market, limit, stop loss, and take profit orders
- 📈 **Interactive Charts** - Visualize trading activity and performance
- 📋 **Trade History** - Complete history of all trades with status tracking
- 📊 **Trading Statistics** - Success rates, volume metrics, and performance analytics
- 🎨 **Modern UI** - Clean, responsive design with Material-UI components
- 🔄 **Real-time Updates** - Live data synchronization and notifications
- 🔒 **Secure Authentication** - User authentication with automatic session timeout after 4 hours of inactivity

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React +      │────│   (FastAPI)     │────│   (PostgreSQL)  │
│   Material-UI)  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                │
                       ┌─────────────────┐
                       │ Delta Exchange  │
                       │      API        │
                       └─────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Delta Exchange API credentials (optional for development)

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/algobot.git
cd algobot

# Create environment file
cp .env.example .env
# Edit .env file with your configuration
```

```bash
git clone <repository-url>
cd algobot
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your Delta Exchange credentials (optional)
# DELTA_API_KEY=your_api_key_here
# DELTA_API_SECRET=your_api_secret_here
```

### 3. Run with Docker Compose

```bash
# Start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 4. Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Development

### Hot Reload Development

The application supports hot reload for both frontend and backend:

- **Frontend**: Vite dev server with hot module replacement
- **Backend**: Uvicorn with auto-reload on file changes
- **Database**: Persistent volumes for data retention

### Project Structure

```
algobot/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Core functionality
│   │   ├── models/        # Database models
│   │   └── main.py        # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── App.jsx        # Main application
│   │   └── main.jsx       # Entry point
│   ├── Dockerfile
│   └── package.json
├── database/
│   └── init.sql           # Database schema
└── docker-compose.yml
```

### API Endpoints

#### Authentication
- `POST /api/auth/connect` - Connect to Delta Exchange
- `GET /api/auth/status` - Check connection status
- `POST /api/auth/disconnect` - Disconnect from Delta Exchange

#### Account Management
- `GET /api/account/balance` - Get account balance
- `GET /api/account/products` - Get available trading products
- `GET /api/account/orders` - Get order history from Delta Exchange

#### Trading
- `POST /api/trading/trade` - Place a trade order
- `GET /api/trading/orders` - Get local trade orders
- `GET /api/trading/orders/{id}` - Get specific order details

#### History & Analytics
- `GET /api/history/trades` - Get trade history
- `GET /api/history/stats` - Get trading statistics
- `GET /api/history/chart-data` - Get data for charts

### Frontend Components

- **ConnectionStatus**: Manage Delta Exchange connection
- **AccountBalance**: Display account balances
- **TradingPanel**: Place buy/sell orders
- **TradeHistory**: Show trade history with status
- **TradingStats**: Display trading statistics
- **ChartDashboard**: Interactive charts and analytics

## Security

### API Key Management

- API keys are stored in environment variables
- Never commit credentials to version control
- Use secure secret management in production
- Credentials are encrypted in transit

### Database Security

- Isolated database container
- Non-root user execution
- Prepared statements prevent SQL injection
- Connection pooling with limits

## Testing

### Manual Testing Workflow

1. **Start the application**:
   ```bash
   docker-compose up --build
   ```

2. **Test connection**:
   - Open http://localhost:3000
   - Click "Connect" in the top-right
   - Enter Delta Exchange API credentials
   - Verify connection status shows "Connected"

3. **Test balance retrieval**:
   - Connected status should show account balances
   - Balances should update automatically

4. **Test trading**:
   - Select a trading pair from the dropdown
   - Choose buy/sell side
   - Enter quantity and price
   - Submit order
   - Verify order appears in trade history

5. **Test dashboard features**:
   - Charts should display trading data
   - Statistics should show accurate counts
   - Trade history should update in real-time

### Automated Testing

```bash
# Run backend tests
cd backend
python -m pytest

# Run frontend tests
cd frontend
npm test
```

## Production Deployment

### Environment Variables

```bash
# Production database
DATABASE_URL=postgresql://user:password@host:5432/database

# Delta Exchange credentials
DELTA_API_KEY=your_production_api_key
DELTA_API_SECRET=your_production_api_secret

# Security
SECRET_KEY=your_strong_secret_key_here
```

### Docker Production Build

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Run in production mode
docker-compose -f docker-compose.prod.yml up -d
```

### Performance Optimization

- Enable connection pooling
- Implement caching for frequently accessed data
- Use CDN for static assets
- Enable gzip compression
- Monitor with logging and metrics

## Troubleshooting

### Common Issues

1. **Database Connection Issues**:
   ```bash
   # Check database logs
   docker-compose logs db
   
   # Restart database
   docker-compose restart db
   ```

2. **API Connection Issues**:
   ```bash
   # Check backend logs
   docker-compose logs backend
   
   # Test API directly
   curl http://localhost:8000/health
   ```

3. **Frontend Issues**:
   ```bash
   # Check frontend logs
   docker-compose logs frontend
   
   # Clear node_modules
   docker-compose down
   docker volume prune
   docker-compose up --build
   ```

### Performance Issues

- Monitor database connection pool
- Check API rate limits
- Optimize database queries
- Use browser dev tools for frontend debugging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation at /docs

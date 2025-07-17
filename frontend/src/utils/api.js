import axios from 'axios';

// Create an axios instance with default configuration
const api = axios.create({
  baseURL: '/',  // Base URL will be relative to the current domain
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Request interceptor for API calls
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for API calls
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle errors globally here
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// API endpoints grouped by category
const endpoints = {
  auth: {
    status: () => api.get('/api/auth/status'),
    connect: (credentials) => api.post('/api/auth/connect', credentials),
    disconnect: () => api.post('/api/auth/disconnect'),
  },
  account: {
    balance: () => api.get('/api/account/balance'),
    products: () => api.get('/api/account/products'),
  },
  trading: {
    placeOrder: (orderData) => api.post('/api/trading/orders', orderData),
    cancelOrder: (orderData) => api.post('/api/trading/orders/cancel', orderData),
    products: (params) => api.get('/api/trading/products', { params }),
    productsBySymbol: (symbol) => api.get(`/api/trading/products/${symbol}`),
    tickers: (params) => api.get('/api/trading/tickers', { params }),
    tickerBySymbol: (symbol) => api.get(`/api/trading/tickers/${symbol}`),
  },
  history: {
    trades: () => api.get('/api/history/trades'),
    stats: () => api.get('/api/history/stats'),
    chartData: () => api.get('/api/history/chart-data'),
  }
};

export { api, endpoints };

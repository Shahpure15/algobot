import axios from 'axios';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: '/',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to inject auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle common errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle 401 Unauthorized errors (token expired or invalid)
    if (error.response && error.response.status === 401) {
      // If not on login page, redirect to login
      if (!window.location.pathname.includes('/login')) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    
    // Handle 403 Forbidden errors
    if (error.response && error.response.status === 403) {
      console.error('Permission denied:', error.response.data);
    }
    
    // Handle 500 server errors
    if (error.response && error.response.status >= 500) {
      console.error('Server error:', error.response.data);
    }
    
    return Promise.reject(error);
  }
);

// API service with organized endpoints
const apiService = {
  // Authentication endpoints
  auth: {
    register: (userData) => api.post('/api/auth/register', userData),
    login: (credentials) => {
      // Format data as form data for OAuth2 compatibility if needed
      const formData = new URLSearchParams();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);
      
      return api.post('/api/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
    },
    me: () => api.get('/api/auth/me'),
    logout: () => api.post('/api/auth/logout'),
    connect: (exchangeCredentials) => api.post('/api/auth/connect', exchangeCredentials),
    disconnect: () => api.post('/api/auth/disconnect'),
    status: () => api.get('/api/auth/status'),
  },
  
  // Account endpoints
  account: {
    balance: () => api.get('/api/account/balance'),
    products: () => api.get('/api/account/products'),
    positions: () => api.get('/api/account/positions'),
  },
  
  // Profile endpoints
  profile: {
    get: () => api.get('/api/profile/'),
    update: (profileData) => api.put('/api/profile/', profileData),
    updateCredentials: (credentialsData) => api.post('/api/profile/credentials', credentialsData),
    deleteCredentials: (provider) => api.delete(`/api/profile/credentials/${provider}`),
    testConnection: (provider) => api.post(`/api/profile/test-connection/${provider}`),
    updatePassword: (passwordData) => api.put('/api/profile/password', passwordData),
  },
  
  // Trading endpoints
  trading: {
    placeTrade: (tradeData) => api.post('/api/trading/orders', tradeData),
    cancelOrder: (orderData) => api.post('/api/trading/orders/cancel', orderData),
    orders: (params) => api.get('/api/trading/orders', { params }),
    products: (params) => api.get('/api/trading/products', { params }),
    productBySymbol: (symbol) => api.get(`/api/trading/products/${symbol}`),
    tickers: (params) => api.get('/api/trading/tickers', { params }),
    tickerBySymbol: (symbol) => api.get(`/api/trading/tickers/${symbol}`),
  },
  
  // History endpoints
  history: {
    trades: (params) => api.get('/api/history/trades', { params }),
    stats: () => api.get('/api/history/stats'),
    chartData: (params) => api.get('/api/history/chart-data', { params }),
  },
};

export default apiService;

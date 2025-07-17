import React, { useState, useEffect } from 'react';
import { 
  ThemeProvider, 
  createTheme, 
  CssBaseline, 
  Box, 
  Container, 
  Typography, 
  AppBar, 
  Toolbar, 
  Grid, 
  Button,
  Paper, 
  Alert, 
  Snackbar 
} from '@mui/material';
import { TrendingUp as TrendingUpIcon, Logout as LogoutIcon } from '@mui/icons-material';
import ConnectionStatus from '../components/ConnectionStatus.jsx';
import AccountBalance from '../components/AccountBalance.jsx';
import TradingPanel from '../components/TradingPanel.jsx';
import TradeHistory from '../components/TradeHistory.jsx';
import TradingStats from '../components/TradingStats.jsx';
import ChartDashboard from '../components/ChartDashboard.jsx';
import ProductsPanel from '../components/ProductsPanel.jsx';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#2196f3',
    },
    secondary: {
      main: '#f50057',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
});

function Dashboard() {
  const { user, logout } = useAuth();
  const [connectionStatus, setConnectionStatus] = useState({
    is_connected: false,
    loading: true
  });
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [lastActivity, setLastActivity] = useState(Date.now());
  const inactivityTimeout = 4 * 60 * 60 * 1000; // 4 hours in milliseconds

  useEffect(() => {
    checkConnectionStatus();
    const connectionInterval = setInterval(checkConnectionStatus, 30000); // Check every 30 seconds
    
    // Set up activity monitoring
    const activityEvents = ['mousedown', 'keypress', 'scroll', 'mousemove', 'click', 'touchstart'];
    const resetInactivityTimer = () => {
      setLastActivity(Date.now());
    };
    
    activityEvents.forEach(event => {
      window.addEventListener(event, resetInactivityTimer);
    });
    
    // Check for inactivity
    const inactivityInterval = setInterval(() => {
      if (Date.now() - lastActivity > inactivityTimeout) {
        handleLogout();
        setNotification({
          open: true,
          message: 'You have been logged out due to inactivity',
          severity: 'info'
        });
      }
    }, 60000); // Check every minute
    
    return () => {
      clearInterval(connectionInterval);
      clearInterval(inactivityInterval);
      activityEvents.forEach(event => {
        window.removeEventListener(event, resetInactivityTimer);
      });
    };
  }, [lastActivity]);

  const checkConnectionStatus = async () => {
    try {
      const response = await axios.get('/api/auth/status');
      setConnectionStatus({ ...response.data, loading: false });
    } catch (error) {
      setConnectionStatus({ is_connected: false, loading: false });
    }
  };

  const handleConnectionChange = (connected) => {
    setConnectionStatus(prev => ({ ...prev, is_connected: connected }));
    setNotification({
      open: true,
      message: connected ? 'Successfully connected to Delta Exchange' : 'Disconnected from Delta Exchange',
      severity: connected ? 'success' : 'warning'
    });
  };

  const handleTradeComplete = (message) => {
    setNotification({
      open: true,
      message: message || 'Trade executed successfully',
      severity: 'success'
    });
    setRefreshTrigger(prev => prev + 1);
  };

  const handleError = (error) => {
    setNotification({
      open: true,
      message: error.message || 'An error occurred',
      severity: 'error'
    });
  };

  const handleCloseNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };
  
  const handleLogout = () => {
    logout();
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <TrendingUpIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Algo Trading Bot Dashboard
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {user && (
              <Typography variant="body2" sx={{ mr: 2 }}>
                Welcome, {user.username}
              </Typography>
            )}
            <ConnectionStatus 
              status={connectionStatus} 
              onConnectionChange={handleConnectionChange}
              onError={handleError}
            />
            <Button 
              color="inherit" 
              startIcon={<LogoutIcon />}
              onClick={handleLogout}
              sx={{ ml: 2 }}
            >
              Logout
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Grid container spacing={3}>
          {/* Account Balance */}
          <Grid item xs={12} md={6} lg={4}>
            <AccountBalance 
              isConnected={connectionStatus.is_connected}
              refreshTrigger={refreshTrigger}
              onError={handleError}
            />
          </Grid>

          {/* Trading Stats */}
          <Grid item xs={12} md={6} lg={4}>
            <TradingStats 
              refreshTrigger={refreshTrigger}
              onError={handleError}
            />
          </Grid>

          {/* Trading Panel */}
          <Grid item xs={12} md={6} lg={4}>
            <TradingPanel 
              isConnected={connectionStatus.is_connected}
              onTradeComplete={handleTradeComplete}
              onError={handleError}
            />
          </Grid>

          {/* Products Panel */}
          <Grid item xs={12}>
            <ProductsPanel 
              isConnected={connectionStatus.is_connected}
              onError={handleError}
            />
          </Grid>

          {/* Charts */}
          <Grid item xs={12} lg={8}>
            <ChartDashboard 
              refreshTrigger={refreshTrigger}
              onError={handleError}
            />
          </Grid>

          {/* Trade History */}
          <Grid item xs={12} lg={4}>
            <TradeHistory 
              refreshTrigger={refreshTrigger}
              onError={handleError}
            />
          </Grid>
        </Grid>
      </Container>

      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification.severity} 
          variant="filled"
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </ThemeProvider>
  );
}

export default Dashboard;

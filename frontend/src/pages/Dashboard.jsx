import React, { useState, useEffect } from 'react';
import { 
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
  Snackbar,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemButton,
  CircularProgress
} from '@mui/material';
import { 
  TrendingUp as TrendingUpIcon, 
  Logout as LogoutIcon,
  Person as PersonIcon,
  Link as LinkIcon,
  Brightness4 as Brightness4Icon,
  Brightness7 as Brightness7Icon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  WifiOff as WifiOffIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import ConnectionStatus from '../components/ConnectionStatus.jsx';
import AccountBalance from '../components/AccountBalance.jsx';
import TradingPanel from '../components/TradingPanel.jsx';
import TradeHistory from '../components/TradeHistory.jsx';
import TradingStats from '../components/TradingStats.jsx';
import ChartDashboard from '../components/ChartDashboard.jsx';
import ProductsPanel from '../components/ProductsPanel.jsx';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

function Dashboard() {
  const { user, logout } = useAuth();
  const { mode, toggleColorMode } = useTheme();
  const navigate = useNavigate();
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
  const [connectDialogOpen, setConnectDialogOpen] = useState(false);
  const [credentials, setCredentials] = useState([]);
  const [connecting, setConnecting] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState(null);
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
    // Simplified - just set as not connected for now
    setConnectionStatus({ is_connected: false, loading: false });
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

  const loadCredentials = async () => {
    try {
      const response = await axios.get('/api/auth/saved-credentials');
      setCredentials(response.data);
    } catch (error) {
      console.error('Error loading credentials:', error);
    }
  };

  const handleConnectClick = () => {
    setConnectDialogOpen(true);
    loadCredentials();
  };

  const handleConnectWithCredential = async (credentialId) => {
    try {
      setConnecting(true);
      const response = await axios.post('/api/auth/connect-with-saved', {}, {
        params: { credential_id: credentialId }
      });
      
      if (response.data.is_connected) {
        setConnectionStatus(prev => ({ ...prev, is_connected: true }));
        setNotification({
          open: true,
          message: 'Successfully connected to Delta Exchange',
          severity: 'success'
        });
        setConnectDialogOpen(false);
        setRefreshTrigger(prev => prev + 1);
        
        // Auto-refresh the page after successful connection
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        setNotification({
          open: true,
          message: 'Failed to connect to Delta Exchange',
          severity: 'error'
        });
      }
    } catch (error) {
      setNotification({
        open: true,
        message: error.response?.data?.detail || 'Connection failed',
        severity: 'error'
      });
    } finally {
      setConnecting(false);
    }
  };

  const handleMenuClick = (event) => {
    setMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: 'background.default' }}>
      <CssBaseline />
      <AppBar position="static" elevation={2} sx={{ backgroundColor: 'primary.main' }}>
        <Toolbar>
          <TrendingUpIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Algo Trading Bot Dashboard
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {user && (
              <Typography variant="body2" sx={{ mr: 2 }}>
                Welcome, {user.username}
              </Typography>
            )}
            
            <Chip
              icon={connectionStatus.loading ? <CircularProgress size={16} /> : 
                   (connectionStatus.is_connected ? <CheckCircleIcon /> : <WifiOffIcon />)}
              label={connectionStatus.loading ? 'Checking...' : 
                   (connectionStatus.is_connected ? 'Connected' : 'Disconnected')}
              color={connectionStatus.is_connected ? 'success' : 'default'}
              variant={connectionStatus.is_connected ? 'filled' : 'outlined'}
              size="small"
            />
            
            <Button 
              color="inherit" 
              startIcon={<LinkIcon />}
              onClick={handleConnectClick}
              disabled={connectionStatus.is_connected}
              sx={{ ml: 1 }}
            >
              Connect
            </Button>
            
            <IconButton 
              color="inherit" 
              onClick={toggleColorMode}
              sx={{ ml: 1 }}
            >
              {mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
            </IconButton>
            
            <Button 
              color="inherit" 
              startIcon={<PersonIcon />}
              onClick={() => navigate('/profile')}
              sx={{ ml: 1 }}
            >
              Profile
            </Button>
            
            <Button 
              color="inherit" 
              startIcon={<LogoutIcon />}
              onClick={handleLogout}
              sx={{ ml: 1 }}
            >
              Logout
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Quick Connect Alert */}
        {!connectionStatus.is_connected && !connectionStatus.loading && (
          <Alert 
            severity="warning" 
            sx={{ mb: 3 }}
            action={
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button 
                  size="small" 
                  variant="outlined" 
                  onClick={() => navigate('/profile')}
                >
                  Set up API Keys
                </Button>
                <Button 
                  size="small" 
                  variant="contained" 
                  onClick={handleConnectClick}
                >
                  Connect
                </Button>
              </Box>
            }
          >
            <Typography variant="body2">
              You're not connected to Delta Exchange. Connect now to start trading!
            </Typography>
          </Alert>
        )}
        
        <Grid container spacing={3}>
          {/* Quick Connect Card - Show if not connected */}
          {!connectionStatus.is_connected && !connectionStatus.loading && (
            <Grid item xs={12}>
              <Paper sx={{ p: 3, textAlign: 'center', backgroundColor: 'background.paper' }}>
                <Typography variant="h6" gutterBottom>
                  Connect to Delta Exchange
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Connect your Delta Exchange API to start trading
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                  <Button 
                    variant="outlined" 
                    onClick={() => navigate('/profile')}
                    startIcon={<PersonIcon />}
                  >
                    Set up API Keys
                  </Button>
                  <Button 
                    variant="contained" 
                    onClick={handleConnectClick}
                    startIcon={<LinkIcon />}
                  >
                    Connect Now
                  </Button>
                </Box>
              </Paper>
            </Grid>
          )}
          
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

      {/* Connect Dialog */}
      <Dialog 
        open={connectDialogOpen} 
        onClose={() => setConnectDialogOpen(false)}
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle>Connect to Delta Exchange</DialogTitle>
        <DialogContent>
          {credentials.filter(c => c.provider === 'delta_exchange').length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                No API credentials found. Please set up your API keys first.
              </Typography>
              <Button 
                variant="contained" 
                onClick={() => {
                  setConnectDialogOpen(false);
                  navigate('/profile');
                }}
                startIcon={<PersonIcon />}
                sx={{ mt: 2 }}
              >
                Set up API Keys
              </Button>
            </Box>
          ) : (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Choose a credential to connect with:
              </Typography>
              <List>
                {credentials
                  .filter(c => c.provider === 'delta_exchange')
                  .map((credential) => (
                    <ListItem key={credential.id} disablePadding>
                      <ListItemButton
                        onClick={() => handleConnectWithCredential(credential.id)}
                        disabled={connecting}
                      >
                        <ListItemIcon>
                          {connecting ? <CircularProgress size={20} /> : <CheckCircleIcon />}
                        </ListItemIcon>
                        <ListItemText
                          primary={credential.credential_name}
                          secondary={
                            credential.last_used 
                              ? `Last used: ${new Date(credential.last_used).toLocaleDateString()}` 
                              : 'Never used'
                          }
                        />
                      </ListItemButton>
                    </ListItem>
                  ))}
              </List>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConnectDialogOpen(false)} disabled={connecting}>
            Cancel
          </Button>
        </DialogActions>
      </Dialog>

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
    </Box>
  );
}

export default Dashboard;

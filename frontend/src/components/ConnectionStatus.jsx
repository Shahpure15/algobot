import React, { useState } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Typography,
  Chip,
  CircularProgress,
  Alert
} from '@mui/material';
import { 
  WifiOff as WifiOffIcon, 
  Wifi as WifiIcon,
  Settings as SettingsIcon 
} from '@mui/icons-material';
import axios from 'axios';

const ConnectionStatus = ({ status, onConnectionChange, onError }) => {
  const [open, setOpen] = useState(false);
  const [credentials, setCredentials] = useState({
    api_key: '',
    api_secret: ''
  });
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState('');

  const handleConnect = async () => {
    if (!credentials.api_key || !credentials.api_secret) {
      setError('Please enter both API key and secret');
      return;
    }

    setConnecting(true);
    setError('');

    try {
      await axios.post('/api/auth/connect', credentials);
      onConnectionChange(true);
      setOpen(false);
      setCredentials({ api_key: '', api_secret: '' });
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Connection failed';
      setError(errorMsg);
      onError(new Error(errorMsg));
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await axios.post('/api/auth/disconnect');
      onConnectionChange(false);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Disconnect failed';
      onError(new Error(errorMsg));
    }
  };

  const handleInputChange = (field) => (event) => {
    setCredentials(prev => ({
      ...prev,
      [field]: event.target.value
    }));
    setError('');
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Chip
        icon={status.loading ? <CircularProgress size={16} /> : (status.is_connected ? <WifiIcon /> : <WifiOffIcon />)}
        label={status.loading ? 'Checking...' : (status.is_connected ? 'Connected' : 'Disconnected')}
        color={status.is_connected ? 'success' : 'default'}
        variant={status.is_connected ? 'filled' : 'outlined'}
      />
      
      <Button
        size="small"
        startIcon={<SettingsIcon />}
        onClick={() => setOpen(true)}
      >
        {status.is_connected ? 'Disconnect' : 'Connect'}
      </Button>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {status.is_connected ? 'Disconnect from Delta Exchange' : 'Connect to Delta Exchange'}
        </DialogTitle>
        <DialogContent>
          {status.is_connected ? (
            <Typography>
              Are you sure you want to disconnect from Delta Exchange?
            </Typography>
          ) : (
            <Box sx={{ mt: 2 }}>
              <TextField
                fullWidth
                label="API Key"
                value={credentials.api_key}
                onChange={handleInputChange('api_key')}
                margin="normal"
                type="password"
                disabled={connecting}
              />
              <TextField
                fullWidth
                label="API Secret"
                value={credentials.api_secret}
                onChange={handleInputChange('api_secret')}
                margin="normal"
                type="password"
                disabled={connecting}
              />
              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                Your credentials are stored securely and used only for trading operations.
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)} disabled={connecting}>
            Cancel
          </Button>
          <Button
            onClick={status.is_connected ? handleDisconnect : handleConnect}
            color={status.is_connected ? 'error' : 'primary'}
            disabled={connecting}
            startIcon={connecting && <CircularProgress size={16} />}
          >
            {connecting ? 'Connecting...' : (status.is_connected ? 'Disconnect' : 'Connect')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ConnectionStatus;

import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
  Divider,
  Chip
} from '@mui/material';
import { 
  AccountBalance as AccountBalanceIcon,
  TrendingUp as TrendingUpIcon 
} from '@mui/icons-material';
import axios from 'axios';

const AccountBalance = ({ isConnected, refreshTrigger, onError }) => {
  const [balances, setBalances] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isConnected) {
      fetchBalance();
    } else {
      setBalances([]);
      setError('');
    }
  }, [isConnected, refreshTrigger]);

  const fetchBalance = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get('/api/account/balance');
      setBalances(response.data.balances || []);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to fetch balance';
      setError(errorMsg);
      onError(new Error(errorMsg));
    } finally {
      setLoading(false);
    }
  };

  const formatBalance = (balance) => {
    const num = parseFloat(balance);
    if (num === 0) return '0.00';
    if (num < 0.01) return num.toFixed(8);
    return num.toFixed(2);
  };

  return (
    <Paper sx={{ p: 3, height: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <AccountBalanceIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6">Account Balance</Typography>
      </Box>

      {!isConnected && (
        <Alert severity="info">
          Connect to Delta Exchange to view your account balance
        </Alert>
      )}

      {isConnected && loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {isConnected && error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {isConnected && !loading && !error && (
        <>
          {balances.length === 0 ? (
            <Alert severity="info">
              No balances found or all balances are zero
            </Alert>
          ) : (
            <List dense>
              {balances.map((balance, index) => (
                <React.Fragment key={balance.asset || index}>
                  <ListItem sx={{ px: 0 }}>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle1" fontWeight="medium">
                            {balance.asset}
                          </Typography>
                          <Chip 
                            size="small" 
                            label={formatBalance(balance.total)} 
                            color="primary"
                            variant="outlined"
                          />
                        </Box>
                      }
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Available: {formatBalance(balance.available)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Locked: {formatBalance(balance.locked)}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < balances.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </>
      )}
    </Paper>
  );
};

export default AccountBalance;

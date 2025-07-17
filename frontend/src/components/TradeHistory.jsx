import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  Badge
} from '@mui/material';
import { 
  History as HistoryIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon
} from '@mui/icons-material';
import axios from 'axios';

const TradeHistory = ({ refreshTrigger, onError }) => {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchTradeHistory();
  }, [refreshTrigger]);

  const fetchTradeHistory = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get('/api/history/trades');
      setTrades(response.data);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to fetch trade history';
      setError(errorMsg);
      onError(new Error(errorMsg));
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'filled':
        return 'success';
      case 'cancelled':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getSideColor = (side) => {
    return side === 'buy' ? 'success' : 'error';
  };

  const getSideIcon = (side) => {
    return side === 'buy' ? <TrendingUpIcon /> : <TrendingDownIcon />;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const formatNumber = (num) => {
    const number = parseFloat(num);
    if (number === 0) return '0.00';
    if (number < 0.01) return number.toFixed(8);
    return number.toFixed(2);
  };

  return (
    <Paper sx={{ p: 3, height: '100%', maxHeight: '600px', overflow: 'auto' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <HistoryIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6">Trade History</Typography>
        {trades.length > 0 && (
          <Badge badgeContent={trades.length} color="primary" sx={{ ml: 1 }} />
        )}
      </Box>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!loading && !error && trades.length === 0 && (
        <Alert severity="info">
          No trade history available
        </Alert>
      )}

      {!loading && !error && trades.length > 0 && (
        <List dense>
          {trades.map((trade, index) => (
            <React.Fragment key={trade.id}>
              <ListItem sx={{ px: 0 }}>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Chip
                        icon={getSideIcon(trade.side)}
                        label={trade.side.toUpperCase()}
                        color={getSideColor(trade.side)}
                        size="small"
                      />
                      <Typography variant="subtitle2" fontWeight="medium">
                        {trade.symbol}
                      </Typography>
                      <Chip
                        label={trade.status}
                        color={getStatusColor(trade.status)}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Qty: {formatNumber(trade.quantity)} @ {formatNumber(trade.price)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total: {formatNumber(parseFloat(trade.quantity) * parseFloat(trade.price))}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(trade.timestamp)}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
              {index < trades.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      )}
    </Paper>
  );
};

export default TradeHistory;

import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert
} from '@mui/material';
import { 
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  SwapHoriz as SwapHorizIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import axios from 'axios';

const TradingStats = ({ refreshTrigger, onError }) => {
  const [stats, setStats] = useState({
    total_trades: 0,
    successful_trades: 0,
    buy_trades: 0,
    sell_trades: 0,
    recent_activity_24h: 0,
    success_rate: 0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchStats();
  }, [refreshTrigger]);

  const fetchStats = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get('/api/history/stats');
      setStats(response.data);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to fetch trading stats';
      setError(errorMsg);
      onError(new Error(errorMsg));
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon, color = 'primary' }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Box sx={{ color: `${color}.main`, mr: 1 }}>
            {icon}
          </Box>
          <Typography variant="h6" component="div">
            {value}
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          {title}
        </Typography>
      </CardContent>
    </Card>
  );

  return (
    <Paper sx={{ p: 3, height: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <AnalyticsIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6">Trading Statistics</Typography>
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

      {!loading && !error && (
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <StatCard
              title="Total Trades"
              value={stats.total_trades}
              icon={<SwapHorizIcon />}
              color="primary"
            />
          </Grid>
          <Grid item xs={6}>
            <StatCard
              title="Success Rate"
              value={`${stats.success_rate.toFixed(1)}%`}
              icon={<CheckCircleIcon />}
              color="success"
            />
          </Grid>
          <Grid item xs={6}>
            <StatCard
              title="Buy Orders"
              value={stats.buy_trades}
              icon={<TrendingUpIcon />}
              color="success"
            />
          </Grid>
          <Grid item xs={6}>
            <StatCard
              title="Sell Orders"
              value={stats.sell_trades}
              icon={<TrendingDownIcon />}
              color="error"
            />
          </Grid>
          <Grid item xs={12}>
            <StatCard
              title="24h Activity"
              value={stats.recent_activity_24h}
              icon={<AnalyticsIcon />}
              color="info"
            />
          </Grid>
        </Grid>
      )}
    </Paper>
  );
};

export default TradingStats;

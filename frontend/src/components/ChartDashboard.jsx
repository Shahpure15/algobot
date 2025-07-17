import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  Grid,
  CircularProgress,
  Alert
} from '@mui/material';
import { 
  ShowChart as ShowChartIcon 
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import axios from 'axios';

const ChartDashboard = ({ refreshTrigger, onError }) => {
  const [chartData, setChartData] = useState({
    daily_trades: [],
    symbol_distribution: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchChartData();
  }, [refreshTrigger]);

  const fetchChartData = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get('/api/history/chart-data');
      setChartData(response.data);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to fetch chart data';
      setError(errorMsg);
      onError(new Error(errorMsg));
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <Paper sx={{ p: 3, height: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <ShowChartIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6">Trading Analytics</Typography>
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
        <Grid container spacing={3}>
          {/* Daily Trading Activity */}
          <Grid item xs={12} md={8}>
            <Typography variant="subtitle1" gutterBottom>
              Daily Trading Activity (Last 30 Days)
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData.daily_trades}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={formatDate}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => formatDate(value)}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="total" 
                  stroke="#8884d8" 
                  name="Total Trades"
                />
                <Line 
                  type="monotone" 
                  dataKey="buy" 
                  stroke="#82ca9d" 
                  name="Buy Orders"
                />
                <Line 
                  type="monotone" 
                  dataKey="sell" 
                  stroke="#ffc658" 
                  name="Sell Orders"
                />
              </LineChart>
            </ResponsiveContainer>
          </Grid>

          {/* Symbol Distribution */}
          <Grid item xs={12} md={4}>
            <Typography variant="subtitle1" gutterBottom>
              Symbol Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData.symbol_distribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ symbol, percent }) => `${symbol} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {chartData.symbol_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Grid>

          {/* Trade Volume by Symbol */}
          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              Trade Volume by Symbol
            </Typography>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData.symbol_distribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="symbol" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Grid>
        </Grid>
      )}
    </Paper>
  );
};

export default ChartDashboard;

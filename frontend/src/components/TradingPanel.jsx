import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Grid,
  Divider,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Switch,
  FormControlLabel
} from '@mui/material';
import { 
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Send as SendIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon 
} from '@mui/icons-material';
import axios from 'axios';

const TradingPanel = ({ isConnected, onTradeComplete, onError }) => {
  const [tabValue, setTabValue] = useState(0);
  const [demoMode, setDemoMode] = useState(false);
  const [formData, setFormData] = useState({
    symbol: '',
    side: 'buy',
    quantity: '',
    price: '',
    order_type: 'limit_order',
    time_in_force: 'gtc',
    post_only: false,
    reduce_only: false,
    client_order_id: '',
    stop_price: ''
  });
  const [products, setProducts] = useState([]);
  const [liveOrders, setLiveOrders] = useState([]);
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isConnected) {
      fetchProducts();
      fetchLiveOrders();
      fetchPositions();
    }
  }, [isConnected, demoMode]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/account/products');
      setProducts(response.data.products || []);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to fetch products';
      onError(new Error(errorMsg));
    } finally {
      setLoading(false);
    }
  };

  const fetchLiveOrders = async () => {
    try {
      const endpoint = demoMode ? '/api/trading/demo-orders' : '/api/trading/live-orders';
      const response = await axios.get(endpoint);
      if (response.data.success) {
        setLiveOrders(response.data.result || []);
      } else {
        // Handle permission error gracefully
        setLiveOrders([]);
        if (response.data.error && response.data.error.includes('permissions')) {
          onError(new Error('API key does not have trading permissions'));
        }
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to fetch live orders';
      setLiveOrders([]);
      onError(new Error(errorMsg));
    }
  };

  const fetchPositions = async () => {
    try {
      const endpoint = demoMode ? '/api/trading/demo-positions' : '/api/trading/positions';
      const response = await axios.get(endpoint);
      if (response.data.success) {
        setPositions(response.data.result || []);
      } else {
        // Handle permission error gracefully
        setPositions([]);
        if (response.data.error && response.data.error.includes('permissions')) {
          onError(new Error('API key does not have trading permissions'));
        }
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to fetch positions';
      setPositions([]);
      onError(new Error(errorMsg));
    }
  };

  const handleInputChange = (field) => (event) => {
    const value = event.target.value;
    
    setFormData(prev => {
      const newData = {
        ...prev,
        [field]: value
      };
      
      // Clear price when switching to market order
      if (field === 'order_type' && value === 'market_order') {
        newData.price = '';
      }
      
      return newData;
    });
    
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate required fields based on order type
    if (!formData.symbol || !formData.quantity) {
      setError('Please fill in symbol and quantity');
      return;
    }

    // For limit orders, price is required
    if (formData.order_type === 'limit_order' && !formData.price) {
      setError('Price is required for limit orders');
      return;
    }
    
    // For stop orders, stop price is required
    if ((formData.order_type === 'stop_loss_order' || formData.order_type === 'take_profit_order') 
        && !formData.stop_price) {
      setError('Stop price is required for stop orders');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const endpoint = demoMode ? '/api/trading/demo-trade' : '/api/trading/trade';
      
      // Prepare order data
      // Prepare order data
      const orderData = {
        symbol: formData.symbol,
        side: formData.side,
        quantity: formData.quantity,
        order_type: formData.order_type,
        time_in_force: formData.time_in_force,
        post_only: formData.post_only,
        reduce_only: formData.reduce_only
      };

      // Only include price for limit orders
      if (formData.order_type === 'limit_order') {
        orderData.price = formData.price;
      }
      
      // Add client_order_id if provided
      if (formData.client_order_id) {
        orderData.client_order_id = formData.client_order_id;
      }
      
      // Add stop_price for stop orders
      if ((formData.order_type === 'stop_loss_order' || formData.order_type === 'take_profit_order') 
          && formData.stop_price) {
        orderData.stop_price = formData.stop_price;
      }

      const response = await axios.post(endpoint, orderData);
      
      if (response.data.success) {
        onTradeComplete(`${formData.side.toUpperCase()} order placed successfully ${demoMode ? '(DEMO)' : ''}`);
        
        // Reset form
        setFormData({
          symbol: '',
          side: 'buy',
          quantity: '',
          price: '',
          order_type: 'limit_order',
          time_in_force: 'gtc',
          post_only: false,
          reduce_only: false,
          client_order_id: '',
          stop_price: ''
        });
        
        // Refresh live orders
        await fetchLiveOrders();
      } else {
        throw new Error(response.data.error || 'Trade failed');
      }
      
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Trade failed';
      setError(errorMsg);
      if (onError) {
        onError(new Error(errorMsg));
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelOrder = async (orderId, productId) => {
    try {
      await axios.post('/api/trading/orders/cancel', {
        order_id: orderId,
        product_id: productId
      });
      
      onTradeComplete(`Order ${orderId} cancelled successfully`);
      await fetchLiveOrders();
      
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to cancel order';
      onError(new Error(errorMsg));
    }
  };

  const getButtonColor = () => {
    return formData.side === 'buy' ? 'success' : 'error';
  };

  const getButtonIcon = () => {
    return formData.side === 'buy' ? <TrendingUpIcon /> : <TrendingDownIcon />;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return 'success';
      case 'pending': return 'warning';
      case 'closed': return 'info';
      case 'cancelled': return 'error';
      default: return 'default';
    }
  };

  const formatPrice = (price) => {
    return parseFloat(price).toFixed(2);
  };

  const formatDateTime = (timestamp) => {
    return new Date(timestamp / 1000).toLocaleString();
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const renderOrderForm = () => (
    <Box sx={{ mt: 2 }}>
      <form onSubmit={handleSubmit}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Symbol</InputLabel>
              <Select
                value={formData.symbol}
                onChange={handleInputChange('symbol')}
                label="Symbol"
                disabled={loading || submitting}
              >
                {products.map((product) => (
                  <MenuItem key={product.symbol} value={product.symbol}>
                    {product.symbol} - {product.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Side</InputLabel>
              <Select
                value={formData.side}
                onChange={handleInputChange('side')}
                label="Side"
                disabled={submitting}
              >
                <MenuItem value="buy">Buy</MenuItem>
                <MenuItem value="sell">Sell</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={6}>
            <TextField
              fullWidth
              label="Quantity"
              value={formData.quantity}
              onChange={handleInputChange('quantity')}
              type="number"
              inputProps={{ step: "0.00000001", min: "0" }}
              disabled={submitting}
            />
          </Grid>

          <Grid item xs={6}>
            <TextField
              fullWidth
              label={formData.order_type === 'market_order' ? 'Price (Market)' : 'Price'}
              value={formData.order_type === 'market_order' ? 'Market Price' : formData.price}
              onChange={handleInputChange('price')}
              type={formData.order_type === 'market_order' ? 'text' : 'number'}
              inputProps={formData.order_type === 'market_order' ? { readOnly: true } : { step: "0.00000001", min: "0" }}
              disabled={submitting || formData.order_type === 'market_order'}
              helperText={formData.order_type === 'market_order' ? 'Market orders execute at current market price' : ''}
            />
          </Grid>

          {(formData.order_type === 'stop_loss_order' || formData.order_type === 'take_profit_order') && (
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Stop Price"
                value={formData.stop_price}
                onChange={handleInputChange('stop_price')}
                type="number"
                inputProps={{ step: "0.00000001", min: "0" }}
                disabled={submitting}
                helperText={`Price at which the ${formData.order_type === 'stop_loss_order' ? 'stop loss' : 'take profit'} order will trigger`}
              />
            </Grid>
          )}

          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Time In Force</InputLabel>
              <Select
                value={formData.time_in_force}
                onChange={handleInputChange('time_in_force')}
                label="Time In Force"
                disabled={submitting}
              >
                <MenuItem value="gtc">Good Till Cancelled (GTC)</MenuItem>
                <MenuItem value="ioc">Immediate or Cancel (IOC)</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.post_only}
                  onChange={(e) => setFormData({...formData, post_only: e.target.checked})}
                  disabled={submitting || formData.order_type === 'market_order'}
                />
              }
              label="Post Only"
            />
            <Typography variant="caption" display="block" sx={{mt: -1}}>
              Only execute as a maker order
            </Typography>
          </Grid>

          <Grid item xs={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.reduce_only}
                  onChange={(e) => setFormData({...formData, reduce_only: e.target.checked})}
                  disabled={submitting}
                />
              }
              label="Reduce Only"
            />
            <Typography variant="caption" display="block" sx={{mt: -1}}>
              Only reduce position size
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Order Type</InputLabel>
              <Select
                value={formData.order_type}
                onChange={handleInputChange('order_type')}
                label="Order Type"
                disabled={submitting}
              >
                <MenuItem value="limit_order">Limit Order</MenuItem>
                <MenuItem value="market_order">Market Order</MenuItem>
                <MenuItem value="stop_loss_order">Stop Loss Order</MenuItem>
                <MenuItem value="take_profit_order">Take Profit Order</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {error && (
            <Grid item xs={12}>
              <Alert severity="error">{error}</Alert>
            </Grid>
          )}

          <Grid item xs={12}>
            <Button
              type="submit"
              variant="contained"
              color={getButtonColor()}
              fullWidth
              size="large"
              disabled={submitting || loading}
              startIcon={submitting ? <CircularProgress size={16} /> : getButtonIcon()}
              sx={{ mt: 2 }}
            >
              {submitting ? 'Placing Order...' : `${demoMode ? 'Demo ' : ''}Place ${formData.side.toUpperCase()} Order`}
            </Button>
          </Grid>
        </Grid>
      </form>
    </Box>
  );

  const renderLiveOrders = () => (
    <Box sx={{ mt: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Live Orders</Typography>
        <IconButton onClick={fetchLiveOrders} size="small">
          <RefreshIcon />
        </IconButton>
      </Box>
      
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Symbol</TableCell>
              <TableCell>Side</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Price</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {liveOrders.map((order) => (
              <TableRow key={order.id}>
                <TableCell>{order.product_symbol}</TableCell>
                <TableCell>
                  <Chip 
                    label={order.side.toUpperCase()}
                    color={order.side === 'buy' ? 'success' : 'error'}
                    size="small"
                  />
                </TableCell>
                <TableCell>{order.size}</TableCell>
                <TableCell>${formatPrice(order.limit_price)}</TableCell>
                <TableCell>
                  <Chip 
                    label={order.state}
                    color={getStatusColor(order.state)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{formatDateTime(order.created_at)}</TableCell>
                <TableCell>
                  <IconButton 
                    onClick={() => handleCancelOrder(order.id, order.product_id)}
                    size="small"
                    color="error"
                  >
                    <CancelIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      {liveOrders.length === 0 && (
        <Alert severity="info">No live orders</Alert>
      )}
    </Box>
  );

  const renderPositions = () => (
    <Box sx={{ mt: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Positions</Typography>
        <IconButton onClick={fetchPositions} size="small">
          <RefreshIcon />
        </IconButton>
      </Box>
      
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Symbol</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Entry Price</TableCell>
              <TableCell>Liquidation Price</TableCell>
              <TableCell>Realized PnL</TableCell>
              <TableCell>Margin</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {positions.map((position) => (
              <TableRow key={position.product_id}>
                <TableCell>{position.product_symbol}</TableCell>
                <TableCell>
                  <Chip 
                    label={position.size}
                    color={position.size > 0 ? 'success' : 'error'}
                    size="small"
                  />
                </TableCell>
                <TableCell>${formatPrice(position.entry_price)}</TableCell>
                <TableCell>${formatPrice(position.liquidation_price)}</TableCell>
                <TableCell>
                  <Chip 
                    label={`$${formatPrice(position.realized_pnl)}`}
                    color={position.realized_pnl >= 0 ? 'success' : 'error'}
                    size="small"
                  />
                </TableCell>
                <TableCell>${formatPrice(position.margin)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      {positions.length === 0 && (
        <Alert severity="info">No open positions</Alert>
      )}
    </Box>
  );

  return (
    <Paper sx={{ p: 3, height: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <SendIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6">Trading Panel</Typography>
        <Box sx={{ ml: 'auto' }}>
          <FormControlLabel
            control={
              <Switch
                checked={demoMode}
                onChange={(e) => setDemoMode(e.target.checked)}
                color="primary"
              />
            }
            label="Demo Mode"
          />
        </Box>
      </Box>

      {demoMode && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Demo mode is enabled. Orders will be simulated and not sent to the exchange.
        </Alert>
      )}

      {!isConnected && (
        <Alert severity="warning">
          Connect to Delta Exchange to start trading
        </Alert>
      )}

      {isConnected && (
        <Box>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="trading tabs">
            <Tab label="Place Order" />
            <Tab label={`Live Orders ${demoMode ? '(Demo)' : ''}`} />
            <Tab label={`Positions ${demoMode ? '(Demo)' : ''}`} />
          </Tabs>

          {tabValue === 0 && renderOrderForm()}
          {tabValue === 1 && renderLiveOrders()}
          {tabValue === 2 && renderPositions()}
        </Box>
      )}
    </Paper>
  );
};

export default TradingPanel;

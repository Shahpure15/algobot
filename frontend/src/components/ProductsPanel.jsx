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
  FormControlLabel,
  Card,
  CardContent,
  CardActions,
  InputAdornment,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import { 
  Search as SearchIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  ExpandMore as ExpandMoreIcon,
  ShowChart as ShowChartIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import axios from 'axios';

const ProductsPanel = ({ isConnected, onError }) => {
  const [tabValue, setTabValue] = useState(0);
  const [demoMode, setDemoMode] = useState(false);
  const [products, setProducts] = useState([]);
  const [tickers, setTickers] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    contract_types: '',
    states: 'live',
    underlying_asset_symbols: ''
  });

  // Load products and tickers on component mount
  useEffect(() => {
    if (isConnected) {
      loadProducts();
      loadTickers();
    }
  }, [isConnected, demoMode]);

  const loadProducts = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const endpoint = demoMode ? '/api/trading/demo-products' : '/api/trading/products';
      const params = demoMode ? {} : filters;
      
      const response = await axios.get(endpoint, { params });
      
      if (response.data.success) {
        setProducts(response.data.result || []);
      } else {
        throw new Error(response.data.error || 'Failed to load products');
      }
    } catch (err) {
      console.error('Error loading products:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load products');
      onError && onError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadTickers = async () => {
    try {
      const endpoint = demoMode ? '/api/trading/demo-tickers' : '/api/trading/tickers';
      const params = demoMode ? {} : {
        contract_types: filters.contract_types,
        underlying_asset_symbols: filters.underlying_asset_symbols
      };
      
      const response = await axios.get(endpoint, { params });
      
      if (response.data.success) {
        setTickers(response.data.result || []);
      } else {
        throw new Error(response.data.error || 'Failed to load tickers');
      }
    } catch (err) {
      console.error('Error loading tickers:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load tickers');
    }
  };

  const loadProductDetails = async (symbol) => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/trading/products/${symbol}`);
      
      if (response.data.success) {
        setSelectedProduct(response.data.result);
      } else {
        throw new Error(response.data.error || 'Failed to load product details');
      }
    } catch (err) {
      console.error('Error loading product details:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load product details');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleDemoModeChange = (event) => {
    setDemoMode(event.target.checked);
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSearch = () => {
    loadProducts();
    loadTickers();
  };

  const handleRefresh = () => {
    loadProducts();
    loadTickers();
  };

  const filteredProducts = products.filter(product =>
    product.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getTickerForProduct = (symbol) => {
    return tickers.find(ticker => ticker.symbol === symbol);
  };

  const formatPrice = (price) => {
    if (!price) return 'N/A';
    return typeof price === 'number' ? price.toFixed(2) : parseFloat(price).toFixed(2);
  };

  const formatPercent = (value) => {
    if (!value) return 'N/A';
    const percent = ((value - 1) * 100).toFixed(2);
    return `${percent}%`;
  };

  const getPriceColor = (current, previous) => {
    if (!current || !previous) return 'inherit';
    return current > previous ? 'green' : current < previous ? 'red' : 'inherit';
  };

  const renderProductsTab = () => (
    <Box>
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={3}>
          <TextField
            fullWidth
            label="Search Products"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <FormControl fullWidth>
            <InputLabel>Contract Types</InputLabel>
            <Select
              value={filters.contract_types}
              onChange={(e) => handleFilterChange('contract_types', e.target.value)}
              label="Contract Types"
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="perpetual_futures">Perpetual Futures</MenuItem>
              <MenuItem value="futures">Futures</MenuItem>
              <MenuItem value="call_options">Call Options</MenuItem>
              <MenuItem value="put_options">Put Options</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={3}>
          <FormControl fullWidth>
            <InputLabel>States</InputLabel>
            <Select
              value={filters.states}
              onChange={(e) => handleFilterChange('states', e.target.value)}
              label="States"
            >
              <MenuItem value="live">Live</MenuItem>
              <MenuItem value="expired">Expired</MenuItem>
              <MenuItem value="upcoming">Upcoming</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={3}>
          <Button
            variant="contained"
            onClick={handleSearch}
            disabled={loading}
            startIcon={<SearchIcon />}
            sx={{ mr: 1 }}
          >
            Search
          </Button>
          <Button
            variant="outlined"
            onClick={handleRefresh}
            disabled={loading}
            startIcon={<RefreshIcon />}
          >
            Refresh
          </Button>
        </Grid>
      </Grid>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Symbol</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>State</TableCell>
              <TableCell>Tick Size</TableCell>
              <TableCell>Initial Margin</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredProducts.map((product) => (
              <TableRow key={product.id}>
                <TableCell>
                  <strong>{product.symbol}</strong>
                </TableCell>
                <TableCell>{product.description}</TableCell>
                <TableCell>
                  <Chip 
                    label={product.contract_type?.replace('_', ' ').toUpperCase() || 'N/A'}
                    color="primary"
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip 
                    label={product.state?.toUpperCase() || 'N/A'}
                    color={product.state === 'live' ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>{product.tick_size || 'N/A'}</TableCell>
                <TableCell>{product.initial_margin || 'N/A'}</TableCell>
                <TableCell>
                  <Button
                    size="small"
                    onClick={() => loadProductDetails(product.symbol)}
                    startIcon={<ShowChartIcon />}
                  >
                    Details
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  const renderTickersTab = () => (
    <Box>
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            label="Search Tickers"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            label="Underlying Assets"
            value={filters.underlying_asset_symbols}
            onChange={(e) => handleFilterChange('underlying_asset_symbols', e.target.value)}
            placeholder="e.g., BTC,ETH,SOL"
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <Button
            variant="contained"
            onClick={handleSearch}
            disabled={loading}
            startIcon={<RefreshIcon />}
          >
            Refresh
          </Button>
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        {tickers.filter(ticker => 
          ticker.symbol.toLowerCase().includes(searchTerm.toLowerCase())
        ).map((ticker) => (
          <Grid item xs={12} md={6} lg={4} key={ticker.symbol}>
            <Card>
              <CardContent>
                <Typography variant="h6" component="div">
                  {ticker.symbol}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Product ID: {ticker.product_id}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Typography variant="h5" component="div">
                    ${formatPrice(ticker.close)}
                  </Typography>
                  <Typography 
                    variant="body2" 
                    color={getPriceColor(ticker.close, ticker.open)}
                  >
                    {ticker.close > ticker.open ? (
                      <TrendingUpIcon fontSize="small" />
                    ) : (
                      <TrendingDownIcon fontSize="small" />
                    )}
                    {formatPercent(ticker.close / ticker.open)}
                  </Typography>
                </Box>
                <Divider sx={{ my: 1 }} />
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">
                    High: ${formatPrice(ticker.high)}
                  </Typography>
                  <Typography variant="body2">
                    Low: ${formatPrice(ticker.low)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">
                    Volume: {ticker.volume?.toLocaleString() || 'N/A'}
                  </Typography>
                  <Typography variant="body2">
                    OI: {ticker.oi?.toLocaleString() || 'N/A'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  const renderProductDetails = () => {
    if (!selectedProduct) return null;

    return (
      <Box sx={{ mt: 2 }}>
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">Product Details: {selectedProduct.symbol}</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography><strong>ID:</strong> {selectedProduct.id}</Typography>
                <Typography><strong>Description:</strong> {selectedProduct.description}</Typography>
                <Typography><strong>Contract Type:</strong> {selectedProduct.contract_type}</Typography>
                <Typography><strong>State:</strong> {selectedProduct.state}</Typography>
                <Typography><strong>Trading Status:</strong> {selectedProduct.trading_status}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography><strong>Tick Size:</strong> {selectedProduct.tick_size}</Typography>
                <Typography><strong>Contract Value:</strong> {selectedProduct.contract_value}</Typography>
                <Typography><strong>Initial Margin:</strong> {selectedProduct.initial_margin}</Typography>
                <Typography><strong>Maintenance Margin:</strong> {selectedProduct.maintenance_margin}</Typography>
                <Typography><strong>Taker Commission:</strong> {selectedProduct.taker_commission_rate}</Typography>
                <Typography><strong>Maker Commission:</strong> {selectedProduct.maker_commission_rate}</Typography>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      </Box>
    );
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" component="h2">
          Products & Markets
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <FormControlLabel
            control={
              <Switch
                checked={demoMode}
                onChange={handleDemoModeChange}
                color="primary"
              />
            }
            label="Demo Mode"
          />
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!isConnected && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Not connected to Delta Exchange. Please check your API configuration.
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Products" icon={<AssessmentIcon />} />
          <Tab label="Tickers" icon={<TimelineIcon />} />
        </Tabs>
      </Box>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      )}

      {tabValue === 0 && renderProductsTab()}
      {tabValue === 1 && renderTickersTab()}
      {renderProductDetails()}
    </Paper>
  );
};

export default ProductsPanel;

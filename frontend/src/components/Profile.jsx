import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Tabs,
  Tab,
  Alert,
  Grid,
  Paper,
  IconButton,
  AppBar,
  Toolbar,
  Chip,
  Divider,
  CircularProgress
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Person as PersonIcon,
  Key as KeyIcon,
  Lock as LockIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Delete as DeleteIcon,
  PlayArrow as TestIcon
} from '@mui/icons-material';

// Tab panel component - moved outside to prevent re-creation on every render
const TabPanel = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
  </div>
);

const Profile = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Form states
  const [profileForm, setProfileForm] = useState({
    email: '',
    full_name: ''
  });
  
  const [credentialsForm, setCredentialsForm] = useState({
    credential_name: '',
    api_key: '',
    api_secret: ''
  });
  
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  
  const [activeTab, setActiveTab] = useState(0);
  const [testing, setTesting] = useState(false);

  // Load profile data
  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/profile/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to load profile');
      }
      
      const data = await response.json();
      setProfile(data);
      setProfileForm({
        email: data.email || '',
        full_name: data.full_name || ''
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/profile/', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profileForm)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update profile');
      }
      
      const data = await response.json();
      setProfile(data);
      setSuccess('Profile updated successfully');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateCredentials = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/profile/credentials', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          provider: 'delta_exchange',
          credential_name: credentialsForm.credential_name,
          api_key: credentialsForm.api_key,
          api_secret: credentialsForm.api_secret
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update credentials');
      }
      
      const data = await response.json();
      
      if (data.is_connected) {
        setSuccess('API credentials saved and connection test successful!');
      } else {
        setSuccess('API credentials saved, but connection test failed. Please verify your credentials.');
      }
      
      setCredentialsForm({ credential_name: '', api_key: '', api_secret: '' });
      loadProfile(); // Reload to show updated credentials
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async () => {
    try {
      setTesting(true);
      setError(null);
      setSuccess(null);
      
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/profile/test-connection/delta_exchange', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSuccess('Connection test successful!');
      } else {
        setError(data.message || 'Connection test failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setTesting(false);
    }
  };

  const deleteCredentials = async () => {
    if (!window.confirm('Are you sure you want to delete your API credentials?')) {
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const response = await fetch('/api/profile/credentials/delta_exchange', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete credentials');
      }
      
      setSuccess('API credentials deleted successfully');
      loadProfile(); // Reload to show updated credentials
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const updatePassword = async (e) => {
    e.preventDefault();
    
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setError('New passwords do not match');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/profile/password', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          current_password: passwordForm.current_password,
          new_password: passwordForm.new_password
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update password');
      }
      
      setSuccess('Password updated successfully');
      setPasswordForm({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !profile) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      {/* Header */}
      <AppBar position="static" sx={{ backgroundColor: '#2196f3' }}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => navigate('/dashboard')}
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Profile Settings
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Alerts */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        {/* Main Content */}
        <Paper elevation={2} sx={{ borderRadius: 2 }}>
          {/* Tabs */}
          <Tabs 
            value={activeTab} 
            onChange={(e, newValue) => setActiveTab(newValue)}
            variant="fullWidth"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab icon={<PersonIcon />} label="Profile" />
            <Tab icon={<KeyIcon />} label="API Credentials" />
            <Tab icon={<LockIcon />} label="Password" />
          </Tabs>

          {/* Profile Tab */}
          <TabPanel value={activeTab} index={0}>
            <Box sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                Profile Information
              </Typography>
              <form onSubmit={updateProfile}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Username"
                      value={profile?.username || ''}
                      disabled
                      helperText="Username cannot be changed"
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Email"
                      type="email"
                      value={profileForm.email}
                      onChange={(e) => setProfileForm({...profileForm, email: e.target.value})}
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Full Name"
                      value={profileForm.full_name}
                      onChange={(e) => setProfileForm({...profileForm, full_name: e.target.value})}
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={loading}
                      startIcon={loading ? <CircularProgress size={20} /> : <PersonIcon />}
                    >
                      {loading ? 'Updating...' : 'Update Profile'}
                    </Button>
                  </Grid>
                </Grid>
              </form>
            </Box>
          </TabPanel>

          {/* API Credentials Tab */}
          <TabPanel value={activeTab} index={1}>
            <Box sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                API Credentials
              </Typography>
              
              {/* Current Credentials */}
              {profile?.credentials?.length > 0 && (
                <Box sx={{ mb: 4 }}>
                  <Typography variant="h6" gutterBottom>
                    Current Credentials
                  </Typography>
                  {profile.credentials.map((cred) => (
                    <Card key={cred.id} sx={{ mb: 2 }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <Box>
                            <Typography variant="h6" gutterBottom>
                              {cred.credential_name}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Provider: {cred.provider}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              API Key: {cred.api_key}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Created: {new Date(cred.created_at).toLocaleDateString()}
                            </Typography>
                            {cred.last_used && (
                              <Typography variant="body2" color="text.secondary">
                                Last used: {new Date(cred.last_used).toLocaleDateString()}
                              </Typography>
                            )}
                            <Chip
                              label={cred.is_active ? 'Active' : 'Inactive'}
                              color={cred.is_active ? 'success' : 'default'}
                              size="small"
                              sx={{ mt: 1 }}
                            />
                          </Box>
                          <Box>
                            <Button
                              variant="outlined"
                              color="success"
                              size="small"
                              startIcon={testing ? <CircularProgress size={16} /> : <TestIcon />}
                              onClick={testConnection}
                              disabled={testing}
                              sx={{ mr: 1 }}
                            >
                              {testing ? 'Testing...' : 'Test'}
                            </Button>
                            <Button
                              variant="outlined"
                              color="error"
                              size="small"
                              startIcon={<DeleteIcon />}
                              onClick={deleteCredentials}
                            >
                              Delete
                            </Button>
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
              
              <Divider sx={{ my: 3 }} />
              
              {/* Add/Update Credentials Form */}
              <Box>
                <Typography variant="h6" gutterBottom>
                  {profile?.credentials?.length > 0 ? 'Update' : 'Add'} Delta Exchange Credentials
                </Typography>
                <form onSubmit={updateCredentials}>
                  <Grid container spacing={3}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Credential Name"
                        value={credentialsForm.credential_name}
                        onChange={(e) => setCredentialsForm({...credentialsForm, credential_name: e.target.value})}
                        placeholder="Enter a name for this API key (e.g., 'Main Trading Account')"
                        required
                      />
                    </Grid>
                    
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="API Key"
                        value={credentialsForm.api_key}
                        onChange={(e) => setCredentialsForm({...credentialsForm, api_key: e.target.value})}
                        placeholder="Enter your Delta Exchange API key"
                        required
                      />
                    </Grid>
                    
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="API Secret"
                        type="password"
                        value={credentialsForm.api_secret}
                        onChange={(e) => setCredentialsForm({...credentialsForm, api_secret: e.target.value})}
                        placeholder="Enter your Delta Exchange API secret"
                        required
                      />
                    </Grid>
                    
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', gap: 2 }}>
                        <Button
                          type="submit"
                          variant="contained"
                          disabled={loading}
                          startIcon={loading ? <CircularProgress size={20} /> : <KeyIcon />}
                        >
                          {loading ? 'Testing & Saving...' : 'Test & Save Credentials'}
                        </Button>
                      </Box>
                    </Grid>
                  </Grid>
                </form>
                
                <Alert severity="warning" sx={{ mt: 3 }}>
                  <Typography variant="body2">
                    <strong>Important:</strong> Your API credentials are unique to your account. 
                    Each API key can only be used by one user. Make sure to use your own Delta Exchange API keys.
                  </Typography>
                </Alert>
              </Box>
            </Box>
          </TabPanel>

          {/* Password Tab */}
          <TabPanel value={activeTab} index={2}>
            <Box sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                Change Password
              </Typography>
              <form onSubmit={updatePassword}>
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Current Password"
                      type="password"
                      value={passwordForm.current_password}
                      onChange={(e) => setPasswordForm({...passwordForm, current_password: e.target.value})}
                      required
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="New Password"
                      type="password"
                      value={passwordForm.new_password}
                      onChange={(e) => setPasswordForm({...passwordForm, new_password: e.target.value})}
                      inputProps={{ minLength: 8 }}
                      required
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Confirm New Password"
                      type="password"
                      value={passwordForm.confirm_password}
                      onChange={(e) => setPasswordForm({...passwordForm, confirm_password: e.target.value})}
                      inputProps={{ minLength: 8 }}
                      required
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={loading}
                      startIcon={loading ? <CircularProgress size={20} /> : <LockIcon />}
                    >
                      {loading ? 'Updating...' : 'Update Password'}
                    </Button>
                  </Grid>
                </Grid>
              </form>
            </Box>
          </TabPanel>
        </Paper>
      </Container>
    </Box>
  );
};

export default Profile;

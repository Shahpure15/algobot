import React, { createContext, useState, useContext, useEffect } from 'react';
import apiService from '../services/api';

// Create the context
const AuthContext = createContext(null);

// Provider component that wraps the app and makes auth available
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initialize - check if user is logged in
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const lastActivity = localStorage.getItem('last_activity');
        const sessionTimeout = 4 * 60 * 60 * 1000; // 4 hours in milliseconds
        
        // Check if token exists and session hasn't timed out
        if (token && lastActivity && (Date.now() - parseInt(lastActivity)) < sessionTimeout) {
          // Update last activity time
          localStorage.setItem('last_activity', Date.now().toString());
          
          // Validate the token and get user info
          const response = await apiService.auth.me();
          setUser(response.data);
        } else if (token) {
          // Session has timed out
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
          localStorage.removeItem('last_activity');
          setError('Session expired. Please login again.');
        }
      } catch (err) {
        // Clear local storage if token is invalid
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        localStorage.removeItem('last_activity');
        console.error('Authentication error:', err);
        setError('Session expired. Please login again.');
      } finally {
        setLoading(false);
      }
    };

    initAuth();
    
    // Set up periodic token validation (every 5 minutes)
    const interval = setInterval(initAuth, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);

  // Login function
  const login = async (credentials) => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.auth.login(credentials);
      
      const { access_token, user } = response.data;
      
      // Store token and user in localStorage, along with activity timestamp
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('last_activity', Date.now().toString());
      
      // Update state
      setUser(user);
      return user;
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Register function
  const register = async (userData) => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.auth.register(userData);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Logout function
  const logout = async () => {
    try {
      // Call logout endpoint to invalidate token on server
      await apiService.auth.logout();
    } catch (error) {
      console.error('Error logging out on server:', error);
    }
    
    // Clear local storage regardless of server response
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    localStorage.removeItem('last_activity');
    setUser(null);
  };

  // Connect exchange function
  const connectExchange = async (credentials) => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.auth.connect(credentials);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to connect exchange. Please check your credentials.');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Disconnect exchange function
  const disconnectExchange = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.auth.disconnect();
      return response.data;
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to disconnect exchange.');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Check exchange connection status
  const checkConnectionStatus = async () => {
    try {
      const response = await apiService.auth.status();
      return response.data;
    } catch (err) {
      console.error('Failed to check connection status:', err);
      return { connected: false };
    }
  };

  // Context value
  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    connectExchange,
    disconnectExchange,
    checkConnectionStatus,
  };

  // Provide the context to children components
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};


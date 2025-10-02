// src/api/AuthContext.jsx
import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import axios from "axios";
import { authApi } from './axios.jsx';
import { 
  hasAccessToken, 
  getAccessToken,
  setAccessToken,
  removeAccessToken,
  getUserFromToken,
  hasSystemRole,
  hasAnySystemRole
} from './TokenUtils';

const AuthContext = createContext();
const AUTH_URL = import.meta.env.VITE_AUTH_URL || "/api/v1";

// Add a module-level rate limiter for profile requests
let lastProfileCheck = 0;
const PROFILE_CHECK_COOLDOWN = 2000; // 2 second minimum between profile checks

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);
  const [refreshAttempted, setRefreshAttempted] = useState(false);
  const [lastCheckTime, setLastCheckTime] = useState(0);
  
  // Use a ref to track pending promises to prevent race conditions
  const pendingAuthCheck = useRef(null);
  // Track the last profile request time
  const lastProfileRequest = useRef(0);

  // Check if user has admin role for TTS system
  const isAdmin = useCallback(() => {
    return user && hasSystemRole(user, 'tts', 'Admin');
  }, [user]);
  
  // Check if user has any role for TTS system
  const hasTtsAccess = useCallback(() => {
    return user && hasAnySystemRole(user, 'tts');
  }, [user]);

  // Helper function to verify token with the auth service
  const verifyToken = useCallback(async () => {
    try {
      const token = getAccessToken();
      if (!token) return false;
      
      // Call the token verify endpoint with correct URL path including api/v1
      const response = await authApi.post(`${AUTH_URL}/api/v1/token/verify/`, { token });
      console.log('Token verification response:', response.status);
      return response.status === 200;
    } catch (error) {
      console.error("Token verification failed:", error);
      return false;
    }
  }, []);

  // Rate-limited profile fetch
  const fetchUserProfile = useCallback(async (force = false) => {
    const now = Date.now();
    // Check if we should throttle requests
    if (!force && now - lastProfileRequest.current < PROFILE_CHECK_COOLDOWN) {
      throw new Error('Rate limited');
    }
    
    lastProfileRequest.current = now;
    lastProfileCheck = now; // Update module-level tracker too
    
    // Extract user data from token
    const userData = getUserFromToken();
    if (userData) {
      return userData;
    }
    throw new Error('No valid user data in token');
  }, []);

  // Check auth status and update user state
  const checkAuthStatus = useCallback(async (force = false) => {
    console.log('Checking authentication status...');
    
    // Don't make multiple simultaneous auth checks unless forced
    if (!force && loading && initialized) return false;
    
    // Add a cooldown period to prevent rapid firing, unless forced
    const now = Date.now();
    if (!force && now - lastCheckTime < 1000) {
      return !!user; // Return current auth state during cooldown
    }
    setLastCheckTime(now);
    
    if (!hasAccessToken()) {
      console.log('No access token found');
      setUser(null);
      setLoading(false);
      setInitialized(true);
      return false;
    }
    
    // If we already have a pending auth check, use that instead of creating a new one
    if (pendingAuthCheck.current && !force) {
      return pendingAuthCheck.current;
    }

    // Create a new promise for this auth check
    const authCheckPromise = (async () => {
      try {
        // Log the token to help with debugging
        console.log('Current token:', getAccessToken());
        
        // Verify token with auth service
        const isValid = await verifyToken();
        console.log('Token is valid:', isValid);
        
        if (isValid) {
          // Use our rate-limited profile fetch
          try {
            const userData = await fetchUserProfile(force);
            console.log('User data retrieved:', userData);
            setUser(userData);
            setLoading(false);
            setInitialized(true);
            return true;
          } catch (error) {
            if (error.message === 'Rate limited') {
              // Return current auth state if rate limited
              return !!user;
            }
            
            // If we get a verification failure, try refreshing the token before giving up
            if (!refreshAttempted) {
              try {
                // Try to refresh token
                console.log('Attempting to refresh token...');
                const refreshResponse = await authApi.post(`${AUTH_URL}/token/refresh/`);
                
                if (refreshResponse.data && refreshResponse.data.access) {
                  // Save new token to localStorage
                  setAccessToken(refreshResponse.data.access);
                  setRefreshAttempted(true);
                  
                  // Try profile again after refresh
                  try {
                    const userData = await fetchUserProfile(true); // Force fetch after refresh
                    setUser(userData);
                    setLoading(false);
                    setInitialized(true);
                    return true;
                  } catch (profileError) {
                    if (profileError.message === 'Rate limited') {
                      return !!user;
                    }
                    removeAccessToken();
                    setUser(null);
                    setLoading(false);
                    setInitialized(true);
                    return false;
                  }
                }
              } catch (refreshError) {
                console.error("Token refresh failed:", refreshError);
                // Refresh failed, user is not authenticated
                removeAccessToken();
                setUser(null);
                setLoading(false);
                setInitialized(true);
                return false;
              }
            }
          }
        }
        
        // Token invalid or couldn't extract user data
        console.log('Token is invalid or user data extraction failed');
        removeAccessToken();
        setUser(null);
        setLoading(false);
        setInitialized(true);
        return false;
      } catch (error) {
        console.error("Auth check failed:", error);
        removeAccessToken();
        setUser(null);
        setLoading(false);
        setInitialized(true);
        return false;
      } finally {
        // Clear the pending promise reference when done
        pendingAuthCheck.current = null;
      }
    })();

    // Store the promise in our ref
    pendingAuthCheck.current = authCheckPromise;
    return authCheckPromise;
  }, [verifyToken, fetchUserProfile, loading, initialized, refreshAttempted, lastCheckTime, user]);

  // Initial authentication check on component mount
  useEffect(() => {
    const initialCheck = async () => {
      // Force an immediate check regardless of cooldown
      await checkAuthStatus(true);
      setRefreshAttempted(false); // Reset for future checks
    };
    
    initialCheck();
  }, []); // Only run once on mount

  // Periodically check auth status to prevent session timeout issues
  useEffect(() => {
    // Only run this if user is already authenticated
    if (!user) return;
    
    // Set up a periodic refresh every 10 minutes
    const refreshInterval = setInterval(() => {
      authApi.post(`${AUTH_URL}/token/refresh/`)
        .then(response => {
          if (response.data && response.data.access) {
            setAccessToken(response.data.access);
          }
        })
        .catch(() => {
          // If refresh fails, check auth status
          checkAuthStatus(true); // Force check to immediately update UI
        });
    }, 10 * 60 * 1000); // 10 minutes
    
    return () => clearInterval(refreshInterval);
  }, [user, checkAuthStatus]);

  // Function to get the current token - useful for components that need direct token access
  const getToken = useCallback(() => {
    return getAccessToken();
  }, []);

  // Refresh auth data
  const refreshAuth = useCallback(async () => {
    // Only refresh if enough time has passed since last profile check
    const now = Date.now();
    if (now - lastProfileCheck < PROFILE_CHECK_COOLDOWN) {
      return !!user; // Return current auth state if we're rate limited
    }
    
    setLoading(true);
    try {
      const result = await checkAuthStatus(true); // Force refresh
      return result;
    } finally {
      setLoading(false);
    }
  }, [checkAuthStatus, user]);

  // Login function
  const login = async (credentials) => {
    try {
      // Log the credentials being sent (without the password for security)
      console.log('Sending login request with email:', credentials.email);
      
      // Format the login data exactly as expected by the backend
      const loginData = {
        email: credentials.email, 
        password: credentials.password,
      };
      
      console.log('Sending login data with fields:', Object.keys(loginData).join(', '));
      
      // Use the correct URL with api/v1 prefix
      const baseUrl = import.meta.env.VITE_AUTH_URL || "";
      const tokenUrl = `${baseUrl}/api/v1/token/obtain/`;
      
      console.log('Sending login request to:', tokenUrl);
      
      // Create a separate axios instance for this specific request with more detailed logging
      const response = await axios.post(tokenUrl, loginData, {
        withCredentials: true,
        headers: {
          "Content-Type": "application/json",
        }
      });
      
      console.log('Login response:', response);
      
      // Check if we have access token in the response
      if (response.data && response.data.access) {
        // Save token to localStorage
        setAccessToken(response.data.access);
      } else {
        console.log('No access token in response data, checking cookies');
      }
      
      // Immediately verify and get user data
      await checkAuthStatus(true);
      
      // Get user data from token
      const userData = getUserFromToken();
      if (userData) {
        console.log('User authenticated successfully:', userData);
        setUser(userData);
        setInitialized(true);
        setLoading(false);
        setRefreshAttempted(false);
        return { success: true };
      } else {
        console.error("Failed to extract user data from token");
        return { 
          success: false, 
          error: "Authentication succeeded but failed to get user data" 
        };
      }
    } catch (error) {
      console.error("Login failed:", error);
      
      // Add more detailed debugging for the error response
      if (error.response) {
        console.error("Status:", error.response.status);
        console.error("Headers:", error.response.headers);
        console.error("Data:", error.response.data);
      } else if (error.request) {
        console.error("Request was made but no response received:", error.request);
      } else {
        console.error("Error setting up the request:", error.message);
      }
      
      // Extract the most useful error message from the response
      let errorDetail = "Login failed. Please check your credentials.";
      
      if (error.response?.data) {
        console.error("Error response data:", error.response.data);
        
        // Check various possible error fields
        if (typeof error.response.data === 'string') {
          errorDetail = error.response.data;
        } else if (error.response.data.detail) {
          errorDetail = error.response.data.detail;
        } else if (error.response.data.non_field_errors) {
          errorDetail = Array.isArray(error.response.data.non_field_errors) 
            ? error.response.data.non_field_errors.join(', ') 
            : error.response.data.non_field_errors;
        } else if (error.response.data.email) {
          errorDetail = Array.isArray(error.response.data.email)
            ? error.response.data.email.join(', ')
            : error.response.data.email;
        } else if (error.response.data.username) {
          errorDetail = Array.isArray(error.response.data.username)
            ? error.response.data.username.join(', ')
            : error.response.data.username;
        } else if (error.response.data.error_code === 'otp_required') {
          errorDetail = "OTP code is required. Please provide your 2FA code.";
        }
      }
      
      return { 
        success: false, 
        error: errorDetail
      };
    }
  };

  // Logout function
  const logout = async () => {
    try {
      // Try to call the logout endpoint if available
      await authApi.post(`${AUTH_URL}/logout/`, {}, {
        withCredentials: true
      }).catch(err => console.warn('Logout API call failed:', err));
    } finally {
      // Always clean up local state
      removeAccessToken();
      setUser(null);
      setInitialized(true); // Keep initialized true to avoid infinite checks
      setLoading(false);
      setRefreshAttempted(false);
      // Redirect to login page
      window.location.href = "/login";
    }
  };

  const value = {
    user,
    setUser,
    loading,
    logout,
    login,
    refreshAuth,
    initialized,
    hasAuth: !!user,
    isAdmin,
    hasTtsAccess,
    checkAuthStatus,
    getToken
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

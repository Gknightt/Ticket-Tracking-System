// src/api/AuthContext.jsx
import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import api from './axios.jsx'; // Use our configured axios instance
import { hasAccessToken, getAccessToken } from './TokenUtils'; // Import token utility functions

const AuthContext = createContext();

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

  // Rate-limited profile fetch
  const fetchProfile = useCallback(async (force = false) => {
    const now = Date.now();
    // Check if we should throttle requests
    if (!force && now - lastProfileRequest.current < PROFILE_CHECK_COOLDOWN) {
      throw new Error('Rate limited');
    }
    
    lastProfileRequest.current = now;
    lastProfileCheck = now; // Update module-level tracker too
    return api.get('users/profile/');
  }, []);

  // Helper function to check if user is authenticated via API call
  const checkAuthStatus = useCallback(async (force = false) => {
    // Don't make multiple simultaneous auth checks unless forced
    if (!force && loading && initialized) return false;
    
    // Add a cooldown period to prevent rapid firing, unless forced
    const now = Date.now();
    if (!force && now - lastCheckTime < 1000) {
      return !!user; // Return current auth state during cooldown
    }
    setLastCheckTime(now);
    
    // First check if we have a token in cookies
    if (!hasAccessToken()) {
      setUser(null);
      return false;
    }
    
    // If we already have a pending auth check, use that instead of creating a new one
    if (pendingAuthCheck.current && !force) {
      return pendingAuthCheck.current;
    }

    // Create a new promise for this auth check
    const authCheckPromise = (async () => {
      try {
        // Now with non-HTTP-only cookies, we can check for them via document.cookie
        // But we still make an API request to verify the token is valid
        // Use our rate-limited profile fetch
        try {
          const response = await fetchProfile(force);
          setUser(response.data);
          return true;
        } catch (error) {
          if (error.message === 'Rate limited') {
            // Return current auth state if rate limited
            return !!user;
          }
          
          // If we get a 401, try refreshing the token first before giving up
          if (error.response?.status === 401 && !refreshAttempted) {
            try {
              // Try to refresh token
              await api.post('token/refresh/');
              setRefreshAttempted(true);
              
              // Try profile again after refresh
              try {
                const retryResponse = await fetchProfile(true); // Force fetch after refresh
                setUser(retryResponse.data);
                return true;
              } catch (profileError) {
                if (profileError.message === 'Rate limited') {
                  return !!user;
                }
                setUser(null);
                return false;
              }
            } catch (refreshError) {
              // Refresh failed, user is not authenticated
              setUser(null);
              return false;
            }
          } else {
            setUser(null);
            return false;
          }
        }
      } finally {
        // Clear the pending promise reference when done
        pendingAuthCheck.current = null;
      }
    })();

    // Store the promise in our ref
    pendingAuthCheck.current = authCheckPromise;
    return authCheckPromise;
  }, [loading, initialized, refreshAttempted, lastCheckTime, user, fetchProfile]);

  // Initial authentication check on app load
  useEffect(() => {
    const initialCheck = async () => {
      // Force an immediate check regardless of cooldown
      await checkAuthStatus(true);
      setLoading(false);
      setInitialized(true);
      setRefreshAttempted(false); // Reset for future checks
    };
    
    initialCheck();
  }, []); // Only run once on mount

  // Periodically check auth status to prevent session timeout issues
  useEffect(() => {
    // Only run this if user is already authenticated
    if (!user) return;
    
    // Set up a periodic refresh every 10 minutes (reduced from 14 for better responsiveness)
    // This is a long interval and won't cause request bursts
    const refreshInterval = setInterval(() => {
      api.post('token/refresh/')
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

  const logout = useCallback(async () => {
    try {
      // Call the backend logout endpoint to clear cookies
      await api.post('users/logout/');
    } catch (error) {
      // Continue with logout even if API call fails
      console.error("Logout API call failed:", error);
    } finally {
      // Clear user state regardless of API call success
      setUser(null);
      setInitialized(true); // Keep initialized true to avoid infinite checks
      setLoading(false);
      setRefreshAttempted(false);
      
      // Force a page reload if needed to clear any lingering state
      // Uncomment if state issues persist after logout
      // window.location.replace('/login');
    }
  }, []);

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

  const login = useCallback((userData) => {
    setUser(userData);
    setInitialized(true);
    setLoading(false);
    setRefreshAttempted(false);
  }, []);

  return (
    <AuthContext.Provider value={{ 
      user, 
      setUser,
      loading, 
      logout, 
      refreshAuth,
      checkAuthStatus,
      login,
      initialized,
      hasAuth: !!user,
      getToken
    }}>
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

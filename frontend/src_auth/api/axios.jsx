// src/api/axios.js
import axios from "axios";
import { getAccessToken } from './TokenUtils'; // Import token utility function

// Use the AUTH_URL which already includes the /api/v1/ prefix
const api = axios.create({
  baseURL: import.meta.env.VITE_AUTH_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Keep this to ensure cookies are still sent
});

// Helper function to get cookie value by name
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

// Add request interceptor to include CSRF token and JWT token
api.interceptors.request.use(
  (config) => {
    // Get CSRF token from cookie
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    
    // Get JWT token from cookie and add to Authorization header
    const accessToken = getAccessToken();
    if (accessToken) {
      config.headers['Authorization'] = `Bearer ${accessToken}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Track if we're currently refreshing to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let failedQueue = [];
// Add refresh cooldown tracking
let lastRefreshAttempt = 0;
const REFRESH_COOLDOWN = 1000; // Reduced to 1 second to improve responsiveness

// Process the queued requests after refresh
const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  failedQueue = [];
};

// Add response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const now = Date.now();
    
    // If we get 401 and haven't already tried to refresh, and it's not the refresh endpoint itself
    if (error.response?.status === 401 && 
        !originalRequest._retry && 
        !originalRequest.url?.includes('/token/refresh/')) {
      
      // Check cooldown period - shorter cooldown for better responsiveness
      if (now - lastRefreshAttempt < REFRESH_COOLDOWN) {
        return Promise.reject(error);
      }
      
      if (isRefreshing) {
        // If we're already refreshing, queue this request instead of making multiple refresh calls
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => {
          // After token is refreshed, retry with new token in header
          const newToken = getAccessToken();
          if (newToken) {
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
          }
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;
      lastRefreshAttempt = now;

      try {
        // Try to refresh token
        await api.post('token/refresh/');
        
        // Get the new token from cookie after refresh
        const newToken = getAccessToken();
        if (newToken) {
          originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
        }
        
        // Process any queued requests
        processQueue(null, newToken);
        
        // Retry the original request
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed
        processQueue(refreshError, null);
        
        // Only redirect if it's not already a login/auth page
        if (!window.location.pathname.includes('/login')) {
          // Use replace instead of href to avoid breaking browser history
          window.location.replace('/login');
        }
        
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;

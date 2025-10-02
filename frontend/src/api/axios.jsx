// src/api/axios.js
import axios from "axios";
import { getAccessToken } from "./TokenUtils";

const api = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_API,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Add withCredentials to send cookies with every request
});

// Add authentication header interceptor
api.interceptors.request.use(
  (config) => {
    // Get token from localStorage or cookies
    const token = getAccessToken();
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Handle unauthorized errors or expired tokens
    if (error.response && error.response.status === 401) {
      // Clear token on 401 errors
      localStorage.removeItem("accessToken");
      
      // Redirect to login if not already on login page
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// Create a separate instance for auth service
// Ensure the baseURL always includes api/v1
const authBaseURL = import.meta.env.VITE_AUTH_URL || "";
// Check if the URL already includes api/v1
const apiPrefix = authBaseURL.includes('/api/v1') ? '' : '/api/v1';

export const authApi = axios.create({
  baseURL: `${authBaseURL}${apiPrefix}`,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Add withCredentials to send cookies with every request
});

// Add same interceptors to authApi
authApi.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    console.log('AuthApi Request URL:', `${config.baseURL}${config.url}`);
    return config;
  },
  (error) => Promise.reject(error)
);

authApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    console.error('AuthApi Error:', error.config?.url, error.message, error.response?.status);
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("accessToken");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;

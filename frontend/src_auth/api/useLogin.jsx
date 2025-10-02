import { useState } from "react";
import api from "./axios.jsx"; // Use our configured axios instance
import { useAuth } from "./AuthContext.jsx";
import { getAccessToken } from './TokenUtils'; // Import token utility function

export function useLogin() {
  const { login: setAuthUser } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [showOTP, setShowOTP] = useState(false);
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      // Always try to login with the token obtain endpoint
      const loginData = { email, password };
      
      // If we're showing OTP screen, include the OTP code
      if (showOTP && otp) {
        loginData.otp_code = otp;
      }
      
      // Use correct path without the /api/v1 prefix since baseURL includes it
      const response = await api.post(`users/login/`, loginData);
      
      // Login successful - cookies are automatically set by the browser
      // We can now directly read the access token from the cookie
      const accessToken = getAccessToken();
      setToken(accessToken); // Store token in component state if needed
      
      // Extract user data from response
      const userData = response.data.user;
      setUser(userData);
      setSuccess(true);
      
      // Update the auth context with user data
      setAuthUser(userData);
      
      // Store only user email for convenience (not tokens)
      localStorage.setItem("userEmail", email);
      
    } catch (err) {
      const errorCode = err.response?.data?.error_code;
      const errorMessage = err.response?.data?.detail || err.response?.data?.message;
      const statusCode = err.response?.status;
      
      if (statusCode === 428) {
        // 428 status indicates 2FA is enabled - request OTP and show OTP screen
        try {
          await requestOTP();
          setShowOTP(true);
          setError("2FA is enabled for your account. Please enter the OTP code sent to your email.");
        } catch (otpError) {
          setError("Failed to send OTP. Please try again.");
        }
      } else if (errorCode === 'otp_required') {
        // Fallback for OTP required error code
        try {
          await requestOTP();
          setShowOTP(true);
          setError("Please enter the OTP code sent to your email.");
        } catch (otpError) {
          setError("Failed to send OTP. Please try again.");
        }
      } else if (errorCode === 'otp_invalid') {
        setError("Invalid or expired OTP code. Please try again.");
      } else if (errorCode === 'otp_expired') {
        setError("OTP code has expired. Please request a new one.");
      } else if (errorCode === 'account_locked') {
        setError("Account is locked due to too many failed login attempts. Please try again later.");
      } else {
        setError(errorMessage || "Invalid email or password.");
      }
      
      console.error("Login error:", err);
    } finally {
      setLoading(false);
    }
  };

  const requestOTP = async () => {
    try {
      // Use correct path without the /api/v1 prefix since baseURL includes it
      await api.post(`users/2fa/request-otp/`, { email, password });
      return true;
    } catch (err) {
      console.error("OTP request error:", err);
      throw err;
    }
  };

  const handleOTPSubmit = async (e) => {
    e.preventDefault();
    if (!otp.trim()) {
      setError("Please enter the OTP code.");
      return;
    }
    
    // Use the same login function but now with OTP
    await handleLogin(e);
  };

  const handleBackToLogin = (e) => {
    e.preventDefault();
    setShowOTP(false);
    setOtp("");
    setError(null);
    setSuccess(false);
    setLoading(false);
    // Keep email and password as they are
  };

  const handleResendOTP = async () => {
    setLoading(true);
    setError(null);
    
    try {
      await requestOTP();
      setError("OTP code has been resent to your email.");
    } catch (err) {
      setError("Failed to resend OTP. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      // Call the backend logout endpoint to clear cookies
      await api.post(`users/logout/`);
    } catch (err) {
      console.error("Logout error:", err);
    } finally {
      // Clear local state and localStorage
      localStorage.removeItem("userEmail");
      setSuccess(false);
      setUser(null);
      setEmail("");
      setPassword("");
      setOtp("");
      setError(null);
      setShowOTP(false);
    }
  };

  return {
    email,
    setEmail,
    password,
    setPassword,
    otp,
    setOtp,
    error,
    success,
    showOTP,
    loading,
    user,
    token, // Now exposing the token if needed
    handleLogin,
    handleOTPSubmit,
    handleBackToLogin,
    handleResendOTP,
    logout,
  };
}

import { useState } from "react";
import axios from "axios";
import { useAuth } from "./AuthContext";

const authURL = import.meta.env.VITE_AUTH_URL;

/**
 * Custom hook to handle login functionality
 * @returns {Object} Login state and handlers
 */
export const useLogin = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [showOTP, setShowOTP] = useState(false);
  const { login } = useAuth();

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setError(null);
    
    try {
      // First phase login - email and password
      const response = await axios.post(
        `${authURL}users/login/`,
        { email, password },
        { withCredentials: true }
      );
      
      if (response.data.requires_otp) {
        setShowOTP(true);
        return;
      }
      
      // No OTP required - standard login
      await login(response.data.access);
      setSuccess(true);
    } catch (err) {
      let errorMessage = "Login failed. Please check your credentials.";
      
      if (err.response && err.response.data && err.response.data.detail) {
        errorMessage = err.response.data.detail;
      }
      
      setError(errorMessage);
    }
  };

  const handleOTPSubmit = async (e) => {
    if (e) e.preventDefault();
    setError(null);
    
    try {
      const response = await axios.post(
        `${authURL}users/login/verify-otp/`,
        { email, otp },
        { withCredentials: true }
      );
      
      // OTP verification successful
      await login(response.data.access);
      setSuccess(true);
    } catch (err) {
      let errorMessage = "OTP verification failed. Please try again.";
      
      if (err.response && err.response.data && err.response.data.detail) {
        errorMessage = err.response.data.detail;
      }
      
      setError(errorMessage);
    }
  };

  const handleBackToLogin = () => {
    setShowOTP(false);
    setOtp("");
    setError(null);
  };

  const handleResendOTP = async () => {
    try {
      await axios.post(
        `${authURL}users/login/resend-otp/`,
        { email },
        { withCredentials: true }
      );
      setError("A new OTP has been sent to your email.");
    } catch (err) {
      setError("Failed to resend OTP. Please try again.");
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
    setError,
    success,
    setSuccess,
    showOTP,
    handleLogin,
    handleOTPSubmit,
    handleBackToLogin,
    handleResendOTP,
  };
};
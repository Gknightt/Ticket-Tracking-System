import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../api/AuthContext";
import api from "../../api/axios";
import styles from "./login.module.css";

// Import our components
import LoadingSpinner from "../../components/LoadingSpinner";
import LoginForm from "../../components/auth/LoginForm";
import OTPForm from "../../components/auth/OTPForm";
import PasswordResetForm from "../../components/auth/PasswordResetForm";

const authURL = import.meta.env.VITE_AUTH_URL;

function Login() {
  // Component state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [initialVerification, setInitialVerification] = useState(true);
  const [forgotMode, setForgotMode] = useState(false);
  const [resetMessage, setResetMessage] = useState("");
  const [resetLoading, setResetLoading] = useState(false);
  const [showOTP, setShowOTP] = useState(false);
  const [success, setSuccess] = useState(false);
  const [disableAnimation, setDisableAnimation] = useState(false);

  // Add a ref to track if navigation is pending
  const navigationPending = useRef(false);

  const navigate = useNavigate();
  const { refreshAuth } = useAuth();

  // Redirect helper - more reliable navigation
  const redirectToHome = useCallback(() => {
    // Prevent multiple redirects
    if (navigationPending.current) return;
    navigationPending.current = true;

    // Short timeout to ensure state updates complete before navigation
    setTimeout(() => {
      navigate('/home', { replace: true });
    }, 100);
  }, [navigate]);

  // Check for existing session - optimized to run only once
  useEffect(() => {
    let isMounted = true;

    const checkSession = async () => {
      try {
        // Use refreshAuth which now handles token checking more reliably and has rate limiting
        const isAuthenticated = await refreshAuth();

        if (isAuthenticated && isMounted) {
          redirectToHome();
          return;
        }
      } catch (error) {
        console.log("Session verification failed:", error);
      } finally {
        if (isMounted) {
          setInitialVerification(false);
        }
      }
    };

    checkSession();

    return () => {
      isMounted = false;
    };
  }, [redirectToHome, refreshAuth]);

  // Handle login form submission
  const handleLogin = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      // First phase login - email and password
      const response = await api.post(
        `users/login/`,
        { email, password }
      );

      if (response.data.requires_otp) {
        setShowOTP(true);
        return;
      }

      // No OTP required - standard login
      setSuccess(true);

      // Update auth context directly with user data from response instead of making another call
      const userData = response.data.user;
      if (userData) {
        refreshAuth(); // This has rate limiting now
        redirectToHome();
      } else {
        // Fallback if user data wasn't included in response
        await refreshAuth();
        redirectToHome();
      }
    } catch (err) {
      let errorMessage = "Login failed. Please check your credentials.";

      if (err.response && err.response.data && err.response.data.detail) {
        errorMessage = err.response.data.detail;
      }

      setError(errorMessage);
    }
  };

  // Handle OTP verification
  const handleOTPSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      const response = await api.post(
        `users/login/verify-otp/`,
        { email, otp }
      );

      // OTP verification successful
      setSuccess(true);

      // Update auth context directly with user data if available
      const userData = response.data?.user;
      if (userData) {
        refreshAuth(); // This has rate limiting now
        redirectToHome();
      } else {
        // Fallback if user data wasn't included in response
        await refreshAuth();
        redirectToHome();
      }
    } catch (err) {
      let errorMessage = "OTP verification failed. Please try again.";

      if (err.response && err.response.data && err.response.data.detail) {
        errorMessage = err.response.data.detail;
      }

      setError(errorMessage);
    }
  };

  // Back to login handler
  const handleBackToLogin = () => {
    setShowOTP(false);
    setOtp("");
    setError(null);
  };

  // Resend OTP handler
  const handleResendOTP = async () => {
    try {
      await api.post(
        `users/login/resend-otp/`,
        { email }
      );
      setError("A new OTP has been sent to your email.");
    } catch (err) {
      setError("Failed to resend OTP. Please try again.");
    }
  };

  // Form submission handlers with loading state
  const onLoginSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await handleLogin(e);
    } finally {
      setIsLoading(false);
    }
  };

  const onOTPSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await handleOTPSubmit(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordReset = async (e) => {
    e.preventDefault();
    setResetLoading(true);
    setResetMessage(""); // Clear previous messages
    try {
      await api.post(`users/password/forgot/`, { email });
    } catch (err) {
      // Do nothing specific for errors to avoid exposing account existence
    } finally {
      setResetMessage(
        "If an account with this email exists, reset instructions have been sent."
      );
      setResetLoading(false);
    }
  };

  // Helper function to handle back navigation without animations
  const handleBackWithoutAnimation = (callback) => {
    setDisableAnimation(true);
    callback();
    // Re-enable animations after a brief delay
    setTimeout(() => setDisableAnimation(false), 50);
  };

  // Show loading spinner while verifying tokens
  if (initialVerification) {
    return <LoadingSpinner message="Verifying session..." />;
  }

  return (
    <main className={`${styles.loginPage} ${disableAnimation ? styles.noAnimation : ''}`}>
      <section className={styles.leftPanel}>
        <div className={styles.leftImage}>
          <img
            src="./tts_bg.jpeg"
            alt="Login illustration"
            className={styles.assetImage}
          />
        </div>
      </section>

      <section className={styles.rightPanel}>
        <header className={styles.formHeader}>
          <section className={styles.logo}>
            <img src="./map-logo.png" alt="TicketFlow logo" />
            <h1 className={styles.logoText}>Map Systems</h1>
          </section>
          <p>Welcome! Please provide your credentials to log in.</p>
        </header>

        {forgotMode ? (
          <PasswordResetForm 
            email={email}
            setEmail={setEmail}
            resetMessage={resetMessage}
            isLoading={resetLoading}
            onSubmit={handlePasswordReset}
            onBack={() => {
              handleBackWithoutAnimation(() => {
                setForgotMode(false);
                setResetMessage("");
              });
            }}
          />
        ) : showOTP ? (
          <OTPForm
            email={email}
            otp={otp}
            setOtp={setOtp}
            error={error}
            isLoading={isLoading}
            onSubmit={onOTPSubmit}
            onBack={(e) => {
              e.preventDefault();
              handleBackWithoutAnimation(() => handleBackToLogin());
            }}
            onResend={handleResendOTP}
          />
        ) : (
          <LoginForm
            email={email}
            setEmail={setEmail}
            password={password}
            setPassword={setPassword}
            error={error}
            isLoading={isLoading}
            onSubmit={onLoginSubmit}
            onForgotPassword={() => setForgotMode(true)}
          />
        )}
      </section>
    </main>
  );
}

export default Login;

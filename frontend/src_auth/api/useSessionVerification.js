import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { hasAccessToken, getAccessToken } from './TokenUtils';
import api from './axios';

// Session verification rate limiting
const SESSION_VERIFY_COOLDOWN = 3000; // 3 seconds minimum between verification attempts
let lastVerificationTime = 0;

// Global verification tracker to prevent duplicate verifications across components
let globalVerificationInProgress = false;
let lastGlobalVerificationTime = 0;
const GLOBAL_VERIFY_COOLDOWN = 1000; // 1 second between global verifications

/**
 * Hook to verify user authentication session
 * Checks for existing token and validates it
 * 
 * @returns {Object} Session verification state
 */
const useSessionVerification = () => {
  const [verifyingToken, setVerifyingToken] = useState(hasAccessToken());
  const [verificationAttempted, setVerificationAttempted] = useState(false);
  const verificationRunning = useRef(false);
  const navigate = useNavigate();
  const { user, refreshAuth } = useAuth();

  // More reliable navigation
  const safeNavigate = useCallback((path) => {
    // Small delay to ensure all state updates are processed
    setTimeout(() => {
      navigate(path, { replace: true });
    }, 100);
  }, [navigate]);

  // Rate limited token verification
  const verifyToken = useCallback(async (token) => {
    const now = Date.now();
    if (now - lastVerificationTime < SESSION_VERIFY_COOLDOWN) {
      throw new Error('Rate limited');
    }
    lastVerificationTime = now;
    
    return api.post('users/token/verify/', { token });
  }, []);

  useEffect(() => {
    // If we already have a user in context, no need to verify
    if (user) {
      setVerifyingToken(false);
      return;
    }

    // Only perform verification if we have an access token
    if (!hasAccessToken()) {
      setVerifyingToken(false);
      setVerificationAttempted(true);
      return;
    }

    // Global verification check - prevent multiple components from verifying simultaneously
    const now = Date.now();
    if (globalVerificationInProgress || now - lastGlobalVerificationTime < GLOBAL_VERIFY_COOLDOWN) {
      // Another verification is already in progress or happened recently
      // Just update local state and wait for auth context to update
      setVerifyingToken(false);
      setVerificationAttempted(true);
      return;
    }

    // Prevent multiple simultaneous verification attempts within this component
    if (verificationRunning.current || verificationAttempted) {
      return;
    }
    
    // Mark verification as running both locally and globally
    verificationRunning.current = true;
    globalVerificationInProgress = true;
    lastGlobalVerificationTime = now;

    // We have an access token but no user, try to authenticate
    const verifySession = async () => {
      try {
        // Use a single verification approach instead of multiple
        // Just use refreshAuth which handles both token validation and user profile fetch
        const isAuthenticated = await refreshAuth();
        if (isAuthenticated) {
          safeNavigate('/home');
        }
      } catch (error) {
        console.log("Auth verification failed:", error);
      } finally {
        setVerifyingToken(false);
        setVerificationAttempted(true);
        verificationRunning.current = false;
        globalVerificationInProgress = false;
      }
    };
    
    verifySession();
  }, [navigate, user, refreshAuth, safeNavigate]);

  return { 
    verifyingToken,
    verificationComplete: verificationAttempted
  };
};

export default useSessionVerification;
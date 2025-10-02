import React, { useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../api/AuthContext.jsx";

export default function ProtectedRoute({ requireAdmin = false }) {
  const { user, loading, initialized } = useAuth();
  const location = useLocation();

  // Avoid redundant calls to checkAuthStatus
  useEffect(() => {
    if (!user && !loading) {
      console.log('ProtectedRoute: Skipping redundant auth check');
    }
  }, [location.pathname, user, loading]);

  useEffect(() => {
    console.log('ProtectedRoute: user =', user);
    console.log('ProtectedRoute: loading =', loading);
    console.log('ProtectedRoute: initialized =', initialized);
  }, [user, loading, initialized]);

  // Show loading while authentication status is being checked
  if (!initialized || loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '16px'
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '4px solid rgba(59, 130, 246, 0.3)',
          borderTop: '4px solid #3b82f6',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          marginBottom: '16px'
        }}></div>
        <style>
          {`@keyframes spin { to { transform: rotate(360deg); } }`}
        </style>
        <p>Verifying authentication...</p>
      </div>
    );
  }

  // If not authenticated, redirect to login
  if (!user) {
    // Redirect to login, preserving the intended destination
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check admin requirements
  if (requireAdmin && !user.is_staff) {
    return <Navigate to="/unauthorized" replace />;
  }

  // If authenticated and meets requirements, render the protected content
  return <Outlet />;
}
import React from 'react';
import { useAuth } from '../../api/AuthContext';

const Home = () => {
  const { user, logout } = useAuth();

  return (
    <div className="home-container" style={{
      padding: '2rem',
      maxWidth: '1200px',
      margin: '0 auto',
    }}>
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem'
      }}>
        <h1>Authentication & Authorization System</h1>
        <button 
          onClick={logout}
          style={{
            padding: '8px 16px',
            backgroundColor: '#f44336',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Logout
        </button>
      </header>

      <div className="welcome-section" style={{
        backgroundColor: '#f5f5f5',
        padding: '2rem',
        borderRadius: '8px',
        marginBottom: '2rem'
      }}>
        <h2>Welcome, {user?.first_name || user?.username || 'User'}!</h2>
        <p>You are now logged in to the secure area of the application.</p>
      </div>

      <div className="user-info" style={{
        backgroundColor: 'white',
        padding: '2rem',
        borderRadius: '8px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h3>Your Profile Information</h3>
        <div style={{ marginTop: '1rem' }}>
          <p><strong>Username:</strong> {user?.username}</p>
          <p><strong>Email:</strong> {user?.email}</p>
          <p><strong>Full Name:</strong> {user?.first_name} {user?.last_name}</p>
          <p><strong>2FA Status:</strong> {user?.otp_enabled ? 'Enabled' : 'Disabled'}</p>
          <p><strong>Account Type:</strong> {user?.is_staff ? 'Administrator' : 'Standard User'}</p>
        </div>
      </div>
    </div>
  );
};

export default Home;
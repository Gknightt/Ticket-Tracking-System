import React from 'react';
import styles from "/src/pages/auth/login.module.css";

/**
 * Login form component for email/password authentication
 * 
 * @param {Object} props Component props
 * @param {string} props.email User email
 * @param {Function} props.setEmail Email state setter
 * @param {string} props.password User password
 * @param {Function} props.setPassword Password state setter
 * @param {string|null} props.error Error message if any
 * @param {boolean} props.isLoading Loading state
 * @param {Function} props.onSubmit Form submit handler
 * @param {Function} props.onForgotPassword Handler for forgot password
 * @returns {JSX.Element} Login form
 */
const LoginForm = ({
  email,
  setEmail,
  password,
  setPassword,
  error,
  isLoading,
  onSubmit,
  onForgotPassword
}) => {
  return (
    <form className={styles.lpForm} onSubmit={onSubmit}>
      <fieldset>
        <label htmlFor="email">Email:</label>
        <input
          type="text"
          id="email"
          name="email"
          placeholder="Enter your email"
          className={styles.input}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          aria-label="Email"
        />
      </fieldset>

      <fieldset>
        <label htmlFor="password">Password:</label>
        <input
          type="password"
          id="password"
          name="password"
          placeholder="Enter your password"
          className={styles.input}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          aria-label="Password"
        />
      </fieldset>

      {error && <p className={styles.error}>{error}</p>}

      <button
        type="submit"
        className={styles.logInButton}
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            <span className={styles.spinner}></span>
            Logging in...
          </>
        ) : (
          "Log In"
        )}
      </button>
      
      <a
        onClick={onForgotPassword}
        className={styles.forgotPassword}
      >
        Forgot Password?
      </a>
    </form>
  );
};

export default LoginForm;
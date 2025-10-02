import React from 'react';
import styles from "../../pages/auth/login.module.css";

/**
 * Password reset request form
 * 
 * @param {Object} props Component props
 * @param {string} props.email User email
 * @param {Function} props.setEmail Email state setter
 * @param {string|null} props.resetMessage Success/info message 
 * @param {boolean} props.isLoading Loading state
 * @param {Function} props.onSubmit Form submit handler
 * @param {Function} props.onBack Handler to go back to login
 * @returns {JSX.Element} Password reset form component
 */
const PasswordResetForm = ({
  email,
  setEmail,
  resetMessage,
  isLoading,
  onSubmit,
  onBack
}) => {
  return (
    <form className={styles.lpForm} onSubmit={onSubmit}>
      <fieldset>
        <label htmlFor="reset-email">Email:</label>
        <input
          type="email"
          id="reset-email"
          name="reset-email"
          placeholder="Enter your email"
          className={styles.input}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          aria-label="Reset Email"
        />
      </fieldset>

      {resetMessage && <p className={styles.info}>{resetMessage}</p>}

      <button
        type="submit"
        className={styles.logInButton}
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            <span className={styles.spinner}></span>
            Sending...
          </>
        ) : (
          "Send Reset Link"
        )}
      </button>
      <button
        type="button"
        onClick={onBack}
        className={styles.backButton}
      >
        Back to Login
      </button>
    </form>
  );
};

export default PasswordResetForm;
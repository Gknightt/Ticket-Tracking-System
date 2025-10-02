import React from 'react';
import styles from "../../pages/auth/login.module.css";

/**
 * OTP verification form component for 2FA
 * 
 * @param {Object} props Component props
 * @param {string} props.email Email address OTP was sent to
 * @param {string} props.otp Current OTP value
 * @param {Function} props.setOtp OTP state setter
 * @param {string|null} props.error Error message if any
 * @param {boolean} props.isLoading Loading state
 * @param {Function} props.onSubmit Form submit handler
 * @param {Function} props.onBack Handler to go back to login
 * @param {Function} props.onResend Handler to resend OTP
 * @returns {JSX.Element} OTP form component
 */
const OTPForm = ({
  email,
  otp,
  setOtp,
  error,
  isLoading,
  onSubmit,
  onBack,
  onResend
}) => {
  return (
    <form className={styles.lpForm} onSubmit={onSubmit}>
      <fieldset>
        <label htmlFor="otp">Enter OTP:</label>
        <input
          type="text"
          id="otp"
          name="otp"
          placeholder="Enter the 6-digit OTP"
          className={styles.input}
          value={otp}
          onChange={(e) => setOtp(e.target.value)}
          maxLength={6}
          required
          aria-label="OTP"
        />
        <small style={{ color: "#666", fontSize: "12px" }}>
          OTP sent to {email}
        </small>
      </fieldset>

      {error && <p className={styles.error}>{error}</p>}

      <button type="submit" className={styles.logInButton} disabled={isLoading}>
        {isLoading ? (
          <>
            <span className={styles.spinner}></span>
            Verifying...
          </>
        ) : (
          "Verify OTP"
        )}
      </button>
      <button
        type="button"
        onClick={onBack}
        className={styles.backButton}
      >
        Back to Login
      </button>
      <button
        type="button"
        onClick={onResend}
        className={styles.resendButton}
      >
        Resend OTP
      </button>
    </form>
  );
};

export default OTPForm;
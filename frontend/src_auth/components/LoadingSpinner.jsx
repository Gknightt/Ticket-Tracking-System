import React from 'react';
import styles from "/src/pages/auth/login.module.css";

/**
 * Reusable loading spinner component
 * @param {Object} props - Component props
 * @param {string} [props.message="Loading..."] - Message to display with spinner
 * @returns {JSX.Element} Loading spinner component
 */
const LoadingSpinner = ({ message = "Loading..." }) => {
  return (
    <div className={styles.loadingContainer}>
      <div className={styles.spinner}></div>
      <p>{message}</p>
    </div>
  );
};

export default LoadingSpinner;
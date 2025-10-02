/**
 * Utility functions for working with authentication tokens
 */

/**
 * Check if access token cookie exists
 * @returns {boolean} True if access token exists
 */
export const hasAccessToken = () => {
  return document.cookie
    .split('; ')
    .some(row => row.startsWith('access_token='));
};

/**
 * Get access token from cookies
 * @returns {string|null} The access token or null if not found
 */
export const getAccessToken = () => {
  const tokenCookie = document.cookie
    .split('; ')
    .find(row => row.startsWith('access_token='));
  
  return tokenCookie ? tokenCookie.split('=')[1] : null;
};
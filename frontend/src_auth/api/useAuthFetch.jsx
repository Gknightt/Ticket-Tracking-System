import api from './axios.jsx';

export const useAuthFetch = () => {
  // Use our configured axios instance that handles cookies automatically
  const authFetch = async (url, options = {}) => {
    try {
      const response = await api({
        url,
        method: options.method || 'GET',
        data: options.body ? JSON.parse(options.body) : options.data,
        headers: options.headers,
        ...options
      });
      return response;
    } catch (error) {
      // Axios throws errors for non-2xx responses, but fetch doesn't
      // To maintain compatibility, we can return the error response
      if (error.response) {
        return error.response;
      }
      throw error;
    }
  };

  return authFetch;
};

import { useState, useEffect } from "react";
import api from "./axios";

const useSecureStepInstance = (stepInstanceId) => {
  const [stepInstance, setStepInstance] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!stepInstanceId) {
      setStepInstance(null);
      setLoading(false);
      return;
    }

    const fetchStepInstance = async () => {
      setLoading(true);
      setError("");
      
      try {
        const response = await api.get(`instances/secure/${stepInstanceId}/`);
        setStepInstance(response.data);
      } catch (err) {
        console.error('Failed to fetch secure step instance:', err);
        
        if (err.response?.status === 403) {
          setError("No authorization to handle this ticket");
        } else if (err.response?.status === 404) {
          setError("Step instance not found");
        } else if (err.response?.status === 401) {
          setError("Authentication required");
        } else {
          setError("Failed to fetch step instance data");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchStepInstance();
  }, [stepInstanceId]);

  const refetch = () => {
    if (stepInstanceId) {
      setLoading(true);
      setError("");
      
      api.get(`instances/secure/${stepInstanceId}/`)
        .then(response => {
          setStepInstance(response.data);
        })
        .catch(err => {
          console.error('Failed to refetch secure step instance:', err);
          
          if (err.response?.status === 403) {
            setError("No authorization to handle this ticket");
          } else if (err.response?.status === 404) {
            setError("Step instance not found");
          } else if (err.response?.status === 401) {
            setError("Authentication required");
          } else {
            setError("Failed to fetch step instance data");
          }
        })
        .finally(() => {
          setLoading(false);
        });
    }
  };

  return { stepInstance, loading, error, refetch };
};

export default useSecureStepInstance;
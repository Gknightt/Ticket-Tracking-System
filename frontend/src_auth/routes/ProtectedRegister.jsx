import { useSearchParams, Navigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import axios from 'axios';
import UserRegistration from '../pages/auth/UserRegistration';

const ProtectedRegister = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [isValid, setIsValid] = useState(null);
  const [invitationData, setInvitationData] = useState(null);

  useEffect(() => {
    const checkToken = async () => {
      try {
        const baseUrl = import.meta.env.VITE_USER_SERVER_API;
        // Use the new invitation token validation endpoint
        const res = await axios.get(`${baseUrl}api/v1/management/invitations/token/${token}/`);
        if (res.data.success) {
          setIsValid(true);
          setInvitationData(res.data.data);
        } else {
          setIsValid(false);
        }
      } catch (err) {
        console.error('Token validation error:', err);
        setIsValid(false);
      }
    };

    if (token) checkToken();
    else setIsValid(false);
  }, [token]);

  if (isValid === null) return <p>Validating invitation...</p>;
  if (!isValid) return <Navigate to="/unauthorized" />;

  return <UserRegistration token={token} invitationData={invitationData} />;
};

export default ProtectedRegister;

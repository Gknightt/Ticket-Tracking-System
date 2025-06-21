import React, { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import axios from "axios";

const verifyURL = import.meta.env.VITE_VERIFY_API;

export default function ProtectedRoute({ requireAdmin = false }) {
  const [isAuthorized, setIsAuthorized] = useState(null);
  const accessToken = localStorage.getItem("accessToken");

  useEffect(() => {
    const verifyToken = async () => {
      if (!accessToken) return setIsAuthorized(false);

      try {
        const res = await axios.get(verifyURL, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

        const isStaff = res.data.is_staff;

        if (requireAdmin && !isStaff) {
          setIsAuthorized(false);
        } else if (!requireAdmin && isStaff) {
          setIsAuthorized(false);
        } else {
          setIsAuthorized(true);
        }
      } catch (err) {
        console.error("Token verification failed", err);
        setIsAuthorized(false);
      }
    };

    verifyToken();
  }, [accessToken, requireAdmin]);

  if (isAuthorized === null) return <div>Loading...</div>;

  return isAuthorized ? <Outlet /> : <Navigate to="/" replace />;
}
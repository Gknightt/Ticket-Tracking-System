import { Route, Routes } from "react-router-dom";
import React from "react";

// Auth components
import Login from "../pages/auth/Login";
import PasswordReset from "../pages/auth/PasswordReset";
import NotFound from "../pages/error/NotFound";
import ProtectedRegister from "./ProtectedRegister";
import ProtectedRoute from "./ProtectedRoute";

// Protected pages
import Home from "../pages/home/Home";

export default function MainRoute() {
  return (
    <Routes>
      {/* PUBLIC ROUTES - Login functionality */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<ProtectedRegister />} />
      <Route path="/reset-password/:uid/:token" element={<PasswordReset />} />
      <Route path="/password-reset" element={<PasswordReset />} />
      
      {/* PROTECTED ROUTES - Require authentication */}
      <Route element={<ProtectedRoute />}>
        {/* Dashboard/Home as index route */}
        <Route path="/" element={<Home />} />
        <Route path="/home" element={<Home />} />
        
        {/* Add more protected routes here as needed */}
      </Route>
      
      {/* ADMIN ROUTES - Require authentication + admin privileges */}
      <Route element={<ProtectedRoute requireAdmin={true} />}>
        {/* Add admin routes here */}
      </Route>
      
      {/* Error handling */}
      <Route path="/unauthorized" element={<NotFound />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

// components/auth/ProtectedRoute.tsx
"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "./AuthContext";
import { Building } from "lucide-react";

interface ProtectedRouteProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  fallback,
}) => {
  const { isAuthenticated, loading } = useAuth();
  const [showAuth, setShowAuth] = useState(false);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      setShowAuth(true);
    }
  }, [loading, isAuthenticated]);

  // Show loading spinner while checking auth
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary to-slate-900">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-white/10 rounded-full animate-pulse">
              <Building className="w-12 h-12 text-white" />
            </div>
          </div>
          <div className="flex items-center gap-2 justify-center">
            <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
          </div>
          <p className="mt-4 text-white text-lg">Loading...</p>
        </div>
      </div>
    );
  }

  // Show fallback or default message if not authenticated
  if (!isAuthenticated) {
    return fallback || (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary to-slate-900">
        <div className="text-center text-white p-8">
          <Building className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <h2 className="text-2xl font-bold mb-2">Authentication Required</h2>
          <p className="text-slate-300">Please log in to access this content.</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
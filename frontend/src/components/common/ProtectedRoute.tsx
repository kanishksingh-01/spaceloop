import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { User } from '../../types';

interface ProtectedRouteProps {
  currentUser: User | null;
  initializing: boolean;
  requiredRole?: 'host' | 'seeker' | 'admin';
  children: React.ReactElement;
  onRequireAuth?: () => void;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  currentUser,
  initializing,
  requiredRole,
  children,
  onRequireAuth,
}) => {
  const location = useLocation();

  if (initializing) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs text-slate-400">Verifying session...</span>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    if (onRequireAuth) {
      onRequireAuth();
    }
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  if (requiredRole === 'host' && !currentUser.is_host) {
    return <Navigate to="/host" replace />;
  }

  return children;
};

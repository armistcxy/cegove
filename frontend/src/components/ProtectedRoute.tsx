import { Navigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

export default function ProtectedRoute({ children, requireAdmin = false }: ProtectedRouteProps) {
  const { isLoggedIn, userProfile, isLoading } = useUser();

  console.log('ProtectedRoute - isLoggedIn:', isLoggedIn);
  console.log('ProtectedRoute - userProfile:', userProfile);
  console.log('ProtectedRoute - requireAdmin:', requireAdmin);
  console.log('ProtectedRoute - isLoading:', isLoading);

  // Wait for profile to load
  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && userProfile?.role !== 'LOCAL_ADMIN') {
    console.log('Access denied - role:', userProfile?.role);
    return <Navigate to="/homepage" replace />;
  }

  return <>{children}</>;
}

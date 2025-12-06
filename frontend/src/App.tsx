import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useUser } from './context/UserContext';
import Header from './components/Header/Header.tsx';
import ProtectedRoute from './components/ProtectedRoute.tsx';
import AdminLayout from './layouts/AdminLayout.tsx';
import HomePage from './pages/Home/HomePage.tsx';
import Movies from './pages/Movies/Movie.tsx';
import MovieDetail from './pages/MovieDetails/MovieDetail.tsx';
import Cinema from './pages/Cinemas/Cinema.tsx';
import MyTickets from './pages/MyTickets/MyTickets.tsx';
import NotAvailable from './pages/NotAvailable/NotAvailable.tsx';
import AuthPage from "./pages/Auth/AuthPage.tsx";
import Profile from "./pages/User/Profile.tsx";
import Dashboard from './pages/Admin/Dashboard.tsx';
import AdminUsers from './pages/Admin/Users.tsx';
import AdminMovies from './pages/Admin/Movies.tsx';
import AdminCinemas from './pages/Admin/Cinemas.tsx';
import AdminAbout from './pages/Admin/About.tsx';

function AppContent() {
  return (
    <div className="App">
      <Routes>
          {/* Admin Routes */}
          <Route path="/admin" element={
            <ProtectedRoute requireAdmin={true}>
              <AdminLayout />
            </ProtectedRoute>
          }>
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="users" element={<AdminUsers />} />
            <Route path="movies" element={<AdminMovies />} />
            <Route path="cinemas" element={<AdminCinemas />} />
            <Route path="about" element={<AdminAbout />} />
          </Route>

          {/* Public Routes with Header */}
          <Route path="*" element={
            <>
              <Header />
              <main className="main-content">
                <Routes>
                  <Route path="/" element={<Navigate to="/homepage" replace />} />
                  <Route path="/homepage" element={<HomePage />} />
                  <Route path="/movie" element={<Movies />} />
                  <Route path="/cinema" element={<Cinema />} />
                  <Route path="/my-tickets" element={<MyTickets />} />
                  <Route path="/MovieDetail/:id" element={<MovieDetail />} />
                  <Route path="/NotAvailable" element={<NotAvailable />} />
                  <Route path="/login" element={<AuthPage />} />
                  <Route path="/register" element={<AuthPage />} />
                  <Route path="/profile" element={<Profile />} />
                </Routes>
              </main>
            </>
          } />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;

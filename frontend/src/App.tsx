import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header/Header.tsx';
import HomePage from './pages/Home/HomePage.tsx';
import Movies from './pages/Movies/Movie.tsx';
import MovieDetail from './pages/MovieDetails/MovieDetail.tsx';
import NotAvailable from './pages/NotAvailable/NotAvailable.tsx';
import AuthPage from "./pages/Auth/AuthPage.tsx";
import Profile from "./pages/User/Profile.tsx";

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/homepage" replace />} />
            <Route path="/homepage" element={<HomePage />} />
            <Route path="/movie" element={<Movies />} />
            <Route path="/MovieDetail/:id" element={<MovieDetail />} />
            <Route path="/NotAvailable" element={<NotAvailable />} />
            <Route path="/login" element={<AuthPage />} />
            <Route path="/register" element={<AuthPage />} />
            <Route path="/profile" element={<Profile />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

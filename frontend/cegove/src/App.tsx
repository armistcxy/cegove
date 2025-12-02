import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header/Header';
import HomePage from './features/Home/HomePage';
import Movies from './features/Movies/Movie';
import './App.css';

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
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

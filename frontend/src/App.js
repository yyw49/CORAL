import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import LabAssistantList from './pages/LabAssistantList';
import CalendarPage from './pages/CalendarPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="nav-container">
            <div className="nav-brand">
              <h1>CORAL Platform</h1>
              <span className="nav-subtitle">USC Marshall Behavioral Research Lab</span>
            </div>
            <ul className="nav-links">
              <li>
                <Link to="/">Dashboard</Link>
              </li>
              <li>
                <Link to="/calendar">Availability Calendar</Link>
              </li>
              <li>
                <Link to="/assistants">Lab Assistants</Link>
              </li>
            </ul>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/calendar" element={<CalendarPage />} />
            <Route path="/assistants" element={<LabAssistantList />} />
          </Routes>
        </main>

        <footer className="footer">
          <p>&copy; 2025 USC Marshall School of Business | CSCI 401 Capstone Project</p>
        </footer>
      </div>
    </Router>
  );
}

// Simple Dashboard component
const Dashboard = () => {
  return (
    <div className="dashboard">
      <div className="welcome-section">
        <h2>Welcome to CORAL</h2>
        <p>Coordinated Operations for Research Assistant Logistics</p>
      </div>

      <div className="dashboard-cards">
        <div className="dashboard-card">
          <h3>📅 Availability Calendar</h3>
          <p>View and manage lab assistant availability schedules</p>
          <Link to="/calendar" className="card-button">View Calendar</Link>
        </div>

        <div className="dashboard-card">
          <h3>👥 Lab Assistants</h3>
          <p>Browse all registered lab assistants and their information</p>
          <Link to="/assistants" className="card-button">View Assistants</Link>
        </div>

        <div className="dashboard-card coming-soon">
          <h3>📊 Projects</h3>
          <p>Manage research projects and assignments</p>
          <span className="coming-soon-badge">Coming Soon</span>
        </div>

        <div className="dashboard-card coming-soon">
          <h3>📈 Reports</h3>
          <p>View analytics and resource utilization metrics</p>
          <span className="coming-soon-badge">Coming Soon</span>
        </div>
      </div>
    </div>
  );
};

export default App;
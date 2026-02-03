import { useState, useEffect } from 'react'
import StudentChat from './components/StudentChat'
import CounselorDashboard from './components/CounselorDashboard'
import ConsensusDemo from './components/ConsensusDemo'
import LandingPage from './components/LandingPage'
import './App.css'

function App() {
  // Restore view from localStorage if available, else default to 'landing'
  const [view, setView] = useState(() => localStorage.getItem('current_view') || 'landing');

  // Persist view state
  useEffect(() => {
    localStorage.setItem('current_view', view);
  }, [view]);

  // Theme state
  const [theme, setTheme] = useState(() => localStorage.getItem('app_theme') || 'dark');

  // Persist theme
  useEffect(() => {
    localStorage.setItem('app_theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  // Handler for navigation
  const handleNavigate = (newView) => {
    setView(newView);
  };

  // If on landing page, show it (it has its own layout)
  if (view === 'landing') {
    return <LandingPage onNavigate={handleNavigate} theme={theme} toggleTheme={toggleTheme} />;
  }

  // Main App Layout
  return (
    <div className="app" data-theme={theme}>
      <header className="app-header">
        <div className="header-content">
          <div className="header-left" onClick={() => handleNavigate('landing')} style={{ cursor: 'pointer' }}>
            <h1 className="logo-text">Beacon</h1>
            <span className="tagline">Mental Health Support</span>
          </div>
          <div className="header-right" style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
            <div className="view-toggle">
              <button
                className={`nav-btn ${view === 'demo' ? 'active' : ''}`}
                onClick={() => handleNavigate('demo')}
              >
                🧠 Consensus Demo
              </button>
              <button
                className={`nav-btn ${view === 'student' ? 'active' : ''}`}
                onClick={() => handleNavigate('student')}
              >
                💬 Student Chat
              </button>
              <button
                className={`nav-btn ${view === 'counselor' ? 'active' : ''}`}
                onClick={() => handleNavigate('counselor')}
              >
                📊 Counselor Dashboard
              </button>
            </div>
            <button onClick={toggleTheme} className="theme-toggle-btn" aria-label="Toggle Theme">
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="main-content-wrapper">
          {view === 'demo' && <ConsensusDemo />}
          {view === 'student' && <StudentChat />}
          {view === 'counselor' && <CounselorDashboard />}
        </div>
      </main>

      {/* Footer only for non-demo/chat full screens if needed, but keeping simple for now */}
      {view !== 'demo' && view !== 'student' && (
        <footer className="app-footer">
          <p>🆘 Crisis? Call 988 or text HOME to 741741</p>
        </footer>
      )}
    </div>
  )
}

export default App

import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ResumeUpload from './components/ResumeUpload';
import CandidateDashboard from './components/CandidateDashboard';
import CandidateProfile from './components/CandidateProfile';
import './App.css';

function App() {
  const [uploadKey, setUploadKey] = useState(0);

  const handleUploadSuccess = () => {
    setUploadKey(prev => prev + 1);
  };

  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-content">
            <Link to="/" className="nav-logo">
              <span className="logo-text">TraqCheck</span>
            </Link>
            <div className="nav-links">
              <Link to="/" className="nav-link">Dashboard</Link>
            </div>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={
              <div className="home-page">
                <div className="hero-section">
                  <h1>Candidate Management System</h1>
                  <p className="hero-subtitle">
                    Upload resumes, extract candidate information, and manage identity documents with AI
                  </p>
                </div>

                <section className="upload-section">
                  <h2>Upload Resume</h2>
                  <ResumeUpload onUploadSuccess={handleUploadSuccess} />
                </section>

                <section className="dashboard-section">
                  <CandidateDashboard key={uploadKey} />
                </section>
              </div>
            } />
            <Route path="/candidate/:id" element={<CandidateProfile />} />
          </Routes>
        </main>

        <footer className="footer">
          <p>2026 TraqCheck - Candidate Management System</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;

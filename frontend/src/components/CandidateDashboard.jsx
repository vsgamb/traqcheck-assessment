import React, { useState, useEffect } from 'react';
import { getCandidates } from '../services/api';
import { useNavigate } from 'react-router-dom';
import './CandidateDashboard.css';

const CandidateDashboard = () => {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadCandidates();
  }, []);

  const loadCandidates = async () => {
    try {
      setLoading(true);
      const data = await getCandidates();
      setCandidates(data);
      setError(null);
    } catch (err) {
      setError('Failed to load candidates');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      completed: { label: 'Completed', className: 'status-completed' },
      pending: { label: 'Pending', className: 'status-pending' },
      processing: { label: 'Processing', className: 'status-processing' }
    };
    const statusInfo = statusMap[status] || statusMap.pending;
    return (
      <span className={`status-badge ${statusInfo.className}`}>
        {statusInfo.label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="dashboard">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading candidates...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error-box">
          <p>{error}</p>
          <button onClick={loadCandidates}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Candidate Dashboard</h2>
        <button onClick={loadCandidates} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>

      {candidates.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📭</div>
          <p>No candidates found</p>
          <p className="empty-subtitle">Upload a resume to get started</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="candidates-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Company</th>
                <th>Designation</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((candidate) => (
                <tr key={candidate.id}>
                  <td className="name-cell">
                    <div className="avatar">{candidate.name?.[0] || '?'}</div>
                    {candidate.name || 'Unknown'}
                  </td>
                  <td>{candidate.email || '-'}</td>
                  <td>{candidate.phone || '-'}</td>
                  <td>{candidate.company || '-'}</td>
                  <td>{candidate.designation || '-'}</td>
                  <td>{getStatusBadge(candidate.extraction_status)}</td>
                  <td>
                    <button
                      onClick={() => navigate(`/candidate/${candidate.id}`)}
                      className="view-btn"
                    >
                      View Profile
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default CandidateDashboard;

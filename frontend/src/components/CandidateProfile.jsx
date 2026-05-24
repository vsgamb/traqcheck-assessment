import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCandidate, requestDocuments, submitDocuments } from '../services/api';
import './CandidateProfile.css';

const CandidateProfile = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [requesting, setRequesting] = useState(false);
  const [uploadingDocs, setUploadingDocs] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [panFile, setPanFile] = useState(null);
  const [aadhaarFile, setAadhaarFile] = useState(null);

  useEffect(() => {
    loadCandidate();
  }, [id]);

  const loadCandidate = async () => {
    try {
      setLoading(true);
      const data = await getCandidate(id);
      setCandidate(data);
      setError(null);
    } catch (err) {
      setError('Failed to load candidate');
    } finally {
      setLoading(false);
    }
  };

  const handleRequestDocuments = async () => {
    try {
      setRequesting(true);
      await requestDocuments(id);
      await loadCandidate();
      alert('Document request sent successfully!');
    } catch (err) {
      alert('Failed to send document request');
    } finally {
      setRequesting(false);
    }
  };

  const handleSubmitDocuments = async (e) => {
    e.preventDefault();
    if (!panFile && !aadhaarFile) {
      alert('Please select at least one document');
      return;
    }

    try {
      setUploadingDocs(true);
      await submitDocuments(id, panFile, aadhaarFile);
      await loadCandidate();
      setShowUploadForm(false);
      setPanFile(null);
      setAadhaarFile(null);
      alert('Documents uploaded successfully!');
    } catch (err) {
      alert('Failed to upload documents');
    } finally {
      setUploadingDocs(false);
    }
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.8) return '#4CAF50';
    if (score >= 0.5) return '#FF9800';
    return '#f44336';
  };

  const getConfidenceLabel = (score) => {
    if (score >= 0.8) return 'High';
    if (score >= 0.5) return 'Medium';
    return 'Low';
  };

  if (loading) {
    return (
      <div className="profile">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading candidate profile...</p>
        </div>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="profile">
        <div className="error-box">
          <p>{error || 'Candidate not found'}</p>
          <button onClick={() => navigate('/')}>Back to Dashboard</button>
        </div>
      </div>
    );
  }

  return (
    <div className="profile">
      <div className="profile-header">
        <button onClick={() => navigate('/')} className="back-btn">
          ← Back
        </button>
        <h2>Candidate Profile</h2>
      </div>

      <div className="profile-content">
        <div className="profile-card">
          <div className="profile-avatar">
            {candidate.name?.[0] || '?'}
          </div>
          <h3>{candidate.name || 'Unknown'}</h3>
          <p className="profile-subtitle">
            {candidate.designation || 'No designation'} 
            {candidate.company && ` at ${candidate.company}`}
          </p>
        </div>

        <div className="info-section">
          <h4>Contact Information</h4>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Email:</span>
              <span className="info-value">{candidate.email || '-'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Phone:</span>
              <span className="info-value">{candidate.phone || '-'}</span>
            </div>
          </div>
        </div>

        <div className="info-section">
          <h4>Professional Details</h4>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Company:</span>
              <span className="info-value">{candidate.company || '-'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Designation:</span>
              <span className="info-value">{candidate.designation || '-'}</span>
            </div>
          </div>
        </div>

        <div className="info-section">
          <h4>Skills</h4>
          <div className="skills-container">
            {candidate.skills && candidate.skills.length > 0 ? (
              candidate.skills.map((skill, index) => (
                <span key={index} className="skill-tag">
                  {skill}
                </span>
              ))
            ) : (
              <p className="no-data">No skills extracted</p>
            )}
          </div>
        </div>

        <div className="info-section">
          <h4>Extraction Confidence Scores</h4>
          <div className="confidence-grid">
            {candidate.confidence_scores && Object.entries(candidate.confidence_scores).map(([field, score]) => (
              <div key={field} className="confidence-item">
                <div className="confidence-header">
                  <span className="confidence-field">{field}</span>
                  <span 
                    className="confidence-label"
                    style={{ color: getConfidenceColor(score) }}
                  >
                    {getConfidenceLabel(score)}
                  </span>
                </div>
                <div className="confidence-bar">
                  <div 
                    className="confidence-fill"
                    style={{ 
                      width: `${score * 100}%`,
                      background: getConfidenceColor(score)
                    }}
                  ></div>
                </div>
                <span className="confidence-score">{(score * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>

        <div className="info-section">
          <div className="section-header">
            <h4>Document Requests</h4>
            <button 
              onClick={handleRequestDocuments} 
              className="request-btn"
              disabled={requesting}
            >
              {requesting ? 'Sending...' : '📨 Request Documents'}
            </button>
          </div>
          
          {candidate.document_requests && candidate.document_requests.length > 0 ? (
            <div className="requests-list">
              {candidate.document_requests.map((req) => (
                <div key={req.id} className="request-card">
                  <div className="request-header">
                    <span className="request-date">
                      {new Date(req.requested_at).toLocaleDateString()}
                    </span>
                    <span className="request-status">{req.status}</span>
                  </div>
                  <div className="request-message">{req.request_message}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-data">No document requests sent yet</p>
          )}
        </div>

        <div className="info-section">
          <div className="section-header">
            <h4>Submitted Documents</h4>
            <button 
              onClick={() => setShowUploadForm(!showUploadForm)} 
              className="upload-toggle-btn"
            >
              {showUploadForm ? 'Cancel' : '📤 Upload Documents'}
            </button>
          </div>

          {showUploadForm && (
            <form onSubmit={handleSubmitDocuments} className="upload-form">
              <div className="form-group">
                <label htmlFor="pan">PAN Card:</label>
                <input
                  type="file"
                  id="pan"
                  accept="image/*,application/pdf"
                  onChange={(e) => setPanFile(e.target.files[0])}
                />
                {panFile && <span className="file-name">✓ {panFile.name}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="aadhaar">Aadhaar Card:</label>
                <input
                  type="file"
                  id="aadhaar"
                  accept="image/*,application/pdf"
                  onChange={(e) => setAadhaarFile(e.target.files[0])}
                />
                {aadhaarFile && <span className="file-name">✓ {aadhaarFile.name}</span>}
              </div>

              <button type="submit" className="submit-btn" disabled={uploadingDocs}>
                {uploadingDocs ? 'Uploading...' : 'Submit Documents'}
              </button>
            </form>
          )}

          {candidate.documents && candidate.documents.length > 0 ? (
            <div className="documents-grid">
              {candidate.documents.map((doc) => (
                <div key={doc.id} className="document-card">
                  <div className="document-icon">
                    {doc.document_type === 'PAN' ? '🆔' : '📋'}
                  </div>
                  <div className="document-info">
                    <span className="document-type">{doc.document_type}</span>
                    <span className="document-date">
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-data">No documents submitted yet</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default CandidateProfile;

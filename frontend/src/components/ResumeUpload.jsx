import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadResume } from '../services/api';
import './ResumeUpload.css';

const ResumeUpload = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setError(null);
    setSuccess(false);
    setProgress(0);

    try {
      const result = await uploadResume(file, setProgress);
      setSuccess(true);
      setProgress(100);
      
      // Notify parent and reset after 2 seconds
      setTimeout(() => {
        onUploadSuccess && onUploadSuccess(result.candidate);
        // Reset to allow another upload
        setTimeout(() => {
          setSuccess(false);
          setProgress(0);
        }, 1500);
      }, 1000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload resume');
      setProgress(0);
    } finally {
      setUploading(false);
    }
  }, [onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxFiles: 1,
    disabled: uploading
  });

  return (
    <div className="resume-upload">
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'uploading' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="dropzone-content">
          {uploading ? (
            <>
              <div className="ui-icon ui-icon-upload" aria-hidden="true"></div>
              <p>Uploading and parsing resume...</p>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <p className="progress-text">{progress}%</p>
            </>
          ) : success ? (
            <>
              <div className="ui-icon ui-icon-success" aria-hidden="true"></div>
              <p className="success-message">Resume uploaded successfully!</p>
              <p className="sub-text">Upload another resume or view the dashboard below</p>
            </>
          ) : (
            <>
              <div className="ui-icon ui-icon-file" aria-hidden="true"></div>
              <p className="main-text">
                {isDragActive
                  ? 'Drop the resume here'
                  : 'Drag & drop a resume here, or click to browse'}
              </p>
              <p className="sub-text">Supports PDF and DOCX files</p>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
    </div>
  );
};

export default ResumeUpload;

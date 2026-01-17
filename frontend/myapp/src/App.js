import React, { useState } from 'react';
import axios from 'axios';
import { 
  Upload, 
  FileAudio, 
  FileVideo, 
  Loader2, 
  CheckCircle2, 
  XCircle,
  Download,
  Sparkles,
  Clock,
  Users,
  Target,
  Calendar,
  ArrowRight
} from 'lucide-react';
import './App.css';

const API_URL = 'http://localhost:5000';

function App() {
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [fileSize, setFileSize] = useState('');
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState('');
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);

  const allowedExtensions = [
    '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.m4v',
    '.mp3', '.wav', '.m4a', '.ogg', '.aac', '.flac'
  ];

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const validateFile = (file) => {
    if (!file) return 'Please select a file';
    
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedExtensions.includes(fileExt)) {
      return `Unsupported file type: ${fileExt}`;
    }
    
    if (file.size > 50 * 1024 * 1024) {
      return `File too large: ${formatFileSize(file.size)} (max 50MB)`;
    }
    
    return null;
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    handleFileSelection(selectedFile);
  };

  const handleFileSelection = (selectedFile) => {
    if (selectedFile) {
      const validationError = validateFile(selectedFile);
      if (validationError) {
        setError(validationError);
        setFile(null);
        setFileName('');
        setFileSize('');
        return;
      }

      setFile(selectedFile);
      setFileName(selectedFile.name);
      setFileSize(formatFileSize(selectedFile.size));
      setError('');
      setSummary('');
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    const formData = new FormData();
    formData.append('video', file);

    setLoading(true);
    setError('');
    setSummary('');
    setProgress(0);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 500);

    try {
      const response = await axios.post(`${API_URL}/process`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      clearInterval(progressInterval);
      setProgress(100);

      if (response.data.success) {
        setSummary(response.data.summary);
      } else {
        setError(response.data.error || 'Failed to generate summary');
      }
    } catch (err) {
      clearInterval(progressInterval);
      setProgress(0);
      setError(err.response?.data?.error || 'An error occurred while processing the file');
    } finally {
      setLoading(false);
    }
  };

  const downloadSummary = () => {
    const element = document.createElement('a');
    const file = new Blob([summary], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `${fileName.split('.')[0]}_summary.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const parseSummary = (text) => {
    const sections = [];
    const lines = text.split('\n');
    let currentSection = { title: '', content: [] };

    lines.forEach(line => {
      if (line.match(/^\*\*.*\*\*:?$/) || line.match(/^#+/)) {
        if (currentSection.title) {
          sections.push(currentSection);
        }
        currentSection = {
          title: line.replace(/\*\*/g, '').replace(/#/g, '').replace(':', '').trim(),
          content: []
        };
      } else if (line.trim()) {
        currentSection.content.push(line);
      }
    });

    if (currentSection.title || currentSection.content.length > 0) {
      sections.push(currentSection);
    }

    return sections;
  };

  const getSectionIcon = (title) => {
    const lowerTitle = title.toLowerCase();
    if (lowerTitle.includes('executive') || lowerTitle.includes('summary')) return <Sparkles />;
    if (lowerTitle.includes('discussion') || lowerTitle.includes('points')) return <Users />;
    if (lowerTitle.includes('decision')) return <CheckCircle2 />;
    if (lowerTitle.includes('action')) return <Target />;
    if (lowerTitle.includes('date') || lowerTitle.includes('deadline')) return <Calendar />;
    if (lowerTitle.includes('next')) return <ArrowRight />;
    return <Clock />;
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="container">
          <div className="logo">
            <Sparkles className="logo-icon" />
            <h1>MeetingSummarizer </h1>
          </div>
          <p className="tagline">Transform your meeting recordings into actionable insights</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        <div className="container">
          {/* Hero Section */}
          <div className="hero">
            <h2>Meeting Summarization</h2>
            <p>Upload your Zoom, Google Meet, or Teams recordings and get instant, structured summaries</p>
          </div>

          {/* Upload Section */}
          <div className="upload-section">
            <div 
              className={`upload-box ${dragActive ? 'drag-active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                type="file"
                id="file-input"
                className="file-input"
                accept="video/*,audio/*"
                onChange={handleFileChange}
              />
              <label htmlFor="file-input" className="upload-label">
                <Upload className="upload-icon" size={48} />
                <h3>Drop your file here or click to browse</h3>
                <p className="upload-hint">
                  Supports MP4, AVI, MOV, MP3, WAV, and more (max 50MB)
                </p>
              </label>

              {fileName && (
                <div className="file-info">
                  {fileName.match(/\.(mp4|avi|mov|mkv|webm|flv|m4v)$/i) ? (
                    <FileVideo className="file-icon" />
                  ) : (
                    <FileAudio className="file-icon" />
                  )}
                  <div className="file-details">
                    <p className="file-name">{fileName}</p>
                    <p className="file-size">{fileSize}</p>
                  </div>
                </div>
              )}
            </div>

            {file && !loading && !summary && (
              <button className="btn btn-primary" onClick={handleSubmit}>
                <Sparkles size={20} />
                Generate Summary
              </button>
            )}
          </div>

          {/* Loading State */}
          {loading && (
            <div className="loading-section">
              <Loader2 className="spinner" size={48} />
              <h3>Analyzing your meeting...</h3>
              <p>This may take a few minutes depending on file size</p>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progress}%` }}></div>
              </div>
              <p className="progress-text">{progress}%</p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="error-section">
              <XCircle size={48} />
              <h3>Error</h3>
              <p>{error}</p>
            </div>
          )}

          {/* Summary Section */}
          {summary && (
            <div className="summary-section">
              <div className="summary-header">
                <div className="summary-title">
                  <CheckCircle2 className="success-icon" size={32} />
                  <h2>Meeting Summary</h2>
                </div>
                <button className="btn btn-secondary" onClick={downloadSummary}>
                  <Download size={20} />
                  Download Summary
                </button>
              </div>

              <div className="summary-content">
                {parseSummary(summary).map((section, index) => (
                  <div key={index} className="summary-card">
                    <div className="card-header">
                      {getSectionIcon(section.title)}
                      <h3>{section.title}</h3>
                    </div>
                    <div className="card-content">
                      {section.content.map((line, i) => (
                        <p key={i}>{line}</p>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <button 
                className="btn btn-outline" 
                onClick={() => {
                  setFile(null);
                  setFileName('');
                  setFileSize('');
                  setSummary('');
                  setError('');
                }}
              >
                Process Another File
              </button>
            </div>
          )}

          {/* Features Section */}
          {!loading && !summary && (
            <div className="features">
              <h3>Features</h3>
              <div className="features-grid">
                <div className="feature-card">
                  <Sparkles className="feature-icon" />
                  <h4>AI-Powered</h4>
                  <p>Uses Google's Gemini 2.5 Flash for accurate summaries</p>
                </div>
                <div className="feature-card">
                  <Clock className="feature-icon" />
                  <h4>Fast Processing</h4>
                  <p>Get your summary in minutes, not hours</p>
                </div>
                <div className="feature-card">
                  <Target className="feature-icon" />
                  <h4>Action Items</h4>
                  <p>Automatically extracts tasks and deadlines</p>
                </div>
                <div className="feature-card">
                  <Download className="feature-icon" />
                  <h4>Export Ready</h4>
                  <p>Download summaries in text format</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
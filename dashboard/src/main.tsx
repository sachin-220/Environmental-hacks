import React, { Component, ErrorInfo, ReactNode } from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import './index.css';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class AppErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  public state: ErrorBoundaryState = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('AERIS Portal Uncaught Error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#F5F6F7',
            padding: '24px',
            fontFamily: 'Calibri, "Segoe UI", Candara, Arial, sans-serif'
          }}
        >
          <div
            style={{
              background: '#FFFFFF',
              border: '1px solid #D9DDE1',
              padding: '32px',
              maxWidth: '650px',
              width: '100%',
              borderRadius: '4px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
            }}
          >
            <div style={{ borderBottom: '2px solid #003366', paddingBottom: '12px', marginBottom: '16px' }}>
              <div style={{ fontSize: '12px', color: '#54595D', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Government of India · Ministry of Earth Sciences · CPCB
              </div>
              <h2 style={{ fontSize: '18px', color: '#003366', margin: '4px 0 0 0' }}>
                AERIS — Atmospheric Emission-Response Intelligence System
              </h2>
            </div>

            <div style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', padding: '12px', borderRadius: '4px', marginBottom: '20px' }}>
              <strong style={{ color: '#991B1B', fontSize: '13px' }}>System Diagnostics Notice:</strong>
              <div style={{ fontSize: '12px', color: '#7F1D1D', marginTop: '4px', fontFamily: 'monospace' }}>
                {this.state.error?.message || 'An unexpected runtime error occurred.'}
              </div>
            </div>

            <p style={{ fontSize: '12px', color: '#54595D', lineHeight: '1.5', marginBottom: '20px' }}>
              The portal encountered an issue while loading an external resource. Click the button below to reload the application.
            </p>

            <button
              onClick={() => window.location.reload()}
              style={{
                background: '#003366',
                color: '#FFFFFF',
                border: 'none',
                padding: '8px 18px',
                fontSize: '12px',
                fontWeight: 'bold',
                cursor: 'pointer',
                borderRadius: '3px'
              }}
            >
              Reload Portal
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  </React.StrictMode>,
);

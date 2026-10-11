import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  onFallback?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class MapErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('MapErrorBoundary caught an error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div
          className="portal-section"
          style={{
            padding: '24px',
            background: '#FEF2F2',
            border: '1px solid #F87171',
            borderRadius: '4px',
            margin: '16px 0',
            textAlign: 'center'
          }}
        >
          <div style={{ fontSize: '15px', fontWeight: 'bold', color: '#991B1B', marginBottom: '8px' }}>
            {this.props.fallbackTitle || 'Map Rendering Notice'}
          </div>
          <p style={{ fontSize: '12px', color: '#7F1D1D', marginBottom: '14px', maxWidth: '600px', margin: '0 auto 14px' }}>
            {this.state.error?.message || 'An unexpected error occurred while rendering the map visualization engine.'}
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '10px' }}>
            {this.props.onFallback && (
              <button
                className="portal-btn"
                onClick={() => {
                  this.setState({ hasError: false, error: null });
                  this.props.onFallback?.();
                }}
                style={{ background: '#003366', color: '#FFFFFF', padding: '6px 14px' }}
              >
                Switch to OpenStreetMap (Leaflet)
              </button>
            )}
            <button
              className="portal-btn-secondary"
              onClick={() => this.setState({ hasError: false, error: null })}
              style={{ padding: '6px 14px' }}
            >
              Retry
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('SpaceLoop Uncaught UI Error:', error, errorInfo);
    // Automatic transparent recovery when chunks change after a deployment
    const isChunkError =
      error?.message &&
      (error.message.includes('dynamically imported module') ||
       error.message.includes('Loading chunk') ||
       error.message.includes('Importing a module script failed'));

    if (isChunkError) {
      const lastReload = sessionStorage.getItem('spaceloop_chunk_reload');
      const now = Date.now();
      if (!lastReload || now - parseInt(lastReload, 10) > 10000) {
        sessionStorage.setItem('spaceloop_chunk_reload', now.toString());
        window.location.reload();
      }
    }
  }

  public handleTryAgain = () => {
    const isChunkError =
      this.state.error?.message &&
      (this.state.error.message.includes('dynamically imported module') ||
       this.state.error.message.includes('Loading chunk') ||
       this.state.error.message.includes('Importing a module script failed'));

    if (isChunkError) {
      window.location.reload();
    } else {
      this.setState({ hasError: false, error: null });
    }
  };

  public handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = '/';
  };

  public render() {
    if (this.state.hasError) {
      const isChunkError =
        this.state.error?.message &&
        (this.state.error.message.includes('dynamically imported module') ||
         this.state.error.message.includes('Loading chunk') ||
         this.state.error.message.includes('Importing a module script failed'));

      return (
        <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-3xl p-8 text-center space-y-5 shadow-2xl">
            <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-2xl flex items-center justify-center mx-auto">
              ⚡
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-black text-white">
                {isChunkError ? 'New Version Available' : 'Something went unexpected'}
              </h2>
              <p className="text-xs text-slate-400 leading-relaxed">
                {isChunkError
                  ? 'A fresh update was just deployed. Click below to load the latest version.'
                  : 'SpaceLoop encountered a momentary interface error. Your session and bookings remain secure.'}
              </p>
            </div>
            {this.state.error?.message && (
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-[11px] font-mono text-rose-300 text-left overflow-x-auto max-h-24">
                {this.state.error.message}
              </div>
            )}
            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                type="button"
                onClick={this.handleTryAgain}
                className="flex-1 py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-white transition"
              >
                {isChunkError ? 'Reload Latest' : 'Try Again'}
              </button>
              <button
                type="button"
                onClick={this.handleReset}
                className="flex-1 py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white transition shadow-lg shadow-indigo-600/30"
              >
                Return to Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

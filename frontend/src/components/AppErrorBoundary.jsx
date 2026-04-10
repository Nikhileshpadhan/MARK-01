import { Component } from 'react'

export default class AppErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-surface p-6">
          <div className="w-full max-w-md rounded-2xl bg-surface-container p-8 text-center">
            <h2 className="text-xl font-semibold text-onSurface">Something went wrong</h2>
            <p className="mt-3 text-sm text-onSurface-variant">
              An unexpected error occurred. Please refresh the page and try again.
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-6 rounded-full bg-primary-container px-6 py-2.5 text-sm font-medium text-white transition-colors duration-200 hover:bg-primary-container/80"
            >
              Reload page
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

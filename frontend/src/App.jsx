import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import AppErrorBoundary from './components/AppErrorBoundary.jsx'
import DashboardLayout from './layout/DashboardLayout'
import HomePage from './pages/HomePage'
import LandingPage from './pages/LandingPage'

const CompanyDetailPage = lazy(() => import('./pages/CompanyDetailPage'))

export default function App() {
  return (
    <AppErrorBoundary>
      <DashboardLayout>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<HomePage />} />
          <Route
            path="/company/:symbol"
            element={
              <Suspense fallback={<div className="rounded-2xl bg-surface-container p-6 text-onSurface-variant">Loading details...</div>}>
                <CompanyDetailPage />
              </Suspense>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </DashboardLayout>
    </AppErrorBoundary>
  )
}

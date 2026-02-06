import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { AdminLayout, PipelineDashboard } from './pages/admin'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        {/* Main App */}
        <Route path="/" element={<App />} />

        {/* Admin Routes */}
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<Navigate to="/admin/discussion-pipeline" replace />} />
          <Route path="discussion-pipeline" element={<PipelineDashboard />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)

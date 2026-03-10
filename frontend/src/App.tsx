import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { useUserStore } from './stores/userStore'
import LoginPage from './pages/LoginPage'
import UploadPage from './pages/UploadPage'
import ReaderPage from './pages/ReaderPage'
import PipelinePage from './pages/PipelinePage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const userId = useUserStore((s) => s.userId)
  if (!userId) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  const navigate = useNavigate()

  return (
    <Routes>
      <Route path="/login" element={<LoginPage onSuccess={() => navigate('/upload')} />} />
      <Route
        path="/upload"
        element={
          <RequireAuth>
            <UploadPage onSuccess={() => navigate('/reader')} />
          </RequireAuth>
        }
      />
      <Route
        path="/reader"
        element={
          <RequireAuth>
            <ReaderPage />
          </RequireAuth>
        }
      />
      <Route path="/pipeline" element={<PipelinePage />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

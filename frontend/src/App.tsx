import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { useUserStore } from './stores/userStore'
import LoginPage from './pages/LoginPage'
import UploadPage from './pages/UploadPage'
import ReaderPage from './pages/ReaderPage'
import LibraryPage from './pages/LibraryPage'
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
      <Route path="/login" element={<LoginPage onSuccess={() => navigate('/library')} />} />
      <Route
        path="/library"
        element={
          <RequireAuth>
            <LibraryPage />
          </RequireAuth>
        }
      />
      <Route path="/upload" element={<Navigate to="/library" replace />} />
      <Route
        path="/reader/:paperId"
        element={
          <RequireAuth>
            <ReaderPage />
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
      {/* 기존 UploadPage는 직접 접근 시에만 fallback으로 유지 */}
      <Route
        path="/upload-legacy"
        element={
          <RequireAuth>
            <UploadPage onSuccess={() => navigate('/library')} />
          </RequireAuth>
        }
      />
      <Route path="/pipeline" element={<PipelinePage />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

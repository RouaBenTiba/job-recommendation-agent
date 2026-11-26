import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { PublicOnlyRoute } from './components/PublicOnlyRoute'
import { ImportPage } from './pages/ImportPage'
import { LoginPage } from './pages/LoginPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { PreferencesPage } from './pages/PreferencesPage'
import { ProfilePage } from './pages/ProfilePage'
import { RegisterPage } from './pages/RegisterPage'

export default function App() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/import" element={<ImportPage />} />
          <Route path="/preferences" element={<PreferencesPage />} />
        </Route>
      </Route>
      <Route path="/" element={<Navigate to="/profile" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import HomePage from './pages/HomePage'
import DropoutPage from './pages/DropoutPage'
import LevelTestPage from './pages/LevelTestPage'
import CoursesPage from './pages/CoursesPage'
import RecommendPage from './pages/RecommendPage'

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/dropout" element={<DropoutPage />} />
          <Route path="/level-test" element={<LevelTestPage />} />
          <Route path="/courses" element={<CoursesPage />} />
          <Route path="/recommend" element={<RecommendPage />} />
        </Routes>
      </Router>
    </ErrorBoundary>
  )
}

export default App

import { useState, useEffect } from 'react'
import './App.css'
import NotificationPanel from './components/NotificationPanel'
import AnalysisPage from './components/AnalysisPage'
import Dashboard from './components/Dashboard'

export interface Attack {
  id: string
  timestamp: number
  endpoint: string
  method: string
  requestsPerSecond: number
  sourceIPs: number
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: 'detected' | 'mitigated' | 'active'
}

function App() {
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'analysis'>('dashboard')
  const [attacks, setAttacks] = useState<Attack[]>([])
  const [notifications, setNotifications] = useState<string[]>([])

  useEffect(() => {
    const mockAttacks: Attack[] = [
      {
        id: 'ATK001',
        timestamp: Date.now() - 300000,
        endpoint: '/api/users',
        method: 'GET',
        requestsPerSecond: 5000,
        sourceIPs: 342,
        severity: 'critical',
        status: 'mitigated'
      },
      {
        id: 'ATK002',
        timestamp: Date.now() - 60000,
        endpoint: '/api/auth/login',
        method: 'POST',
        requestsPerSecond: 2300,
        sourceIPs: 156,
        severity: 'high',
        status: 'active'
      },
      {
        id: 'ATK003',
        timestamp: Date.now() - 10000, 
        endpoint: '/api/products',
        method: 'GET',
        requestsPerSecond: 890,
        sourceIPs: 87,
        severity: 'medium',
        status: 'detected'
      }
    ]
    setAttacks(mockAttacks)
    setNotifications([
      'Critical DDoS Attack Detected on /api/users - 5000 req/s',
      'High Severity Attack on /api/auth/login - ACTIVE'
    ])
  }, [])

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🛡️ DDoS Attack Detection System</h1>
        <nav className="nav-buttons">
          <button 
            className={`nav-btn ${currentPage === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentPage('dashboard')}
          >
            Dashboard
          </button>
          <button 
            className={`nav-btn ${currentPage === 'analysis' ? 'active' : ''}`}
            onClick={() => setCurrentPage('analysis')}
          >
            Analysis
          </button>
        </nav>
      </header>

      <NotificationPanel notifications={notifications} />

      {currentPage === 'dashboard' && <Dashboard attacks={attacks} />}
      {currentPage === 'analysis' && <AnalysisPage attacks={attacks} />}
    </div>
  )
}

export default App

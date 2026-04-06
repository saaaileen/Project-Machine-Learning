import type { Attack } from '../App'
import './Dashboard.css'

interface DashboardProps {
  attacks: Attack[]
}

function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'critical': return '#ff0000'
    case 'high': return '#ff6600'
    case 'medium': return '#ffcc00'
    case 'low': return '#00cc00'
    default: return '#999'
  }
}

function getStatusBadge(status: string): string {
  switch (status) {
    case 'active': return '🔴 ACTIVE'
    case 'detected': return '🟡 DETECTED'
    case 'mitigated': return '🟢 MITIGATED'
    default: return status
  }
}

function formatTime(timestamp: number): string {
  const now = Date.now()
  const diff = now - timestamp
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (seconds < 60) return `${seconds}s ago`
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export default function Dashboard({ attacks }: DashboardProps) {
  const activeAttacks = attacks.filter(a => a.status === 'active').length
  const totalAttacks = attacks.length
  const avgRequestsPerSecond = Math.round(
    attacks.reduce((sum, a) => sum + a.requestsPerSecond, 0) / attacks.length
  )

  return (
    <div className="dashboard">
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Active Attacks</h3>
          <p className="stat-value">{activeAttacks}</p>
        </div>
        <div className="stat-card">
          <h3>Total Detected</h3>
          <p className="stat-value">{totalAttacks}</p>
        </div>
        <div className="stat-card">
          <h3>Avg Req/s</h3>
          <p className="stat-value">{avgRequestsPerSecond}</p>
        </div>
      </div>

      <div className="attacks-section">
        <h2>Recent Attack Events</h2>
        <div className="attacks-list">
          {attacks.map((attack) => (
            <div 
              key={attack.id} 
              className="attack-card"
              style={{ borderLeftColor: getSeverityColor(attack.severity) }}
            >
              <div className="attack-header">
                <div className="attack-title">
                  <strong>{attack.endpoint}</strong>
                  <span className="method-badge">{attack.method}</span>
                </div>
                <div className="attack-status" style={{ color: getSeverityColor(attack.severity) }}>
                  {getStatusBadge(attack.status)}
                </div>
              </div>
              
              <div className="attack-details">
                <div className="detail-row">
                  <span className="label">ID:</span>
                  <span className="value">{attack.id}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Time:</span>
                  <span className="value">{formatTime(attack.timestamp)}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Requests/s:</span>
                  <span className="value" style={{ color: getSeverityColor(attack.severity) }}>
                    {attack.requestsPerSecond.toLocaleString()}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="label">Source IPs:</span>
                  <span className="value">{attack.sourceIPs}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Severity:</span>
                  <span 
                    className="severity-badge"
                    style={{ 
                      backgroundColor: getSeverityColor(attack.severity),
                      color: attack.severity === 'low' ? '#000' : '#fff'
                    }}
                  >
                    {attack.severity.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

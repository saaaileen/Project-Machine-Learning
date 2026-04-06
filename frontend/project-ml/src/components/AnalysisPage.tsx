import { useState } from 'react'
import type { Attack } from '../App'
import './AnalysisPage.css'

interface AnalysisPageProps {
  attacks: Attack[]
}

export default function AnalysisPage({ attacks }: AnalysisPageProps) {
  const [selectedAttack, setSelectedAttack] = useState<Attack | null>(
    attacks.length > 0 ? attacks[0] : null
  )

  function formatFullTime(timestamp: number): string {
    return new Date(timestamp).toLocaleString()
  }

  function calculateDuration(timestamp: number): string {
    const duration = Date.now() - timestamp
    const minutes = Math.floor((duration / 1000) / 60)
    const seconds = Math.floor((duration / 1000) % 60)
    return `${minutes}m ${seconds}s`
  }

  function getAttackDescription(attack: Attack): string {
    const descriptions: Record<string, string> = {
      critical: `CRITICAL: ${attack.requestsPerSecond.toLocaleString()} requests per second overwhelmed the ${attack.endpoint} endpoint. Attack appears to be coordinated from ${attack.sourceIPs} unique IP addresses.`,
      high: `HIGH SEVERITY: Sustained attack on ${attack.endpoint} with ${attack.requestsPerSecond.toLocaleString()} req/s. Distributed across ${attack.sourceIPs} sources.`,
      medium: `MODERATE: ${attack.endpoint} experiencing elevated traffic (${attack.requestsPerSecond} req/s) from ${attack.sourceIPs} IPs.`,
      low: `LOW: Minor spike on ${attack.endpoint} (${attack.requestsPerSecond} req/s) - likely false positive or testing.`
    }
    return descriptions[attack.severity] || 'Unknown attack type'
  }

  function getMitigationSteps(attack: Attack): string[] {
    const steps: Record<string, string[]> = {
      critical: [
        'Enable rate limiting (100 req/min per IP)',
        'Activate WAF rules',
        'Route traffic through CDN with DDoS protection',
        'Block source IP ranges identified in analysis',
        'Scale up backend infrastructure'
      ],
      high: [
        'Increase rate limiting threshold',
        'Enable basic WAF rules',
        'Monitor traffic patterns',
        'Prepare for traffic spike'
      ],
      medium: [
        'Monitor the situation',
        'Check for legitimate traffic increase',
        'Enable standard rate limiting'
      ],
      low: [
        'Log the event',
        'Continue regular monitoring'
      ]
    }
    return steps[attack.severity] || []
  }

  const byEndpoint = attacks.reduce((acc, attack) => {
    acc[attack.endpoint] = (acc[attack.endpoint] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const bySeverity = attacks.reduce((acc, attack) => {
    acc[attack.severity] = (acc[attack.severity] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div className="analysis-page">
      <div className="analysis-container">
        <div className="analysis-left">
          <h2>Attack Timeline</h2>
          <div className="attack-list">
            {attacks.map((attack) => (
              <div
                key={attack.id}
                className={`attack-timeline-item ${selectedAttack?.id === attack.id ? 'selected' : ''}`}
                onClick={() => setSelectedAttack(attack)}
              >
                <div className="timeline-indicator" style={{ backgroundColor: 
                  attack.severity === 'critical' ? '#ff0000' :
                  attack.severity === 'high' ? '#ff6600' :
                  attack.severity === 'medium' ? '#ffcc00' : '#00cc00'
                }}></div>
                <div className="timeline-info">
                  <strong>{attack.endpoint}</strong>
                  <small>{attack.severity.toUpperCase()}</small>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="analysis-right">
          {selectedAttack && (
            <>
              <div className="attack-analysis">
                <h2>Attack Analysis: {selectedAttack.id}</h2>

                <section className="analysis-section">
                  <h3>📊 Overview</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <label>Endpoint</label>
                      <span className="value">{selectedAttack.endpoint}</span>
                    </div>
                    <div className="info-item">
                      <label>HTTP Method</label>
                      <span className="value">{selectedAttack.method}</span>
                    </div>
                    <div className="info-item">
                      <label>Detected At</label>
                      <span className="value">{formatFullTime(selectedAttack.timestamp)}</span>
                    </div>
                    <div className="info-item">
                      <label>Duration</label>
                      <span className="value">{calculateDuration(selectedAttack.timestamp)}</span>
                    </div>
                    <div className="info-item">
                      <label>Status</label>
                      <span className={`value status-${selectedAttack.status}`}>
                        {selectedAttack.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="info-item">
                      <label>Severity</label>
                      <span className={`value severity-${selectedAttack.severity}`}>
                        {selectedAttack.severity.toUpperCase()}
                      </span>
                    </div>
                  </div>
                </section>

                <section className="analysis-section">
                  <h3>Attack Pattern</h3>
                  <p className="description">{getAttackDescription(selectedAttack)}</p>
                  <div className="metrics">
                    <div className="metric">
                      <span className="metric-label">Requests per Second:</span>
                      <span className="metric-value">{selectedAttack.requestsPerSecond.toLocaleString()}</span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">Unique Source IPs:</span>
                      <span className="metric-value">{selectedAttack.sourceIPs}</span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">Avg Req per IP:</span>
                      <span className="metric-value">
                        {(selectedAttack.requestsPerSecond / selectedAttack.sourceIPs).toFixed(0)}
                      </span>
                    </div>
                  </div>
                </section>

                <section className="analysis-section">
                  <h3>Mitigation Steps</h3>
                  <ol className="mitigation-steps">
                    {getMitigationSteps(selectedAttack).map((step, idx) => (
                      <li key={idx}>{step}</li>
                    ))}
                  </ol>
                </section>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="statistics-section">
        <h2>Overall Statistics</h2>
        <div className="stats-grid">
          <div className="stat-box">
            <h4>Attacks by Endpoint</h4>
            <div className="stat-content">
              {Object.entries(byEndpoint).map(([endpoint, count]) => (
                <div key={endpoint} className="stat-row">
                  <span>{endpoint}</span>
                  <span className="count">{count}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="stat-box">
            <h4>Attacks by Severity</h4>
            <div className="stat-content">
              {Object.entries(bySeverity).map(([severity, count]) => (
                <div key={severity} className="stat-row">
                  <span>{severity.toUpperCase()}</span>
                  <span className="count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

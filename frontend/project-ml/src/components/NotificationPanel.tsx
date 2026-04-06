import './NotificationPanel.css'

interface NotificationPanelProps {
  notifications: string[]
}

export default function NotificationPanel({ notifications }: NotificationPanelProps) {
  return (
    <div className="notification-panel">
      <div className="notification-container">
        {notifications.length === 0 ? (
          <div className="notification-item safe">
            <span className="indicator"></span>
            All systems secure - No active attacks detected
          </div>
        ) : (
          notifications.map((notif, index) => (
            <div key={index} className="notification-item alert">
              <span className="indicator"></span>
              {notif}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

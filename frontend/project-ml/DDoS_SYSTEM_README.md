# 🛡️ DDoS Attack Detection & Analysis System

A modern web application for monitoring, detecting, and analyzing DDoS (Distributed Denial of Service) attacks on your website. This system provides real-time notifications and comprehensive analytics about attack patterns.

## 📋 Features

### 1. **Real-time Notifications**
   - Instant alerts when DDoS attacks are detected
   - Color-coded severity indicators (Critical, High, Medium, Low)
   - Status indicators (Active, Detected, Mitigated)
   - Safe state notification when no attacks are detected

### 2. **Dashboard**
   - **Live Statistics**
     - Total number of active attacks
     - Total attacks detected
     - Average requests per second across all attacks
   
   - **Attack Event List**
     - Detailed attack cards with attack information
     - Shows endpoint being attacked
     - HTTP method used
     - Current status
     - Request rate metrics
     - Number of unique source IP addresses
     - Severity classification

### 3. **Analysis Page**
   - **Attack Timeline**: Visual timeline of all detected attacks
   - **Detailed Analysis**:
     - Complete attack overview with metadata
     - Attack pattern description
     - Request metrics and distribution analysis
     - Recommended mitigation steps based on severity
   
   - **Overall Statistics**:
     - Breakdown of attacks by endpoint
     - Analysis by severity level

## 🎨 Dashboard Components

### Notification Panel
- Shows active alert notifications at the top of the page
- Displays critical and high-severity attacks
- Shows success message when all systems are secure

### Dashboard View
- **Stats Cards**: Key metrics at a glance
- **Attack Cards**: Detailed information for each recent attack
- Color-coded left border by severity level
- Quick reference badges for HTTP methods

### Analysis View
- **Interactive Attack Timeline**: Click to select attacks for detailed analysis
- **Comprehensive Description**: Understanding what happened during the attack
- **Mitigation Steps**: Actionable recommendations for response
- **Statistical Breakdown**: Patterns and distributions

## 🚨 Severity Levels

- **🔴 CRITICAL** (Red): 4000+ req/s - Immediate action required
- **🟠 HIGH** (Orange): 1000-3999 req/s - Urgent attention needed
- **🟡 MEDIUM** (Yellow): 500-999 req/s - Should investigate
- **🟢 LOW** (Green): <500 req/s - Monitor for patterns

## 📊 Attack Status

- **🔴 ACTIVE**: Attack currently in progress
- **🟡 DETECTED**: Attack identified but not yet fully assessed
- **🟢 MITIGATED**: Attack has been stopped or blocked

## 🛠️ Technology Stack

- **Frontend Framework**: React 19
- **Language**: TypeScript
- **Build Tool**: Vite
- **Styling**: CSS3 with CSS Grid and Flexbox
- **UI Pattern**: Component-based architecture

## 📦 Data Points Tracked

Each attack record includes:
- Attack ID (e.g., ATK001)
- Timestamp of detection
- Target endpoint (e.g., /api/users)
- HTTP method (GET, POST, etc.)
- Requests per second
- Number of unique source IPs
- Severity classification
- Current status

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Open your browser to `http://localhost:5173`

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## 📱 Responsive Design

The application is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile devices

Navigation automatically adjusts for smaller screens.

## 🎯 Usage Guide

### Dashboard
1. Check the **Notification Panel** at the top for active alerts
2. View **Key Statistics** showing active attacks and average request rates
3. Browse the **Recent Attack Events** list for detailed information
4. Click on specific attack endpoints for more details

### Analysis Page
1. Select an attack from the **Attack Timeline** on the left
2. Review the **Overview** section for basic attack information
3. Check the **Attack Pattern** description for context
4. Follow the **Mitigation Steps** recommendations

## 🔍 Mock Data

The system currently uses mock data for demonstration. Attack events include:
- Critical attack on `/api/users` (5000 req/s) - MITIGATED
- High severity attack on `/api/auth/login` (2300 req/s) - ACTIVE
- Medium severity on `/api/products` (890 req/s) - DETECTED

To integrate with a real backend, replace the mock data in `App.tsx` with API calls.

## 🔗 API Integration (Future)

The application is structured to easily connect to a backend API. Modify the `useEffect` hook in `App.tsx` to call your real attack detection API.

Example endpoint structure:
```
GET /api/attacks
GET /api/attacks/:id
GET /api/statistics
```

## 📝 Customization

### Changing Colors
Edit color variables in `src/index.css`:
- `--accent-primary`: Main brand color
- `--danger`, `--warning`, `--success`: Alert colors

### Modifying Attack Data Structure
Update the `Attack` interface in `src/App.tsx` to match your API response format.

## ⚖️ License

This project is provided as-is for educational and testing purposes.

## 📞 Support

For questions or issues, please refer to the component documentation in the source code.

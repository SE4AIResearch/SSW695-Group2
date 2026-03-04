# Bug Triaging System - Web Dashboard

AI-powered bug triaging dashboard for automated categorization and assignment.

## Prerequisites

- Node.js 18+ ([Download here](https://nodejs.org/))
- npm (comes with Node.js)

## Setup

1. **Clone the repository**
```bash
git clone https://github.com/YOUR-USERNAME/SSW695-Group2.git
cd SSW695-Group2/web-dashboard
```

2. **Install dependencies**
```bash
npm install
```

3. **Create environment file**
Create `.env` file in the root:
```env
REACT_APP_GITHUB_CLIENT_ID=your_github_client_id_here
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## Run

**Start development server:**
```bash
npm start
```

The app will open at `http://localhost:3000`

**Default login:**
- Email: `admin@test.com`
- Password: `admin123`

Or use **Sign in with GitHub**

## Build for Production
```bash
npm run build
```

Output will be in the `build/` folder.

## Project Structure
```
web-dashboard/
├── public/
├── src/
│   ├── components/    # Reusable components
│   ├── pages/         # Main pages (Login, Dashboard, etc.)
│   └── services/      # API and auth services
├── package.json
└── README.md
```

## Available Pages

- `/login` - Login page
- `/dashboard` - Main dashboard with analytics
- `/team` - Team management (coming soon)

## Tech Stack

- React 18
- Material-UI (MUI)
- Recharts (for graphs)
- React Router
- Axios

## Troubleshooting

**Port already in use:**
```bash
# Kill process on port 3000
npx kill-port 3000
# Or change port
PORT=3001 npm start
```

**Dependencies error:**
```bash
rm -rf node_modules package-lock.json
npm install
```

## Team

SSW695 Capstone - Group 2

---

For detailed documentation, see the main project README.
# SmartCommerce Kenya - Frontend

React + Vite frontend for SmartCommerce Kenya e-commerce platform.

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The app will be available at http://localhost:5173

### Build

```bash
npm run build
```

### Lint

```bash
npm run lint
```

### Test

```bash
npm test
```

## Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/          # Page components
├── hooks/          # Custom React hooks
├── services/       # API services
├── store/          # State management (Zustand)
├── utils/          # Utility functions
└── App.jsx         # Main app component
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `VITE_API_URL` - Backend API URL

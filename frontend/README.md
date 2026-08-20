# CodeSanitize - Frontend

React + TypeScript + Vite web interface for **CodeSanitize**.

## Features

- Modern dark-mode developer UI with line numbers and monospace editor
- Live backend connection health and latency indicator
- Language selection with syntax samples
- Explicit pipeline readiness indicators with zero fake analysis mockups
- Safe transformation controls with planned extension indicators

## Getting Started

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The application will be accessible at `http://127.0.0.1:5173`.
Vite is pre-configured to proxy `/api` requests to `http://127.0.0.1:8000`.

### 3. Production Build & Typecheck

```bash
npm run build
```

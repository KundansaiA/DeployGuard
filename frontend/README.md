# Frontend — DeployGuard

React + TypeScript dashboard for DeployGuard.

## Structure

```
src/
├── api/          # Typed API client modules (no direct fetch in components)
├── components/   # Reusable UI components
├── pages/        # Top-level page components
├── types/        # Shared TypeScript types
└── main.tsx      # Application entry point
```

## Quick start

```bash
npm install
npm run dev       # dev server on http://localhost:5173
npm run build     # production build
npm test          # run all tests
```

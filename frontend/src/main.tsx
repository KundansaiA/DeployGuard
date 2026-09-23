import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AnalysisListPage from './pages/AnalysisListPage';
import AnalysisDetailPage from './pages/AnalysisDetailPage';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/analyses" replace />} />
        <Route path="/analyses" element={<AnalysisListPage />} />
        <Route path="/analyses/:id" element={<AnalysisDetailPage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);

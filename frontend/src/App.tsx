import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { WorkspaceProvider } from './context/WorkspaceContext';
import { DashboardLayout } from './layout/DashboardLayout';
import { Dashboard } from './pages/Dashboard';
import { Analyze } from './pages/Analyze';
import { Transform } from './pages/Transform';
import { Security } from './pages/Security';
import { Provenance } from './pages/Provenance';
import { ScanHistory } from './pages/ScanHistory';
import { Settings } from './pages/Settings';

export function App() {
  return (
    <WorkspaceProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<DashboardLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="analyze" element={<Analyze />} />
            <Route path="transform" element={<Transform />} />
            <Route path="security" element={<Security />} />
            <Route path="provenance" element={<Provenance />} />
            <Route path="history" element={<ScanHistory />} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </WorkspaceProvider>
  );
}

export default App;

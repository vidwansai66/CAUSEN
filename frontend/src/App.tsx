import { Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';

// Placeholder Pages
import Overview from './pages/Overview/Overview';
import LiveProduction from './pages/LiveProduction/LiveProduction';
import IncidentAnalysis from './pages/IncidentAnalysis/IncidentAnalysis';
import RecoverySimulator from './pages/RecoverySimulator/RecoverySimulator';
import MaintenanceActions from './pages/MaintenanceActions/MaintenanceActions';
import SystemActivity from './pages/SystemActivity/SystemActivity';

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<Overview />} />
        <Route path="live" element={<LiveProduction />} />
        <Route path="incident" element={<IncidentAnalysis />} />
        <Route path="simulator" element={<RecoverySimulator />} />
        <Route path="actions" element={<MaintenanceActions />} />
        <Route path="activity" element={<SystemActivity />} />
      </Route>
    </Routes>
  );
}

export default App;

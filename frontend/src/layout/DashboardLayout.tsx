import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopNavbar } from './TopNavbar';
import { PrintableReport } from '../components/PrintableReport';

export const DashboardLayout: React.FC = () => {
  return (
    <div className="enterprise-dashboard-root">
      {/* Fixed Left Sidebar */}
      <Sidebar />

      {/* Main Viewport Container */}
      <div className="main-viewport-wrapper">
        {/* Top Navbar */}
        <TopNavbar />

        {/* Dynamic Page Content Outlet */}
        <main className="content-outlet-scrollable">
          <Outlet />
        </main>
      </div>

      {/* Dedicated Print-Optimized Report (Hidden on Screen, Rendered Exclusively on @media print) */}
      <PrintableReport />
    </div>
  );
};


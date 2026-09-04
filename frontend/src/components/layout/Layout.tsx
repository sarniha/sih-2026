import React from "react";
import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export const Layout: React.FC = () => {
  return (
    <div className="flex flex-col h-screen w-screen bg-[#0b0f17] text-slate-100 overflow-hidden">
      {/* Top Command Header */}
      <Header />

      {/* Main Workspace Rail + Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Navigation Sidebar */}
        <Sidebar />

        {/* Page Viewport Area */}
        <main className="flex-1 h-full overflow-hidden bg-[#0b0f17] relative flex flex-col">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

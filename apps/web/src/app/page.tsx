'use client';

import { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import MissionControl from '@/components/MissionControl';
import ActiveOperation from '@/components/ActiveOperation';
import KnowledgeBase from '@/components/KnowledgeBase';
import ToolsPage from '@/components/ToolsPage';
import AgentsPage from '@/components/AgentsPage';
import axios from 'axios';

export default function Home() {
  const [view, setView] = useState<'dashboard' | 'active_scan' | 'knowledge' | 'tools' | 'agents'>('dashboard');
  const [target, setTarget] = useState('');

  const handleExecute = async (prompt: string, selectedTasks: string[]) => {
    // 1. Determine Target (Mock logic for UI demo)
    const extractedTarget = prompt.split(' ').find(w => w.includes('.')) || '174.138.49.41';
    setTarget(extractedTarget);

    // 2. Switch View (simulating immediate response, real app would wait for ack)
    setView('active_scan');

    // 3. Fire & Forget API call
    try {
      await axios.post('http://localhost:8000/api/v1/scan/start', {
        target: extractedTarget,
        scan_type: 'custom',
        tasks: selectedTasks
      });
    } catch (e) {
      console.error("API link failed, showing UI demo only");
    }
  };

  return (
    <div className="flex h-screen w-full bg-[#050505]">
      {/* Sidebar is always present */}
      <Sidebar onViewChange={setView} currentView={view} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative overflow-hidden">
        {view === 'dashboard' && <MissionControl onExecute={handleExecute} />}
        {view === 'active_scan' && <ActiveOperation target={target} />}
        {view === 'knowledge' && <KnowledgeBase />}
        {view === 'tools' && <ToolsPage />}
        {view === 'agents' && <AgentsPage />}
      </div>
    </div>
  );
}

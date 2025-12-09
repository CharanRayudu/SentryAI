'use client';

import { useState } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import CommandCenter from '@/components/CommandCenter';
import SchedulesPage from '@/components/SchedulesPage';
import IntegrationsPage from '@/components/IntegrationsPage';
import FindingsTable from '@/components/FindingsTable';
import ActiveOperation from '@/components/ActiveOperation';

type ViewType = 'new' | 'agents' | 'files' | 'knowledge' | 'console' | 'findings' | 'operations' | 'schedules' | 'integrations';

export default function Home() {
    const [activeView, setActiveView] = useState<ViewType>('new');
    const [activeTarget, setActiveTarget] = useState<string | null>(null);

    const handleExecute = (prompt: string, tasks: string[]) => {
        // Extract target from prompt (simple heuristic)
        const targetMatch = prompt.match(/([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}/);
        if (targetMatch) {
            setActiveTarget(targetMatch[0]);
            setActiveView('operations');
        }
    };

    const renderContent = () => {
        switch (activeView) {
            case 'new':
                return <CommandCenter />;
            
            case 'operations':
                if (activeTarget) {
                    return (
                        <ActiveOperation 
                            target={activeTarget} 
                            onComplete={() => {
                                setActiveTarget(null);
                                setActiveView('findings');
                            }}
                        />
                    );
                }
                return <CommandCenter />;
            
            case 'findings':
                return <FindingsTable />;
            
            case 'schedules':
                return <SchedulesPage />;
            
            case 'integrations':
                return <IntegrationsPage />;
            
            case 'agents':
            case 'files':
            case 'knowledge':
            case 'console':
                return (
                    <div className="flex-1 flex items-center justify-center">
                        <div className="text-center">
                            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-zinc-900 border border-zinc-800 mb-4">
                                <span className="text-2xl">🚧</span>
                            </div>
                            <h3 className="text-lg font-medium text-white mb-2 capitalize">{activeView}</h3>
                            <p className="text-sm text-zinc-500">This section is under construction</p>
                        </div>
                    </div>
                );
            
            default:
                return <CommandCenter />;
        }
    };

    return (
        <div className="flex h-screen bg-[#050505] text-white overflow-hidden">
            <Sidebar activeView={activeView} onViewChange={(view) => setActiveView(view as ViewType)} />
            {renderContent()}
        </div>
    );
}

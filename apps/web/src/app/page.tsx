'use client';

import { useState } from 'react';
import { AppLayout } from '@/components/layout/AppLayout';
import Sidebar from '@/components/layout/Sidebar';
import PromptInput from '@/components/PromptInput';
import TaskExecutionList from '@/components/TaskExecutionList';
import WorkspacePanel from '@/components/WorkspacePanel';
import FindingsTable from '@/components/FindingsTable';
import SchedulesPage from '@/components/SchedulesPage';
import IntegrationsPage from '@/components/IntegrationsPage';
import ActiveOperation from '@/components/ActiveOperation';
import { useTaskStore } from '@/stores/useTaskStore';

function OperationsPage() {
    return (
        <div className="flex flex-col h-full p-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-white">Active Operations</h1>
                <p className="text-zinc-500 text-sm">Monitor your running security scans</p>
            </div>
            <div className="flex-1 flex items-center justify-center neo-panel rounded-xl border-dashed">
                <div className="text-center text-zinc-500">
                    <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-medium text-white mb-2">No active operations</h3>
                    <p className="text-sm">Start a new scan to see it here</p>
                </div>
            </div>
        </div>
    );
}

function KnowledgePage() {
    return (
        <div className="flex flex-col h-full p-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-white">Knowledge Base</h1>
                <p className="text-zinc-500 text-sm">Upload documents to enhance AI context</p>
            </div>
            <div className="flex-1 flex items-center justify-center neo-panel rounded-xl border-dashed">
                <div className="text-center text-zinc-500">
                    <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-medium text-white mb-2">No documents uploaded</h3>
                    <p className="text-sm mb-4">Upload Swagger specs, network diagrams, or security policies</p>
                    <button className="btn-gradient">Upload Document</button>
                </div>
            </div>
        </div>
    );
}

function AgentsPage() {
    const agents = [
        { name: 'Pentest Agent', status: 'online', tasks: 0, description: 'Full-stack penetration testing' },
        { name: 'Recon Agent', status: 'online', tasks: 0, description: 'Subdomain & asset discovery' },
        { name: 'Vuln Scanner', status: 'online', tasks: 0, description: 'CVE & vulnerability detection' },
        { name: 'Code Reviewer', status: 'idle', tasks: 0, description: 'Static code analysis' },
    ];

    return (
        <div className="flex flex-col h-full p-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-white">AI Agents</h1>
                <p className="text-zinc-500 text-sm">Manage your security agents</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {agents.map((agent) => (
                    <div key={agent.name} className="neo-panel p-5 rounded-xl hover:border-white/[0.15] transition-all cursor-pointer">
                        <div className="flex items-start justify-between mb-3">
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30 flex items-center justify-center">
                                <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                            </div>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${agent.status === 'online' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-zinc-500/10 text-zinc-400 border border-zinc-500/20'}`}>
                                {agent.status}
                            </span>
                        </div>
                        <h3 className="font-semibold text-white mb-1">{agent.name}</h3>
                        <p className="text-sm text-zinc-500">{agent.description}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}

function ConsolePage() {
    return (
        <div className="flex flex-col h-full p-6">
            <div className="mb-4">
                <h1 className="text-2xl font-bold text-white">Console</h1>
                <p className="text-zinc-500 text-sm">System logs and debug output</p>
            </div>
            <div className="flex-1 neo-panel rounded-xl overflow-hidden flex flex-col">
                <div className="flex items-center justify-between px-4 py-2 bg-white/[0.02] border-b border-white/[0.06]">
                    <span className="text-xs font-mono text-zinc-500">SYSTEM_CONSOLE</span>
                    <div className="flex gap-1.5">
                        <div className="w-2 h-2 rounded-full bg-green-500/50" />
                    </div>
                </div>
                <div className="flex-1 p-4 font-mono text-sm text-zinc-400 overflow-y-auto custom-scrollbar">
                    <div className="text-green-400">[SentryAI] System initialized</div>
                    <div className="text-zinc-500">[INFO] Waiting for commands...</div>
                    <div className="text-zinc-500">[INFO] Connected to local worker</div>
                    <div className="mt-2">
                        <span className="text-purple-400">$</span>
                        <span className="ml-2 animate-pulse">_</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

function FilesPage() {
    return (
        <div className="flex flex-col h-full p-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-white">Files</h1>
                <p className="text-zinc-500 text-sm">Scan outputs and reports</p>
            </div>
            <div className="flex-1 flex items-center justify-center neo-panel rounded-xl border-dashed">
                <div className="text-center text-zinc-500">
                    <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-medium text-white mb-2">No files yet</h3>
                    <p className="text-sm">Scan outputs will appear here</p>
                </div>
            </div>
        </div>
    );
}

export default function Home() {
    const [activeView, setActiveView] = useState('new');
    const { omnibarPosition } = useTaskStore();

    const renderContent = () => {
        switch (activeView) {
            case 'findings':
                return <FindingsTable />;
            case 'schedules':
                return <SchedulesPage />;
            case 'integrations':
                return <IntegrationsPage />;
            case 'operations':
                return <OperationsPage />;
            case 'knowledge':
                return <KnowledgePage />;
            case 'agents':
                return <AgentsPage />;
            case 'console':
                return <ConsolePage />;
            case 'files':
                return <FilesPage />;
            case 'new':
            default:
                return (
                    <div className={`
                        w-full h-full flex flex-col p-6 transition-all duration-500
                        ${omnibarPosition === 'center' ? 'justify-center items-center' : 'justify-start'}
                    `}>
                        <div className={`
                            w-full max-w-4xl mx-auto flex flex-col transition-all duration-500
                            ${omnibarPosition === 'center' ? 'flex-grow-0' : 'flex-grow h-full'}
                        `}>
                            <PromptInput />

                            {omnibarPosition === 'top' && (
                                <div className="flex-grow flex flex-col overflow-hidden">
                                    <div className="flex-shrink-0 max-h-[40%] overflow-y-auto custom-scrollbar pr-2">
                                        <TaskExecutionList />
                                    </div>
                                    <WorkspacePanel />
                                </div>
                            )}
                        </div>
                    </div>
                );
        }
    };

    return (
        <AppLayout
            sidebar={
                <Sidebar
                    activeView={activeView}
                    onViewChange={setActiveView}
                />
            }
        >
            {renderContent()}
        </AppLayout>
    );
}
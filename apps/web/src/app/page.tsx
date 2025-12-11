'use client';

import { useState, useEffect, useMemo, useRef } from 'react';
import { useAgentSocket } from '@/hooks/useAgentSocket';
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

type PlanProposalMessage = {
    type: 'server:plan_proposal';
    mission_id?: string;
    plan_id?: string;
    thought_process?: string;
    steps?: string[];
};

function OperationsPage() {
    const { activeTaskId } = useTaskStore();

    if (activeTaskId) {
        return <ActiveOperation taskId={activeTaskId} />;
    }

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

type KnowledgeDoc = { name: string; size: number; uploadedAt: string };

function KnowledgePage() {
    const [documents, setDocuments] = useState<KnowledgeDoc[]>([]);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(event.target.files || []);
        if (!files.length) return;

        const timestamp = new Date().toLocaleString();
        const uploaded = files.map((file) => ({ name: file.name, size: file.size, uploadedAt: timestamp }));
        setDocuments((prev) => [...uploaded, ...prev]);
        event.target.value = '';
    };

    const removeDocument = (name: string) => {
        setDocuments((prev) => prev.filter((doc) => doc.name !== name));
    };

    return (
        <div className="flex flex-col h-full p-6">
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Knowledge Base</h1>
                    <p className="text-zinc-500 text-sm">Upload documents to enhance AI context</p>
                </div>
                <button
                    onClick={() => fileInputRef.current?.click()}
                    className="btn-gradient"
                >
                    Upload Document
                </button>
                <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    className="hidden"
                    onChange={handleUpload}
                />
            </div>

            <div className="flex-1 neo-panel rounded-xl border-dashed p-6 overflow-y-auto">
                {documents.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center text-zinc-500">
                        <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto mb-4">
                            <svg className="w-8 h-8 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-medium text-white mb-2">No documents uploaded</h3>
                        <p className="text-sm mb-4">Upload Swagger specs, network diagrams, or security policies</p>
                        <button className="btn-gradient" onClick={() => fileInputRef.current?.click()}>Choose files</button>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {documents.map((doc) => (
                            <div
                                key={doc.name}
                                className="flex items-center justify-between p-4 rounded-lg border border-white/10 bg-white/[0.02]"
                            >
                                <div>
                                    <p className="text-white text-sm font-medium">{doc.name}</p>
                                    <p className="text-xs text-zinc-500">{(doc.size / 1024).toFixed(1)} KB · Uploaded {doc.uploadedAt}</p>
                                </div>
                                <button
                                    className="text-xs text-red-400 hover:text-red-300"
                                    onClick={() => removeDocument(doc.name)}
                                >
                                    Remove
                                </button>
                            </div>
                        ))}
                    </div>
                )}
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
    const { activeTaskId } = useTaskStore();

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
                    {activeTaskId ? (
                        <LogStream taskId={activeTaskId} />
                    ) : (
                        <div className="text-zinc-600 italic">No active session connected...</div>
                    )}
                </div>
            </div>
        </div>
    );
}

function LogStream({ taskId }: { taskId: string }) {
    const { tasks } = useTaskStore();
    const task = tasks.find(t => t.id === taskId);

    if (!task) return null;

    return (
        <div className="space-y-1">
            <div className="text-green-400">[SentryAI] Session {taskId} initialized</div>
            {task.logs.map((log, i) => (
                <div key={i} className="text-zinc-300">
                    <span className="text-purple-500 mr-2">$</span>
                    {log}
                </div>
            ))}
            {task.status === 'running' && (
                <div className="mt-2">
                    <span className="text-purple-400">$</span>
                    <span className="ml-2 animate-pulse">_</span>
                </div>
            )}
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
    const { omnibarPosition, updateTask, tasks } = useTaskStore();
    const { lastMessage } = useAgentSocket();

    const stats = useMemo(() => {
        const fileCount = tasks.reduce((acc, task) => acc + (task.artifacts?.length ?? 0), 0);
        const running = tasks.filter((task) => task.status === 'running').length;
        const logLines = tasks.reduce((acc, task) => acc + task.logs.length, 0);

        return [
            { label: 'Tasks', value: tasks.length },
            { label: 'Running', value: running },
            { label: 'Files', value: fileCount },
            { label: 'Logs', value: logLines }
        ];
    }, [tasks]);

    // Handle WebSocket messages globally
    useEffect(() => {
        if (lastMessage) {
            if (lastMessage.type === 'server:plan_proposal') {
                const plan = lastMessage as PlanProposalMessage;
                console.log("Received plan proposal:", plan);

                // Find task by mission_id or active task
                // Since the message usually comes after start, we assume we want to update the relevant task.
                // The task ID in store matches mission_id.
                if (plan.mission_id || plan.plan_id) {
                    const missionId = plan.mission_id || plan.plan_id;
                    updateTask(missionId, {
                        status: 'planning',
                        plan: {
                            thought_process: plan.thought_process,
                            steps: plan.steps
                        }
                    });
                    // eslint-disable-next-line react-hooks/set-state-in-effect
                    setActiveView('operations');
                }
            } else if (lastMessage.type === 'server:job_status') {
                // Handle other status updates if needed
                if (lastMessage.status === 'running' && lastMessage.mission_id) {
                    updateTask(lastMessage.mission_id as string, { status: 'running' });
                }
            }
        }
    }, [lastMessage, updateTask]);

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
                    <div className={`w-full h-full flex flex-col transition-all duration-500 ${omnibarPosition === 'center' ? 'justify-center items-center' : 'justify-start'} py-8`}>
                        <div className="relative w-full max-w-6xl mx-auto flex flex-col gap-6">
                            <div className="absolute inset-0 -z-10 pointer-events-none">
                                <div className="absolute -top-32 right-10 w-72 h-72 bg-primary-glow blur-[160px] opacity-30" />
                                <div className="absolute top-10 left-0 w-64 h-64 bg-blue-500/30 blur-[150px] opacity-30" />
                            </div>

                            <div className={`flex flex-col gap-2 ${omnibarPosition === 'center' ? 'text-center items-center' : 'text-left'}`}>
                                <p className="text-xs uppercase tracking-[0.24em] text-zinc-600 font-semibold">Matrix API Security</p>
                                <h1 className="text-4xl font-semibold text-white leading-tight">Describe the task you want me to execute.</h1>
                                <p className="text-zinc-500 max-w-2xl">Delegate research, reconnaissance, and vulnerability discovery to the autonomous agent. I will track artifacts, connections, and variables as the mission unfolds.</p>
                                <div className="flex flex-wrap gap-2 mt-1">
                                    {stats.map((stat) => (
                                        <span key={stat.label} className="stat-pill">
                                            {stat.label} · {stat.value}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <PromptInput />

                            <div className="glass-card border border-white/10 rounded-2xl overflow-hidden">
                                <div className="px-5 py-4 border-b border-white/5 flex items-center gap-3 text-sm text-white">
                                    <div className="w-8 h-8 rounded-full bg-white/[0.05] border border-white/10 flex items-center justify-center">
                                        <svg viewBox="0 0 24 24" className="w-4 h-4 text-white" fill="none" stroke="currentColor" strokeWidth="1.4">
                                            <path d="M3 9h18M4 5h16M6 13h12M9 17h6" strokeLinecap="round" />
                                        </svg>
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-xs uppercase tracking-[0.22em] text-zinc-500">Mission Planning</span>
                                        <span>Generating plan...</span>
                                    </div>
                                </div>
                                <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-zinc-300">
                                    {[
                                        'Researching · api security vulnerabilities, OWASP top 10',
                                        'Memory recall · found 4 relevant conversations',
                                        'Knowledge search · api-endpoints.yaml, nuclei-templates.json, auth-flow-...',
                                        'Web search · matrix corp api documentation, recent CVEs',
                                        'Analyzing · identifying attack vectors and test scenarios',
                                    ].map((item) => (
                                        <div key={item} className="flex items-center gap-2 rounded-xl bg-white/[0.03] border border-white/5 px-3 py-2">
                                            <span className="w-2 h-2 rounded-full bg-amber-400" />
                                            <span className="text-zinc-200">{item}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="glass-card border border-white/10 rounded-2xl overflow-hidden">
                                <div className="flex items-center gap-2 px-5 py-3 border-b border-white/5 text-sm text-zinc-400">
                                    {stats.map((tab, idx) => (
                                        <button
                                            key={tab.label}
                                            className={`pill-tab ${idx === 0 ? 'active' : ''}`}
                                        >
                                            {tab.label} {tab.value}
                                        </button>
                                    ))}
                                </div>
                                <div className="p-4">
                                    <TaskExecutionList />
                                </div>
                            </div>

                            {omnibarPosition === 'top' && (
                                <WorkspacePanel />
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

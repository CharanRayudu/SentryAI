import React, { useState } from 'react';
import { Terminal, FileText, Code2, Maximize2, MoreHorizontal } from 'lucide-react';
import { useTaskStore } from '@/stores/useTaskStore';

function LogStream({ taskId }: { taskId: string }) {
    const { tasks } = useTaskStore();
    const task = tasks.find(t => t.id === taskId);

    if (!task) return null;

    return (
        <div className="space-y-1">
            <div className="text-green-400 mb-2"># Mission: {task.title} (ID: {task.id})</div>
            {task.logs.map((log, i) => (
                <div key={i} className="text-zinc-300">
                    <span className="text-zinc-600 mr-2">[{i}]</span>
                    {log}
                </div>
            ))}
            {task.status === 'running' && (
                <div className="mt-2">
                    <span className="text-purple-400 animate-pulse">_</span>
                </div>
            )}
        </div>
    );
}

export default function WorkspacePanel() {
    const [activeTab, setActiveTab] = useState<'terminal' | 'report' | 'diff'>('terminal');
    const { activeTaskId } = useTaskStore();

    return (
        <div className="flex-grow flex flex-col mt-6 w-full max-w-5xl mx-auto min-h-[320px] glass-card border border-white/10">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06] bg-white/[0.02]">
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setActiveTab('terminal')}
                        className={`pill-tab ${activeTab === 'terminal' ? 'active' : ''}`}
                    >
                        <div className="flex items-center gap-1.5 text-sm">
                            <Terminal size={14} />
                            Console
                        </div>
                    </button>
                    <button
                        onClick={() => setActiveTab('report')}
                        className={`pill-tab ${activeTab === 'report' ? 'active' : ''}`}
                    >
                        <div className="flex items-center gap-1.5 text-sm">
                            <FileText size={14} />
                            Report
                        </div>
                    </button>
                    <button
                        onClick={() => setActiveTab('diff')}
                        className={`pill-tab ${activeTab === 'diff' ? 'active' : ''}`}
                    >
                        <div className="flex items-center gap-1.5 text-sm">
                            <Code2 size={14} />
                            Diff
                        </div>
                    </button>
                </div>

                <div className="flex items-center gap-2 text-xs text-zinc-500">
                    <span className="stat-pill">
                        <span className="w-2 h-2 rounded-full bg-green-400 inline-flex" />
                        Live
                    </span>
                    <button className="toolbar-btn">
                        <Maximize2 size={14} />
                    </button>
                    <button className="toolbar-btn">
                        <MoreHorizontal size={14} />
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 relative font-mono text-sm overflow-hidden">
                {activeTab === 'terminal' && (
                    <div className="absolute inset-0 p-5 overflow-auto custom-scrollbar bg-gradient-to-b from-white/[0.01] to-transparent">
                        {activeTaskId ? (
                            <LogStream taskId={activeTaskId} />
                        ) : (
                            <div className="text-zinc-500 mb-2">SentryAI Terminal v2.0.4 initialized... waiting for mission.</div>
                        )}
                    </div>
                )}

                {activeTab === 'report' && (
                    <div className="absolute inset-0 flex items-center justify-center text-zinc-600">
                        No active reports generated.
                    </div>
                )}

                {activeTab === 'diff' && (
                    <div className="absolute inset-0 flex items-center justify-center text-zinc-600">
                        No pending code changes.
                    </div>
                )}
            </div>
        </div>
    );
}

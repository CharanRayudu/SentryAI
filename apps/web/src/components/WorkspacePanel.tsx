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
        <div className="flex-grow flex flex-col bg-surface-900 border-t border-border-subtle mt-4 min-h-[300px]">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-4 py-2 border-b border-border-subtle bg-surface-950/50">
                <div className="flex items-center gap-1">
                    <button
                        onClick={() => setActiveTab('terminal')}
                        className={`px-3 py-1.5 rounded-t-md text-xs font-medium flex items-center gap-2 border-t-2 transition-colors ${activeTab === 'terminal' ? 'border-purple-500 bg-surface-900 text-white' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}
                    >
                        <Terminal size={12} />
                        CONSOLE
                    </button>
                    <button
                        onClick={() => setActiveTab('report')}
                        className={`px-3 py-1.5 rounded-t-md text-xs font-medium flex items-center gap-2 border-t-2 transition-colors ${activeTab === 'report' ? 'border-purple-500 bg-surface-900 text-white' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}
                    >
                        <FileText size={12} />
                        REPORT
                    </button>
                    <button
                        onClick={() => setActiveTab('diff')}
                        className={`px-3 py-1.5 rounded-t-md text-xs font-medium flex items-center gap-2 border-t-2 transition-colors ${activeTab === 'diff' ? 'border-purple-500 bg-surface-900 text-white' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}
                    >
                        <Code2 size={12} />
                        DIFF
                    </button>
                </div>

                <div className="flex items-center gap-2">
                    <button className="p-1.5 text-zinc-500 hover:text-white rounded hover:bg-white/5">
                        <Maximize2 size={14} />
                    </button>
                    <button className="p-1.5 text-zinc-500 hover:text-white rounded hover:bg-white/5">
                        <MoreHorizontal size={14} />
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 relative font-mono text-sm overflow-hidden">
                {activeTab === 'terminal' && (
                    <div className="absolute inset-0 p-4 overflow-auto custom-scrollbar">
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

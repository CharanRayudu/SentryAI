import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    CheckCircle2,
    Circle,
    XCircle,
    Loader2,
    ChevronRight,
    Terminal as TerminalIcon
} from 'lucide-react';
import { useTaskStore, Task } from '@/stores/useTaskStore';

const statusChip = (status: Task['status']) => {
    switch (status) {
        case 'running':
            return { label: 'Running', className: 'text-purple-300 bg-purple-500/10 border border-purple-500/30' };
        case 'success':
            return { label: 'Complete', className: 'text-green-300 bg-green-500/10 border border-green-500/30' };
        case 'failed':
            return { label: 'Attention', className: 'text-red-300 bg-red-500/10 border border-red-500/30' };
        default:
            return { label: 'Queued', className: 'text-zinc-300 bg-white/5 border border-white/10' };
    }
};

const formatDuration = (task: Task) => {
    const end = task.endTime ?? Date.now();
    const seconds = Math.max(1, Math.round((end - task.startTime) / 1000));
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const rem = seconds % 60;
    return `${minutes}m ${rem.toString().padStart(2, '0')}s`;
};

const TaskRow = ({ task }: { task: Task }) => {
    const [expanded, setExpanded] = useState(task.status === 'failed' || task.status === 'running');
    const chip = statusChip(task.status);

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full"
        >
            <div
                onClick={() => setExpanded(!expanded)}
                className={`
                    w-full flex items-center gap-4 py-3 px-4 rounded-2xl cursor-pointer soft-card transition-all border
                    ${task.status === 'running' ? 'border-purple-500/30 shadow-[0_10px_30px_rgba(0,0,0,0.35)]' : 'hover:border-white/15'}
                `}
            >
                <div className="w-9 h-9 rounded-full bg-white/[0.03] border border-white/10 flex items-center justify-center">
                    {task.status === 'running' && <Loader2 className="text-purple-400 w-5 h-5 animate-spin" />}
                    {task.status === 'success' && <CheckCircle2 className="text-terminal-green w-5 h-5" />}
                    {task.status === 'failed' && <XCircle className="text-terminal-red w-5 h-5" />}
                    {task.status === 'idle' && <Circle className="text-zinc-500 w-5 h-5" />}
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-medium text-base text-white truncate">{task.title}</h3>
                        <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold uppercase ${chip.className}`}>
                            {chip.label}
                        </span>
                    </div>
                    <p className="text-xs text-zinc-500 mt-0.5">
                        Mission ID: {task.id}
                    </p>
                    {task.status === 'running' && (
                        <p className="text-xs text-purple-300/80 mt-1 font-mono">
                            Processing... live logs streaming
                        </p>
                    )}
                </div>

                <div className="text-xs text-zinc-500 font-mono text-right">
                    {formatDuration(task)}
                </div>

                <ChevronRight size={16} className={`text-zinc-600 transition-transform ${expanded ? 'rotate-90' : ''}`} />
            </div>

            <AnimatePresence>
                {expanded && task.logs.length > 0 && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="pl-14 pr-4 pb-4 overflow-hidden"
                    >
                        <div className="bg-[#050505] rounded-xl border border-white/[0.08] p-3 font-mono text-xs text-zinc-300 overflow-x-auto shadow-inner">
                            {task.logs.map((log, i) => (
                                <div key={i} className="mb-1 whitespace-pre-wrap font-mono">
                                    <span className="text-zinc-600 mr-2">{'>'}</span>
                                    {log}
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default function TaskExecutionList() {
    const { tasks, setOmnibarPosition } = useTaskStore();

    return (
        <div className="w-full max-w-5xl mx-auto py-4 space-y-2">
            {tasks.length > 0 ? (
                tasks.map((task) => (
                    <TaskRow key={task.id} task={task} />
                ))
            ) : (
                <div className="h-32 flex flex-col items-center justify-center border border-dashed border-white/10 rounded-2xl text-center text-zinc-600 gap-2">
                    <TerminalIcon className="w-7 h-7 opacity-50" />
                    <p className="text-sm">No missions yet. Start one to see live progress.</p>
                    <button
                        className="btn-gradient text-xs"
                        onClick={() => setOmnibarPosition('center')}
                    >
                        Open mission launcher
                    </button>
                </div>
            )}
        </div>
    );
}

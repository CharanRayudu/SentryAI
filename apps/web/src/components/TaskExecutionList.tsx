import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    CheckCircle2,
    Circle,
    XCircle,
    Loader2,
    ChevronRight,
    Terminal as TerminalIcon,
    RefreshCcw
} from 'lucide-react';
import { useTaskStore, Task } from '@/stores/useTaskStore';

const SAMPLE_RECENTS = [
    { title: 'Nuclei templates for previously known vulnerabilities', owner: 'Ananya Sharma', date: 'Dec 1', duration: '3m 24s' },
    { title: 'API endpoint enumeration', owner: 'Jake Morrison', date: 'Nov 30', duration: '9m 02s' },
    { title: 'Authentication flow analysis', owner: 'Yuki Tanaka', date: 'Nov 29', duration: '45m 23s' },
    { title: 'Rate limiting bypass testing', owner: 'Rahul Verma', date: 'Nov 28', duration: '12m 05s' },
    { title: 'JWT token security audit', owner: 'Tyler Brooks', date: 'Nov 27', duration: '10m 11s' },
];

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

const SampleRow = ({ item }: { item: typeof SAMPLE_RECENTS[0] }) => (
    <div className="flex items-center gap-3 py-3 px-4 rounded-2xl soft-card border border-white/5 hover:border-white/15 transition-all">
        <div className="w-9 h-9 rounded-full bg-white/[0.03] border border-white/10 flex items-center justify-center text-sm text-white/80">
            <RefreshCcw size={16} />
        </div>
        <div className="flex-1 min-w-0">
            <p className="text-base text-white truncate">{item.title}</p>
            <p className="text-xs text-zinc-600">{item.date} · {item.owner}</p>
        </div>
        <div className="text-xs text-zinc-500">{item.duration}</div>
    </div>
);

export default function TaskExecutionList() {
    const { tasks } = useTaskStore();

    return (
        <div className="w-full max-w-5xl mx-auto py-4 space-y-2">
            {tasks.length > 0 ? (
                tasks.map((task) => (
                    <TaskRow key={task.id} task={task} />
                ))
            ) : (
                <>
                    <div className="flex items-center justify-between px-1 pb-1">
                        <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-zinc-600 font-semibold">
                            <span className="w-2 h-2 rounded-full bg-zinc-500" />
                            Task backlog
                        </div>
                        <div className="text-[11px] text-zinc-600">Recent activity</div>
                    </div>
                    {SAMPLE_RECENTS.map((item) => (
                        <SampleRow key={item.title} item={item} />
                    ))}
                    <div className="h-28 flex items-center justify-center border border-dashed border-white/10 rounded-2xl text-center text-zinc-600">
                        <div>
                            <TerminalIcon className="w-7 h-7 mx-auto mb-2 opacity-50" />
                            <p className="text-sm">Your missions will stream here once started.</p>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Circle, XCircle, Loader2, ChevronRight, Terminal as TerminalIcon } from 'lucide-react';
import { useTaskStore, Task } from '@/stores/useTaskStore';

// Typewriter Hook
const useTypewriter = (text: string, speed = 10) => {
    const [displayedText, setDisplayedText] = useState("");

    useEffect(() => {
        setDisplayedText("");
        let i = 0;
        const timer = setInterval(() => {
            if (i < text.length) {
                setDisplayedText((prev) => prev + text.charAt(i));
                i++;
            } else {
                clearInterval(timer);
            }
        }, speed);
        return () => clearInterval(timer);
    }, [text, speed]);

    return displayedText;
};

const TaskRow = ({ task }: { task: Task }) => {
    const [expanded, setExpanded] = useState(task.status === 'failed' || task.status === 'running');

    // Status Icons
    const StatusIcon = () => {
        switch (task.status) {
            case 'success': return <CheckCircle2 className="text-terminal-green w-5 h-5" />;
            case 'failed': return <XCircle className="text-terminal-red w-5 h-5" />;
            case 'running': return <Loader2 className="text-purple-400 w-5 h-5 animate-spin" />;
            default: return <Circle className="text-zinc-600 w-5 h-5" />;
        }
    };

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full"
        >
            <div
                onClick={() => setExpanded(!expanded)}
                className={`
                    w-full flex items-center gap-4 py-3 px-4 rounded-xl cursor-pointer border transition-colors
                    ${task.status === 'running' ? 'bg-white/[0.02] border-purple-500/20' : 'bg-transparent border-transparent hover:bg-white/[0.02]'}
                `}
            >
                <StatusIcon />

                <div className="flex-1">
                    <h3 className={`font-medium text-sm ${task.status === 'idle' ? 'text-zinc-500' : 'text-zinc-200'}`}>
                        {task.title}
                    </h3>
                    {task.status === 'running' && (
                        <p className="text-xs text-purple-400/80 mt-0.5 font-mono animate-pulse">
                            Processing...
                        </p>
                    )}
                </div>

                <div className="text-xs text-zinc-600 font-mono">
                    {task.endTime ? `${((task.endTime - task.startTime) / 1000).toFixed(1)}s` : ''}
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
                        <div className="bg-[#050505] rounded-lg border border-white/[0.08] p-3 font-mono text-xs text-zinc-400 overflow-x-auto">
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
    const { tasks } = useTaskStore();

    return (
        <div className="w-full max-w-3xl mx-auto py-4 space-y-2">
            {tasks.map((task) => (
                <TaskRow key={task.id} task={task} />
            ))}

            {tasks.length === 0 && (
                <div className="h-40 flex items-center justify-center border border-dashed border-zinc-800 rounded-xl">
                    <div className="text-center text-zinc-600">
                        <TerminalIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">Ready for initialization</p>
                    </div>
                </div>
            )}
        </div>
    );
}

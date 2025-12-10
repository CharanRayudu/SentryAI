'use client';

import { useState, useEffect } from 'react';
import {
    Terminal,
    Shield,
    AlertTriangle,
    CheckCircle,
    Loader2,
    Maximize2,
    Activity,
    Target
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ActiveOperationProps {
    target: string;
    onComplete: () => void;
}

export default function ActiveOperation({ target, onComplete }: ActiveOperationProps) {
    const [status, setStatus] = useState('Initializing agents...');
    const [progress, setProgress] = useState(0);
    const [logs, setLogs] = useState<string[]>([]);

    useEffect(() => {
        // Simulation of mission progress
        const interval = setInterval(() => {
            setProgress(prev => {
                if (prev >= 100) {
                    clearInterval(interval);
                    setTimeout(onComplete, 1000);
                    return 100;
                }
                const increment = Math.random() * 5;
                return Math.min(prev + increment, 100);
            });

            // Random log generation
            if (Math.random() > 0.7) {
                const newLog = `[${new Date().toLocaleTimeString()}] Scanning port ${Math.floor(Math.random() * 65535)}`;
                setLogs(prev => [...prev.slice(-9), newLog]);
                setStatus(prev => prev === 'Analyzing results...' ? prev : 'Scanning target infrastructure...');
            }
        }, 500);

        return () => clearInterval(interval);
    }, [onComplete]);

    return (
        <div className="flex-1 flex flex-col p-6 h-full overflow-hidden">
            {/* Header / HUD */}
            <div className="flex items-center justify-between mb-6 neo-panel p-4 rounded-lg bg-black/40 border-[#ffffff0a]">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded bg-purple-500/10 border border-purple-500/20 flex items-center justify-center animate-pulse">
                        <Target className="text-purple-400" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold tracking-tight mb-0.5">{target}</h2>
                        <div className="flex items-center gap-2 text-xs text-zinc-400 font-mono">
                            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                            ACTIVE OPERATION
                        </div>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-3xl font-mono font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400">
                        {Math.floor(progress)}%
                    </div>
                    <div className="text-xs text-zinc-500 font-mono uppercase tracking-wider">Completion</div>
                </div>
            </div>

            {/* Main Terminal View */}
            <div className="flex-1 neo-panel rounded-lg border-[#ffffff0a] relative overflow-hidden flex flex-col bg-[#050505]">
                {/* Terminal Header */}
                <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-[#ffffff05]">
                    <div className="flex items-center gap-2">
                        <Terminal size={14} className="text-zinc-500" />
                        <span className="text-xs font-mono text-zinc-400">AGENT_OUTPUT</span>
                    </div>
                    <div className="flex gap-1.5">
                        <div className="w-2 h-2 rounded-full bg-red-500/20" />
                        <div className="w-2 h-2 rounded-full bg-amber-500/20" />
                        <div className="w-2 h-2 rounded-full bg-green-500/20" />
                    </div>
                </div>

                {/* Terminal Content */}
                <div className="flex-1 p-4 font-mono text-sm overflow-y-auto space-y-2">
                    {logs.map((log, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="text-zinc-300 border-l-2 border-transparent hover:border-purple-500 pl-2 transition-colors"
                        >
                            <span className="text-green-500 mr-2">$</span>
                            {log}
                        </motion.div>
                    ))}
                    <div className="flex items-center gap-2 text-purple-400 animate-pulse">
                        <span className="text-green-500">$</span>
                        <span className="w-2 h-4 bg-purple-400" />
                    </div>
                </div>

                {/* Status Bar */}
                <div className="bg-white/5 border-t border-[#ffffff05] px-4 py-2 flex items-center gap-4 text-xs font-mono text-zinc-500">
                    <div className="flex items-center gap-1.5">
                        <Activity size={12} />
                        <span>Agents: 4 Online</span>
                    </div>
                    <div className="h-3 w-px bg-zinc-800" />
                    <div>Tasks: {Math.floor(progress / 10)}/12</div>
                    <div className="ml-auto text-purple-400">{status}</div>
                </div>
            </div>

        </div>
    );
}

'use client';

import { useState, useEffect } from 'react';
import {
    Paperclip,
    Mic,
    ArrowUp,
    Zap,
    Globe,
    Cpu,
    ChevronDown,
    Loader2,
    CheckCircle2,
    AlertCircle,
    FileJson,
    X,
    Play
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Mock Data for the Plan
const MOCK_PLAN = [
    { id: '1', title: 'Enumerate all API endpoints from OpenAPI specification', time: '0m 03s', selected: true },
    { id: '2', title: 'Test authentication mechanisms on each endpoint', time: '0m 03s', selected: true },
    { id: '3', title: 'Check for rate limiting bypass vulnerabilities', time: '0m 02s', selected: true },
    { id: '4', title: 'Analyze JWT token implementation and expiration', time: '0m 02s', selected: false }, // Default disabled example
    { id: '5', title: 'Test for IDOR vulnerabilities on user-specific endpoints', time: '0m 01s', selected: true },
];

export default function MissionControl({ onExecute }: { onExecute: (prompt: string, selectedTasks: string[]) => void }) {
    const [prompt, setPrompt] = useState('');
    const [status, setStatus] = useState<'idle' | 'planning' | 'review' | 'executing'>('idle');
    const [planSteps, setPlanSteps] = useState([
        { label: 'Researching context...', status: 'waiting' },
        { label: 'Memory recall (Found 4 relevant conversations)', status: 'waiting' },
        { label: 'Knowledge search (api-endpoints.yaml, nuclei-templates.json)', status: 'waiting' },
        { label: 'Generating attack vectors', status: 'waiting' }
    ]);
    const [checklist, setChecklist] = useState(MOCK_PLAN);

    // Simulate the "Thinking" process
    const startPlanning = () => {
        if (!prompt.trim()) return;
        setStatus('planning');

        // Sequence the fake loader steps
        const timeouts: NodeJS.Timeout[] = [];

        planSteps.forEach((_, i) => {
            timeouts.push(setTimeout(() => {
                setPlanSteps(prev => prev.map((step, idx) =>
                    idx === i ? { ...step, status: 'active' } : idx < i ? { ...step, status: 'done' } : step
                ));
            }, i * 1200));
        });

        // Finish planning
        timeouts.push(setTimeout(() => {
            setPlanSteps(prev => prev.map(s => ({ ...s, status: 'done' })));
            setStatus('review');
        }, planSteps.length * 1200 + 500));
    };

    const toggleTask = (id: string) => {
        setChecklist(prev => prev.map(t => t.id === id ? { ...t, selected: !t.selected } : t));
    };

    const handleExecute = () => {
        const selected = checklist.filter(t => t.selected).map(t => t.title);
        onExecute(prompt, selected);
    };

    const activeCount = checklist.filter(t => t.selected).length;

    return (
        <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full p-8 pt-10 h-full overflow-y-auto">

            {/* Header */}
            <div className="mb-8 text-center space-y-2">
                <h1 className="text-3xl font-semibold text-white tracking-tight">Mission Control</h1>
                <p className="text-gray-500">Orchestrate your autonomous security workforce.</p>
            </div>

            {/* Main Input Area */}
            <div className="bg-[#111] border border-[#333] rounded-2xl p-4 shadow-2xl relative group focus-within:border-gray-500 transition-colors">
                <textarea
                    className="w-full bg-transparent text-lg text-white placeholder-gray-500 resize-none outline-none h-20 font-normal"
                    placeholder="Describe the task (e.g., 'Audit the billing API for IDOR')..."
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            startPlanning();
                        }
                    }}
                    disabled={status !== 'idle'}
                />

                {/* Action Bar */}
                <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center gap-2">
                        <button className="p-2 text-gray-400 hover:text-white hover:bg-white/5 rounded-full transition-colors">
                            <Paperclip size={18} />
                        </button>
                        <div className="h-4 w-[1px] bg-[#333] mx-1"></div>
                        <Chip icon={<Globe size={14} className="text-blue-400" />} label="Plan" />
                        <Chip icon={<Zap size={14} className="text-yellow-400" />} label="Auto" />
                    </div>

                    <button
                        onClick={startPlanning}
                        disabled={status !== 'idle' || !prompt.trim()}
                        className={`p-2 rounded-full transition-all ${status === 'idle' && prompt.trim() ? 'bg-white text-black hover:scale-105' : 'bg-[#333] text-gray-500'}`}
                    >
                        <ArrowUp size={20} />
                    </button>
                </div>
            </div>

            {/* PLANNING PHASE: THOUGHT PROCESS */}
            <AnimatePresence>
                {(status === 'planning' || status === 'review') && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-6 bg-[#0a0a0a] border border-[#222] rounded-xl p-6"
                    >
                        <div className="flex items-center gap-2 mb-4">
                            {status === 'planning' ? <Loader2 size={18} className="animate-spin text-purple-500" /> : <CheckCircle2 size={18} className="text-green-500" />}
                            <span className="text-sm font-medium text-white">
                                {status === 'planning' ? 'Generating Plan...' : 'Plan Generated'}
                            </span>
                        </div>

                        <div className="space-y-3 pl-2">
                            {planSteps.map((step, idx) => (
                                <div key={idx} className="flex items-center gap-3 text-sm">
                                    <div className="w-4 flex justify-center">
                                        {step.status === 'waiting' && <div className="w-1.5 h-1.5 rounded-full bg-gray-700" />}
                                        {step.status === 'active' && <Loader2 size={14} className="animate-spin text-purple-400" />}
                                        {step.status === 'done' && <CheckCircle2 size={14} className="text-green-500" />}
                                    </div>
                                    <span className={`${step.status === 'active' ? 'text-white' : 'text-gray-500'}`}>
                                        {step.label}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* REVIEW PHASE: CHECKLIST */}
            <AnimatePresence>
                {status === 'review' && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-6"
                    >
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-medium text-white">Proposed Security Tasks</h2>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setStatus('idle')}
                                    className="px-4 py-2 rounded-lg border border-[#333] text-sm text-gray-400 hover:text-white hover:bg-[#222]"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleExecute}
                                    className="px-4 py-2 rounded-lg bg-white text-black text-sm font-medium hover:bg-gray-200 flex items-center gap-2"
                                >
                                    <Play size={16} fill="currentColor" />
                                    Execute {activeCount} Parallel Tasks
                                </button>
                            </div>
                        </div>

                        <div className="space-y-2">
                            {checklist.map((task) => (
                                <div
                                    key={task.id}
                                    onClick={() => toggleTask(task.id)}
                                    className={`
                    group flex items-center justify-between p-4 rounded-lg cursor-pointer border transition-all
                    ${task.selected
                                            ? 'bg-[#1a1a1a] border-purple-500/30 hover:border-purple-500/50'
                                            : 'bg-[#0a0a0a] border-[#222] opacity-60 hover:opacity-100'}
                  `}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`
                      w-5 h-5 rounded border flex items-center justify-center transition-colors
                      ${task.selected ? 'bg-purple-500 border-purple-500' : 'border-gray-600'}
                    `}>
                                            {task.selected && <CheckCircle2 size={14} className="text-white" />}
                                        </div>
                                        <span className="text-sm font-medium text-gray-200">{task.title}</span>
                                    </div>

                                    <div className="flex items-center gap-4">
                                        <span className="text-xs text-gray-600 font-mono hidden group-hover:block">est. {task.time}</span>
                                        <div className="w-1.5 h-1.5 rounded-full bg-gray-600"></div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

        </div>
    );
}

function Chip({ icon, label }: { icon: any, label: string }) {
    return (
        <div className="flex items-center gap-2 bg-[#1a1a1a] border border-[#333] rounded-full px-3 py-1.5 cursor-pointer hover:border-gray-500 transition-colors">
            {icon}
            <span className="text-xs font-medium text-gray-300">{label}</span>
            <ChevronDown size={12} className="text-gray-500" />
        </div>
    );
}

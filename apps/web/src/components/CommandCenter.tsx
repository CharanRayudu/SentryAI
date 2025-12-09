'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ArrowUp,
    Paperclip,
    Sparkles,
    ChevronDown,
    Check,
    Loader2,
    AlertCircle,
    Clock,
    ChevronRight,
    Terminal,
    Play,
    Pause,
    RotateCcw,
    ExternalLink,
    Zap,
    Shield,
    Search,
    Network,
    Code2,
    FileCode
} from 'lucide-react';
import { useAgentSocket } from '@/hooks/useAgentSocket';

// --- Types ---
interface Task {
    id: string;
    title: string;
    tool: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    duration?: number;
    output?: string;
    expanded?: boolean;
}

interface AgentMode {
    id: string;
    name: string;
    icon: React.ElementType;
    description: string;
}

const AGENT_MODES: AgentMode[] = [
    { id: 'auto', name: 'Auto', icon: Sparkles, description: 'AI chooses the best approach' },
    { id: 'pentest', name: 'Pentest', icon: Shield, description: 'Penetration testing focus' },
    { id: 'recon', name: 'Recon', icon: Search, description: 'Reconnaissance & discovery' },
    { id: 'code', name: 'Code Review', icon: Code2, description: 'Static code analysis' },
];

const QUICK_TAGS = [
    { id: 'infra', label: 'Infra', icon: Network },
    { id: 'threat', label: 'Threat Modeling', icon: Shield },
    { id: 'pentest', label: 'Pentest', icon: Zap },
    { id: 'compliance', label: 'Compliance', icon: FileCode },
];

export default function CommandCenter() {
    const [input, setInput] = useState('');
    const [tasks, setTasks] = useState<Task[]>([]);
    const [isExecuting, setIsExecuting] = useState(false);
    const [selectedMode, setSelectedMode] = useState<AgentMode>(AGENT_MODES[0]);
    const [modeDropdownOpen, setModeDropdownOpen] = useState(false);
    const [selectedTags, setSelectedTags] = useState<string[]>([]);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const { isConnected, lastMessage, sendMessage, connectionError } = useAgentSocket();

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
        }
    }, [input]);

    // Handle WebSocket messages
    useEffect(() => {
        if (!lastMessage) return;

        if (lastMessage.type === 'server:plan_proposal') {
            const newTasks: Task[] = lastMessage.steps.map((step: any) => ({
                id: step.id.toString(),
                title: step.title,
                tool: step.tool,
                status: 'pending',
            }));
            setTasks(newTasks);
            setIsExecuting(false);
        }

        if (lastMessage.type === 'server:agent_thought') {
            // Could update UI to show thinking state
        }
    }, [lastMessage]);

    const handleSubmit = () => {
        if (!input.trim() || isExecuting) return;

        setIsExecuting(true);
        setTasks([]);

        sendMessage('client:message', { 
            content: input,
            mode: selectedMode.id,
            tags: selectedTags
        });
    };

    const handleExecutePlan = () => {
        if (tasks.length === 0) return;

        const approvedTasks = tasks.filter(t => t.status === 'pending').map(t => t.id);
        sendMessage('client:confirm_plan', { approved_steps: approvedTasks });

        // Simulate task execution
        simulateExecution();
    };

    const simulateExecution = () => {
        setIsExecuting(true);
        let currentIndex = 0;

        const runNextTask = () => {
            if (currentIndex >= tasks.length) {
                setIsExecuting(false);
                return;
            }

            // Set current task to running
            setTasks(prev => prev.map((t, i) => 
                i === currentIndex ? { ...t, status: 'running' as const } : t
            ));

            // Simulate completion after random time
            const duration = 1500 + Math.random() * 2000;
            setTimeout(() => {
                setTasks(prev => prev.map((t, i) => 
                    i === currentIndex ? { 
                        ...t, 
                        status: 'completed' as const,
                        duration: duration / 1000,
                        output: `Successfully completed ${t.title}`
                    } : t
                ));
                currentIndex++;
                runNextTask();
            }, duration);
        };

        runNextTask();
    };

    const toggleTag = (tagId: string) => {
        setSelectedTags(prev => 
            prev.includes(tagId) 
                ? prev.filter(t => t !== tagId)
                : [...prev, tagId]
        );
    };

    const toggleTaskExpanded = (taskId: string) => {
        setTasks(prev => prev.map(t => 
            t.id === taskId ? { ...t, expanded: !t.expanded } : t
        ));
    };

    const getStatusIcon = (status: Task['status']) => {
        switch (status) {
            case 'pending': return <div className="w-4 h-4 rounded-full border-2 border-zinc-600" />;
            case 'running': return <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />;
            case 'completed': return <Check className="w-4 h-4 text-green-400" />;
            case 'failed': return <AlertCircle className="w-4 h-4 text-red-400" />;
        }
    };

    return (
        <div className="flex-1 flex flex-col h-screen overflow-hidden">
            {/* Header */}
            <header className="flex items-center justify-between px-8 py-4 border-b border-white/[0.06]">
                <div>
                    <h1 className="text-xl font-semibold text-white">Command Center</h1>
                    <p className="text-sm text-zinc-500">Execute security operations with AI assistance</p>
                </div>
                <div className="flex items-center gap-3">
                    {/* Connection Status */}
                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
                        isConnected 
                            ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                            : 'bg-red-500/10 text-red-400 border border-red-500/20'
                    }`}>
                        <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
                        {isConnected ? 'Connected' : 'Disconnected'}
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto">
                <div className="max-w-4xl mx-auto px-8 py-8 space-y-6">
                    {/* Omnibar Input */}
                    <div className="input-glow p-4">
                        {/* Mode Selector */}
                        <div className="flex items-center gap-2 mb-3">
                            <div className="relative">
                                <button
                                    onClick={() => setModeDropdownOpen(!modeDropdownOpen)}
                                    className="flex items-center gap-2 px-3 py-1.5 bg-white/[0.03] hover:bg-white/[0.05] rounded-lg text-sm text-zinc-400 transition-colors"
                                >
                                    <selectedMode.icon size={14} className="text-purple-400" />
                                    {selectedMode.name}
                                    <ChevronDown size={12} />
                                </button>

                                <AnimatePresence>
                                    {modeDropdownOpen && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 4 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: 4 }}
                                            className="absolute top-full left-0 mt-1 w-56 p-1 bg-[#121212] border border-white/[0.1] rounded-lg shadow-xl z-50"
                                        >
                                            {AGENT_MODES.map((mode) => (
                                                <button
                                                    key={mode.id}
                                                    onClick={() => {
                                                        setSelectedMode(mode);
                                                        setModeDropdownOpen(false);
                                                    }}
                                                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                                                        selectedMode.id === mode.id 
                                                            ? 'bg-purple-500/10 text-purple-400'
                                                            : 'text-zinc-400 hover:bg-white/[0.05] hover:text-white'
                                                    }`}
                                                >
                                                    <mode.icon size={16} />
                                                    <div className="text-left">
                                                        <p className="text-sm font-medium">{mode.name}</p>
                                                        <p className="text-[11px] text-zinc-500">{mode.description}</p>
                                                    </div>
                                                </button>
                                            ))}
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>

                        {/* Textarea */}
                        <div className="flex items-end gap-3">
                            <div className="flex-1 relative">
                                <textarea
                                    ref={textareaRef}
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault();
                                            handleSubmit();
                                        }
                                    }}
                                    placeholder="Describe the task you want me to execute..."
                                    className="w-full bg-transparent text-white placeholder-zinc-600 text-base resize-none focus:outline-none min-h-[52px] pr-10"
                                    rows={1}
                                />
                                <button className="absolute right-0 bottom-1 p-2 text-zinc-600 hover:text-zinc-400 transition-colors">
                                    <Paperclip size={18} />
                                </button>
                            </div>

                            <button
                                onClick={handleSubmit}
                                disabled={!input.trim() || isExecuting}
                                className="btn-gradient flex items-center justify-center w-10 h-10 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isExecuting ? (
                                    <Loader2 size={18} className="animate-spin" />
                                ) : (
                                    <ArrowUp size={18} />
                                )}
                            </button>
                        </div>

                        {/* Quick Tags */}
                        <div className="flex items-center gap-2 mt-4 pt-4 border-t border-white/[0.06]">
                            {QUICK_TAGS.map((tag) => (
                                <button
                                    key={tag.id}
                                    onClick={() => toggleTag(tag.id)}
                                    className={`pill ${selectedTags.includes(tag.id) ? 'active' : ''}`}
                                >
                                    <tag.icon size={12} className="mr-1.5" />
                                    {tag.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Connection Error */}
                    {connectionError && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex items-center gap-3 px-4 py-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-400 text-sm"
                        >
                            <AlertCircle size={16} />
                            <span>{connectionError}</span>
                        </motion.div>
                    )}

                    {/* Task Stream */}
                    {tasks.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="space-y-3"
                        >
                            <div className="flex items-center justify-between">
                                <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">
                                    Execution Plan
                                </h2>
                                <div className="flex items-center gap-2">
                                    <span className="text-xs text-zinc-500">
                                        {tasks.filter(t => t.status === 'completed').length}/{tasks.length} completed
                                    </span>
                                    {tasks.every(t => t.status === 'pending') && (
                                        <button
                                            onClick={handleExecutePlan}
                                            className="btn-gradient text-sm px-4 py-1.5 flex items-center gap-2"
                                        >
                                            <Play size={14} />
                                            Execute Plan
                                        </button>
                                    )}
                                </div>
                            </div>

                            <div className="space-y-2">
                                {tasks.map((task, index) => (
                                    <motion.div
                                        key={task.id}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: index * 0.05 }}
                                    >
                                        <div
                                            onClick={() => toggleTaskExpanded(task.id)}
                                            className={`task-row cursor-pointer ${
                                                task.status === 'running' ? 'border-purple-500/30 bg-purple-500/5' : ''
                                            }`}
                                        >
                                            {getStatusIcon(task.status)}
                                            
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm text-white truncate">{task.title}</p>
                                                <p className="text-xs text-zinc-500 font-mono">{task.tool}</p>
                                            </div>

                                            <div className="flex items-center gap-3">
                                                {task.duration && (
                                                    <span className="text-xs text-zinc-500 flex items-center gap-1">
                                                        <Clock size={12} />
                                                        {task.duration.toFixed(1)}s
                                                    </span>
                                                )}
                                                <ChevronRight 
                                                    size={16} 
                                                    className={`text-zinc-600 transition-transform ${task.expanded ? 'rotate-90' : ''}`}
                                                />
                                            </div>
                                        </div>

                                        <AnimatePresence>
                                            {task.expanded && task.output && (
                                                <motion.div
                                                    initial={{ height: 0, opacity: 0 }}
                                                    animate={{ height: 'auto', opacity: 1 }}
                                                    exit={{ height: 0, opacity: 0 }}
                                                    className="overflow-hidden"
                                                >
                                                    <div className="mt-1 ml-7 p-3 bg-[#0d0d0d] rounded-lg border border-white/[0.04]">
                                                        <pre className="text-xs text-zinc-400 font-mono whitespace-pre-wrap">
                                                            {task.output}
                                                        </pre>
                                                    </div>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </motion.div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {/* Empty State */}
                    {tasks.length === 0 && !isExecuting && (
                        <div className="text-center py-16">
                            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 mb-4">
                                <Sparkles className="w-8 h-8 text-purple-400" />
                            </div>
                            <h3 className="text-lg font-medium text-white mb-2">Ready for your command</h3>
                            <p className="text-sm text-zinc-500 max-w-md mx-auto">
                                Describe a security task in natural language and I&apos;ll create an execution plan. 
                                Try &quot;Scan example.com for vulnerabilities&quot; to get started.
                            </p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}


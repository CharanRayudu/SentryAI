'use client';

import { useState, useEffect, useCallback } from 'react';
import { Sparkles, ArrowRight, Command, AlertCircle, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAgentSocket } from '@/hooks/useAgentSocket';

interface CommandCenterProps {
    onMissionStart?: (target: string) => void;
    onViewChange?: (view: string) => void;
}

export default function CommandCenter({ onMissionStart, onViewChange }: CommandCenterProps) {
    const [input, setInput] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [lastMessage, setLastMessage] = useState<string | null>(null);
    const [activeMissionId, setActiveMissionId] = useState<string | null>(null);
    const [activeRunId, setActiveRunId] = useState<string | null>(null);
    
    const { isConnected, sendMessage, stopMission, connectionError, lastMessage: wsMessage } = useAgentSocket();

    // Handle WebSocket messages
    useEffect(() => {
        if (wsMessage) {
            const messageType = wsMessage.type;
            
            if (messageType === 'server:agent_thought') {
                setLastMessage(wsMessage.log || 'Processing...');
            } else if (messageType === 'server:plan_proposal') {
                setLastMessage('Execution plan generated. Reviewing...');
                setIsSubmitting(false);
                // Navigate to operations view if callback provided
                if (onViewChange) {
                    setTimeout(() => onViewChange('operations'), 1000);
                }
            } else if (messageType === 'server:error') {
                setLastMessage(`Error: ${wsMessage.message || 'Unknown error'}`);
                setIsSubmitting(false);
            } else if (messageType === 'server:job_status') {
                setLastMessage(`Mission ${wsMessage.status || 'started'}`);
                if (wsMessage.mission_id) {
                    setActiveMissionId(wsMessage.mission_id);
                }
                if (wsMessage.run_id) {
                    setActiveRunId(wsMessage.run_id);
                }
                setIsSubmitting(false);
            } else if (messageType === 'server:job_log') {
                setLastMessage(wsMessage.log || 'Processing...');
            }
        }
    }, [wsMessage, onViewChange]);

    const handleSubmit = useCallback((message: string) => {
        if (!message.trim()) {
            return;
        }

        if (!isConnected) {
            setLastMessage('Not connected to backend. Please check your connection.');
            return;
        }

        setIsSubmitting(true);
        setLastMessage('Sending mission objective...');
        setActiveMissionId(null);
        setActiveRunId(null);

        // Extract target from message for callback
        const targetMatch = message.match(/(?:scan|audit|test|check)\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/i);
        const target = targetMatch ? targetMatch[1] : message.split(/\s+/).find(word => 
            word.includes('.') && !word.startsWith('http')
        ) || 'unknown';

        // Send message via WebSocket
        sendMessage('client:message', {
            content: message,
            context_files: []
        });

        // Call mission start callback if provided
        if (onMissionStart) {
            onMissionStart(target);
        }
    }, [isConnected, sendMessage, onMissionStart]);

    const handleStop = useCallback(() => {
        stopMission(activeMissionId ?? undefined, activeRunId ?? undefined);
        setIsSubmitting(false);
        setLastMessage('Stopping mission...');
    }, [stopMission, activeMissionId, activeRunId]);

    const handleQuickAction = useCallback((action: string) => {
        const messages: Record<string, string> = {
            'Deep Scan': 'Perform a deep security scan with comprehensive vulnerability assessment',
            'Map Infrastructure': 'Map the infrastructure and discover all assets, subdomains, and services',
            'Generate Report': 'Generate a comprehensive security assessment report'
        };

        const message = messages[action] || action;
        setInput(message);
        handleSubmit(message);
    }, [handleSubmit]);

    const handleKeyPress = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(input);
        }
    }, [input, handleSubmit]);

    return (
        <div className="flex-1 flex flex-col items-center justify-center p-8 relative overflow-hidden">

            {/* Ambient Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-purple-600/20 blur-[100px] rounded-full pointer-events-none" />

            {/* Connection Status Indicator */}
            <AnimatePresence>
                {connectionError && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="absolute top-4 right-4 z-20 flex items-center gap-2 px-4 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm"
                    >
                        <AlertCircle size={16} />
                        <span>{connectionError}</span>
                    </motion.div>
                )}
                {isConnected && !connectionError && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="absolute top-4 right-4 z-20 flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400 text-sm"
                    >
                        <CheckCircle2 size={16} />
                        <span>Connected</span>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Central Visual: The "Brain" */}
            <div className="relative mb-12">
                <div className={`w-32 h-32 rounded-full border border-purple-500/30 flex items-center justify-center relative ${isConnected ? 'animate-pulse-glow' : 'opacity-50'}`}>
                    <div className="absolute inset-0 rounded-full border border-cyan-500/20 animate-spin transition-all duration-[3000ms]" />
                    <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-600 to-cyan-600 blur-md opacity-50" />
                    <Sparkles className={`relative z-10 w-12 h-12 ${isConnected ? 'text-white' : 'text-zinc-600'}`} />
                </div>
            </div>

            {/* Hero Text */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center mb-10 z-10"
            >
                <h1 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight">
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-purple-100 to-white text-glow">
                        What is your objective?
                    </span>
                </h1>
                <p className="text-zinc-400 text-lg max-w-xl mx-auto">
                    Initialize autonomous reconnaissance or specify a target for security audit.
                </p>
            </motion.div>

            {/* Main Input Field */}
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 }}
                className="w-full max-w-2xl relative z-10"
            >
                <div className="group relative">
                    <div className={`absolute -inset-0.5 bg-gradient-to-r from-purple-600 to-cyan-600 rounded-xl opacity-30 group-hover:opacity-100 transition duration-500 blur ${isSubmitting ? 'opacity-100' : ''}`} />
                    <div className="relative flex items-center bg-[#0a0a0a] rounded-xl border border-white/10 p-2 shadow-2xl">
                        <div className="pl-4 pr-3 text-zinc-500">
                            <Command size={20} />
                        </div>
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="e.g., Scan example.com for vulnerabilities..."
                            disabled={isSubmitting || !isConnected}
                            className="flex-1 bg-transparent border-none text-lg text-white placeholder-zinc-600 focus:ring-0 focus:outline-none h-12 neo-input disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                        <div className="flex gap-2">
                            <button
                                onClick={() => handleSubmit(input)}
                                disabled={isSubmitting || !isConnected || !input.trim()}
                                className="p-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white/10"
                            >
                                {isSubmitting ? (
                                    <motion.div
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                    >
                                        <ArrowRight size={20} />
                                    </motion.div>
                                ) : (
                                    <ArrowRight size={20} />
                                )}
                            </button>
                            <button
                                onClick={handleStop}
                                disabled={!isConnected || !activeMissionId}
                                className="p-2 bg-red-500/20 hover:bg-red-500/30 text-red-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                title="Stop current mission"
                            >
                                Stop
                            </button>
                        </div>
                    </div>
                </div>

                {/* Status Message */}
                <AnimatePresence>
                    {lastMessage && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="mt-4 text-center text-sm text-zinc-400"
                        >
                            {lastMessage}
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Quick Actions */}
                <div className="mt-8 flex justify-center gap-4 flex-wrap">
                    <button
                        onClick={() => handleQuickAction('Deep Scan')}
                        disabled={isSubmitting || !isConnected}
                        className="px-4 py-2 rounded-full border border-white/10 bg-white/5 text-sm text-zinc-400 hover:text-white hover:border-purple-500/50 hover:bg-purple-500/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:text-zinc-400 disabled:hover:border-white/10"
                    >
                        Deep Scan
                    </button>
                    <button
                        onClick={() => handleQuickAction('Map Infrastructure')}
                        disabled={isSubmitting || !isConnected}
                        className="px-4 py-2 rounded-full border border-white/10 bg-white/5 text-sm text-zinc-400 hover:text-white hover:border-cyan-500/50 hover:bg-cyan-500/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:text-zinc-400 disabled:hover:border-white/10"
                    >
                        Map Infrastructure
                    </button>
                    <button
                        onClick={() => handleQuickAction('Generate Report')}
                        disabled={isSubmitting || !isConnected}
                        className="px-4 py-2 rounded-full border border-white/10 bg-white/5 text-sm text-zinc-400 hover:text-white hover:border-pink-500/50 hover:bg-pink-500/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:text-zinc-400 disabled:hover:border-white/10"
                    >
                        Generate Report
                    </button>
                </div>
            </motion.div>

        </div>
    );
}

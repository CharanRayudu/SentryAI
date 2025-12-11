import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Paperclip, Bot, ArrowUp, ChevronDown, Sparkles, Link2, Globe2, Clock3, Mic } from 'lucide-react';
import { useTaskStore } from '@/stores/useTaskStore';

export default function PromptInput() {
    const [prompt, setPrompt] = useState("");
    const [agentMenuOpen, setAgentMenuOpen] = useState(false);
    const [isFocused, setIsFocused] = useState(false);

    const { omnibarPosition, setOmnibarPosition, startMission } = useTaskStore();

    const handleSubmit = async () => {
        if (!prompt.trim()) return;

        // Optimistic Update handled in store
        await startMission(prompt);
        setPrompt("");
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <motion.div
            layoutId="omnibar"
            className={`w-full max-w-5xl mx-auto z-50 ${omnibarPosition === 'top' ? 'mb-6' : 'mb-0'}`}
            initial={false}
        >
            <div className="relative group rounded-[26px] glass-card overflow-hidden border border-white/10 shadow-2xl">
                <div className={`absolute inset-0 opacity-0 transition-opacity duration-500 ${isFocused ? 'opacity-100' : ''}`}>
                    <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 via-pink-500/10 to-blue-500/10 blur-2xl" />
                </div>

                <div className="relative flex flex-col gap-4 p-5 md:p-6">
                    <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.18em] text-zinc-600 font-semibold">
                        <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_12px_rgba(74,222,128,0.7)]" />
                            Live agent
                        </div>
                        <button
                            onClick={() => setOmnibarPosition(omnibarPosition === 'center' ? 'top' : 'center')}
                            className="stat-pill bg-white/5 border-white/10 text-[10px] uppercase tracking-[0.18em]"
                        >
                            {omnibarPosition === 'center' ? 'Dock to top' : 'Center stage'}
                        </button>
                    </div>

                    <textarea
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        onFocus={() => setIsFocused(true)}
                        onBlur={() => setIsFocused(false)}
                        onKeyDown={handleKeyDown}
                        placeholder="Describe the task you want me to execute..."
                        className="w-full bg-transparent text-xl md:text-2xl leading-relaxed text-white placeholder-zinc-600 outline-none resize-none min-h-[120px] px-2 md:px-1 font-light"
                        rows={2}
                        style={{ height: 'auto', minHeight: '120px' }}
                    />

                    <div className="flex items-center justify-between rounded-2xl bg-white/[0.02] border border-white/[0.04] px-3 py-2 md:px-4 md:py-3">
                        <div className="flex items-center gap-1 md:gap-2">
                            <button className="toolbar-btn"><Paperclip size={16} /></button>
                            <button className="toolbar-btn"><Sparkles size={16} /></button>
                            <button className="toolbar-btn"><ChevronDown size={16} /></button>

                            <div className="relative ml-1">
                                <button
                                    onClick={() => setAgentMenuOpen(!agentMenuOpen)}
                                    className="flex items-center gap-2 px-3 py-2 bg-white/[0.03] hover:bg-white/[0.05] rounded-full border border-white/10 text-xs font-medium text-zinc-200 transition-all"
                                >
                                    <Bot size={14} className="text-purple-400" />
                                    <span>Agent</span>
                                    <ChevronDown size={12} className="text-zinc-500" />
                                </button>

                                <AnimatePresence>
                                    {agentMenuOpen && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: 10 }}
                                            className="absolute top-full left-0 mt-2 w-52 bg-surface-900 border border-white/10 rounded-xl shadow-2xl overflow-hidden p-1 z-50"
                                        >
                                            {['Pentest Agent', 'Code Reviewer', 'Security Auditor'].map((agent) => (
                                                <button
                                                    key={agent}
                                                    onClick={() => setAgentMenuOpen(false)}
                                                    className="w-full text-left px-3 py-2 text-sm text-zinc-300 hover:text-white hover:bg-white/5 rounded-lg transition-colors flex items-center gap-2"
                                                >
                                                    <Sparkles size={12} className="text-purple-400" />
                                                    {agent}
                                                </button>
                                            ))}
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            <button className="toolbar-btn"><Link2 size={16} /></button>
                            <button className="toolbar-btn"><Globe2 size={16} /></button>
                            <button className="toolbar-btn"><Clock3 size={16} /></button>
                            <div className="flex items-center gap-2">
                                <button className="toolbar-btn"><Mic size={16} /></button>
                                <button className="p-2.5 rounded-full border border-white/10 bg-white/[0.03] text-zinc-300 hover:text-white hover:border-white/20 transition">
                                    <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5}>
                                        <path d="M12 18.5v-13" strokeLinecap="round" />
                                        <path d="M7 13l5 5 5-5" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                </button>
                                <button
                                    onClick={handleSubmit}
                                    disabled={!prompt.trim()}
                                    className={`
                                        w-11 h-11 rounded-full transition-all duration-300 flex items-center justify-center
                                        ${prompt.trim()
                                            ? 'bg-gradient-to-br from-purple-500 to-pink-500 text-white shadow-lg shadow-purple-900/40 hover:scale-105'
                                            : 'bg-white/5 text-zinc-600 cursor-not-allowed'}
                                    `}
                                >
                                    <ArrowUp size={22} />
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {omnibarPosition === 'center' && (
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center mt-4 text-zinc-500 text-sm font-mono"
                >
                    Press <span className="text-zinc-400">Enter</span> to execute mission
                </motion.p>
            )}
        </motion.div>
    );
}

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Paperclip, Bot, ArrowUp, ChevronDown, Sparkles } from 'lucide-react';
import { useTaskStore } from '@/stores/useTaskStore';

export default function PromptInput() {
    const [prompt, setPrompt] = useState("");
    const [isFocused, setIsFocused] = useState(false);
    const [agentMenuOpen, setAgentMenuOpen] = useState(false);

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
            className={`w-full max-w-3xl mx-auto z-50 ${omnibarPosition === 'top' ? 'mb-6' : 'mb-0'}`}
            initial={false}
        >
            <div className={`
                relative group rounded-2xl bg-surface-800 border transition-all duration-300
                ${isFocused ? 'border-purple-500/50 shadow-[0_0_20px_rgba(168,85,247,0.15)]' : 'border-white/10 hover:border-white/20'}
            `}>
                {/* Glow Effect */}
                <div className={`absolute inset-0 rounded-2xl bg-gradient-to-r from-purple-500/10 to-pink-500/10 opacity-0 transition-opacity duration-500 ${isFocused ? 'opacity-100' : ''}`} />

                <div className="relative p-2 flex flex-col gap-2">
                    {/* Text Area */}
                    <textarea
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        onFocus={() => setIsFocused(true)}
                        onBlur={() => setIsFocused(false)}
                        onKeyDown={handleKeyDown}
                        placeholder="Define mission parameters..."
                        className="w-full bg-transparent text-lg text-white placeholder-zinc-500 outline-none resize-none min-h-[56px] px-3 py-2 font-light"
                        rows={1}
                        style={{ height: 'auto', minHeight: '56px' }}
                    />

                    {/* Controls Toolbar */}
                    <div className="flex items-center justify-between px-2">
                        <div className="flex items-center gap-2">
                            {/* Attachment */}
                            <button className="p-2 text-zinc-500 hover:text-white transition-colors rounded-lg hover:bg-white/5">
                                <Paperclip size={18} />
                            </button>

                            {/* Agent Selector */}
                            <div className="relative">
                                <button
                                    onClick={() => setAgentMenuOpen(!agentMenuOpen)}
                                    className="flex items-center gap-2 px-3 py-1.5 bg-surface-900 rounded-full border border-white/10 text-xs font-medium text-zinc-300 hover:text-white hover:border-white/20 transition-all"
                                >
                                    <Bot size={14} className="text-purple-400" />
                                    <span>Pentest Agent</span>
                                    <ChevronDown size={12} className="text-zinc-500" />
                                </button>

                                <AnimatePresence>
                                    {agentMenuOpen && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: 10 }}
                                            className="absolute top-full left-0 mt-2 w-48 bg-surface-900 border border-white/10 rounded-xl shadow-xl overflow-hidden p-1 z-50"
                                        >
                                            {['Pentest Agent', 'Code Reviewer', 'Security Auditor'].map((agent) => (
                                                <button
                                                    key={agent}
                                                    onClick={() => setAgentMenuOpen(false)}
                                                    className="w-full text-left px-3 py-2 text-sm text-zinc-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors flex items-center gap-2"
                                                >
                                                    <Sparkles size={12} className="text-purple-500" />
                                                    {agent}
                                                </button>
                                            ))}
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>

                        {/* Submit Button */}
                        <button
                            onClick={handleSubmit}
                            disabled={!prompt.trim()}
                            className={`
                                p-2 rounded-xl transition-all duration-300 flex items-center justify-center
                                ${prompt.trim()
                                    ? 'bg-gradient-to-br from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-900/40 hover:scale-105'
                                    : 'bg-zinc-800 text-zinc-600 cursor-not-allowed'}
                            `}
                        >
                            <ArrowUp size={20} />
                        </button>
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

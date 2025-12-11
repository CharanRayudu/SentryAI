import React, { useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Paperclip, Bot, ArrowUp, ChevronDown, Sparkles, Link2, Globe2, Clock3, Mic } from 'lucide-react';
import { useTaskStore } from '@/stores/useTaskStore';

export default function PromptInput() {
    const [prompt, setPrompt] = useState("");
    const [agentMenuOpen, setAgentMenuOpen] = useState(false);
    const [isFocused, setIsFocused] = useState(false);
    const [attachments, setAttachments] = useState<string[]>([]);
    const [templatesOpen, setTemplatesOpen] = useState(false);
    const [webSearchEnabled, setWebSearchEnabled] = useState(false);
    const [linkCollectionEnabled, setLinkCollectionEnabled] = useState(false);
    const [schedulePreset, setSchedulePreset] = useState<'Run now' | 'Hourly' | 'Daily'>('Run now');
    const [listening, setListening] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const templateOptions = [
        'Enumerate application attack surface and list reachable services.',
        'Probe authentication and session management with safe defaults.',
        'Search for common misconfigurations and insecure headers.',
        'Summarize remediation steps for each confirmed finding.'
    ];

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

    const handleAttachment = (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(event.target.files || []).map(file => file.name);
        if (files.length === 0) return;
        setAttachments((prev) => [...prev, ...files]);
        event.target.value = '';
    };

    const removeAttachment = (name: string) => {
        setAttachments((prev) => prev.filter((file) => file !== name));
    };

    const toggleSchedulePreset = () => {
        setSchedulePreset((prev) => {
            if (prev === 'Run now') return 'Hourly';
            if (prev === 'Hourly') return 'Daily';
            return 'Run now';
        });
    };

    const applyTemplate = (template: string) => {
        setPrompt((prev) => prev ? `${prev}\n${template}` : template);
        setTemplatesOpen(false);
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
                        <div className="flex items-center gap-1 md:gap-2 relative">
                            <button
                                className={`toolbar-btn ${attachments.length ? 'text-purple-300' : ''}`}
                                onClick={() => fileInputRef.current?.click()}
                                title="Attach reference files"
                            >
                                <Paperclip size={16} />
                            </button>
                            <div className="relative">
                                <button
                                    className={`toolbar-btn ${templatesOpen ? 'text-purple-300' : ''}`}
                                    onClick={() => setTemplatesOpen(!templatesOpen)}
                                    title="Open prompt templates"
                                >
                                    <Sparkles size={16} />
                                </button>
                                <button
                                    className={`toolbar-btn ${templatesOpen ? 'text-purple-300' : ''}`}
                                    onClick={() => setTemplatesOpen(!templatesOpen)}
                                    title="Show templates"
                                >
                                    <ChevronDown size={16} />
                                </button>

                                <AnimatePresence>
                                    {templatesOpen && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: 10 }}
                                            className="absolute left-0 mt-2 w-72 bg-surface-900 border border-white/10 rounded-xl shadow-2xl overflow-hidden p-1 z-50"
                                        >
                                            {templateOptions.map((template) => (
                                                <button
                                                    key={template}
                                                    onClick={() => applyTemplate(template)}
                                                    className="w-full text-left px-3 py-2 text-sm text-zinc-300 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                                                >
                                                    {template}
                                                </button>
                                            ))}
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>

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
                            <button
                                className={`toolbar-btn ${linkCollectionEnabled ? 'text-purple-300 bg-white/[0.06]' : ''}`}
                                onClick={() => setLinkCollectionEnabled(!linkCollectionEnabled)}
                                title="Collect source links"
                            >
                                <Link2 size={16} />
                            </button>
                            <button
                                className={`toolbar-btn ${webSearchEnabled ? 'text-purple-300 bg-white/[0.06]' : ''}`}
                                onClick={() => setWebSearchEnabled(!webSearchEnabled)}
                                title="Allow web discovery"
                            >
                                <Globe2 size={16} />
                            </button>
                            <button
                                className={`toolbar-btn ${schedulePreset !== 'Run now' ? 'text-purple-300 bg-white/[0.06]' : ''}`}
                                onClick={toggleSchedulePreset}
                                title={`Schedule: ${schedulePreset}`}
                            >
                                <Clock3 size={16} />
                            </button>
                            <div className="flex items-center gap-2">
                                <button
                                    className={`toolbar-btn ${listening ? 'text-purple-300 bg-white/[0.06]' : ''}`}
                                    onClick={() => setListening(!listening)}
                                    title={listening ? 'Listening' : 'Start voice capture'}
                                >
                                    <Mic size={16} />
                                </button>
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

                    <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        className="hidden"
                        onChange={handleAttachment}
                    />

                    {(attachments.length > 0 || linkCollectionEnabled || webSearchEnabled || schedulePreset !== 'Run now' || listening) && (
                        <div className="flex flex-wrap gap-2 mt-3">
                            {attachments.map((file) => (
                                <span key={file} className="px-3 py-1 rounded-full bg-white/[0.04] border border-white/10 text-xs text-zinc-200 flex items-center gap-2">
                                    {file}
                                    <button className="text-zinc-500 hover:text-white" onClick={() => removeAttachment(file)}>×</button>
                                </span>
                            ))}
                            {linkCollectionEnabled && <span className="stat-pill text-purple-200">Link collection on</span>}
                            {webSearchEnabled && <span className="stat-pill text-purple-200">Web search enabled</span>}
                            {schedulePreset !== 'Run now' && <span className="stat-pill text-purple-200">{schedulePreset} cadence</span>}
                            {listening && <span className="stat-pill text-purple-200">Listening for voice notes</span>}
                        </div>
                    )}
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

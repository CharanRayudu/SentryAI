'use client';

import { useState } from 'react';
import {
    Search,
    Github,
    Terminal,
    CheckCircle2,
    Download,
    Play,
    Settings,
    Plus
} from 'lucide-react';
import { motion } from 'framer-motion';

interface Tool {
    id: string;
    name: string;
    repo: string;
    description: string;
    status: 'installed' | 'installing' | 'ready';
    version: string;
}

export default function ToolsPage() {
    const [repoUrl, setRepoUrl] = useState('');
    const [tools, setTools] = useState<Tool[]>([
        { id: '1', name: 'Nuclei', repo: 'projectdiscovery/nuclei', description: 'Fast and customizable vulnerability scanner', status: 'installed', version: 'v3.1.0' },
        { id: '2', name: 'Subfinder', repo: 'projectdiscovery/subfinder', description: 'Passive subdomain discovery tool', status: 'installed', version: 'v2.6.3' },
        { id: '3', name: 'Naabu', repo: 'projectdiscovery/naabu', description: 'Fast port scanner', status: 'ready', version: 'v2.1.1' },
    ]);

    const installTool = () => {
        if (!repoUrl) return;

        // Simulate GitHub parsing
        const name = repoUrl.split('/').pop()?.replace('.git', '') || 'Unknown Tool';

        const newTool: Tool = {
            id: Date.now().toString(),
            name: name,
            repo: repoUrl.replace('https://github.com/', ''),
            description: 'Custom community tool',
            status: 'installing',
            version: 'latest'
        };

        setTools(prev => [newTool, ...prev]);
        setRepoUrl('');

        // Simulate installation process
        setTimeout(() => {
            setTools(prev => prev.map(t => t.id === newTool.id ? { ...t, status: 'installed' } : t));
        }, 3000);
    };

    return (
        <div className="flex flex-col h-full bg-[#050505] text-white">
            {/* Header */}
            <div className="p-8 border-b border-[#222]">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h1 className="text-3xl font-semibold tracking-tight mb-2">Tool Arsenal</h1>
                        <p className="text-gray-500 max-w-2xl">
                            Equip your agents with the latest open-source security tools.
                            Paste a GitHub repository URL, and SentryAI will automatically build, configure, and sandox the tool for agent use.
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <button className="flex items-center gap-2 px-4 py-2 bg-[#1a1a1a] hover:bg-[#222] border border-[#333] rounded-lg transition-colors text-sm font-medium">
                            <Terminal size={16} /> View Logs
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 bg-white text-black hover:bg-gray-200 rounded-lg transition-colors text-sm font-medium">
                            <Plus size={16} /> Create Tool Wrapper
                        </button>
                    </div>
                </div>

                {/* Installer Bar */}
                <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <Github size={20} className="text-gray-500 group-focus-within:text-white transition-colors" />
                    </div>
                    <input
                        type="text"
                        className="w-full bg-[#0a0a0a] border border-[#333] rounded-xl py-4 pl-12 pr-32 text-white placeholder-gray-600 focus:outline-none focus:border-purple-500/50 transition-all shadow-lg"
                        placeholder="Paste GitHub Repository URL (e.g., https://github.com/sqlmapproject/sqlmap)"
                        value={repoUrl}
                        onChange={(e) => setRepoUrl(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && installTool()}
                    />
                    <button
                        onClick={installTool}
                        disabled={!repoUrl}
                        className="absolute right-2 top-2 bottom-2 px-4 bg-[#1a1a1a] hover:bg-[#fff] hover:text-black border border-[#333] rounded-lg text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Install
                    </button>
                </div>
            </div>

            {/* Tools Grid */}
            <div className="p-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 overflow-y-auto">
                {tools.map((tool) => (
                    <div key={tool.id} className="bg-[#0a0a0a] border border-[#222] rounded-xl p-5 hover:border-purple-500/30 transition-all group relative overflow-hidden">
                        {tool.status === 'installing' && (
                            <div className="absolute inset-0 bg-black/80 flex items-center justify-center z-10 backdrop-blur-sm">
                                <div className="flex flex-col items-center gap-2">
                                    <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
                                    <span className="text-xs font-mono text-purple-400">CLONING REPO...</span>
                                </div>
                            </div>
                        )}

                        <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-[#111] border border-[#222] flex items-center justify-center group-hover:border-purple-500/50 transition-colors">
                                    <Terminal size={20} className="text-gray-400 group-hover:text-purple-400" />
                                </div>
                                <div>
                                    <h3 className="font-medium text-white">{tool.name}</h3>
                                    <div className="flex items-center gap-2 text-xs text-gray-500">
                                        <Github size={10} />
                                        <span>{tool.repo}</span>
                                    </div>
                                </div>
                            </div>
                            <div className={`
                flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-medium uppercase tracking-wider border
                ${tool.status === 'installed' ? 'bg-green-500/10 text-green-500 border-green-500/20' : 'bg-gray-800 text-gray-400 border-gray-700'}
              `}>
                                {tool.status === 'installed' ? <CheckCircle2 size={10} /> : <Download size={10} />}
                                {tool.status}
                            </div>
                        </div>

                        <p className="text-sm text-gray-400 mb-4 h-10 line-clamp-2">
                            {tool.description}
                        </p>

                        <div className="flex items-center justify-between pt-4 border-t border-[#1a1a1a]">
                            <span className="text-xs font-mono text-gray-600">{tool.version}</span>
                            <div className="flex gap-2">
                                <button className="p-1.5 hover:bg-[#222] rounded text-gray-400 hover:text-white transition-colors">
                                    <Settings size={14} />
                                </button>
                                <button className="p-1.5 hover:bg-[#222] rounded text-gray-400 hover:text-white transition-colors">
                                    <Play size={14} />
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

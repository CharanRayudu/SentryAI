'use client';

import { useState } from 'react';
import {
    Bot,
    Search,
    Settings,
    Globe,
    Wrench,
    Copy,
    MoreHorizontal,
    Sparkles,
    ChevronDown
} from 'lucide-react';
import { motion } from 'framer-motion';

const AGENTS = [
    { id: '1', name: 'Matrix Microservices Security Specialist', role: 'Security Auditor', active: true },
    { id: '2', name: 'Vercel Security Auditor', role: 'Infra Sec', active: false },
    { id: '3', name: 'API Reconnaissance Specialist', role: 'Recon', active: false },
    { id: '4', name: 'Penetration Testing Planner', role: 'Planner', active: false },
    { id: '5', name: 'Code Security Testing Specialist', role: 'SAST', active: false },
];

const DEFAULT_CONTEXT = `You are an elite security specialist for ProjectDiscovery Aurora — a distributed, cloud-scale vulnerability scanning orchestration platform built with Go 1.24.2, Echo v4, NATS JetStream, PostgreSQL, Redis, and Nuclei v3.

**YOUR PRIMARY RESPONSIBILITIES:**
1. **Security Code Reviews**: Review Aurora pull requests and code changes for security vulnerabilities
2. **Architecture Analysis**: Assess security implications of system design changes
3. **Vulnerability Assessment**: Identify and verify exploitable security flaws
4. **Threat Modeling**: Understand Aurora's threat landscape and attack vectors

**CRITICAL: UNDERSTAND AURORA'S DESIGN BEFORE FLAGGING VULNERABILITIES**

⚠️ **MANDATORY PRE-ASSESSMENT CHECKLIST** ⚠️
Before reporting ANY vulnerability, you MUST:
1. **Read the PR Description Thoroughly**
   - Understand the PURPOSE of the code change
   - Identify if it's a new feature, bug fix, or infrastructure change`;

export default function AgentsPage() {
    const [selectedAgentId, setSelectedAgentId] = useState('1');
    const [context, setContext] = useState(DEFAULT_CONTEXT);

    const selectedAgent = AGENTS.find(a => a.id === selectedAgentId);

    return (
        <div className="flex h-full bg-[#050505] text-white overflow-hidden">

            {/* 1. LEFT PANE: AGENT LIST */}
            <div className="w-80 border-r border-[#222] flex flex-col bg-[#0a0a0a]">
                <div className="p-4 border-b border-[#222]">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="font-semibold text-lg">Agents</h2>
                        <Search size={16} className="text-gray-500" />
                    </div>

                    <button className="w-full flex items-center justify-between px-3 py-2 rounded-lg border border-[#333] text-sm text-gray-400 hover:text-white hover:bg-[#111] transition-colors mb-2">
                        <div className="flex items-center gap-2">
                            <Globe size={14} />
                            <span>Explore Community Agents</span>
                        </div>
                        <ChevronDown size={14} />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                    {AGENTS.map((agent) => (
                        <div
                            key={agent.id}
                            onClick={() => setSelectedAgentId(agent.id)}
                            className={`
                p-3 rounded-lg cursor-pointer transition-all border
                ${selectedAgentId === agent.id
                                    ? 'bg-[#1a1a1a] border-purple-500/30 text-white'
                                    : 'bg-transparent border-transparent text-gray-400 hover:bg-[#111] hover:text-gray-200'}
              `}
                        >
                            <div className="text-sm font-medium mb-0.5">{agent.name}</div>
                            <div className="text-xs opacity-60 truncate">{agent.role}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* 2. RIGHT PANE: AGENT EDITOR */}
            <div className="flex-1 flex flex-col bg-[#050505]">

                {/* Header */}
                <div className="h-16 border-b border-[#222] flex items-center justify-between px-6 bg-[#0a0a0a]">
                    <div>
                        <h1 className="font-semibold text-lg">{selectedAgent?.name}</h1>
                        <p className="text-xs text-gray-500 max-w-xl truncate">
                            Specializes in systematic security auditing of distributed vulnerability scanning platforms including CORS misconfigurations.
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-[#333] bg-[#050505] text-xs font-medium text-gray-300">
                            <Sparkles size={12} className="text-purple-400" />
                            Knowledge Auto
                            <ChevronDown size={12} className="ml-1 opacity-50" />
                        </div>
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-[#333] bg-[#050505] text-xs font-medium text-gray-300">
                            <Wrench size={12} className="text-blue-400" />
                            Tools Auto
                            <ChevronDown size={12} className="ml-1 opacity-50" />
                        </div>

                        <button className="px-4 py-1.5 bg-white text-black text-xs font-bold uppercase tracking-wider rounded-full hover:bg-gray-200 transition-colors">
                            Publish
                        </button>
                        <MoreHorizontal size={16} className="text-gray-500 cursor-pointer" />
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex items-center gap-6 px-6 border-b border-[#222] text-sm font-medium text-gray-500">
                    <button className="py-3 text-white border-b-2 border-purple-500 flex items-center gap-2">
                        <span>&lt;/&gt;</span> System Context
                    </button>
                    <button className="py-3 hover:text-gray-300 flex items-center gap-2">
                        <Wrench size={14} /> Tools
                    </button>
                    <button className="py-3 hover:text-gray-300 flex items-center gap-2">
                        <span>&gt;_</span> Installation
                    </button>
                    <button className="py-3 hover:text-gray-300">When to Use</button>
                </div>

                {/* Editor Area */}
                <div className="flex-1 p-6 overflow-hidden flex flex-col">
                    <div className="flex items-center justify-between mb-2">
                        <div className="text-xs font-bold text-gray-500 uppercase tracking-widest">System Context</div>
                        <button className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors">
                            <Copy size={12} /> Copy
                        </button>
                    </div>

                    <div className="flex-1 bg-[#0a0a0a] border border-[#222] rounded-lg overflow-hidden relative font-mono text-sm leading-relaxed">
                        {/* Line Numbers Fake */}
                        <div className="absolute left-0 top-0 bottom-0 w-10 bg-[#111] border-r border-[#222] text-gray-600 flex flex-col items-end pt-4 pr-3 select-none text-xs">
                            {Array.from({ length: 20 }).map((_, i) => <div key={i}>{i + 1}</div>)}
                        </div>

                        <textarea
                            className="w-full h-full bg-transparent text-gray-300 p-4 pl-12 resize-none outline-none focus:bg-[#0f0f0f] transition-colors"
                            value={context}
                            onChange={(e) => setContext(e.target.value)}
                            spellCheck="false"
                        />
                    </div>
                </div>

            </div>
        </div>
    );
}

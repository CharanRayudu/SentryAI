'use client';

import { useState, useRef, useEffect } from 'react';
import { Terminal, Globe, Shield, CheckCircle, Circle, Play, Pause, Maximize2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Mimics the "Phase 1: Port Scanning" view
export default function ActiveOperation({ target }: { target: string }) {
    const [logs, setLogs] = useState<string[]>([
        `$ masscan ${target} -p1-65535 --rate=10000 --open`,
        `Starting masscan 1.3.2 at ${new Date().toUTCString()}`,
        "Initiating SYN Stealth Scan",
        "Scanning 1 hosts [65535 ports/host]",
        "rate: 5.51-kpps, 0.69% done, 5:14:25 remaining, found=0",
        "rate: 9.95-kpps, 61.05% done, 0:00:04 remaining, found=1",
        "Discovered open port 3000/tcp on " + target
    ]);

    return (
        <div className="flex flex-col h-screen w-full bg-[#050505] text-white overflow-hidden">
            {/* Top Bar */}
            <div className="flex items-center justify-between px-6 py-3 border-b border-[#222] bg-[#0a0a0a]">
                <div className="flex items-center gap-3">
                    <LoaderIcon />
                    <span className="text-sm font-medium text-gray-300">
                        Perform comprehensive port scan on <span className="text-white">{target}</span>... (1/4)
                    </span>
                </div>
                <button className="text-xs text-gray-500 hover:text-white flex items-center gap-1">
                    <Maximize2 size={12} /> Fullscreen
                </button>
            </div>

            <div className="flex-1 flex overflow-hidden">
                {/* LEFT: Task Steps */}
                <div className="w-[400px] border-r border-[#222] bg-[#0a0a0a] p-4 flex flex-col gap-6 overflow-y-auto">
                    <div>
                        <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Tasks</h3>
                        <div className="space-y-4">
                            <StepItem status="active" label={`Perform comprehensive port scan on ${target} to identify all open ports`} />
                            <StepItem status="pending" label="Enumerate service versions and perform banner grabbing" />
                            <StepItem status="pending" label="Map exposed endpoints and web application structure" />
                            <StepItem status="pending" label="Analyze web application technology stack" />
                        </div>
                    </div>
                </div>

                {/* RIGHT: Thinking & Terminal */}
                <div className="flex-1 flex flex-col bg-[#050505]">

                    {/* Thinking Block */}
                    <div className="p-8 border-b border-[#222]">
                        <div className="text-xs font-bold text-gray-600 uppercase tracking-widest mb-2">Thinking and Tools</div>
                        <h2 className="text-2xl font-semibold mb-2">Phase 1: Port Scanning & Service Enumeration</h2>
                        <p className="text-gray-400 text-sm mb-6">Starting with rapid port discovery using masscan to identify attack surface.</p>

                        <div className="bg-[#111] border border-[#222] rounded-lg p-4">
                            <div className="flex items-center gap-2 mb-2 text-purple-400">
                                <Shield size={16} />
                                <span className="text-sm font-semibold">Excellent! 3 open ports discovered:</span>
                            </div>
                            <ul className="list-disc list-inside text-sm text-gray-300 space-y-1 ml-2">
                                <li><span className="font-mono text-white">22/tcp</span> (SSH)</li>
                                <li><span className="font-mono text-white">3000/tcp</span> (Web service - target)</li>
                                <li><span className="font-mono text-white">12345/tcp</span> (Unknown service)</li>
                            </ul>
                        </div>
                    </div>

                    {/* Terminal Block */}
                    <div className="flex-1 bg-[#050505] p-4 font-mono text-xs overflow-y-auto relative">
                        <div className="absolute top-0 left-0 px-4 py-2 text-[10px] text-gray-500 font-bold tracking-widest uppercase bg-[#050505] w-full border-b border-[#222]">Terminal</div>
                        <div className="mt-8 space-y-1 text-gray-400">
                            {logs.map((log, i) => (
                                <div key={i} className={log.startsWith('$') ? 'text-green-400 font-bold' : ''}>{log}</div>
                            ))}
                            <div className="flex items-center gap-2">
                                <span className="text-green-500">{'>'}</span>
                                <span className="animate-pulse bg-gray-600 w-2 h-4 block"></span>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}

function StepItem({ status, label }: { status: 'done' | 'active' | 'pending', label: string }) {
    return (
        <div className="flex gap-3">
            <div className="mt-0.5">
                {status === 'active' && <LoaderIcon />}
                {status === 'pending' && <Circle size={18} className="text-gray-700" />}
                {status === 'done' && <CheckCircle size={18} className="text-green-500" />}
            </div>
            <span className={`text-sm ${status === 'active' ? 'text-white' : 'text-gray-500'}`}>{label}</span>
        </div>
    );
}

function LoaderIcon() {
    return (
        <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
        >
            <div className="w-4 h-4 border-2 border-gray-600 border-t-white rounded-full"></div>
        </motion.div>
    );
}

'use client';

import { useEffect, useRef, useState } from 'react';
import { Wifi } from 'lucide-react';

interface Log {
    id: string;
    timestamp: string;
    message: string;
    type: 'info' | 'warning' | 'error' | 'success';
}

const MOCK_LOGS: Log[] = [
    { id: '1', timestamp: '14:20:01', message: 'System initialized', type: 'info' },
    { id: '2', timestamp: '14:20:05', message: 'Connected to Temporal Cloud', type: 'success' },
    { id: '3', timestamp: '14:21:12', message: 'Scanning ports on target 192.168.1.5', type: 'info' },
    { id: '4', timestamp: '14:21:45', message: 'Port 80 OPEN (http)', type: 'warning' },
    { id: '5', timestamp: '14:22:01', message: 'Nuclei scan started: cve-2023-xxxx', type: 'info' },
];

export default function IntelPanel() {
    const scrollRef = useRef<HTMLDivElement>(null);
    const [logs] = useState<Log[]>(MOCK_LOGS);

    // Auto-scroll to bottom of logs
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="flex flex-col h-full p-4 gap-4">
            {/* Header */}
            <div className="flex items-center justify-between px-2 py-2 border-b border-[#ffffff0a]">
                <div className="flex items-center gap-2">
                    <Wifi size={14} className="text-green-500 animate-pulse" />
                    <span className="text-xs font-bold tracking-widest text-white uppercase">Live Feed</span>
                </div>
                <div className="text-[10px] text-zinc-500 font-mono">SECURE</div>
            </div>

            {/* Live Logs */}
            <div className="flex-1 flex flex-col min-h-0 bg-black/40 rounded-lg border border-[#ffffff0a]">
                <div className="px-3 py-2 bg-white/5 border-b border-[#ffffff05] flex justify-between items-center">
                    <span className="text-[10px] uppercase text-zinc-400 font-medium">System Events</span>
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-ping" />
                </div>

                <div
                    ref={scrollRef}
                    className="flex-1 overflow-y-auto p-3 space-y-2 font-mono text-[11px]"
                >
                    {logs.map((log) => (
                        <div key={log.id} className="flex gap-2 opacity-80 hover:opacity-100 transition-opacity">
                            <span className="text-zinc-600 shrink-0">[{log.timestamp}]</span>
                            <span className={`
                                ${log.type === 'info' ? 'text-zinc-300' : ''}
                                ${log.type === 'warning' ? 'text-amber-400' : ''}
                                ${log.type === 'error' ? 'text-red-400' : ''}
                                ${log.type === 'success' ? 'text-green-400' : ''}
                            `}>
                                {log.type === 'warning' && '⚠ '}
                                {log.message}
                            </span>
                        </div>
                    ))}
                    <div className="h-4" /> {/* Spacer */}
                </div>
            </div>

            {/* Recent Alerts (Mini Findings) */}
            <div className="h-1/3 flex flex-col min-h-0">
                <div className="px-2 py-2 mb-2 flex justify-between items-center">
                    <span className="text-[10px] uppercase text-zinc-500 font-bold tracking-wider">Priority Alerts</span>
                    <span className="text-[10px] text-zinc-600">3 New</span>
                </div>

                <div className="space-y-2 overflow-y-auto pr-1">
                    <div className="p-3 neo-card bg-red-500/5 border-red-500/20 group cursor-pointer hover:bg-red-500/10">
                        <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-bold text-red-400 group-hover:text-red-300">SQL Injection</span>
                            <span className="px-1.5 py-0.5 text-[9px] bg-red-500/20 text-red-400 rounded uppercase">Critical</span>
                        </div>
                        <p className="text-[10px] text-zinc-400 truncate">/api/v1/users endpoint exposed to sqli...</p>
                    </div>

                    <div className="p-3 neo-card bg-amber-500/5 border-amber-500/20 group cursor-pointer hover:bg-amber-500/10">
                        <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-bold text-amber-400 group-hover:text-amber-300">Exposed .git</span>
                            <span className="px-1.5 py-0.5 text-[9px] bg-amber-500/20 text-amber-400 rounded uppercase">Medium</span>
                        </div>
                        <p className="text-[10px] text-zinc-400 truncate">.git directory found at root of web...</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

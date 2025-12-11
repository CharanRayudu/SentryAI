'use client';

import {
    Shield,
    Activity,
    Terminal,
    Database,
    Power,
    Cpu,
    Network
} from 'lucide-react';

interface SystemPanelProps {
    activeView: string;
    onViewChange: (view: string) => void;
}

export default function SystemPanel({ activeView, onViewChange }: SystemPanelProps) {
    const navItems = [
        { id: 'new', label: 'Mission Control', icon: Shield },
        { id: 'operations', label: 'Active Ops', icon: Activity },
        { id: 'findings', label: 'Intel Database', icon: Database },
        { id: 'console', label: 'Terminal', icon: Terminal },
    ];

    return (
        <div className="flex flex-col h-full p-4 gap-6">
            {/* Header */}
            <div className="flex items-center gap-3 px-2 py-2 border-b border-[#ffffff0a]">
                <div className="w-8 h-8 rounded bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center shadow-[0_0_15px_rgba(147,51,234,0.5)]">
                    <Shield className="w-4 h-4 text-white" />
                </div>
                <div>
                    <h2 className="text-xs font-bold tracking-widest text-white uppercase">Sentry<span className="text-purple-400">AI</span></h2>
                    <p className="text-[10px] text-zinc-500 font-mono">SYS.ONLINE</p>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-2">
                <div className="text-[10px] text-zinc-500 font-mono uppercase tracking-wider px-2 mb-2">Modules</div>
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onViewChange(item.id)}
                        className={`w-full flex items-center gap-3 px-3 py-3 rounded-md transition-all duration-200 border border-transparent
                            ${activeView === item.id
                                ? 'bg-purple-500/10 border-purple-500/30 text-white shadow-[0_0_10px_rgba(168,85,247,0.2)]'
                                : 'text-zinc-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        <item.icon size={16} />
                        <span className="text-sm font-medium tracking-wide">{item.label}</span>
                        {activeView === item.id && (
                            <div className="ml-auto w-1.5 h-1.5 rounded-full bg-purple-400 shadow-[0_0_5px_currentColor]" />
                        )}
                    </button>
                ))}
            </nav>

            {/* System Diagnostics (Visual Filler) */}
            <div className="mt-auto neo-panel p-4 rounded-lg space-y-4">
                <div className="text-[10px] text-zinc-500 font-mono uppercase tracking-wider mb-2">Diagnostics</div>

                <div className="space-y-1">
                    <div className="flex justify-between text-[10px] text-zinc-400">
                        <span className="flex items-center gap-1"><Cpu size={10} /> CPU</span>
                        <span className="text-green-400">12%</span>
                    </div>
                    <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                        <div className="h-full w-[12%] bg-green-500 shadow-[0_0_5px_currentColor]" />
                    </div>
                </div>

                <div className="space-y-1">
                    <div className="flex justify-between text-[10px] text-zinc-400">
                        <span className="flex items-center gap-1"><Database size={10} /> MEM</span>
                        <span className="text-purple-400">34%</span>
                    </div>
                    <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                        <div className="h-full w-[34%] bg-purple-500 shadow-[0_0_5px_currentColor]" />
                    </div>
                </div>

                <div className="space-y-1">
                    <div className="flex justify-between text-[10px] text-zinc-400">
                        <span className="flex items-center gap-1"><Network size={10} /> NET</span>
                        <span className="text-cyan-400">ACTIVE</span>
                    </div>
                    <div className="flex gap-0.5">
                        {[...Array(10)].map((_, i) => (
                            <div key={i} className={`h-1 w-full rounded-sm ${i < 8 ? 'bg-cyan-500' : 'bg-zinc-800'} animate-pulse`} style={{ animationDelay: `${i * 100}ms` }} />
                        ))}
                    </div>
                </div>
            </div>

            {/* Footer */}
            <button className="flex items-center gap-2 px-3 py-2 text-xs text-zinc-500 hover:text-red-400 transition-colors">
                <Power size={14} />
                <span>Disconnect</span>
            </button>
        </div>
    );
}

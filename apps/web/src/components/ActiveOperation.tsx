'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Terminal,
    Globe,
    Shield,
    Check,
    Loader2,
    Play,
    Pause,
    Maximize2,
    AlertTriangle,
    ChevronRight,
    Clock,
    Cpu
} from 'lucide-react';

interface ActiveOperationProps {
    target: string;
    onComplete?: () => void;
}

interface DiscoveredService {
    port: number;
    service: string;
    version?: string;
    status: 'open' | 'filtered';
}

export default function ActiveOperation({ target, onComplete }: ActiveOperationProps) {
    const [logs, setLogs] = useState<string[]>([]);
    const [isMounted, setIsMounted] = useState(false);
    const [discoveredServices, setDiscoveredServices] = useState<DiscoveredService[]>([]);
    const [currentStep, setCurrentStep] = useState(0);
    const [progress, setProgress] = useState(0);
    const logsEndRef = useRef<HTMLDivElement>(null);

    // Initialize logs after mount to avoid hydration mismatch
    useEffect(() => {
        setLogs([
            `$ masscan ${target} -p1-65535 --rate=10000 --open`,
            `[${new Date().toLocaleTimeString()}] Starting masscan 1.3.2`,
            "Initiating SYN Stealth Scan",
            "Scanning 1 hosts [65535 ports/host]",
        ]);
        setIsMounted(true);
    }, [target]);

    // Simulate progressive log updates (only after mount)
    useEffect(() => {
        if (!isMounted) return;
        
        const additionalLogs = [
            "rate: 5.51-kpps, 15% done",
            "rate: 9.95-kpps, 35% done",
            `Discovered open port 22/tcp on ${target}`,
            "rate: 9.95-kpps, 55% done",
            `Discovered open port 443/tcp on ${target}`,
            "rate: 9.95-kpps, 75% done",
            `Discovered open port 3000/tcp on ${target}`,
            "rate: 9.95-kpps, 95% done",
            "Scan complete. 3 open ports found.",
            `$ nmap -sV -p22,443,3000 ${target}`,
            "Starting Nmap 7.94 ( https://nmap.org )",
            "22/tcp   open  ssh      OpenSSH 8.9p1",
            "443/tcp  open  ssl/http nginx 1.18.0",
            "3000/tcp open  http     Node.js Express",
            "Service detection complete.",
        ];

        const services: DiscoveredService[] = [
            { port: 22, service: 'ssh', version: 'OpenSSH 8.9p1', status: 'open' },
            { port: 443, service: 'https', version: 'nginx 1.18.0', status: 'open' },
            { port: 3000, service: 'http', version: 'Node.js Express', status: 'open' },
        ];

        let index = 0;
        const interval = setInterval(() => {
            if (index < additionalLogs.length) {
                setLogs(prev => [...prev, additionalLogs[index]]);
                setProgress(Math.min(100, ((index + 1) / additionalLogs.length) * 100));
                
                // Add discovered services
                if (additionalLogs[index].includes('Discovered')) {
                    const portMatch = additionalLogs[index].match(/(\d+)\/tcp/);
                    if (portMatch) {
                        const portNum = parseInt(portMatch[1]);
                        const service = services.find(s => s.port === portNum);
                        if (service) {
                            setDiscoveredServices(prev => [...prev, service]);
                        }
                    }
                }
                
                index++;
            } else {
                clearInterval(interval);
                setTimeout(() => {
                    setCurrentStep(1);
                    onComplete?.();
                }, 2000);
            }
        }, 600);

        return () => clearInterval(interval);
    }, [isMounted, target, onComplete]);

    // Auto-scroll logs
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const steps = [
        { label: 'Port Discovery', status: currentStep > 0 ? 'done' : 'active' },
        { label: 'Service Detection', status: currentStep > 0 ? 'active' : 'pending' },
        { label: 'Vulnerability Scan', status: 'pending' },
        { label: 'Report Generation', status: 'pending' },
    ];

    const getStepIcon = (status: string) => {
        switch (status) {
            case 'done': return <Check size={14} className="text-green-400" />;
            case 'active': return <Loader2 size={14} className="text-purple-400 animate-spin" />;
            default: return <div className="w-3.5 h-3.5 rounded-full border-2 border-zinc-700" />;
        }
    };

    return (
        <div className="flex-1 flex flex-col h-screen bg-[#050505] overflow-hidden">
            {/* Header */}
            <header className="flex items-center justify-between px-6 py-3 border-b border-white/[0.06] bg-[#0a0a0a]">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                        <span className="text-sm font-medium text-white">Live Operation</span>
                    </div>
                    <span className="text-sm text-zinc-500">•</span>
                    <span className="text-sm text-zinc-400 font-mono">{target}</span>
                </div>
                <div className="flex items-center gap-2">
                    <button className="btn-ghost flex items-center gap-1.5 text-xs">
                        <Pause size={12} /> Pause
                    </button>
                    <button className="btn-ghost flex items-center gap-1.5 text-xs">
                        <Maximize2 size={12} /> Fullscreen
                    </button>
                </div>
            </header>

            {/* Progress Steps */}
            <div className="px-6 py-4 border-b border-white/[0.06] bg-[#0a0a0a]/50">
                <div className="flex items-center gap-2">
                    {steps.map((step, i) => (
                        <div key={i} className="flex items-center">
                            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs ${
                                step.status === 'active' ? 'bg-purple-500/10 text-purple-400' :
                                step.status === 'done' ? 'bg-green-500/10 text-green-400' :
                                'bg-zinc-800/50 text-zinc-500'
                            }`}>
                                {getStepIcon(step.status)}
                                {step.label}
                            </div>
                            {i < steps.length - 1 && (
                                <ChevronRight size={14} className="text-zinc-700 mx-1" />
                            )}
                        </div>
                    ))}
                </div>
                
                {/* Progress Bar */}
                <div className="mt-3 h-1 bg-zinc-800 rounded-full overflow-hidden">
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                    />
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden">
                {/* Terminal */}
                <div className="flex-1 flex flex-col border-r border-white/[0.06]">
                    <div className="terminal-header">
                        <div className="terminal-dot bg-red-500" />
                        <div className="terminal-dot bg-yellow-500" />
                        <div className="terminal-dot bg-green-500" />
                        <span className="ml-3 text-xs text-zinc-500">Terminal Output</span>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 font-mono text-[13px] bg-[#0d0d0d]">
                        <div className="space-y-1">
                            {logs.map((log, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    className={`
                                        ${log?.startsWith?.('$') ? 'text-green-400 font-semibold' : ''}
                                        ${log?.includes?.('Discovered') || log?.includes?.('open') ? 'text-cyan-400' : ''}
                                        ${log?.includes?.('complete') || log?.includes?.('done') ? 'text-emerald-400' : ''}
                                        ${log?.includes?.('error') || log?.includes?.('failed') ? 'text-red-400' : ''}
                                        ${!log?.startsWith?.('$') && !log?.includes?.('Discovered') && !log?.includes?.('complete') && !log?.includes?.('error') ? 'text-zinc-400' : ''}
                                    `}
                                >
                                    {log || ''}
                                </motion.div>
                            ))}
                            <div ref={logsEndRef} />
                        </div>
                        
                        {/* Cursor */}
                        <div className="flex items-center gap-2 mt-2">
                            <span className="text-green-400">❯</span>
                            <motion.span
                                animate={{ opacity: [1, 0] }}
                                transition={{ duration: 0.5, repeat: Infinity }}
                                className="w-2 h-4 bg-green-400"
                            />
                        </div>
                    </div>
                </div>

                {/* Sidebar - Discovered Assets */}
                <div className="w-80 flex flex-col bg-[#0a0a0a]">
                    <div className="px-4 py-3 border-b border-white/[0.06]">
                        <h3 className="text-sm font-medium text-white">Discovered Assets</h3>
                        <p className="text-xs text-zinc-500">{discoveredServices.length} services found</p>
                    </div>
                    
                    <div className="flex-1 overflow-y-auto p-3 space-y-2">
                        <AnimatePresence>
                            {discoveredServices.map((service, i) => (
                                <motion.div
                                    key={service.port}
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="p-3 bg-[#121212] border border-white/[0.06] rounded-lg"
                                >
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                            <div className={`w-2 h-2 rounded-full ${
                                                service.status === 'open' ? 'bg-green-500' : 'bg-amber-500'
                                            }`} />
                                            <span className="text-sm font-medium text-white">
                                                Port {service.port}
                                            </span>
                                        </div>
                                        <span className="text-[10px] px-1.5 py-0.5 bg-cyan-500/10 text-cyan-400 rounded">
                                            {service.service.toUpperCase()}
                                        </span>
                                    </div>
                                    {service.version && (
                                        <p className="text-xs text-zinc-500 font-mono">{service.version}</p>
                                    )}
                                </motion.div>
                            ))}
                        </AnimatePresence>

                        {discoveredServices.length === 0 && (
                            <div className="flex flex-col items-center justify-center py-8 text-center">
                                <Loader2 className="w-8 h-8 text-zinc-700 animate-spin mb-3" />
                                <p className="text-sm text-zinc-500">Scanning for services...</p>
                            </div>
                        )}
                    </div>

                    {/* Stats */}
                    <div className="p-4 border-t border-white/[0.06]">
                        <div className="grid grid-cols-2 gap-3">
                            <div className="p-3 bg-[#121212] rounded-lg">
                                <div className="flex items-center gap-2 text-zinc-500 mb-1">
                                    <Clock size={12} />
                                    <span className="text-[10px] uppercase">Duration</span>
                                </div>
                                <p className="text-lg font-mono text-white">
                                    {Math.floor(logs.length * 0.6)}s
                                </p>
                            </div>
                            <div className="p-3 bg-[#121212] rounded-lg">
                                <div className="flex items-center gap-2 text-zinc-500 mb-1">
                                    <Cpu size={12} />
                                    <span className="text-[10px] uppercase">Packets</span>
                                </div>
                                <p className="text-lg font-mono text-white">
                                    {(logs.length * 1247).toLocaleString()}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

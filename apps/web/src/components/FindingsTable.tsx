'use client';

import { AlertTriangle, CheckCircle } from 'lucide-react';

const FINDINGS = [
    { id: 'VULN-001', type: 'SQL Injection', severity: 'critical', location: '/api/login', status: 'open' },
    { id: 'VULN-002', type: 'XSS Reflected', severity: 'high', location: '/search?q=', status: 'open' },
    { id: 'VULN-003', type: 'Exposed .env', severity: 'critical', location: '/.env', status: 'fixed' },
    { id: 'VULN-004', type: 'Missing Headers', severity: 'low', location: 'Global', status: 'open' },
    { id: 'VULN-005', type: 'Open Port 8080', severity: 'medium', location: '192.168.1.5:8080', status: 'open' },
];

export default function FindingsTable() {
    return (
        <div className="flex-1 flex flex-col p-6 h-full overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-zinc-400">
                        Security Findings
                    </h1>
                    <p className="text-zinc-500">Vulnerabilities detected across 3 active targets</p>
                </div>
                <div className="flex gap-2">
                    <div className="px-3 py-1 neo-panel rounded text-xs text-red-400 border-red-500/30">
                        2 Critical
                    </div>
                    <div className="px-3 py-1 neo-panel rounded text-xs text-amber-400 border-amber-500/30">
                        1 High
                    </div>
                </div>
            </div>

            {/* Table Container */}
            <div className="flex-1 neo-panel rounded-lg overflow-hidden flex flex-col border-[#ffffff0a] bg-[#050505]">
                {/* Table Header */}
                <div className="grid grid-cols-12 gap-4 px-6 py-3 bg-white/5 border-b border-[#ffffff05] text-xs font-medium text-zinc-400 uppercase tracking-wider">
                    <div className="col-span-2">ID</div>
                    <div className="col-span-3">Vulnerability</div>
                    <div className="col-span-2">Severity</div>
                    <div className="col-span-3">Location</div>
                    <div className="col-span-2 text-right">Status</div>
                </div>

                {/* Table Body */}
                <div className="flex-1 overflow-y-auto">
                    {FINDINGS.map((finding) => (
                        <div
                            key={finding.id}
                            className="grid grid-cols-12 gap-4 px-6 py-4 border-b border-[#ffffff05] hover:bg-white/5 transition-colors group items-center"
                        >
                            <div className="col-span-2 font-mono text-xs text-zinc-500 group-hover:text-purple-400 transition-colors">
                                {finding.id}
                            </div>
                            <div className="col-span-3 font-medium text-zinc-200">
                                {finding.type}
                            </div>
                            <div className="col-span-2">
                                <span className={`
                                    px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border
                                    ${finding.severity === 'critical' ? 'bg-red-500/10 text-red-400 border-red-500/20' : ''}
                                    ${finding.severity === 'high' ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' : ''}
                                    ${finding.severity === 'medium' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' : ''}
                                    ${finding.severity === 'low' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : ''}
                                `}>
                                    {finding.severity}
                                </span>
                            </div>
                            <div className="col-span-3 font-mono text-xs text-zinc-500 truncate">
                                {finding.location}
                            </div>
                            <div className="col-span-2 text-right">
                                {finding.status === 'fixed' ? (
                                    <span className="inline-flex items-center gap-1.5 text-xs text-green-400">
                                        <CheckCircle size={12} /> Fixed
                                    </span>
                                ) : (
                                    <span className="inline-flex items-center gap-1.5 text-xs text-zinc-400">
                                        <AlertTriangle size={12} /> Open
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

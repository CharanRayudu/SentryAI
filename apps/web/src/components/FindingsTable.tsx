'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    AlertTriangle,
    AlertCircle,
    Info,
    Shield,
    ExternalLink,
    Filter,
    Download,
    ChevronDown,
    Search,
    X,
    Clock,
    Globe,
    Terminal,
    Copy,
    Check,
    Zap
} from 'lucide-react';

// --- Types ---
interface Finding {
    id: string;
    severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
    title: string;
    host: string;
    path: string;
    tool: string;
    status: 'new' | 'confirmed' | 'false_positive' | 'resolved';
    timestamp: string;
    description?: string;
    evidence?: string;
    remediation?: string;
    cvss?: number;
    cwe?: string;
}

// Sample data
const SAMPLE_FINDINGS: Finding[] = [
    {
        id: '1',
        severity: 'critical',
        title: 'SQL Injection in Login Form',
        host: 'api.example.com',
        path: '/api/v1/auth/login',
        tool: 'nuclei',
        status: 'new',
        timestamp: '2024-01-15T10:30:00Z',
        description: 'The login endpoint is vulnerable to SQL injection attacks through the username parameter.',
        evidence: "POST /api/v1/auth/login\nContent-Type: application/json\n\n{\"username\": \"admin' OR '1'='1\", \"password\": \"test\"}",
        remediation: 'Use parameterized queries or prepared statements for all database queries.',
        cvss: 9.8,
        cwe: 'CWE-89'
    },
    {
        id: '2',
        severity: 'high',
        title: 'Cross-Site Scripting (XSS)',
        host: 'www.example.com',
        path: '/search',
        tool: 'nuclei',
        status: 'confirmed',
        timestamp: '2024-01-15T10:25:00Z',
        description: 'Reflected XSS vulnerability in the search parameter.',
        cvss: 7.5,
        cwe: 'CWE-79'
    },
    {
        id: '3',
        severity: 'medium',
        title: 'Missing Security Headers',
        host: 'www.example.com',
        path: '/',
        tool: 'httpx',
        status: 'new',
        timestamp: '2024-01-15T10:20:00Z',
        description: 'The application is missing important security headers including X-Frame-Options and Content-Security-Policy.',
        cvss: 5.3,
        cwe: 'CWE-693'
    },
    {
        id: '4',
        severity: 'low',
        title: 'Server Version Disclosure',
        host: 'api.example.com',
        path: '/',
        tool: 'httpx',
        status: 'resolved',
        timestamp: '2024-01-15T10:15:00Z',
        description: 'The server reveals its version in HTTP headers.',
        cvss: 3.1,
        cwe: 'CWE-200'
    },
    {
        id: '5',
        severity: 'info',
        title: 'Open Port Detected',
        host: 'db.example.com',
        path: ':5432',
        tool: 'naabu',
        status: 'new',
        timestamp: '2024-01-15T10:10:00Z',
        description: 'PostgreSQL port is accessible from the network.',
    },
];

const SEVERITY_CONFIG = {
    critical: { 
        color: 'text-red-400', 
        bg: 'bg-red-500/10', 
        border: 'border-red-500/20',
        icon: AlertTriangle,
        label: 'Critical'
    },
    high: { 
        color: 'text-orange-400', 
        bg: 'bg-orange-500/10', 
        border: 'border-orange-500/20',
        icon: AlertCircle,
        label: 'High'
    },
    medium: { 
        color: 'text-amber-400', 
        bg: 'bg-amber-500/10', 
        border: 'border-amber-500/20',
        icon: Shield,
        label: 'Medium'
    },
    low: { 
        color: 'text-blue-400', 
        bg: 'bg-blue-500/10', 
        border: 'border-blue-500/20',
        icon: Info,
        label: 'Low'
    },
    info: { 
        color: 'text-zinc-400', 
        bg: 'bg-zinc-500/10', 
        border: 'border-zinc-500/20',
        icon: Info,
        label: 'Info'
    },
};

const STATUS_CONFIG = {
    new: { color: 'text-purple-400', bg: 'bg-purple-500/10', label: 'New' },
    confirmed: { color: 'text-red-400', bg: 'bg-red-500/10', label: 'Confirmed' },
    false_positive: { color: 'text-zinc-400', bg: 'bg-zinc-500/10', label: 'False Positive' },
    resolved: { color: 'text-green-400', bg: 'bg-green-500/10', label: 'Resolved' },
};

export default function FindingsTable() {
    const [findings] = useState<Finding[]>(SAMPLE_FINDINGS);
    const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [severityFilter, setSeverityFilter] = useState<string[]>([]);
    const [copied, setCopied] = useState(false);

    const filteredFindings = findings.filter(f => {
        const matchesSearch = f.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            f.host.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesSeverity = severityFilter.length === 0 || severityFilter.includes(f.severity);
        return matchesSearch && matchesSeverity;
    });

    const severityCounts = findings.reduce((acc, f) => {
        acc[f.severity] = (acc[f.severity] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="flex-1 flex h-screen overflow-hidden">
            {/* Main Content */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Header */}
                <header className="px-8 py-4 border-b border-white/[0.06]">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h1 className="text-xl font-semibold text-white">Security Findings</h1>
                            <p className="text-sm text-zinc-500">{findings.length} vulnerabilities discovered</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <button className="btn-ghost flex items-center gap-2 text-sm">
                                <Download size={16} />
                                Export
                            </button>
                        </div>
                    </div>

                    {/* Filters */}
                    <div className="flex items-center gap-4">
                        {/* Search */}
                        <div className="flex-1 max-w-md">
                            <div className="relative">
                                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
                                <input
                                    type="text"
                                    placeholder="Search findings..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 bg-white/[0.03] border border-white/[0.06] rounded-lg text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-purple-500/50"
                                />
                            </div>
                        </div>

                        {/* Severity Pills */}
                        <div className="flex items-center gap-2">
                            {Object.entries(SEVERITY_CONFIG).map(([key, config]) => (
                                <button
                                    key={key}
                                    onClick={() => setSeverityFilter(prev => 
                                        prev.includes(key) ? prev.filter(s => s !== key) : [...prev, key]
                                    )}
                                    className={`pill ${severityFilter.includes(key) ? 'active' : ''}`}
                                >
                                    <span className={`w-2 h-2 rounded-full ${config.bg} ${severityFilter.includes(key) ? '' : 'opacity-50'}`} 
                                          style={{ backgroundColor: key === 'critical' ? '#ef4444' : key === 'high' ? '#f97316' : key === 'medium' ? '#f59e0b' : key === 'low' ? '#3b82f6' : '#71717a' }} />
                                    {config.label}
                                    <span className="text-zinc-500 ml-1">({severityCounts[key] || 0})</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </header>

                {/* Table */}
                <div className="flex-1 overflow-y-auto p-6">
                    <div className="space-y-2">
                        {filteredFindings.map((finding) => {
                            const severity = SEVERITY_CONFIG[finding.severity];
                            const status = STATUS_CONFIG[finding.status];
                            const SeverityIcon = severity.icon;

                            return (
                                <motion.div
                                    key={finding.id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    onClick={() => setSelectedFinding(finding)}
                                    className={`task-row cursor-pointer ${selectedFinding?.id === finding.id ? 'border-purple-500/30 bg-purple-500/5' : ''}`}
                                >
                                    {/* Severity Icon */}
                                    <div className={`p-2 rounded-lg ${severity.bg}`}>
                                        <SeverityIcon size={16} className={severity.color} />
                                    </div>

                                    {/* Content */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <p className="text-sm font-medium text-white truncate">{finding.title}</p>
                                            {finding.cvss && (
                                                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${severity.bg} ${severity.color}`}>
                                                    CVSS {finding.cvss}
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-3 mt-1 text-xs text-zinc-500">
                                            <span className="flex items-center gap-1">
                                                <Globe size={12} />
                                                {finding.host}{finding.path}
                                            </span>
                                            <span className="flex items-center gap-1">
                                                <Terminal size={12} />
                                                {finding.tool}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Status */}
                                    <span className={`text-xs px-2 py-1 rounded-full ${status.bg} ${status.color}`}>
                                        {status.label}
                                    </span>

                                    {/* Time */}
                                    <span className="text-xs text-zinc-500 flex items-center gap-1">
                                        <Clock size={12} />
                                        {new Date(finding.timestamp).toLocaleTimeString()}
                                    </span>
                                </motion.div>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Detail Panel */}
            <AnimatePresence>
                {selectedFinding && (
                    <motion.div
                        initial={{ width: 0, opacity: 0 }}
                        animate={{ width: 420, opacity: 1 }}
                        exit={{ width: 0, opacity: 0 }}
                        className="h-full border-l border-white/[0.06] bg-[#0a0a0a] overflow-hidden"
                    >
                        <div className="h-full overflow-y-auto">
                            {/* Header */}
                            <div className="sticky top-0 bg-[#0a0a0a] border-b border-white/[0.06] p-4">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1 min-w-0 pr-4">
                                        <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium mb-2 ${SEVERITY_CONFIG[selectedFinding.severity].bg} ${SEVERITY_CONFIG[selectedFinding.severity].color}`}>
                                            {SEVERITY_CONFIG[selectedFinding.severity].label}
                                            {selectedFinding.cvss && <span>• CVSS {selectedFinding.cvss}</span>}
                                        </div>
                                        <h2 className="text-lg font-semibold text-white">{selectedFinding.title}</h2>
                                    </div>
                                    <button 
                                        onClick={() => setSelectedFinding(null)}
                                        className="p-1 hover:bg-white/[0.05] rounded"
                                    >
                                        <X size={18} className="text-zinc-500" />
                                    </button>
                                </div>
                            </div>

                            {/* Content */}
                            <div className="p-4 space-y-6">
                                {/* Meta Info */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-[10px] uppercase tracking-wider text-zinc-600 mb-1">Host</p>
                                        <p className="text-sm text-white font-mono">{selectedFinding.host}</p>
                                    </div>
                                    <div>
                                        <p className="text-[10px] uppercase tracking-wider text-zinc-600 mb-1">Path</p>
                                        <p className="text-sm text-white font-mono">{selectedFinding.path}</p>
                                    </div>
                                    <div>
                                        <p className="text-[10px] uppercase tracking-wider text-zinc-600 mb-1">Tool</p>
                                        <p className="text-sm text-white">{selectedFinding.tool}</p>
                                    </div>
                                    {selectedFinding.cwe && (
                                        <div>
                                            <p className="text-[10px] uppercase tracking-wider text-zinc-600 mb-1">CWE</p>
                                            <p className="text-sm text-cyan-400">{selectedFinding.cwe}</p>
                                        </div>
                                    )}
                                </div>

                                {/* Description */}
                                {selectedFinding.description && (
                                    <div>
                                        <p className="text-[10px] uppercase tracking-wider text-zinc-600 mb-2">Description</p>
                                        <p className="text-sm text-zinc-300 leading-relaxed">{selectedFinding.description}</p>
                                    </div>
                                )}

                                {/* Evidence */}
                                {selectedFinding.evidence && (
                                    <div>
                                        <div className="flex items-center justify-between mb-2">
                                            <p className="text-[10px] uppercase tracking-wider text-zinc-600">Evidence</p>
                                            <button 
                                                onClick={() => copyToClipboard(selectedFinding.evidence || '')}
                                                className="text-xs text-zinc-500 hover:text-white flex items-center gap-1"
                                            >
                                                {copied ? <Check size={12} /> : <Copy size={12} />}
                                                {copied ? 'Copied' : 'Copy'}
                                            </button>
                                        </div>
                                        <pre className="p-3 bg-[#0d0d0d] rounded-lg border border-white/[0.04] text-xs text-green-400 font-mono overflow-x-auto whitespace-pre-wrap">
                                            {selectedFinding.evidence}
                                        </pre>
                                    </div>
                                )}

                                {/* Remediation */}
                                {selectedFinding.remediation && (
                                    <div>
                                        <p className="text-[10px] uppercase tracking-wider text-zinc-600 mb-2">Remediation</p>
                                        <div className="p-3 bg-green-500/5 border border-green-500/20 rounded-lg">
                                            <p className="text-sm text-green-400">{selectedFinding.remediation}</p>
                                        </div>
                                    </div>
                                )}

                                {/* Actions */}
                                <div className="pt-4 border-t border-white/[0.06] space-y-2">
                                    <button className="w-full btn-gradient flex items-center justify-center gap-2">
                                        <Zap size={16} />
                                        Create Jira Ticket
                                    </button>
                                    <button className="w-full btn-ghost flex items-center justify-center gap-2 border border-white/[0.06]">
                                        <ExternalLink size={16} />
                                        View in Scanner
                                    </button>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

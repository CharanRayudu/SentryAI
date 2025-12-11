'use client';

import { useState } from 'react';
import { AlertTriangle, CheckCircle } from 'lucide-react';

type Finding = {
    id: string;
    type: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    location: string;
    status: 'open' | 'fixed';
};

const emptyFinding: Finding = {
    id: '',
    type: '',
    severity: 'medium',
    location: '',
    status: 'open'
};

export default function FindingsTable() {
    const [findings, setFindings] = useState<Finding[]>([]);
    const [draft, setDraft] = useState<Finding>(emptyFinding);
    const [showForm, setShowForm] = useState(false);

    const addFinding = () => {
        if (!draft.id.trim() || !draft.type.trim() || !draft.location.trim()) return;
        setFindings((prev) => [{ ...draft, id: draft.id.trim() }, ...prev]);
        setDraft(emptyFinding);
        setShowForm(false);
    };

    const toggleStatus = (id: string) => {
        setFindings((prev) => prev.map((finding) =>
            finding.id === id
                ? { ...finding, status: finding.status === 'open' ? 'fixed' : 'open' }
                : finding
        ));
    };

    return (
        <div className="flex-1 flex flex-col p-6 h-full overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-zinc-400">
                        Security Findings
                    </h1>
                    <p className="text-zinc-500">Track vulnerabilities discovered by your missions</p>
                </div>
                <button
                    onClick={() => setShowForm(!showForm)}
                    className="btn-gradient"
                >
                    {showForm ? 'Close form' : 'Add finding'}
                </button>
            </div>

            {showForm && (
                <div className="neo-panel rounded-xl border border-white/10 p-4 mb-4 grid grid-cols-1 md:grid-cols-4 gap-3">
                    <input
                        value={draft.id}
                        onChange={(e) => setDraft({ ...draft, id: e.target.value })}
                        placeholder="Finding ID"
                        className="px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.08] text-sm text-white"
                    />
                    <input
                        value={draft.type}
                        onChange={(e) => setDraft({ ...draft, type: e.target.value })}
                        placeholder="Vulnerability type"
                        className="px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.08] text-sm text-white"
                    />
                    <select
                        value={draft.severity}
                        onChange={(e) => setDraft({ ...draft, severity: e.target.value as Finding['severity'] })}
                        className="px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.08] text-sm text-white"
                    >
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                    </select>
                    <input
                        value={draft.location}
                        onChange={(e) => setDraft({ ...draft, location: e.target.value })}
                        placeholder="Location (e.g., /api/login)"
                        className="px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.08] text-sm text-white"
                    />
                    <div className="md:col-span-4 flex justify-end gap-2">
                        <button
                            className="btn-ghost"
                            onClick={() => { setShowForm(false); setDraft(emptyFinding); }}
                        >
                            Cancel
                        </button>
                        <button className="btn-gradient" onClick={addFinding} disabled={!draft.id || !draft.type || !draft.location}>
                            Save finding
                        </button>
                    </div>
                </div>
            )}

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
                    {findings.length === 0 ? (
                        <div className="flex h-full items-center justify-center text-center text-zinc-500 p-8">
                            <div>
                                <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
                                <p className="text-sm">No findings yet. Add one when a mission reports a vulnerability.</p>
                            </div>
                        </div>
                    ) : (
                        findings.map((finding) => (
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
                                <div className="col-span-2 text-right flex items-center justify-end gap-3">
                                    {finding.status === 'fixed' ? (
                                        <span className="inline-flex items-center gap-1.5 text-xs text-green-400">
                                            <CheckCircle size={12} /> Fixed
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center gap-1.5 text-xs text-zinc-400">
                                            <AlertTriangle size={12} /> Open
                                        </span>
                                    )}
                                    <button
                                        className="text-xs text-purple-300 hover:text-white"
                                        onClick={() => toggleStatus(finding.id)}
                                    >
                                        {finding.status === 'fixed' ? 'Reopen' : 'Resolve'}
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}

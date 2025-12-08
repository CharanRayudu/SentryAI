'use client';

import { useState } from 'react';
import { Upload, FileText, Database, Plus, X } from 'lucide-react';

export default function KnowledgeBase() {
    const [activeTab, setActiveTab] = useState<'docs' | 'specs'>('specs');

    return (
        <div className="flex flex-col h-full bg-[#050505] text-white">
            {/* Header */}
            <div className="p-6 border-b border-[#222]">
                <h1 className="text-2xl font-semibold mb-1">Knowledge & Specs</h1>
                <p className="text-sm text-gray-500">Upload OpenAPI specs, architecture diagrams, and custom tool definitions.</p>
            </div>

            {/* Upload Zone */}
            <div className="p-6">
                <div className="border border-dashed border-[#333] hover:border-purple-500/50 bg-[#0a0a0a] rounded-xl p-8 flex flex-col items-center justify-center transition-colors cursor-pointer group">
                    <div className="w-12 h-12 rounded-full bg-[#111] flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                        <Upload size={20} className="text-gray-400 group-hover:text-purple-400" />
                    </div>
                    <h3 className="text-sm font-medium mb-1">Drop specifications here</h3>
                    <p className="text-xs text-gray-500">Supports .yaml, .json, .pdf, .md</p>
                </div>
            </div>

            {/* File Lists */}
            <div className="flex-1 px-6">
                <div className="flex gap-4 border-b border-[#222] mb-4">
                    <TabButton label="API Specs" active={activeTab === 'specs'} onClick={() => setActiveTab('specs')} />
                    <TabButton label="Documents" active={activeTab === 'docs'} onClick={() => setActiveTab('docs')} />
                </div>

                <div className="space-y-2">
                    <FileItem name="billing-api-v2.yaml" type="OPENAPI" size="1.2 MB" />
                    <FileItem name="auth-flow-diagram.pdf" type="PDF" size="4.5 MB" />
                    <FileItem name="legacy-endpoints.json" type="JSON" size="12 KB" />
                </div>
            </div>
        </div>
    );
}

function TabButton({ label, active, onClick }: { label: string, active: boolean, onClick: () => void }) {
    return (
        <button
            onClick={onClick}
            className={`pb-2 text-sm font-medium transition-colors border-b-2 ${active ? 'border-purple-500 text-white' : 'border-transparent text-gray-500 hover:text-gray-300'}`}
        >
            {label}
        </button>
    );
}

function FileItem({ name, type, size }: { name: string, type: string, size: string }) {
    return (
        <div className="flex items-center justify-between p-3 rounded-lg border border-[#222] bg-[#0a0a0a] hover:bg-[#111] transition-colors group">
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-[#1a1a1a] flex items-center justify-center">
                    <FileText size={14} className="text-gray-400" />
                </div>
                <div>
                    <div className="text-sm text-gray-200">{name}</div>
                    <div className="text-[10px] text-gray-600">{size}</div>
                </div>
            </div>
            <div className="flex items-center gap-3">
                <span className="text-[10px] font-mono bg-[#1a1a1a] text-gray-500 px-2 py-1 rounded">{type}</span>
                <button className="text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity">
                    <X size={14} />
                </button>
            </div>
        </div>
    );
}

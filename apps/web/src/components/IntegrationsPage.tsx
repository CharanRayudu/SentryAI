'use client';

import { useState, type ReactNode } from 'react';
import {
    Webhook,
    Plus,
    Settings,
    Trash2,
    TestTube,
    Bell,
    ChevronRight,
    Loader2,
    CheckCircle2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

type Integration = {
    id: string;
    type: 'slack' | 'jira' | 'linear' | 'discord' | 'webhook';
    name: string;
    config: Record<string, string>;
    enabled: boolean;
    lastUsed: string | null;
    events: string[];
};

type IntegrationType = {
    id: string;
    name: string;
    description: string;
    icon: ReactNode;
    color: string;
    fields: { key: string; label: string; placeholder: string; type: 'text' | 'password' | 'url' }[];
    events: string[];
};

const INTEGRATION_TYPES: IntegrationType[] = [
    {
        id: 'slack',
        name: 'Slack',
        description: 'Post vulnerability reports and alerts to Slack channels',
        icon: <SlackIcon />,
        color: '#4A154B',
        fields: [
            { key: 'webhook_url', label: 'Webhook URL', placeholder: 'https://hooks.slack.com/services/...', type: 'url' },
            { key: 'channel', label: 'Channel (optional)', placeholder: '#security-alerts', type: 'text' }
        ],
        events: ['scan_complete', 'vulnerability_found', 'scan_failed']
    },
    {
        id: 'jira',
        name: 'Jira',
        description: 'Automatically create tickets for discovered vulnerabilities',
        icon: <JiraIcon />,
        color: '#0052CC',
        fields: [
            { key: 'base_url', label: 'Jira URL', placeholder: 'https://your-domain.atlassian.net', type: 'url' },
            { key: 'email', label: 'Email', placeholder: 'your@email.com', type: 'text' },
            { key: 'api_token', label: 'API Token', placeholder: 'Your Jira API token', type: 'password' },
            { key: 'project_key', label: 'Project Key', placeholder: 'SEC', type: 'text' }
        ],
        events: ['vulnerability_found', 'high_severity_finding']
    },
    {
        id: 'linear',
        name: 'Linear',
        description: 'Create issues in Linear for security findings',
        icon: <LinearIcon />,
        color: '#5E6AD2',
        fields: [
            { key: 'api_key', label: 'API Key', placeholder: 'lin_api_...', type: 'password' },
            { key: 'team_id', label: 'Team ID', placeholder: 'Your Linear team ID', type: 'text' }
        ],
        events: ['vulnerability_found', 'scan_complete']
    },
    {
        id: 'discord',
        name: 'Discord',
        description: 'Send alerts to Discord channels via webhooks',
        icon: <DiscordIcon />,
        color: '#5865F2',
        fields: [
            { key: 'webhook_url', label: 'Webhook URL', placeholder: 'https://discord.com/api/webhooks/...', type: 'url' }
        ],
        events: ['scan_complete', 'vulnerability_found', 'scan_failed']
    },
    {
        id: 'webhook',
        name: 'Custom Webhook',
        description: 'Send events to any HTTP endpoint',
        icon: <Webhook size={24} className="text-white" />,
        color: '#6B7280',
        fields: [
            { key: 'url', label: 'Endpoint URL', placeholder: 'https://your-api.com/webhooks/sentry', type: 'url' },
            { key: 'secret', label: 'Secret (optional)', placeholder: 'Webhook signing secret', type: 'password' }
        ],
        events: ['scan_complete', 'vulnerability_found', 'scan_failed', 'schedule_triggered']
    }
];

export default function IntegrationsPage() {
    const [integrations, setIntegrations] = useState<Integration[]>([]);
    const [showAddModal, setShowAddModal] = useState(false);
    const [selectedType, setSelectedType] = useState<IntegrationType | null>(null);
    const [testingId, setTestingId] = useState<string | null>(null);

    const toggleIntegration = (id: string) => {
        setIntegrations(prev => prev.map(i =>
            i.id === id ? { ...i, enabled: !i.enabled } : i
        ));
    };

    const deleteIntegration = (id: string) => {
        setIntegrations(prev => prev.filter(i => i.id !== id));
    };

    const testIntegration = async (id: string) => {
        setTestingId(id);
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 2000));
        setTestingId(null);
    };

    return (
        <div className="flex flex-col h-full bg-[#050505] text-white overflow-hidden">

            {/* Header */}
            <div className="p-8 border-b border-[#222]">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#06B6D4] to-[#7C3AED] flex items-center justify-center shadow-[0_0_30px_rgba(6,182,212,0.3)]">
                            <Webhook size={24} className="text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">Integrations</h1>
                            <p className="text-gray-500 text-sm mt-1">
                                Connect SentryAI to your workflow tools for automated alerts and ticket creation
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="flex items-center gap-2 px-5 py-2.5 bg-white text-black hover:bg-gray-200 rounded-lg transition-all text-sm font-bold shadow-[0_0_20px_rgba(255,255,255,0.1)]"
                    >
                        <Plus size={18} />
                        Add Integration
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-8">

                {integrations.length === 0 && (
                    <div className="mb-8 p-6 border border-[#222] rounded-xl bg-[#0b0b0b] flex items-center justify-between">
                        <div>
                            <h3 className="text-lg font-semibold text-white">No integrations connected</h3>
                            <p className="text-sm text-gray-500 mt-1">Use the catalog below to connect notifications or ticketing.</p>
                        </div>
                        <button
                            onClick={() => setShowAddModal(true)}
                            className="px-4 py-2 bg-white text-black rounded-lg font-semibold hover:bg-gray-200 transition-colors"
                        >
                            Add Integration
                        </button>
                    </div>
                )}

                {/* Active Integrations */}
                {integrations.length > 0 && (
                    <div className="mb-10">
                        <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">
                            Connected Integrations
                        </h2>
                        <div className="space-y-3">
                            {integrations.map((integration, idx) => {
                                const typeInfo = INTEGRATION_TYPES.find(t => t.id === integration.type)!;
                                return (
                                    <motion.div
                                        key={integration.id}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: idx * 0.05 }}
                                        className={`
                                            bg-[#0a0a0a] border rounded-xl p-5 transition-all
                                            ${integration.enabled ? 'border-[#222] hover:border-[#333]' : 'border-[#1a1a1a] opacity-60'}
                                        `}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                {/* Icon */}
                                                <div
                                                    className="w-12 h-12 rounded-xl flex items-center justify-center"
                                                    style={{ backgroundColor: typeInfo.color }}
                                                >
                                                    {typeInfo.icon}
                                                </div>

                                                {/* Info */}
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <h3 className="font-semibold text-white">{integration.name}</h3>
                                                        <span className="text-xs text-gray-600 font-mono bg-[#111] px-2 py-0.5 rounded">
                                                            {typeInfo.name}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                                                        <span className="flex items-center gap-1">
                                                            <Bell size={10} />
                                                            {integration.events.length} events
                                                        </span>
                                                        {integration.lastUsed && (
                                                            <span>
                                                                Last used: {new Date(integration.lastUsed).toLocaleDateString()}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Actions */}
                                            <div className="flex items-center gap-3">
                                                {/* Test Button */}
                                                <button
                                                    onClick={() => testIntegration(integration.id)}
                                                    disabled={testingId === integration.id}
                                                    className="flex items-center gap-1.5 px-3 py-1.5 bg-[#111] hover:bg-[#1a1a1a] border border-[#333] rounded-lg text-xs font-medium text-gray-300 transition-colors disabled:opacity-50"
                                                >
                                                    {testingId === integration.id ? (
                                                        <Loader2 size={12} className="animate-spin" />
                                                    ) : (
                                                        <TestTube size={12} />
                                                    )}
                                                    Test
                                                </button>

                                                {/* Toggle */}
                                                <button
                                                    onClick={() => toggleIntegration(integration.id)}
                                                    className={`w-10 h-6 rounded-full relative transition-colors ${integration.enabled ? 'bg-[#10B981]' : 'bg-[#333]'}`}
                                                >
                                                    <motion.div
                                                        className="absolute top-1 w-4 h-4 bg-white rounded-full shadow"
                                                        animate={{ left: integration.enabled ? '22px' : '4px' }}
                                                        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                                                    />
                                                </button>

                                                {/* Settings */}
                                                <button className="p-2 hover:bg-[#1a1a1a] rounded-lg text-gray-500 hover:text-white transition-colors">
                                                    <Settings size={16} />
                                                </button>

                                                {/* Delete */}
                                                <button
                                                    onClick={() => deleteIntegration(integration.id)}
                                                    className="p-2 hover:bg-red-500/10 rounded-lg text-gray-500 hover:text-red-400 transition-colors"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </div>
                                    </motion.div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Available Integrations */}
                <div>
                    <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">
                        Available Integrations
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {INTEGRATION_TYPES.map((type) => (
                            <button
                                key={type.id}
                                onClick={() => {
                                    setSelectedType(type);
                                    setShowAddModal(true);
                                }}
                                className="group text-left bg-[#0a0a0a] border border-[#222] rounded-xl p-5 hover:border-[#333] hover:bg-[#0f0f0f] transition-all"
                            >
                                <div className="flex items-start justify-between mb-3">
                                    <div
                                        className="w-12 h-12 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110"
                                        style={{ backgroundColor: type.color }}
                                    >
                                        {type.icon}
                                    </div>
                                    <ChevronRight size={16} className="text-gray-600 group-hover:text-white group-hover:translate-x-1 transition-all" />
                                </div>
                                <h3 className="font-semibold text-white mb-1">{type.name}</h3>
                                <p className="text-sm text-gray-500 line-clamp-2">{type.description}</p>
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Add Integration Modal */}
            <AnimatePresence>
                {showAddModal && (
                    <AddIntegrationModal
                        type={selectedType}
                        onClose={() => {
                            setShowAddModal(false);
                            setSelectedType(null);
                        }}
                        onAdd={(integration) => {
                            setIntegrations(prev => [integration, ...prev]);
                            setShowAddModal(false);
                            setSelectedType(null);
                        }}
                    />
                )}
            </AnimatePresence>
        </div>
    );
}

function AddIntegrationModal({
    type,
    onClose,
    onAdd
}: {
    type: IntegrationType | null;
    onClose: () => void;
    onAdd: (integration: Integration) => void;
}) {
    const [selectedType, setSelectedType] = useState<IntegrationType | null>(type);
    const [name, setName] = useState('');
    const [config, setConfig] = useState<Record<string, string>>({});
    const [selectedEvents, setSelectedEvents] = useState<string[]>([]);

    const handleAdd = () => {
        if (!selectedType || !name) return;

        const integration: Integration = {
            id: Date.now().toString(),
            type: selectedType.id as Integration['type'],
            name,
            config,
            enabled: true,
            lastUsed: null,
            events: selectedEvents
        };

        onAdd(integration);
    };

    const toggleEvent = (event: string) => {
        setSelectedEvents(prev =>
            prev.includes(event)
                ? prev.filter(e => e !== event)
                : [...prev, event]
        );
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
            <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />

            <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="relative w-full max-w-lg bg-[#0a0a0a] border border-[#222] rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col"
            >
                {/* Header */}
                <div className="px-6 py-5 border-b border-[#222] bg-[#080808]">
                    <h2 className="text-xl font-bold text-white">
                        {selectedType ? `Connect ${selectedType.name}` : 'Add Integration'}
                    </h2>
                    <p className="text-sm text-gray-500 mt-1">
                        {selectedType?.description || 'Choose an integration to connect'}
                    </p>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-5">
                    {/* Type Selection (if no type selected) */}
                    {!selectedType && (
                        <div className="grid grid-cols-2 gap-3">
                            {INTEGRATION_TYPES.map((t) => (
                                <button
                                    key={t.id}
                                    onClick={() => setSelectedType(t)}
                                    className="flex items-center gap-3 p-3 bg-[#111] border border-[#222] rounded-lg hover:border-[#333] transition-colors text-left"
                                >
                                    <div
                                        className="w-10 h-10 rounded-lg flex items-center justify-center"
                                        style={{ backgroundColor: t.color }}
                                    >
                                        {t.icon}
                                    </div>
                                    <span className="font-medium text-white">{t.name}</span>
                                </button>
                            ))}
                        </div>
                    )}

                    {/* Configuration Form */}
                    {selectedType && (
                        <>
                            {/* Name */}
                            <div>
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
                                    Integration Name
                                </label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder={`e.g., ${selectedType.name} - Security Team`}
                                    className="w-full bg-[#111] border border-[#333] rounded-lg px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-[#7C3AED] transition-colors"
                                />
                            </div>

                            {/* Dynamic Fields */}
                            {selectedType.fields.map((field) => (
                                <div key={field.key}>
                                    <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
                                        {field.label}
                                    </label>
                                    <input
                                        type={field.type === 'password' ? 'password' : 'text'}
                                        value={config[field.key] || ''}
                                        onChange={(e) => setConfig(prev => ({ ...prev, [field.key]: e.target.value }))}
                                        placeholder={field.placeholder}
                                        className="w-full bg-[#111] border border-[#333] rounded-lg px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-[#7C3AED] transition-colors font-mono text-sm"
                                    />
                                </div>
                            ))}

                            {/* Event Selection */}
                            <div>
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
                                    Trigger Events
                                </label>
                                <div className="space-y-2">
                                    {selectedType.events.map((event) => (
                                        <button
                                            key={event}
                                            onClick={() => toggleEvent(event)}
                                            className={`w-full flex items-center justify-between p-3 rounded-lg border transition-all ${selectedEvents.includes(event)
                                                    ? 'bg-[#7C3AED]/10 border-[#7C3AED]/30 text-white'
                                                    : 'bg-[#111] border-[#222] text-gray-400 hover:border-[#333]'
                                                }`}
                                        >
                                            <span className="text-sm font-medium">
                                                {event.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                                            </span>
                                            {selectedEvents.includes(event) && (
                                                <CheckCircle2 size={16} className="text-[#7C3AED]" />
                                            )}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-[#222] bg-[#080808] flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-gray-400 hover:text-white transition-colors text-sm font-medium"
                    >
                        Cancel
                    </button>
                    {selectedType && (
                        <button
                            onClick={handleAdd}
                            disabled={!name || selectedEvents.length === 0}
                            className="px-5 py-2 bg-[#7C3AED] hover:bg-[#6D28D9] disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white text-sm font-bold transition-colors"
                        >
                            Connect
                        </button>
                    )}
                </div>
            </motion.div>
        </motion.div>
    );
}

// --- Brand Icons ---
function SlackIcon() {
    return (
        <svg viewBox="0 0 24 24" className="w-6 h-6" fill="white">
            <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zm1.271 0a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zm0 1.271a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zm10.124 2.521a2.528 2.528 0 0 1 2.52-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.52V8.834zm-1.271 0a2.528 2.528 0 0 1-2.521 2.521 2.528 2.528 0 0 1-2.521-2.521V2.522A2.528 2.528 0 0 1 15.166 0a2.528 2.528 0 0 1 2.521 2.522v6.312zm-2.521 10.124a2.528 2.528 0 0 1 2.521 2.52A2.528 2.528 0 0 1 15.166 24a2.528 2.528 0 0 1-2.521-2.522v-2.52h2.521zm0-1.271a2.528 2.528 0 0 1-2.521-2.521 2.528 2.528 0 0 1 2.521-2.521h6.312A2.528 2.528 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.521h-6.312z" />
        </svg>
    );
}

function JiraIcon() {
    return (
        <svg viewBox="0 0 24 24" className="w-6 h-6" fill="white">
            <path d="M11.571 11.513H0a5.218 5.218 0 0 0 5.232 5.215h2.13v2.057A5.215 5.215 0 0 0 12.575 24V12.518a1.005 1.005 0 0 0-1.005-1.005zm5.723-5.756H5.736a5.215 5.215 0 0 0 5.215 5.214h2.129v2.058a5.218 5.218 0 0 0 5.215 5.214V6.758a1.001 1.001 0 0 0-1.001-1.001zM23.013 0H11.455a5.215 5.215 0 0 0 5.215 5.215h2.129v2.057A5.215 5.215 0 0 0 24 12.483V1.005A1.005 1.005 0 0 0 23.013 0z" />
        </svg>
    );
}

function LinearIcon() {
    return (
        <svg viewBox="0 0 24 24" className="w-6 h-6" fill="white">
            <path d="M2.088 10.282c-.166.205-.317.43-.455.664L12.38 21.693c.234-.138.459-.29.664-.455L2.088 10.282zm-.81 2.015a9.99 9.99 0 0 0-.242.906l9.761 9.761c.314-.066.62-.147.906-.242L1.278 12.297zm11.045 10.548a10.037 10.037 0 0 0 5.054-2.009L4.164 7.623a10.037 10.037 0 0 0-2.009 5.054l10.178 10.168zM22.68 14.093a10.014 10.014 0 0 0 .284-2.093c0-5.523-4.477-10-10-10-5.523 0-10 4.477-10 10 0 .714.075 1.411.218 2.083l19.498-.01v.02z" />
        </svg>
    );
}

function DiscordIcon() {
    return (
        <svg viewBox="0 0 24 24" className="w-6 h-6" fill="white">
            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
        </svg>
    );
}


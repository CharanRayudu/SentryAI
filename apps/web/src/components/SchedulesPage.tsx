'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Calendar,
    Clock,
    Plus,
    Play,
    Trash2,
    Edit2,
    Check,
    X,
    AlertCircle,
    RefreshCw
} from 'lucide-react';

interface Schedule {
    id: string;
    name: string;
    target: string;
    cron: string;
    cronReadable: string;
    enabled: boolean;
    lastRun: string | null;
    nextRun: string;
    status: 'idle' | 'running' | 'success' | 'failed';
    autoPilot: boolean;
}

const CRON_PRESETS = [
    { label: 'Hourly', cron: '0 * * * *', readable: 'Every hour' },
    { label: 'Daily', cron: '0 9 * * *', readable: 'Every day at 9:00 AM' },
    { label: 'Weekly', cron: '0 9 * * 1', readable: 'Every Monday at 9:00 AM' },
    { label: 'Monthly', cron: '0 0 1 * *', readable: 'First day of every month' },
];

export default function SchedulesPage() {
    const [schedules, setSchedules] = useState<Schedule[]>([]);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const blankSchedule = {
        name: '',
        target: '',
        cron: '0 9 * * 1',
        cronReadable: 'Every Monday at 9:00 AM',
        autoPilot: false
    };
    const [newSchedule, setNewSchedule] = useState({ ...blankSchedule });
    const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null);

    const toggleSchedule = (id: string) => {
        setSchedules(prev => prev.map(s => 
            s.id === id ? { ...s, enabled: !s.enabled } : s
        ));
    };

    const deleteSchedule = (id: string) => {
        setSchedules(prev => prev.filter(s => s.id !== id));
        if (editingSchedule?.id === id) {
            setEditingSchedule(null);
        }
    };

    const createSchedule = () => {
        if (editingSchedule) {
            setSchedules(prev => prev.map((schedule) =>
                schedule.id === editingSchedule.id
                    ? {
                        ...schedule,
                        name: newSchedule.name,
                        target: newSchedule.target,
                        cron: newSchedule.cron,
                        cronReadable: newSchedule.cronReadable,
                        autoPilot: newSchedule.autoPilot
                    }
                    : schedule
            ));
        } else {
            const schedule: Schedule = {
                id: Date.now().toString(),
                name: newSchedule.name,
                target: newSchedule.target,
                cron: newSchedule.cron,
                cronReadable: newSchedule.cronReadable,
                enabled: true,
                lastRun: null,
                nextRun: new Date(Date.now() + 86400000).toISOString(),
                status: 'idle',
                autoPilot: newSchedule.autoPilot
            };
            setSchedules(prev => [...prev, schedule]);
        }

        setShowCreateModal(false);
        setEditingSchedule(null);
        setNewSchedule({ ...blankSchedule });
    };

    const runSchedule = (id: string) => {
        setSchedules(prev => prev.map((schedule) =>
            schedule.id === id
                ? {
                    ...schedule,
                    enabled: true,
                    status: 'running',
                    lastRun: new Date().toISOString(),
                    nextRun: new Date(Date.now() + 3600000).toISOString()
                }
                : schedule
        ));

        setTimeout(() => {
            setSchedules(prev => prev.map((schedule) =>
                schedule.id === id
                    ? { ...schedule, status: 'success' }
                    : schedule
            ));
        }, 1500);
    };

    const openForEdit = (schedule: Schedule) => {
        setEditingSchedule(schedule);
        setShowCreateModal(true);
        setNewSchedule({
            name: schedule.name,
            target: schedule.target,
            cron: schedule.cron,
            cronReadable: schedule.cronReadable,
            autoPilot: schedule.autoPilot
        });
    };

    const openCreateModal = () => {
        setEditingSchedule(null);
        setNewSchedule({ ...blankSchedule });
        setShowCreateModal(true);
    };

    const closeModal = () => {
        setShowCreateModal(false);
        setEditingSchedule(null);
        setNewSchedule({ ...blankSchedule });
    };

    const getStatusConfig = (status: Schedule['status']) => {
        switch (status) {
            case 'running':
                return { icon: RefreshCw, color: 'text-purple-400', bg: 'bg-purple-500/10', label: 'Running', animate: true };
            case 'success':
                return { icon: Check, color: 'text-green-400', bg: 'bg-green-500/10', label: 'Success', animate: false };
            case 'failed':
                return { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-500/10', label: 'Failed', animate: false };
            default:
                return { icon: Clock, color: 'text-zinc-400', bg: 'bg-zinc-500/10', label: 'Idle', animate: false };
        }
    };

    return (
        <div className="flex-1 flex flex-col h-screen overflow-hidden">
            {/* Header */}
            <header className="px-8 py-4 border-b border-white/[0.06]">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-semibold text-white">Scheduled Jobs</h1>
                        <p className="text-sm text-zinc-500">Automate recurring security scans</p>
                    </div>
                    <button
                        onClick={openCreateModal}
                        className="btn-gradient flex items-center gap-2"
                    >
                        <Plus size={16} />
                        New Schedule
                    </button>
                </div>
            </header>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-4xl mx-auto space-y-3">
                    {schedules.map((schedule) => {
                        const statusConfig = getStatusConfig(schedule.status);
                        const StatusIcon = statusConfig.icon;

                        return (
                            <motion.div
                                key={schedule.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`task-row ${!schedule.enabled ? 'opacity-50' : ''}`}
                            >
                                {/* Toggle */}
                                <button
                                    onClick={() => toggleSchedule(schedule.id)}
                                    className={`relative w-10 h-6 rounded-full transition-colors ${
                                        schedule.enabled ? 'bg-purple-500' : 'bg-zinc-700'
                                    }`}
                                >
                                    <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
                                        schedule.enabled ? 'left-5' : 'left-1'
                                    }`} />
                                </button>

                                {/* Content */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <p className="text-sm font-medium text-white">{schedule.name}</p>
                                        {schedule.autoPilot && (
                                            <span className="text-[10px] px-1.5 py-0.5 bg-cyan-500/10 text-cyan-400 rounded-full border border-cyan-500/20">
                                                Auto-Pilot
                                            </span>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-4 mt-1 text-xs text-zinc-500">
                                        <span className="font-mono">{schedule.target}</span>
                                        <span className="flex items-center gap-1">
                                            <Calendar size={12} />
                                            {schedule.cronReadable}
                                        </span>
                                    </div>
                                </div>

                                {/* Status */}
                                <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${statusConfig.bg} ${statusConfig.color}`}>
                                    <StatusIcon size={12} className={statusConfig.animate ? 'animate-spin' : ''} />
                                    {statusConfig.label}
                                </div>

                                {/* Next Run */}
                                <div className="text-right">
                                    <p className="text-[10px] text-zinc-600 uppercase">Next Run</p>
                                    <p className="text-xs text-zinc-400">
                                        {new Date(schedule.nextRun).toLocaleDateString()}
                                    </p>
                                </div>

                                {/* Actions */}
                                <div className="flex items-center gap-1">
                                    <button
                                        onClick={() => runSchedule(schedule.id)}
                                        className="p-2 hover:bg-white/[0.05] rounded-lg text-zinc-500 hover:text-white transition-colors"
                                    >
                                        <Play size={14} />
                                    </button>
                                    <button
                                        onClick={() => openForEdit(schedule)}
                                        className="p-2 hover:bg-white/[0.05] rounded-lg text-zinc-500 hover:text-white transition-colors"
                                    >
                                        <Edit2 size={14} />
                                    </button>
                                    <button
                                        onClick={() => deleteSchedule(schedule.id)}
                                        className="p-2 hover:bg-red-500/10 rounded-lg text-zinc-500 hover:text-red-400 transition-colors"
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            </motion.div>
                        );
                    })}

                    {schedules.length === 0 && (
                        <div className="text-center py-16">
                            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-zinc-900 border border-zinc-800 mb-4">
                                <Calendar className="w-8 h-8 text-zinc-600" />
                            </div>
                            <h3 className="text-lg font-medium text-white mb-2">No scheduled jobs</h3>
                            <p className="text-sm text-zinc-500 mb-4">Create a schedule to automate security scans</p>
                            <button
                                onClick={openCreateModal}
                                className="btn-gradient"
                            >
                                Create Schedule
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Create Modal */}
            <AnimatePresence>
                {showCreateModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
                        onClick={closeModal}
                    >
                        <motion.div
                            initial={{ scale: 0.95, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.95, opacity: 0 }}
                            onClick={(e) => e.stopPropagation()}
                            className="w-full max-w-lg bg-[#0a0a0a] border border-white/[0.1] rounded-xl shadow-2xl"
                        >
                            {/* Modal Header */}
                            <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06]">
                                <h2 className="text-lg font-semibold text-white">{editingSchedule ? 'Update Schedule' : 'Create Schedule'}</h2>
                                <button
                                    onClick={closeModal}
                                    className="p-1 hover:bg-white/[0.05] rounded"
                                >
                                    <X size={18} className="text-zinc-500" />
                                </button>
                            </div>

                            {/* Modal Body */}
                            <div className="p-6 space-y-4">
                                {/* Name */}
                                <div>
                                    <label className="block text-xs text-zinc-500 uppercase tracking-wider mb-2">Name</label>
                                    <input
                                        type="text"
                                        value={newSchedule.name}
                                        onChange={(e) => setNewSchedule(prev => ({ ...prev, name: e.target.value }))}
                                        placeholder="Weekly Vulnerability Scan"
                                        className="w-full px-4 py-2.5 bg-white/[0.03] border border-white/[0.06] rounded-lg text-white placeholder-zinc-600 focus:outline-none focus:border-purple-500/50"
                                    />
                                </div>

                                {/* Target */}
                                <div>
                                    <label className="block text-xs text-zinc-500 uppercase tracking-wider mb-2">Target</label>
                                    <input
                                        type="text"
                                        value={newSchedule.target}
                                        onChange={(e) => setNewSchedule(prev => ({ ...prev, target: e.target.value }))}
                                        placeholder="example.com or *.example.com"
                                        className="w-full px-4 py-2.5 bg-white/[0.03] border border-white/[0.06] rounded-lg text-white placeholder-zinc-600 focus:outline-none focus:border-purple-500/50 font-mono"
                                    />
                                </div>

                                {/* Schedule Presets */}
                                <div>
                                    <label className="block text-xs text-zinc-500 uppercase tracking-wider mb-2">Schedule</label>
                                    <div className="grid grid-cols-4 gap-2">
                                        {CRON_PRESETS.map((preset) => (
                                            <button
                                                key={preset.cron}
                                                onClick={() => setNewSchedule(prev => ({ 
                                                    ...prev, 
                                                    cron: preset.cron, 
                                                    cronReadable: preset.readable 
                                                }))}
                                                className={`pill ${newSchedule.cron === preset.cron ? 'active' : ''}`}
                                            >
                                                {preset.label}
                                            </button>
                                        ))}
                                    </div>
                                    <p className="text-xs text-zinc-500 mt-2">{newSchedule.cronReadable}</p>
                                </div>

                                {/* Auto-Pilot Toggle */}
                                <div className="flex items-center justify-between p-4 bg-white/[0.02] rounded-lg">
                                    <div>
                                        <p className="text-sm font-medium text-white">Auto-Pilot Mode</p>
                                        <p className="text-xs text-zinc-500">Execute without manual approval</p>
                                    </div>
                                    <button
                                        onClick={() => setNewSchedule(prev => ({ ...prev, autoPilot: !prev.autoPilot }))}
                                        className={`relative w-10 h-6 rounded-full transition-colors ${
                                            newSchedule.autoPilot ? 'bg-purple-500' : 'bg-zinc-700'
                                        }`}
                                    >
                                        <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
                                            newSchedule.autoPilot ? 'left-5' : 'left-1'
                                        }`} />
                                    </button>
                                </div>
                            </div>

                            {/* Modal Footer */}
                            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/[0.06]">
                                <button
                                    onClick={closeModal}
                                    className="btn-ghost"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={createSchedule}
                                    disabled={!newSchedule.name || !newSchedule.target}
                                    className="btn-gradient disabled:opacity-50"
                                >
                                    {editingSchedule ? 'Update Schedule' : 'Create Schedule'}
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

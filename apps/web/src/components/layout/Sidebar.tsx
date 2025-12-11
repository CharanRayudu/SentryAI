'use client';

import { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Plus,
    Bot,
    FolderOpen,
    BookOpen,
    Terminal,
    Settings,
    ChevronDown,
    Search,
    Shield,
    Activity,
    Calendar,
    Link2,
    User,
    LogOut,
    Sparkles
} from 'lucide-react';

interface Project {
    id: string;
    name: string;
    status: 'active' | 'completed' | 'pending';
    lastActive: string;
}

interface NavItem {
    icon: React.ElementType;
    label: string;
    id: string;
    badge?: number;
}

const NAV_ITEMS: NavItem[] = [
    { icon: Plus, label: 'New Task', id: 'new' },
    { icon: Bot, label: 'Agents', id: 'agents' },
    { icon: FolderOpen, label: 'Files', id: 'files' },
    { icon: BookOpen, label: 'Knowledge', id: 'knowledge' },
    { icon: Terminal, label: 'Console', id: 'console' },
];

const SECONDARY_NAV: NavItem[] = [
    { icon: Shield, label: 'Findings', id: 'findings' },
    { icon: Activity, label: 'Operations', id: 'operations' },
    { icon: Calendar, label: 'Schedules', id: 'schedules' },
    { icon: Link2, label: 'Integrations', id: 'integrations' },
];

interface SidebarProps {
    activeView: string;
    onViewChange: (view: string) => void;
}

export default function Sidebar({ activeView, onViewChange }: SidebarProps) {
    const [projectsExpanded, setProjectsExpanded] = useState(true);
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [projects, setProjects] = useState<Project[]>([]);
    const [newProjectName, setNewProjectName] = useState('');
    const [newProjectStatus, setNewProjectStatus] = useState<Project['status']>('active');
    const [showProjectForm, setShowProjectForm] = useState(false);

    const canCreateProject = useMemo(() => newProjectName.trim().length > 1, [newProjectName]);

    const handleCreateProject = () => {
        if (!canCreateProject) return;

        const now = new Date();
        const project: Project = {
            id: crypto.randomUUID(),
            name: newProjectName.trim(),
            status: newProjectStatus,
            lastActive: now.toLocaleString()
        };

        setProjects((prev) => [project, ...prev]);
        setNewProjectName('');
        setNewProjectStatus('active');
        setShowProjectForm(false);
    };

    return (
        <aside className="w-[260px] h-screen flex flex-col bg-surface-900 border-r border-border-subtle">
            {/* Logo */}
            <div className="p-4 border-b border-white/[0.06]">
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-white" />
                        </div>
                        <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-[#0a0a0a]" />
                    </div>
                    <div>
                        <h1 className="text-sm font-semibold text-white">SentryAI</h1>
                        <p className="text-[11px] text-zinc-500">v2.0 • Online</p>
                    </div>
                </div>
            </div>

            {/* Search */}
            <div className="p-3">
                <div className="flex items-center gap-2 px-3 py-2 bg-white/[0.03] rounded-lg border border-white/[0.06] text-zinc-500 text-sm">
                    <Search size={14} />
                    <span>Search...</span>
                    <kbd className="ml-auto text-[10px] px-1.5 py-0.5 bg-white/[0.05] rounded border border-white/[0.1]">⌘K</kbd>
                </div>
            </div>

            {/* Primary Nav */}
            <nav className="px-3 space-y-1">
                {NAV_ITEMS.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onViewChange(item.id)}
                        className={`nav-item w-full ${activeView === item.id ? 'active' : ''}`}
                    >
                        <item.icon size={18} />
                        <span className="flex-1 text-left">{item.label}</span>
                        {item.badge && (
                            <span className="text-[10px] px-1.5 py-0.5 bg-purple-500/20 text-purple-400 rounded-full">
                                {item.badge}
                            </span>
                        )}
                    </button>
                ))}
            </nav>

            {/* Divider */}
            <div className="my-3 mx-3 border-t border-white/[0.06]" />

            {/* Secondary Nav */}
            <nav className="px-3 space-y-1">
                <p className="px-3 py-1.5 text-[10px] uppercase tracking-wider text-zinc-600 font-semibold">
                    Operations
                </p>
                {SECONDARY_NAV.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onViewChange(item.id)}
                        className={`nav-item w-full ${activeView === item.id ? 'active' : ''}`}
                    >
                        <item.icon size={18} />
                        <span className="flex-1 text-left">{item.label}</span>
                        {item.badge && (
                            <span className="text-[10px] px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded-full">
                                {item.badge}
                            </span>
                        )}
                    </button>
                ))}
            </nav>

            {/* Divider */}
            <div className="my-3 mx-3 border-t border-white/[0.06]" />

            {/* Projects */}
            <div className="flex-1 overflow-hidden flex flex-col">
                <div
                    className="flex items-center justify-between px-4 py-2 text-sm hover:bg-white/[0.02] transition-colors cursor-pointer"
                >
                    <span
                        onClick={() => setProjectsExpanded(!projectsExpanded)}
                        className="text-[10px] uppercase tracking-wider text-zinc-600 font-semibold cursor-pointer flex-1"
                    >
                        Projects
                    </span>
                    <div className="flex items-center gap-1">
                        <button
                            className="p-1 hover:bg-white/[0.05] rounded"
                            onClick={(e) => {
                                e.stopPropagation();
                                setShowProjectForm((prev) => !prev);
                                setProjectsExpanded(true);
                            }}
                            aria-label="Add project"
                        >
                            <Plus size={14} className="text-zinc-500" />
                        </button>
                        <span
                            onClick={() => setProjectsExpanded(!projectsExpanded)}
                            className="cursor-pointer"
                        >
                            <ChevronDown
                                size={14}
                                className={`text-zinc-500 transition-transform ${projectsExpanded ? '' : '-rotate-90'}`}
                            />
                        </span>
                    </div>
                </div>

                <AnimatePresence>
                    {projectsExpanded && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-y-auto px-2 space-y-0.5"
                        >
                            {showProjectForm && (
                                <div className="p-3 mb-1 rounded-lg border border-white/[0.08] bg-white/[0.02] space-y-2">
                                    <input
                                        value={newProjectName}
                                        onChange={(e) => setNewProjectName(e.target.value)}
                                        placeholder="Project name"
                                        className="w-full px-3 py-2 rounded-md bg-[#0b0b0b] border border-white/10 text-sm text-white focus:outline-none focus:border-purple-500/50"
                                    />
                                    <div className="flex items-center gap-2">
                                        <select
                                            value={newProjectStatus}
                                            onChange={(e) => setNewProjectStatus(e.target.value as Project['status'])}
                                            className="flex-1 px-3 py-2 rounded-md bg-[#0b0b0b] border border-white/10 text-sm text-white focus:outline-none focus:border-purple-500/50"
                                        >
                                            <option value="active">Active</option>
                                            <option value="pending">Pending</option>
                                            <option value="completed">Completed</option>
                                        </select>
                                        <button
                                            onClick={handleCreateProject}
                                            disabled={!canCreateProject}
                                            className="px-3 py-2 rounded-md bg-purple-600 text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            Save
                                        </button>
                                    </div>
                                </div>
                            )}

                            {projects.length === 0 && !showProjectForm && (
                                <div className="px-3 py-4 text-sm text-zinc-600 border border-dashed border-white/10 rounded-lg text-center">
                                    No projects yet. Click the plus icon to add one.
                                </div>
                            )}

                            {projects.map((project) => (
                                <button
                                    key={project.id}
                                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/[0.03] transition-colors group"
                                >
                                    <div className={`w-2 h-2 rounded-full ${project.status === 'active' ? 'bg-green-500' :
                                            project.status === 'pending' ? 'bg-amber-500' : 'bg-zinc-600'
                                        }`} />
                                    <span className="flex-1 text-left text-sm text-zinc-400 group-hover:text-zinc-200 truncate">
                                        {project.name}
                                    </span>
                                    <span className="text-[10px] text-zinc-600 opacity-0 group-hover:opacity-100 transition-opacity">
                                        {project.lastActive}
                                    </span>
                                </button>
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* User Profile */}
            <div className="p-3 border-t border-white/[0.06]">
                <div className="relative">
                    <button
                        onClick={() => setUserMenuOpen(!userMenuOpen)}
                        className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-white/[0.03] transition-colors"
                    >
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center text-white text-sm font-medium">
                            S
                        </div>
                        <div className="flex-1 text-left">
                            <p className="text-sm text-zinc-200">Security Team</p>
                            <p className="text-[11px] text-zinc-500">Pro Plan</p>
                        </div>
                        <ChevronDown size={14} className="text-zinc-500" />
                    </button>

                    <AnimatePresence>
                        {userMenuOpen && (
                            <motion.div
                                initial={{ opacity: 0, y: 4 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: 4 }}
                                className="absolute bottom-full left-0 right-0 mb-2 p-1 bg-[#121212] border border-white/[0.1] rounded-lg shadow-xl"
                            >
                                <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-zinc-400 hover:text-white hover:bg-white/[0.05] rounded-md transition-colors">
                                    <User size={14} />
                                    Profile
                                </button>
                                <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-zinc-400 hover:text-white hover:bg-white/[0.05] rounded-md transition-colors">
                                    <Settings size={14} />
                                    Settings
                                </button>
                                <div className="my-1 border-t border-white/[0.06]" />
                                <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-md transition-colors">
                                    <LogOut size={14} />
                                    Sign Out
                                </button>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </aside>
    );
}







import {
    Folder,
    Database,
    Terminal,
    Wrench,
    Box,
    Layers,
    Settings,
    Plus,
    Cpu
} from 'lucide-react';

interface SidebarProps {
    onViewChange: (view: 'dashboard' | 'active_scan' | 'knowledge' | 'tools' | 'agents') => void;
    currentView: string;
}

export default function Sidebar({ onViewChange, currentView }: SidebarProps) {
    return (
        <div className="w-64 h-screen bg-[#0a0a0a] border-r border-[#222] flex flex-col text-sm">
            {/* Brand */}
            <div
                className="p-4 flex items-center gap-2 mb-4 cursor-pointer"
                onClick={() => onViewChange('dashboard')}
            >
                <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-purple-500 to-blue-500 shadow-[0_0_10px_rgba(168,85,247,0.5)]"></div>
                <span className="font-semibold tracking-wide text-white">sentry</span>
            </div>

            {/* Main Nav */}
            <div className="flex-1 px-2 space-y-1">
                <NavItem
                    icon={<Plus size={16} />}
                    label="New Task"
                    shortcut="⌘J"
                    onClick={() => onViewChange('dashboard')}
                />

                <div className="pt-4 pb-2 px-2 text-xs font-medium text-gray-500 uppercase tracking-wider">Workspace</div>

                <NavItem
                    icon={<Cpu size={16} />}
                    label="Agents"
                    active={currentView === 'agents'}
                    onClick={() => onViewChange('agents')}
                />
                <NavItem
                    icon={<Folder size={16} />}
                    label="Files"
                />
                <NavItem
                    icon={<Database size={16} />}
                    label="Knowledge"
                    active={currentView === 'knowledge'}
                    onClick={() => onViewChange('knowledge')}
                />
                <NavItem
                    icon={<Wrench size={16} />}
                    label="Tools"
                    active={currentView === 'tools'}
                    onClick={() => onViewChange('tools')}
                />
                <NavItem
                    icon={<Terminal size={16} />}
                    label="Terminal"
                />

                <div className="pt-6 pb-2 px-2 text-xs font-medium text-gray-500 uppercase tracking-wider">Projects</div>
                <NavItem icon={<Box size={16} />} label="Auth Protocol Audit" />
                <NavItem icon={<Layers size={16} />} label="SOC 2 Sprint" />
                <NavItem icon={<Box size={16} />} label="Matrix API Check" />
            </div>

            {/* User */}
            <div className="p-4 border-t border-[#222]">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-gray-800 border border-gray-700"></div>
                    <div className="flex flex-col">
                        <span className="text-xs font-medium text-white">Admin User</span>
                        <span className="text-[10px] text-gray-500">Pro Plan</span>
                    </div>
                    <Settings size={14} className="ml-auto text-gray-500" />
                </div>
            </div>
        </div>
    );
}

interface NavItemProps {
    icon: any;
    label: string;
    active?: boolean;
    shortcut?: string;
    onClick?: () => void;
}

function NavItem({ icon, label, active, shortcut, onClick }: NavItemProps) {
    return (
        <div
            onClick={onClick}
            className={`
      flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer group transition-all
      ${active ? 'bg-white/5 text-white' : 'text-gray-400 hover:text-white hover:bg-white/5'}
    `}>
            <span className={active ? 'text-purple-400' : 'group-hover:text-gray-300'}>{icon}</span>
            <span className="flex-1">{label}</span>
            {shortcut && <span className="text-[10px] bg-[#222] px-1.5 py-0.5 rounded text-gray-500 border border-[#333]">{shortcut}</span>}
        </div>
    );
}

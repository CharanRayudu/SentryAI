import React from "react";

interface AppLayoutProps {
    sidebar: React.ReactNode;
    children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ sidebar, children }) => {
    return (
        <div className="flex h-screen w-full overflow-hidden bg-surface-950 text-white selection:bg-terminal-green/30 selection:text-white">
            {/* Sidebar Area */}
            <aside className="w-[260px] flex-shrink-0 border-r border-border-subtle bg-surface-900 flex flex-col z-20">
                {sidebar}
            </aside>

            {/* Main Stage */}
            <main className="flex-grow relative flex flex-col h-full overflow-hidden">
                {/* Decorative Grid Background */}
                <div className="absolute inset-0 pointer-events-none opacity-20"
                    style={{
                        backgroundImage: "linear-gradient(var(--border-subtle) 1px, transparent 1px), linear-gradient(90deg, var(--border-subtle) 1px, transparent 1px)",
                        backgroundSize: "40px 40px"
                    }}
                />

                {/* Content Layer */}
                <div className="relative z-10 w-full h-full flex flex-col">
                    {children}
                </div>
            </main>
        </div>
    );
};

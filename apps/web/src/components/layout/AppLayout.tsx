import React from "react";

interface AppLayoutProps {
    sidebar: React.ReactNode;
    children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ sidebar, children }) => {
    return (
        <div className="flex h-screen w-full overflow-hidden bg-surface-950 text-white selection:bg-terminal-green/30 selection:text-white">
            {/* Sidebar Area */}
            <aside className="w-[260px] flex-shrink-0 border-r border-border-subtle bg-surface-900/80 backdrop-blur-xl flex flex-col z-20 relative">
                <div className="absolute inset-0 pointer-events-none opacity-60" style={{
                    background: "radial-gradient(80% 60% at 20% 0%, rgba(236, 72, 153, 0.08) 0%, rgba(5,5,5,0) 60%)"
                }} />
                {sidebar}
            </aside>

            {/* Main Stage */}
            <main className="flex-grow relative flex flex-col h-full overflow-hidden">
                {/* Decorative Background */}
                <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute inset-0 opacity-25"
                        style={{
                            backgroundImage: "linear-gradient(var(--border-subtle) 1px, transparent 1px), linear-gradient(90deg, var(--border-subtle) 1px, transparent 1px)",
                            backgroundSize: "46px 46px"
                        }}
                    />
                    <div className="absolute -right-40 -top-40 w-[480px] h-[480px] bg-primary-glow blur-[120px] opacity-40" />
                    <div className="absolute -left-40 top-40 w-[320px] h-[320px] bg-blue-500/40 blur-[120px] opacity-30" />
                </div>

                {/* Content Layer */}
                <div className="relative z-10 w-full h-full flex flex-col px-4 md:px-10">
                    {children}
                </div>
            </main>
        </div>
    );
};

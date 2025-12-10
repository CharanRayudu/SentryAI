'use client';

import { ReactNode } from 'react';

interface SymmetricalLayoutProps {
    leftPanel: ReactNode;
    centerStage: ReactNode;
    rightPanel: ReactNode;
}

export default function SymmetricalLayout({
    leftPanel,
    centerStage,
    rightPanel
}: SymmetricalLayoutProps) {
    return (
        <div className="flex h-screen w-full bg-[#030303] text-white overflow-hidden relative selection:bg-purple-500/30 selection:text-white">
            {/* Background Grid */}
            <div className="absolute inset-0 bg-grid-pattern opacity-30 pointer-events-none z-0" />

            {/* Main 3-Column Grid */}
            <main className="relative z-10 w-full h-full grid grid-cols-[300px_1fr_350px] gap-0">

                {/* Left Panel: System Status (Navigation/Diagnostics) */}
                <aside className="h-full border-r border-[#ffffff0a] bg-[#050505]/80 backdrop-blur-md flex flex-col">
                    {leftPanel}
                </aside>

                {/* Center Stage: Mission Control */}
                <section className="h-full relative flex flex-col overflow-hidden bg-gradient-to-b from-[#030303] to-[#080808]">
                    {centerStage}
                </section>

                {/* Right Panel: Intelligence (Logs/Findings) */}
                <aside className="h-full border-l border-[#ffffff0a] bg-[#050505]/80 backdrop-blur-md flex flex-col">
                    {rightPanel}
                </aside>

            </main>
        </div>
    );
}

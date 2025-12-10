'use client';

import { useState } from 'react';
import { Sparkles, ArrowRight, Command } from 'lucide-react';
import { motion } from 'framer-motion';

export default function CommandCenter() {
    const [input, setInput] = useState('');

    return (
        <div className="flex-1 flex flex-col items-center justify-center p-8 relative overflow-hidden">

            {/* Ambient Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-purple-600/20 blur-[100px] rounded-full pointer-events-none" />

            {/* Central Visual: The "Brain" */}
            <div className="relative mb-12">
                <div className="w-32 h-32 rounded-full border border-purple-500/30 flex items-center justify-center relative animate-pulse-glow">
                    <div className="absolute inset-0 rounded-full border border-cyan-500/20 animate-spin transition-all duration-[3000ms]" />
                    <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-600 to-cyan-600 blur-md opacity-50" />
                    <Sparkles className="relative z-10 w-12 h-12 text-white" />
                </div>
            </div>

            {/* Hero Text */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center mb-10 z-10"
            >
                <h1 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight">
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-purple-100 to-white text-glow">
                        What is your objective?
                    </span>
                </h1>
                <p className="text-zinc-400 text-lg max-w-xl mx-auto">
                    Initialize autonomous reconnaissance or specify a target for security audit.
                </p>
            </motion.div>

            {/* Main Input Field */}
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 }}
                className="w-full max-w-2xl relative z-10"
            >
                <div className="group relative">
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600 to-cyan-600 rounded-xl opacity-30 group-hover:opacity-100 transition duration-500 blur" />
                    <div className="relative flex items-center bg-[#0a0a0a] rounded-xl border border-white/10 p-2 shadow-2xl">
                        <div className="pl-4 pr-3 text-zinc-500">
                            <Command size={20} />
                        </div>
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="e.g., Scan example.com for vulnerabilities..."
                            className="flex-1 bg-transparent border-none text-lg text-white placeholder-zinc-600 focus:ring-0 focus:outline-none h-12 neo-input"
                        />
                        <button className="p-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors ml-2">
                            <ArrowRight size={20} />
                        </button>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="mt-8 flex justify-center gap-4">
                    <button className="px-4 py-2 rounded-full border border-white/10 bg-white/5 text-sm text-zinc-400 hover:text-white hover:border-purple-500/50 hover:bg-purple-500/10 transition-all">
                        Deep Scan
                    </button>
                    <button className="px-4 py-2 rounded-full border border-white/10 bg-white/5 text-sm text-zinc-400 hover:text-white hover:border-cyan-500/50 hover:bg-cyan-500/10 transition-all">
                        Map Infrastructure
                    </button>
                    <button className="px-4 py-2 rounded-full border border-white/10 bg-white/5 text-sm text-zinc-400 hover:text-white hover:border-pink-500/50 hover:bg-pink-500/10 transition-all">
                        Generate Report
                    </button>
                </div>
            </motion.div>

        </div>
    );
}


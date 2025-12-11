import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, Shield, AlertTriangle, Terminal, Play, X } from 'lucide-react';

interface PlanStep {
    id: number;
    tool: string;
    args: string;
    description: string;
}

interface PlanApprovalProps {
    plan: {
        thought_process: string;
        steps: PlanStep[];
    };
    onApprove: (approvedSteps: PlanStep[]) => void;
    onCancel: () => void;
}

export default function PlanApproval({ plan, onApprove, onCancel }: PlanApprovalProps) {
    const [selectedSteps, setSelectedSteps] = useState<number[]>(plan.steps.map(s => s.id));
    const [isSubmitting, setIsSubmitting] = useState(false);

    const toggleStep = (id: number) => {
        if (selectedSteps.includes(id)) {
            setSelectedSteps(selectedSteps.filter(s => s !== id));
        } else {
            setSelectedSteps([...selectedSteps, id]);
        }
    };

    const handleApprove = () => {
        setIsSubmitting(true);
        const approved = plan.steps.filter(s => selectedSteps.includes(s.id));
        onApprove(approved);
    };

    return (
        <div className="flex-1 flex flex-col p-6 h-full overflow-hidden relative">
            {/* Background Effects */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(168,85,247,0.05),transparent_40%)] pointer-events-none" />

            <div className="flex items-center justify-between mb-8 relative z-10">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Shield className="text-purple-400" size={24} />
                        Mission Plan
                    </h1>
                    <p className="text-zinc-500 mt-1">Review and authorize the proposed offensive security operations.</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={onCancel}
                        className="px-4 py-2 rounded-lg border border-white/10 text-zinc-400 hover:bg-white/5 hover:text-white transition-colors text-sm font-medium"
                    >
                        Abort
                    </button>
                    <button
                        onClick={handleApprove}
                        disabled={isSubmitting || selectedSteps.length === 0}
                        className="px-6 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-500/20 text-sm font-bold tracking-wide transition-all disabled:opacity-50 flex items-center gap-2"
                    >
                        {isSubmitting ? 'Authenticating...' : (
                            <>
                                <Play size={16} fill="currentColor" />
                                EXECUTE
                            </>
                        )}
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto pr-2 space-y-6 relative z-10">
                {/* Reasoning Card */}
                <div className="p-5 rounded-xl border border-purple-500/20 bg-purple-500/5 backdrop-blur-sm">
                    <h3 className="text-xs font-bold text-purple-300 uppercase tracking-wider mb-2 flex items-center gap-2">
                        <Terminal size={14} />
                        Strategic Reasoning
                    </h3>
                    <p className="text-sm text-zinc-300 leading-relaxed font-mono">
                        {plan.thought_process}
                    </p>
                </div>

                {/* Steps List */}
                <div className="space-y-3">
                    <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider px-1">Execution Sequence</h3>

                    {plan.steps.map((step) => {
                        const isSelected = selectedSteps.includes(step.id);
                        return (
                            <motion.div
                                key={step.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: step.id * 0.05 }}
                                onClick={() => toggleStep(step.id)}
                                className={`
                                    group relative p-4 rounded-xl border cursor-pointer transition-all duration-200
                                    ${isSelected
                                        ? 'bg-white/5 border-purple-500/30 shadow-[0_4px_20px_rgba(0,0,0,0.2)]'
                                        : 'bg-black/20 border-white/5 opacity-60 hover:opacity-100 hover:border-white/10'
                                    }
                                `}
                            >
                                <div className="flex items-start gap-4">
                                    <div className={`
                                        w-6 h-6 rounded flex items-center justify-center border transition-colors mt-0.5
                                        ${isSelected
                                            ? 'bg-purple-500 border-purple-400 text-white'
                                            : 'border-zinc-700 bg-zinc-900 text-transparent group-hover:border-zinc-500'
                                        }
                                    `}>
                                        <Check size={14} strokeWidth={3} />
                                    </div>

                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-1">
                                            <span className="font-mono text-sm font-bold text-purple-200">{step.tool}</span>
                                            <span className="text-xs text-zinc-500 font-mono px-2 py-0.5 rounded bg-white/5 border border-white/5">
                                                {step.args}
                                            </span>
                                        </div>
                                        <p className="text-sm text-zinc-400">{step.description}</p>
                                    </div>

                                    <div className="text-xs font-mono text-zinc-600">
                                        STEP {step.id.toString().padStart(2, '0')}
                                    </div>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>

                <div className="flex items-start gap-3 p-4 rounded-lg bg-amber-500/5 border border-amber-500/10 text-amber-500/80 text-xs">
                    <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                    <p>
                        <span className="font-bold block mb-1">Authorized Personnel Only</span>
                        By executing this plan, you confirm that you have authorization to scan the target infrastructure.
                        This action will be logged.
                    </p>
                </div>
            </div>
        </div>
    );
}

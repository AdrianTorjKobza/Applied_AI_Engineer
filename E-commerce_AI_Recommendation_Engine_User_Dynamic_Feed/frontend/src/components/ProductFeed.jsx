import React from 'react';
import { Flame, Dumbbell, Compass, ShoppingBag } from 'lucide-react';

// 1. Centralized Style Registry mapping categories to specific visual asset tokens
const CATEGORY_MAP = {
    running_gear: {
        label: 'Running',
        icon: Flame,
        theme: 'from-blue-500/20 to-indigo-500/5 border-blue-500/30 text-blue-400 bg-blue-500/10',
    },
    weightlifting: {
        label: 'Strength',
        icon: Dumbbell,
        theme: 'from-purple-500/20 to-fuchsia-500/5 border-purple-500/30 text-purple-400 bg-purple-500/10',
    },
    outdoor: {
        label: 'Outdoor',
        icon: Compass,
        theme: 'from-emerald-500/20 to-teal-500/5 border-emerald-500/30 text-emerald-400 bg-emerald-500/10',
    }
};

export default function ProductFeed({ feed }) {
    // Helper to extract programmatic category flags based on product names
    const getCategoryConfig = (name) => {
        const lowerName = name.toLowerCase();
        if (lowerName.includes('run') || lowerName.includes('sprint') || lowerName.includes('hydration')) {
            return CATEGORY_MAP.running_gear;
        }
        if (lowerName.includes('barbell') || lowerName.includes('kettlebell') || lowerName.includes('squat') || lowerName.includes('bench')) {
            return CATEGORY_MAP.weightlifting;
        }
        return CATEGORY_MAP.outdoor;
    };

    if (feed.length === 0) {
        return (
            <div className="text-center py-20 text-slate-500 border-2 border-dashed border-slate-800 rounded-xl bg-slate-900/20">
                <ShoppingBag className="w-10 h-10 mx-auto text-slate-700 mb-3" />
                <p className="font-medium text-slate-400">No products matching intent matrix.</p>
                <p className="text-xs text-slate-600 mt-1">Execute your database seeding script to instantiate assets.</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {feed.map((item) => {
                const config = getCategoryConfig(item.name);
                const Icon = config.icon;

                return (
                    <div 
                        key={item.product_id} 
                        className={`bg-gradient-to-br ${config.theme.split(' ').slice(0,2).join(' ')} bg-slate-900 border border-slate-800/80 rounded-xl p-5 flex flex-col justify-between transition-all duration-300 hover:border-slate-700 hover:-translate-y-0.5 shadow-md`}
                    >
                        <div className="flex justify-between items-start gap-4">
                            <div>
                                <span className={`inline-flex items-center gap-1.5 text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${config.theme.split(' ').slice(2).join(' ')}`}>
                                    <Icon className="w-3 h-3" /> {config.label}
                                </span>
                                <h3 className="font-semibold text-slate-100 text-base mt-2 tracking-tight leading-snug">{item.name}</h3>
                            </div>
                            
                            {/* Score Ring / Badge */}
                            <div className="text-right flex flex-col items-end shrink-0">
                                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Match Engine</span>
                                <span className="text-xl font-black text-emerald-400 mt-0.5 tracking-tighter">
                                    {(item.match_score * 100).toFixed(0)}<span className="text-xs font-medium text-emerald-500/70">%</span>
                                </span>
                            </div>
                        </div>

                        <div className="flex justify-between items-center mt-5 pt-3 border-t border-slate-800/60">
                            <span className="text-[10px] font-mono text-slate-500 tracking-wider">SKU: {item.product_id}</span>
                            <button className="text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 px-3 py-1.5 rounded-lg transition-colors">
                                Simulate Interaction
                            </button>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
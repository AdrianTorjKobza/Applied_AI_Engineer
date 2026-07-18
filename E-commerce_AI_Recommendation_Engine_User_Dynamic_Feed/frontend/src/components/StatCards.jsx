import React from 'react';
import { Award, Zap, Clock } from 'lucide-react';

export default function StatCards({ affinities, feed }) {
    // 1. Calculate highest affinity category dynamically
    const dominantCategory = affinities && affinities.length > 0
        ? [...affinities].sort((a, b) => b.score - a.score)[0]
        : { category: 'None', score: 0 };

    // 2. Count top tier matching products (match score greater than 0.6)
    const hotProductsCount = feed.filter(item => item.match_score >= 0.6).length;

    const stats = [
        {
            name: 'Dominant Affinity',
            value: dominantCategory.category,
            subtext: `${dominantCategory.score.toFixed(0)}% AI Confidence`,
            icon: Zap,
            color: 'text-amber-400 bg-amber-500/10 border-amber-500/20'
        },
        {
            name: 'Tailored Catalog Size',
            value: `${feed.length} Items`,
            subtext: 'Sorted entirely on DB-side',
            icon: Award,
            color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20'
        },
        {
            name: 'High-Match Recommendations',
            value: hotProductsCount,
            subtext: 'Match scores greater than 60%',
            icon: Clock,
            color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
        }
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            {stats.map((stat, idx) => {
                const Icon = stat.icon;
                return (
                    <div key={idx} className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-xl p-5 flex items-center justify-between shadow-lg">
                        <div>
                            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{stat.name}</p>
                            <h4 className="text-2xl font-bold text-slate-100 mt-1 tracking-tight">{stat.value}</h4>
                            <p className="text-xs text-slate-500 mt-1">{stat.subtext}</p>
                        </div>
                        <div className={`p-3 rounded-xl border ${stat.color}`}>
                            <Icon className="w-5 h-5" />
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
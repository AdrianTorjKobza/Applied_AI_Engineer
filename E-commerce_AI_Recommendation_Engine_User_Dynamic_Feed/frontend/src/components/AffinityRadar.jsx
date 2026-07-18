import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

export default function AffinityRadar({ data }) {
    if (!data) return null;

    return (
        <div className="h-80 w-full bg-slate-900/60 backdrop-blur-md rounded-xl shadow-lg border border-slate-800 p-5 flex flex-col justify-between">
            <div>
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">AI Persona Matrix</h3>
                <p className="text-xs text-slate-500 mt-0.5">Real-time vector profiling weights</p>
            </div>
            
            <div className="h-60 w-full mt-2">
                <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
                        <PolarGrid stroke="#334155" />
                        <PolarAngleAxis 
                            dataKey="category" 
                            tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 500 }} 
                        />
                        <PolarRadiusAxis 
                            angle={30} 
                            domain={[0, 100]} 
                            tick={false} 
                            axisLine={false} 
                        />
                        <Radar 
                            name="Affinity Score" 
                            dataKey="score" 
                            stroke="#6366f1" 
                            fill="url(#radarGradient)" 
                            fillOpacity={0.45} 
                        />
                        <defs>
                            <linearGradient id="radarGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8}/>
                                <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.2}/>
                            </linearGradient>
                        </defs>
                    </RadarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
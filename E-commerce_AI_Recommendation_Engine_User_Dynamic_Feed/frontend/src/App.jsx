import React, { useState } from 'react';
import { Cpu, RefreshCw } from 'lucide-react';
import { useDashboardData } from './hooks/useDashboardData';
import StatCards from './components/StatCards';
import AffinityRadar from './components/AffinityRadar';
import ProductFeed from './components/ProductFeed';

export default function App() {
    const [selectedUser, setSelectedUser] = useState('user_100');
    const { affinities, feed, isLoading, error } = useDashboardData(selectedUser);

    const mockUsers = ['user_100', 'user_101', 'user_102', 'user_103', 'user_104', 'user_105'];

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100 font-sans tracking-tight antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
            {/* Subtle background glow mesh */}
            <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

            <div className="max-w-6xl mx-auto p-4 sm:p-6 lg:p-8 relative z-10">
                {/* Global Application Nav Bar */}
                <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8 border-b border-slate-800 pb-5">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/20">
                            <Cpu className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold tracking-tight text-slate-100">Protos Personalization Matrix</h1>
                            <p className="text-xs text-slate-400">Behavioral Affinity Vector & Dot-Product Sorting Engine</p>
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-3 w-full sm:w-auto">
                        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider hidden sm:inline">Active Test Profile:</label>
                        <select 
                            value={selectedUser}
                            onChange={(e) => setSelectedUser(e.target.value)}
                            className="w-full sm:w-auto bg-slate-900 border border-slate-800 text-slate-200 text-sm font-medium rounded-xl focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 block p-2.5 shadow-inner transition-all hover:bg-slate-850 cursor-pointer"
                        >
                            {mockUsers.map(user => (
                                <option key={user} value={user}>Simulated Profile {user.replace('_', ' #')}</option>
                            ))}
                        </select>
                    </div>
                </header>

                {error && (
                    <div className="p-4 mb-6 text-sm text-red-400 bg-red-950/40 border border-red-900/50 rounded-xl backdrop-blur-md">
                        Network Error: {error}. Is your FastAPI system initialized?
                    </div>
                )}

                {/* KPI Overview Block */}
                {!isLoading && <StatCards affinities={affinities} feed={feed} />}

                {isLoading ? (
                    <div className="flex flex-col justify-center items-center h-80 gap-3 border border-slate-800 rounded-2xl bg-slate-900/10">
                        <RefreshCw className="animate-spin text-indigo-400 w-8 h-8" />
                        <p className="text-xs text-slate-500 font-mono tracking-widest uppercase">Fetching Neural Cache...</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                        {/* Visualization Pillar */}
                        <div className="lg:col-span-4 space-y-6">
                            <AffinityRadar data={affinities} />
                            
                            <div className="bg-gradient-to-br from-indigo-950/40 to-slate-900/60 backdrop-blur-md rounded-xl p-5 border border-indigo-900/30 shadow-lg">
                                <h4 className="font-semibold text-indigo-300 text-sm tracking-tight flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                                    Pipeline Telemetry Active
                                </h4>
                                <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                                    Execute <code className="bg-slate-950 px-1.5 py-0.5 rounded font-mono text-indigo-400 border border-slate-800">mock_generator.py</code> in your host shell. Changing consumer profiles will capture real-time weights calculated via LangChain.
                                </p>
                            </div>
                        </div>

                        {/* Recommendation Catalog Pillar */}
                        <div className="lg:col-span-8">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-base font-bold text-slate-200 tracking-tight uppercase tracking-wider text-xs">Dynamic Feed Stream</h2>
                                <span className="text-[10px] font-mono text-slate-500">Sorted dynamically via PostgreSQL query engine</span>
                            </div>
                            <ProductFeed feed={feed} />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
import { useState, useEffect } from 'react';
import { fetchUserAffinities, fetchPersonalizedFeed } from '../services/api';

export const useDashboardData = (userId) => {
    const [affinities, setAffinities] = useState(null);
    const [feed, setFeed] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadData = async () => {
            setIsLoading(true);
            try {
                const [affinityData, feedData] = await Promise.all([
                    fetchUserAffinities(userId),
                    fetchPersonalizedFeed(userId)
                ]);
                
                const chartData = [
                    { category: 'Running', score: affinityData.running * 100 },
                    { category: 'Weightlifting', score: affinityData.weightlifting * 100 },
                    { category: 'Outdoor', score: affinityData.outdoor * 100 }
                ];
                
                setAffinities(chartData);
                setFeed(feedData.feed);
                setError(null);
            } catch (err) {
                setError(err.message);
            } finally {
                setIsLoading(false);
            }
        };

        loadData();
    }, [userId]);

    return { affinities, feed, isLoading, error };
};
const API_BASE = '/v1';

export const fetchUserAffinities = async (userId) => {
    const res = await fetch(`${API_BASE}/affinities/${userId}`);
    if (!res.ok) throw new Error('Failed to fetch affinities');
    return res.json();
};

export const fetchPersonalizedFeed = async (userId) => {
    const res = await fetch(`${API_BASE}/feed/${userId}`);
    if (!res.ok) throw new Error('Failed to fetch feed');
    return res.json();
};
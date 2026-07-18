import { useState, useEffect } from 'react';
import { getRecommendations, sendEvent } from './api/recommendationService';
import ProductCard from './components/ProductCard';

export default function App() {
  const [feed, setFeed] = useState([]);
  const userId = "user_101";

  const loadFeed = async () => {
    const data = await getRecommendations(userId);
    setFeed(data.recommended_feed);
  };

  const handleSimulateClick = async (category) => {
    await sendEvent({
      user_id: userId,
      event_type: "click",
      product_id: "prod_demo_1",
      category: category,
      attributes: { duration_seconds: 5 }
    });
    // Wait briefly for the worker to process then refresh
    setTimeout(loadFeed, 1000);
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h1 className="text-2xl font-bold mb-6">Personalized Feed</h1>
      <div className="mb-8 flex gap-4">
        {['running_gear', 'weightlifting', 'outdoor'].map(cat => (
          <button 
            key={cat}
            onClick={() => handleSimulateClick(cat)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Click {cat}
          </button>
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {feed.map(item => <ProductCard key={item.product_id} item={item} />)}
      </div>
    </div>
  );
}
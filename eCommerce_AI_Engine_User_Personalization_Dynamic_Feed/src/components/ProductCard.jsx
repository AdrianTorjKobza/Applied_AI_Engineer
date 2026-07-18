export default function ProductCard({ item }) {
  return (
    <div className="p-4 bg-white rounded shadow border-l-4 border-blue-500">
      <h3 className="font-bold">{item.name}</h3>
      <p className="text-sm text-gray-600">Match Score: {item.match_score}</p>
    </div>
  );
}
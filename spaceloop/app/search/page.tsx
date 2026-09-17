"use client";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { rankListings, ParsedIntent } from "@/lib/ranking";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  const fetchAndRank = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    try {
      const { data } = await supabase.from("listings").select("*");
      if (!query.trim()) {
        setResults(data || []);
        setLoading(false);
        return;
      }
      const res = await fetch("/api/ai/parse-query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const parsed: ParsedIntent = await res.json();
      setResults(rankListings(data || [], parsed));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAndRank(); }, []);

  return (
    <main className="max-w-5xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-6">SpaceLoop Search</h1>
      <form onSubmit={fetchAndRank} className="flex gap-2 mb-8">
        <input
          type="text"
          className="flex-1 border p-3 rounded-lg"
          placeholder="e.g. Quiet garage in East Austin under $60"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" disabled={loading} className="bg-black text-white px-6 py-3 rounded-lg">
          {loading ? "Searching..." : "Search"}
        </button>
      </form>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {results.map((item) => (
          <div key={item.id} className="border rounded-xl p-5 shadow-sm bg-white">
            <h3 className="font-semibold text-lg">{item.title}</h3>
            <p className="text-gray-500 text-sm mb-2">{item.location}</p>
            <p className="text-xl font-bold mb-3">${item.price}</p>
            {item.matchReason && (
              <p className="text-xs bg-emerald-50 text-emerald-800 p-2 rounded mb-3">{item.matchReason}</p>
            )}
            <button className="w-full border border-black py-2 rounded">Book Space</button>
          </div>
        ))}
      </div>
    </main>
  );
}
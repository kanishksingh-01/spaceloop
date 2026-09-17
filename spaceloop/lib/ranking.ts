export interface ParsedIntent {
  space_type?: string | null;
  min_size?: number | null;
  max_budget?: number | null;
  budget_unit?: string | null;
  location_hint?: string | null;
  purpose_keywords: string[];
}
export function rankListings(listings: any[], intent: ParsedIntent) {
  return listings
    .map((item) => {
      let score = 0;
      const reasons: string[] = [];
      if (intent.space_type && item.space_type?.toLowerCase() === intent.space_type.toLowerCase()) {
        score += 30;
        reasons.push("Matches type (" + item.space_type + ")");
      }
      if (intent.max_budget && item.price <= intent.max_budget) {
        score += 25;
        reasons.push("Within budget ($" + item.price + ")");
      }
      if (intent.location_hint && (item.location || item.location_name || "").toLowerCase().includes(intent.location_hint.toLowerCase())) {
        score += 20;
        reasons.push("Located near " + intent.location_hint);
      }
      const allText = (item.title + " " + (item.description || "")).toLowerCase();
      let hits = 0;
      (intent.purpose_keywords || []).forEach((kw) => {
        if (allText.includes(kw.toLowerCase())) hits++;
      });
      if (hits > 0) {
        score += Math.min(hits * 8, 25);
        reasons.push("Matches: " + intent.purpose_keywords.slice(0, 2).join(", "));
      }
      return {
        ...item,
        matchScore: score,
        matchReason: reasons.length > 0 ? reasons.join(" • ") : "Available space nearby",
      };
    })
    .sort((a, b) => b.matchScore - a.matchScore);
}
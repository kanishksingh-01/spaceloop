import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const query = (body.query || "").toLowerCase();

    // 1. Instant local parser (Zero failure, zero wait time)
    let space_type: string | null = null;
    if (query.includes("garage")) space_type = "garage";
    else if (query.includes("studio")) space_type = "studio";
    else if (query.includes("office") || query.includes("desk")) space_type = "office";
    else if (query.includes("storage") || query.includes("warehouse")) space_type = "storage";
    else if (query.includes("backyard") || query.includes("garden")) space_type = "backyard";

    // Extract budget like $50, 50$, under 50, etc.
    let max_budget: number | null = null;
    const budgetMatch = query.match(/(?:under|\$|below|\s)(\d{2,4})(?:\$|\/hr|\/mo)?/);
    if (budgetMatch && budgetMatch[1]) {
      max_budget = parseInt(budgetMatch[1], 10);
    }

    // Extract size like 200 sqft, 500 sq ft
    let min_size: number | null = null;
    const sizeMatch = query.match(/(\d{2,4})\s*(?:sqft|sq\s*ft|feet)/);
    if (sizeMatch && sizeMatch[1]) {
      min_size = parseInt(sizeMatch[1], 10);
    }

    // Extract location
    let location_hint: string | null = null;
    const locations = ["east austin", "downtown", "south congress", "north loop", "central", "austin", "pune", "korba"];
    for (const loc of locations) {
      if (query.includes(loc)) {
        location_hint = loc;
        break;
      }
    }

    // Clean keywords
    const stopWords = new Set(["i", "need", "a", "for", "in", "with", "under", "looking", "want", "the", "and", "or", "to", "my"]);
    const purpose_keywords = query
      .replace(/[^\w\s]/g, "")
      .split(/\s+/)
      .filter((w: string) => w.length > 2 && !stopWords.has(w));

    const result = {
      space_type,
      min_size,
      max_budget,
      budget_unit: max_budget ? (max_budget < 100 ? "hour" : "month") : null,
      location_hint,
      purpose_keywords
    };

    // Return instant parsed result
    return NextResponse.json(result);
  } catch (error: any) {
    return NextResponse.json({
      space_type: null,
      min_size: null,
      max_budget: null,
      budget_unit: null,
      location_hint: null,
      purpose_keywords: []
    });
  }
}

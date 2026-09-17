import { GoogleGenAI, Type } from "@google/genai";
import { NextResponse } from "next/server";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || "" });

export async function POST(req: Request) {
  try {
    const { description, space_type } = await req.json();
    const prompt = \`Analyze space type "\${space_type}" with description: "\${description}". Extract category tags, suitability tags, and a 1-sentence best-use recommendation.\`;

    const response = await ai.models.generateContent({
      model: "gemini-3.8-flash",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            category_tags: { type: Type.ARRAY, items: { type: Type.STRING } },
            suitability_tags: { type: Type.ARRAY, items: { type: Type.STRING } },
            best_use: { type: Type.STRING },
          },
          required: ["category_tags", "suitability_tags", "best_use"],
        },
      },
    });

    return NextResponse.json(JSON.parse(response.text || "{}"));
  } catch (error) {
    return NextResponse.json({ error: "Tagging failed" }, { status: 500 });
  }
}

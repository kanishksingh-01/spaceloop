from typing import List
from app.schemas.risk import FactorDetail


class ExplanationEngine:
    """Decomposes risk scores into explainable, structured factors and executive summaries."""

    @staticmethod
    def synthesize(factors: List[FactorDetail], total_score: float, risk_level: str) -> List[FactorDetail]:
        """Sorts factors by contribution descending and ensures formatted rationale."""
        sorted_factors = sorted(factors, key=lambda f: f.contribution, reverse=True)
        return sorted_factors

    @staticmethod
    def generate_narrative_summary(factors: List[FactorDetail], risk_level: str) -> str:
        """Generates a concise plain-English sentence summarizing the top contributing drivers."""
        if not factors or risk_level == "LOW":
            return "Activity is consistent with established contextual baselines."

        top_factors = sorted(factors, key=lambda f: f.contribution, reverse=True)[:3]
        explanations = [f.explanation.rstrip(".") for f in top_factors]
        summary = f"Flagged as {risk_level} risk primarily due to: {'; '.join(explanations)}."
        return summary

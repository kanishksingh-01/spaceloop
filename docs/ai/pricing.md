# AI Pricing Engine
Implements the Non-Linear SqFt Polynomial Multiplier Model:
`sqft_adj = max(0.8, min(2.5, sqft / 250.0))`
`Rate = Base * (0.6 + 0.4 * sqft_adj)`

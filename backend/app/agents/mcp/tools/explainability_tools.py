"""
MCP Explainability Tools for FinFind ExplainabilityAgent.

Tools for explaining recommendations and product matches.
"""

import logging
from typing import Dict, Any, List, Optional, ClassVar

from pydantic import BaseModel, Field

from ..protocol import (
    MCPTool, MCPToolMetadata, MCPToolOutput,
    MCPError, MCPErrorCode
)
from ...services import get_qdrant_service, get_embedding_service, get_cache_service
from ...config import get_config

logger = logging.getLogger(__name__)


# ========================================
# Input Schemas
# ========================================

class SimilarityExplanationInput(BaseModel):
    """Input for similarity explanation."""
    query: str = Field(..., description="Original search query")
    product: Dict[str, Any] = Field(..., description="Product to explain")
    include_breakdown: bool = Field(default=True, description="Include score breakdown")


class FinancialFitInput(BaseModel):
    """Input for financial fit explanation."""
    product: Dict[str, Any] = Field(..., description="Product to explain")
    user_profile: Dict[str, Any] = Field(..., description="User financial profile")
    include_alternatives: bool = Field(default=False, description="Suggest alternatives if poor fit")


class AttributeMatchInput(BaseModel):
    """Input for attribute matching."""
    query: str = Field(..., description="Search query")
    product: Dict[str, Any] = Field(..., description="Product to analyze")
    attributes: Optional[List[str]] = Field(
        default=None,
        description="Specific attributes to check"
    )


class NaturalExplanationInput(BaseModel):
    """Input for natural language explanation."""
    product: Dict[str, Any] = Field(..., description="Product to explain")
    query: Optional[str] = Field(default=None, description="Original query")
    user_profile: Optional[Dict[str, Any]] = Field(default=None, description="User profile")
    explanation_type: str = Field(
        default="recommendation",
        description="Type: recommendation, match, financial, comparison"
    )
    tone: str = Field(default="helpful", description="Tone: helpful, concise, detailed")


# ========================================
# Get Similarity Explanation Tool
# ========================================

class GetSimilarityExplanationTool(MCPTool):
    """
    MCP tool for explaining semantic similarity between query and product.
    
    Provides detailed breakdown of:
    - Overall similarity score
    - Matching concepts
    - Relevance factors
    """
    
    name: str = "get_similarity_explanation"
    description: str = """
    Explains why a product matches a search query semantically.
    Provides similarity score and identifies matching concepts.
    Helps users understand why a product was recommended.
    """
    args_schema: type = SimilarityExplanationInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="get_similarity_explanation",
        description="Explain semantic match between query and product",
        category="explainability",
        tags=["explanation", "similarity", "semantic"],
        requires_embedding=True,
        cacheable=True,
        cache_ttl_seconds=600,
        avg_latency_ms=100
    )
    
    def _execute(
        self,
        query: str,
        product: Dict[str, Any],
        include_breakdown: bool = True
    ) -> MCPToolOutput:
        """Explain similarity."""
        
        embedding_service = get_embedding_service()
        cache = get_cache_service()
        
        product_id = product.get("id", "unknown")
        cache_key = f"{query}:{product_id}"
        
        # Check cache
        cached = cache.get("similarity_explanation", cache_key)
        if cached:
            return MCPToolOutput.success_response(data=cached, cache_hit=True)
        
        # Get embeddings
        query_embedding = embedding_service.embed(query)
        
        # Build product text for embedding
        product_text = self._build_product_text(product)
        product_embedding = embedding_service.embed(product_text)
        
        # Calculate similarity
        similarity = embedding_service.similarity(query_embedding, product_embedding)
        
        # Find matching terms
        query_terms = set(query.lower().split())
        product_terms = set(product_text.lower().split())
        matching_terms = query_terms.intersection(product_terms)
        
        # Analyze which fields contribute to match
        field_contributions = {}
        if include_breakdown:
            fields_to_check = ["name", "description", "category", "brand", "tags"]
            
            for field in fields_to_check:
                field_value = product.get(field, "")
                if isinstance(field_value, list):
                    field_value = " ".join(field_value)
                if field_value:
                    field_embedding = embedding_service.embed(str(field_value))
                    field_sim = embedding_service.similarity(query_embedding, field_embedding)
                    field_contributions[field] = round(field_sim, 3)
        
        # Determine match quality
        if similarity >= 0.8:
            match_quality = "excellent"
            match_description = "This product is an excellent match for your search"
        elif similarity >= 0.6:
            match_quality = "good"
            match_description = "This product matches most aspects of your search"
        elif similarity >= 0.4:
            match_quality = "moderate"
            match_description = "This product partially matches your search"
        else:
            match_quality = "low"
            match_description = "This product has limited relevance to your search"
        
        explanation = {
            "similarity_score": round(similarity, 4),
            "match_quality": match_quality,
            "match_description": match_description,
            "matching_terms": list(matching_terms),
            "field_contributions": field_contributions if include_breakdown else None,
            "primary_match_field": max(
                field_contributions.items(),
                key=lambda x: x[1]
            )[0] if field_contributions else None
        }
        
        # Cache result
        cache.set("similarity_explanation", cache_key, explanation, ttl=600)
        
        return MCPToolOutput.success_response(data=explanation)
    
    def _build_product_text(self, product: Dict) -> str:
        """Build searchable text from product."""
        parts = []
        
        if product.get("name"):
            parts.append(product["name"])
        if product.get("description"):
            parts.append(product["description"])
        if product.get("category"):
            parts.append(f"category: {product['category']}")
        if product.get("brand"):
            parts.append(f"brand: {product['brand']}")
        if product.get("tags"):
            parts.append(" ".join(product["tags"]))
        
        return " ".join(parts)


# ========================================
# Get Financial Fit Explanation Tool
# ========================================

class GetFinancialFitExplanationTool(MCPTool):
    """
    MCP tool for explaining financial fit.
    
    Analyzes and explains:
    - Budget compatibility
    - Affordability assessment
    - Value proposition
    """
    
    name: str = "get_financial_fit_explanation"
    description: str = """
    Explains why a product fits or doesn't fit user's budget.
    Analyzes affordability, budget impact, and value.
    Provides actionable insights for financial decisions.
    """
    args_schema: type = FinancialFitInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="get_financial_fit_explanation",
        description="Explain product-budget fit",
        category="explainability",
        tags=["explanation", "financial", "budget"],
        requires_qdrant=False,
        cacheable=False,
        avg_latency_ms=30
    )
    
    def _execute(
        self,
        product: Dict[str, Any],
        user_profile: Dict[str, Any],
        include_alternatives: bool = False
    ) -> MCPToolOutput:
        """Explain financial fit."""
        
        price = product.get("price", 0)
        financial = user_profile.get("financial", {})
        
        budget_max = financial.get("budget_max")
        budget_min = financial.get("budget_min")
        monthly_budget = financial.get("monthly_budget")
        disposable_income = financial.get("disposable_income")
        risk_tolerance = financial.get("risk_tolerance", "medium")
        
        # Analysis components
        analysis = {
            "budget_analysis": {},
            "income_analysis": {},
            "value_analysis": {},
            "overall_fit": {}
        }
        
        # Budget analysis
        if budget_max:
            budget_ratio = price / budget_max
            analysis["budget_analysis"] = {
                "within_budget": price <= budget_max,
                "budget_utilization": round(budget_ratio * 100, 1),
                "remaining_budget": max(0, budget_max - price),
                "explanation": self._budget_explanation(price, budget_max)
            }
        
        # Income/monthly impact analysis
        if monthly_budget:
            monthly_impact = (price / monthly_budget) * 100
            analysis["income_analysis"] = {
                "monthly_impact_percent": round(monthly_impact, 1),
                "months_to_save": round(price / monthly_budget, 1) if monthly_budget > 0 else None,
                "explanation": self._income_explanation(price, monthly_budget, disposable_income)
            }
        
        # Value analysis
        rating = product.get("rating", 3)
        review_count = product.get("review_count", 0)
        
        value_score = self._calculate_value_score(price, rating, review_count, budget_max)
        analysis["value_analysis"] = {
            "value_score": round(value_score, 2),
            "price_per_rating_point": round(price / max(rating, 1), 2),
            "explanation": self._value_explanation(value_score, rating, review_count)
        }
        
        # Overall fit determination
        fit_score = self._calculate_overall_fit(
            price, budget_max, monthly_budget, disposable_income, risk_tolerance
        )
        
        if fit_score >= 0.8:
            fit_level = "excellent"
            recommendation = "This purchase aligns well with your financial situation"
        elif fit_score >= 0.6:
            fit_level = "good"
            recommendation = "This is a reasonable purchase within your means"
        elif fit_score >= 0.4:
            fit_level = "moderate"
            recommendation = "Consider if this purchase is a priority"
        elif fit_score >= 0.2:
            fit_level = "stretch"
            recommendation = "This would stretch your budget - consider alternatives"
        else:
            fit_level = "poor"
            recommendation = "This exceeds your comfortable spending range"
        
        analysis["overall_fit"] = {
            "fit_score": round(fit_score, 3),
            "fit_level": fit_level,
            "recommendation": recommendation
        }
        
        return MCPToolOutput.success_response(
            data={
                "product_id": product.get("id"),
                "product_price": price,
                "analysis": analysis,
                "fit_level": fit_level,
                "fit_score": round(fit_score, 3)
            }
        )
    
    def _budget_explanation(self, price: float, budget_max: float) -> str:
        ratio = price / budget_max
        if ratio <= 0.5:
            return f"At ${price:.2f}, this uses only {ratio*100:.0f}% of your ${budget_max:.2f} budget, leaving plenty of room"
        elif ratio <= 0.8:
            return f"This ${price:.2f} purchase uses {ratio*100:.0f}% of your budget - a significant but manageable expense"
        elif ratio <= 1.0:
            return f"At ${price:.2f}, this nearly exhausts your ${budget_max:.2f} budget"
        else:
            return f"This ${price:.2f} item exceeds your ${budget_max:.2f} budget by ${price-budget_max:.2f}"
    
    def _income_explanation(
        self,
        price: float,
        monthly_budget: float,
        disposable_income: Optional[float]
    ) -> str:
        months = price / monthly_budget if monthly_budget > 0 else float('inf')
        
        if months < 0.5:
            return "This purchase represents less than half a month's budget"
        elif months < 1:
            return f"You could save for this in about {months:.1f} months"
        elif months < 3:
            return f"Saving for {months:.1f} months would cover this purchase"
        else:
            return f"This would require {months:.1f} months of saving"
    
    def _value_explanation(
        self,
        value_score: float,
        rating: float,
        review_count: int
    ) -> str:
        if value_score >= 0.8:
            return f"Excellent value with {rating:.1f}⭐ rating from {review_count} reviews"
        elif value_score >= 0.6:
            return f"Good value proposition based on {rating:.1f}⭐ rating"
        elif value_score >= 0.4:
            return "Average value for the price point"
        else:
            return "Consider if the quality justifies the price"
    
    def _calculate_value_score(
        self,
        price: float,
        rating: float,
        review_count: int,
        budget_max: Optional[float]
    ) -> float:
        # Base value from rating
        value = (rating / 5.0) * 0.6
        
        # Boost for many reviews (social proof)
        if review_count > 500:
            value += 0.2
        elif review_count > 100:
            value += 0.1
        
        # Price efficiency (lower price relative to budget = better value)
        if budget_max and price > 0:
            efficiency = 1 - (price / budget_max)
            value += efficiency * 0.2
        
        return min(1.0, value)
    
    def _calculate_overall_fit(
        self,
        price: float,
        budget_max: Optional[float],
        monthly_budget: Optional[float],
        disposable_income: Optional[float],
        risk_tolerance: str
    ) -> float:
        fit = 1.0
        
        # Budget impact
        if budget_max:
            ratio = price / budget_max
            if ratio > 1:
                fit *= 0.3
            elif ratio > 0.8:
                fit *= 0.6
            elif ratio > 0.5:
                fit *= 0.85
        
        # Monthly budget impact
        if monthly_budget:
            monthly_ratio = price / monthly_budget
            if monthly_ratio > 3:
                fit *= 0.5
            elif monthly_ratio > 1:
                fit *= 0.7
        
        # Risk tolerance adjustment
        risk_adjustments = {
            "conservative": 0.8,
            "moderate": 0.9,
            "medium": 0.9,
            "aggressive": 1.0
        }
        fit *= risk_adjustments.get(risk_tolerance, 0.9)
        
        return fit


# ========================================
# Get Attribute Matches Tool
# ========================================

class GetAttributeMatchesTool(MCPTool):
    """
    MCP tool for identifying matching attributes.
    
    Shows which product attributes match the query:
    - Explicit matches (keywords)
    - Implicit matches (semantic)
    - Missing attributes
    """
    
    name: str = "get_attribute_matches"
    description: str = """
    Identifies which product attributes match the search query.
    Shows explicit keyword matches and semantic connections.
    Highlights both matching and missing attributes.
    """
    args_schema: type = AttributeMatchInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="get_attribute_matches",
        description="Identify query-product attribute matches",
        category="explainability",
        tags=["attributes", "matching", "analysis"],
        requires_embedding=True,
        cacheable=True,
        cache_ttl_seconds=600,
        avg_latency_ms=80
    )
    
    # Common attributes to analyze
    DEFAULT_ATTRIBUTES: ClassVar[List[str]] = [
        "name", "brand", "category", "price", "color",
        "size", "material", "features", "tags", "description"
    ]
    
    def _execute(
        self,
        query: str,
        product: Dict[str, Any],
        attributes: Optional[List[str]] = None
    ) -> MCPToolOutput:
        """Analyze attribute matches."""
        
        embedding_service = get_embedding_service()
        
        attrs_to_check = attributes or self.DEFAULT_ATTRIBUTES
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        matches = {
            "exact_matches": [],
            "partial_matches": [],
            "semantic_matches": [],
            "no_matches": []
        }
        
        query_embedding = embedding_service.embed(query)
        
        for attr in attrs_to_check:
            value = product.get(attr)
            if value is None:
                continue
            
            # Convert to string
            if isinstance(value, list):
                value_str = " ".join(str(v) for v in value)
            else:
                value_str = str(value)
            
            value_lower = value_str.lower()
            value_terms = set(value_lower.split())
            
            # Check for exact matches
            common_terms = query_terms.intersection(value_terms)
            if common_terms:
                matches["exact_matches"].append({
                    "attribute": attr,
                    "value": value_str,
                    "matching_terms": list(common_terms)
                })
                continue
            
            # Check for partial matches (substring)
            partial = False
            for term in query_terms:
                if len(term) > 3 and term in value_lower:
                    matches["partial_matches"].append({
                        "attribute": attr,
                        "value": value_str,
                        "matching_substring": term
                    })
                    partial = True
                    break
            
            if partial:
                continue
            
            # Check semantic similarity
            value_embedding = embedding_service.embed(value_str)
            similarity = embedding_service.similarity(query_embedding, value_embedding)
            
            if similarity > 0.5:
                matches["semantic_matches"].append({
                    "attribute": attr,
                    "value": value_str,
                    "similarity": round(similarity, 3)
                })
            else:
                matches["no_matches"].append({
                    "attribute": attr,
                    "value": value_str[:50] + "..." if len(value_str) > 50 else value_str
                })
        
        # Calculate match summary
        total_attrs = (
            len(matches["exact_matches"]) +
            len(matches["partial_matches"]) +
            len(matches["semantic_matches"]) +
            len(matches["no_matches"])
        )
        
        matching_attrs = (
            len(matches["exact_matches"]) +
            len(matches["partial_matches"]) +
            len(matches["semantic_matches"])
        )
        
        match_percentage = (matching_attrs / total_attrs * 100) if total_attrs > 0 else 0
        
        return MCPToolOutput.success_response(
            data={
                "query": query,
                "product_id": product.get("id"),
                "matches": matches,
                "summary": {
                    "total_attributes_checked": total_attrs,
                    "matching_attributes": matching_attrs,
                    "match_percentage": round(match_percentage, 1),
                    "exact_match_count": len(matches["exact_matches"]),
                    "semantic_match_count": len(matches["semantic_matches"])
                }
            }
        )


# ========================================
# Generate Natural Explanation Tool
# ========================================

class GenerateNaturalExplanationTool(MCPTool):
    """
    MCP tool for generating human-readable explanations.
    
    Creates natural language explanations combining:
    - Similarity analysis
    - Financial fit
    - User preferences
    """
    
    name: str = "generate_natural_explanation"
    description: str = """
    Generates a human-readable explanation for a recommendation.
    Combines semantic match, financial fit, and preferences.
    Adapts tone and detail level to user preference.
    """
    args_schema: type = NaturalExplanationInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="generate_natural_explanation",
        description="Generate human-readable recommendation explanation",
        category="explainability",
        tags=["explanation", "natural_language", "summary"],
        requires_llm=True,
        cacheable=True,
        cache_ttl_seconds=600,
        avg_latency_ms=300
    )
    
    def _execute(
        self,
        product: Dict[str, Any],
        query: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        explanation_type: str = "recommendation",
        tone: str = "helpful"
    ) -> MCPToolOutput:
        """Generate natural explanation."""
        
        # Build explanation components
        components = []
        
        product_name = product.get("name", "This product")
        price = product.get("price", 0)
        rating = product.get("rating", 0)
        category = product.get("category", "")
        brand = product.get("brand", "")
        
        # Opening based on type
        if explanation_type == "recommendation":
            if query:
                components.append(
                    f"Based on your search for \"{query}\", I recommend **{product_name}**."
                )
            else:
                components.append(f"I recommend **{product_name}**.")
        elif explanation_type == "match":
            components.append(f"**{product_name}** matches your criteria.")
        elif explanation_type == "comparison":
            components.append(f"Here's why **{product_name}** stands out:")
        
        # Add relevance explanation
        if query and product.get("score"):
            score = product["score"]
            if score > 0.8:
                components.append(
                    "This is an excellent match for what you're looking for."
                )
            elif score > 0.6:
                components.append("This closely matches your search criteria.")
        
        # Add product highlights
        highlights = []
        if brand:
            highlights.append(f"from {brand}")
        if rating and rating >= 4:
            highlights.append(f"rated {rating}⭐")
        if product.get("review_count", 0) > 100:
            highlights.append(f"with {product['review_count']} reviews")
        
        if highlights:
            components.append(f"It's {', '.join(highlights)}.")
        
        # Financial fit explanation
        if user_profile:
            financial = user_profile.get("financial", {})
            budget_max = financial.get("budget_max")
            
            if budget_max:
                if price <= budget_max * 0.5:
                    components.append(
                        f"At **${price:.2f}**, it's well within your budget of ${budget_max:.2f}."
                    )
                elif price <= budget_max:
                    components.append(
                        f"Priced at **${price:.2f}**, it fits your ${budget_max:.2f} budget."
                    )
                else:
                    over = price - budget_max
                    components.append(
                        f"At **${price:.2f}**, it's ${over:.2f} over your budget."
                    )
        else:
            components.append(f"It's priced at **${price:.2f}**.")
        
        # Add category context
        if category:
            components.append(f"In the {category} category.")
        
        # Tone adjustment
        explanation = " ".join(components)
        
        if tone == "concise":
            # Shorten explanation
            explanation = explanation.split(".")[0] + "."
        elif tone == "detailed":
            # Add more details
            features = product.get("features", [])
            if features:
                explanation += f"\n\nKey features: {', '.join(features[:5])}."
            
            description = product.get("description", "")
            if description:
                explanation += f"\n\n{description[:200]}..."
        
        return MCPToolOutput.success_response(
            data={
                "explanation": explanation,
                "explanation_type": explanation_type,
                "tone": tone,
                "product_id": product.get("id"),
                "key_points": {
                    "product_name": product_name,
                    "price": price,
                    "rating": rating,
                    "budget_fit": user_profile.get("financial", {}).get("budget_max", 0) >= price if user_profile else None
                }
            }
        )

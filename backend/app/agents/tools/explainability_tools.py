"""
Explainability Tools for FinFind ExplainabilityAgent.

Provides tools for generating transparent explanations
of why products are recommended.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_groq import ChatGroq
from qdrant_client.models import Filter, FieldCondition, MatchValue

from .qdrant_tools import get_qdrant_client
from ..config import get_config

logger = logging.getLogger(__name__)


# ========================================
# Input Schemas
# ========================================

class GetSimilarityScoreInput(BaseModel):
    """Input schema for similarity score retrieval."""
    
    query: str = Field(description="The original search query")
    product_id: str = Field(description="Product ID to get score for")
    include_matching_terms: bool = Field(
        default=True,
        description="Include terms that contributed to the match"
    )


class ExplainFinancialFitInput(BaseModel):
    """Input schema for financial fit explanation."""
    
    product_price: float = Field(description="Product price")
    user_budget_max: Optional[float] = Field(
        default=None,
        description="User's max budget"
    )
    user_monthly_income: Optional[float] = Field(
        default=None,
        description="User's monthly income"
    )
    affordability_score: Optional[float] = Field(
        default=None,
        description="Pre-calculated affordability score"
    )


class GenerateExplanationInput(BaseModel):
    """Input schema for explanation generation."""
    
    product: Dict = Field(description="Product data")
    user_profile: Optional[Dict] = Field(
        default=None,
        description="User profile"
    )
    query: Optional[str] = Field(
        default=None,
        description="Original search query"
    )
    similarity_score: Optional[float] = Field(
        default=None,
        description="Semantic similarity score"
    )
    affordability_score: Optional[float] = Field(
        default=None,
        description="Affordability score"
    )
    explanation_type: str = Field(
        default="detailed",
        description="Type: brief, detailed, comprehensive"
    )


# ========================================
# Get Similarity Score Tool
# ========================================

class GetSimilarityScoreTool(BaseTool):
    """
    Tool for retrieving and explaining similarity scores.
    
    Provides detailed breakdown of why a product matched
    a search query.
    """
    
    name: str = "get_similarity_score"
    description: str = """Get the semantic similarity score between a query and product.
Use this to explain why a product matched a search.
Returns:
- Similarity score (0-1)
- Matching terms/concepts
- Relevance explanation"""
    
    args_schema: Type[BaseModel] = GetSimilarityScoreInput
    
    def _run(
        self,
        query: str,
        product_id: str,
        include_matching_terms: bool = True,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Get similarity score."""
        try:
            from .qdrant_tools import embed_text
            
            client = get_qdrant_client()
            config = get_config().qdrant
            
            # Get product
            product_results = client.scroll(
                collection_name=config.products_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="original_id",
                            match=MatchValue(value=product_id)
                        )
                    ]
                ),
                limit=1,
                with_vectors=True
            )
            
            if not product_results[0]:
                return {
                    "success": False,
                    "error": f"Product {product_id} not found"
                }
            
            product_point = product_results[0][0]
            product = product_point.payload
            product_vector = product_point.vector
            
            # Generate query embedding and calculate similarity
            query_vector = embed_text(query)
            
            # Calculate cosine similarity
            import numpy as np
            query_np = np.array(query_vector)
            product_np = np.array(product_vector)
            similarity = float(np.dot(query_np, product_np) / (
                np.linalg.norm(query_np) * np.linalg.norm(product_np)
            ))
            
            # Find matching terms
            matching_terms = []
            if include_matching_terms:
                query_terms = set(query.lower().split())
                
                # Check title
                title = product.get('title', '').lower()
                title_terms = set(title.split())
                title_matches = query_terms & title_terms
                if title_matches:
                    matching_terms.extend([f"title:{t}" for t in title_matches])
                
                # Check category
                category = product.get('category', '').lower()
                if any(t in category.lower() for t in query_terms):
                    matching_terms.append(f"category:{category}")
                
                # Check features
                features = product.get('features', [])
                for feature in features[:5]:
                    feature_lower = feature.lower()
                    if any(t in feature_lower for t in query_terms):
                        matching_terms.append(f"feature:{feature[:30]}")
            
            # Determine relevance level
            if similarity >= 0.8:
                relevance = "highly_relevant"
                explanation = "Very strong semantic match with your search"
            elif similarity >= 0.6:
                relevance = "relevant"
                explanation = "Good semantic match with your search"
            elif similarity >= 0.4:
                relevance = "somewhat_relevant"
                explanation = "Moderate match - related to your search"
            else:
                relevance = "weakly_relevant"
                explanation = "Loosely related to your search"
            
            return {
                "success": True,
                "query": query,
                "product_id": product_id,
                "product_title": product.get('title'),
                "similarity_score": round(similarity, 4),
                "relevance_level": relevance,
                "explanation": explanation,
                "matching_terms": matching_terms
            }
            
        except Exception as e:
            logger.exception(f"Similarity score error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version."""
        return self._run(*args, **kwargs)


# ========================================
# Explain Financial Fit Tool
# ========================================

class ExplainFinancialFitTool(BaseTool):
    """
    Tool for explaining financial fit.
    
    Provides detailed explanation of how a product
    fits the user's financial situation.
    """
    
    name: str = "explain_financial_fit"
    description: str = """Explain how well a product fits a user's financial situation.
Use this to provide transparency about affordability.
Returns:
- Fit level (excellent, good, stretch, poor)
- Budget comparison
- Recommendations"""
    
    args_schema: Type[BaseModel] = ExplainFinancialFitInput
    
    def _run(
        self,
        product_price: float,
        user_budget_max: Optional[float] = None,
        user_monthly_income: Optional[float] = None,
        affordability_score: Optional[float] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Explain financial fit."""
        try:
            explanations = []
            fit_factors = []
            
            # Budget analysis
            if user_budget_max:
                budget_ratio = product_price / user_budget_max
                budget_pct = round(budget_ratio * 100, 1)
                
                if budget_ratio <= 0.5:
                    fit_factors.append("well_under_budget")
                    explanations.append(
                        f"This product is only {budget_pct}% of your budget - "
                        "leaving room for accessories or savings."
                    )
                elif budget_ratio <= 0.8:
                    fit_factors.append("within_budget")
                    explanations.append(
                        f"At {budget_pct}% of your budget, this fits comfortably "
                        "within your stated price range."
                    )
                elif budget_ratio <= 1.0:
                    fit_factors.append("at_budget_limit")
                    explanations.append(
                        f"At {budget_pct}% of your budget, this is at the upper "
                        "end of your price range."
                    )
                elif budget_ratio <= 1.2:
                    fit_factors.append("slightly_over_budget")
                    explanations.append(
                        f"At {budget_pct}% of your budget, this is slightly over "
                        "your limit. Consider if it's worth the stretch."
                    )
                else:
                    fit_factors.append("significantly_over_budget")
                    explanations.append(
                        f"At {budget_pct}% of your budget, this significantly "
                        "exceeds your stated limit."
                    )
            
            # Income analysis
            if user_monthly_income:
                income_ratio = product_price / user_monthly_income
                income_pct = round(income_ratio * 100, 1)
                
                if income_ratio <= 0.1:
                    fit_factors.append("low_income_impact")
                    explanations.append(
                        f"At {income_pct}% of monthly income, this has minimal "
                        "impact on your finances."
                    )
                elif income_ratio <= 0.25:
                    fit_factors.append("moderate_income_impact")
                    explanations.append(
                        f"At {income_pct}% of monthly income, this is a moderate "
                        "purchase that should be planned for."
                    )
                elif income_ratio <= 0.5:
                    fit_factors.append("significant_income_impact")
                    explanations.append(
                        f"At {income_pct}% of monthly income, this is a significant "
                        "purchase. Consider spreading the cost if possible."
                    )
                else:
                    fit_factors.append("major_income_impact")
                    explanations.append(
                        f"At {income_pct}% of monthly income, this represents a "
                        "major financial commitment."
                    )
            
            # Determine overall fit
            if affordability_score:
                if affordability_score >= 0.8:
                    fit_level = "excellent"
                    summary = "Excellent financial fit - this purchase aligns well with your finances."
                elif affordability_score >= 0.6:
                    fit_level = "good"
                    summary = "Good financial fit - a comfortable purchase within your means."
                elif affordability_score >= 0.4:
                    fit_level = "stretch"
                    summary = "Stretch fit - this will require careful budgeting."
                else:
                    fit_level = "poor"
                    summary = "Poor fit - consider alternatives or saving longer."
            else:
                # Infer from factors
                if "well_under_budget" in fit_factors or "low_income_impact" in fit_factors:
                    fit_level = "excellent"
                    summary = "Excellent financial fit based on available data."
                elif "within_budget" in fit_factors:
                    fit_level = "good"
                    summary = "Good financial fit based on available data."
                elif "at_budget_limit" in fit_factors or "slightly_over_budget" in fit_factors:
                    fit_level = "stretch"
                    summary = "This purchase may stretch your budget."
                else:
                    fit_level = "unknown"
                    summary = "Unable to determine financial fit - limited financial data available."
            
            return {
                "success": True,
                "product_price": product_price,
                "fit_level": fit_level,
                "summary": summary,
                "fit_factors": fit_factors,
                "detailed_explanations": explanations,
                "affordability_score": affordability_score
            }
            
        except Exception as e:
            logger.exception(f"Financial fit explanation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version."""
        return self._run(*args, **kwargs)


# ========================================
# Generate Explanation Tool
# ========================================

class GenerateExplanationTool(BaseTool):
    """
    Tool for generating comprehensive product explanations.
    
    Uses LLM to generate human-readable explanations
    combining all factors.
    """
    
    name: str = "generate_explanation"
    description: str = """Generate a comprehensive explanation for why a product is recommended.
Combines:
- Semantic relevance to search
- Financial fit analysis
- Feature match with preferences
- Rating and reviews summary

Creates a natural, helpful explanation for the user."""
    
    args_schema: Type[BaseModel] = GenerateExplanationInput
    
    def _run(
        self,
        product: Dict,
        user_profile: Optional[Dict] = None,
        query: Optional[str] = None,
        similarity_score: Optional[float] = None,
        affordability_score: Optional[float] = None,
        explanation_type: str = "detailed",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Generate explanation."""
        try:
            config = get_config()
            
            # Build explanation prompt
            product_info = f"""
Product: {product.get('title', 'Unknown')}
Category: {product.get('category', 'Unknown')}
Price: ${product.get('price', 'N/A')}
Rating: {product.get('rating', 'N/A')}/5
Features: {', '.join(product.get('features', [])[:5])}
"""
            
            user_info = ""
            if user_profile:
                user_info = f"""
User Profile:
- Persona: {user_profile.get('persona_type', 'Unknown')}
- Budget: ${user_profile.get('financial_context', {}).get('budget_max', 'N/A')}
- Preferred Categories: {', '.join(user_profile.get('preferences', {}).get('preferred_categories', [])[:3])}
"""
            
            scores_info = ""
            if similarity_score is not None:
                scores_info += f"- Semantic Match: {similarity_score:.2f}/1.0\n"
            if affordability_score is not None:
                scores_info += f"- Affordability: {affordability_score:.2f}/1.0\n"
            
            # Determine explanation length
            length_guidance = {
                "brief": "2-3 sentences",
                "detailed": "4-5 sentences",
                "comprehensive": "6-8 sentences with bullet points"
            }
            
            prompt = f"""Generate a helpful explanation for why this product is recommended to the user.

{product_info}
{user_info}
Search Query: {query or 'General browsing'}

Matching Scores:
{scores_info if scores_info else 'No scores available'}

Write a {length_guidance.get(explanation_type, '4-5 sentences')} explanation that:
1. Explains why this product matches what they're looking for
2. Addresses the financial fit (if budget info available)
3. Highlights key features that align with their needs
4. Is helpful and transparent, not salesy

Explanation:"""

            llm = ChatGroq(
                model=config.llm.model,
                api_key=config.llm.api_key,
                temperature=0.3
            )
            
            response = llm.invoke(prompt)
            explanation = response.content.strip()
            
            # Build structured response
            return {
                "success": True,
                "product_id": product.get('id') or product.get('original_id'),
                "product_title": product.get('title'),
                "explanation": explanation,
                "explanation_type": explanation_type,
                "factors": {
                    "similarity_score": similarity_score,
                    "affordability_score": affordability_score,
                    "rating": product.get('rating'),
                    "price": product.get('price')
                }
            }
            
        except Exception as e:
            logger.exception(f"Explanation generation error: {e}")
            
            # Fallback to template explanation
            fallback = f"This {product.get('category', 'product')} "
            if similarity_score and similarity_score > 0.6:
                fallback += "closely matches your search criteria. "
            if affordability_score and affordability_score > 0.6:
                fallback += "It fits well within your budget. "
            if product.get('rating', 0) >= 4:
                fallback += f"With a {product.get('rating')}/5 rating, it's well-reviewed by other customers."
            
            return {
                "success": False,
                "error": str(e),
                "product_id": product.get('id'),
                "explanation": fallback,
                "explanation_type": "fallback"
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version."""
        return self._run(*args, **kwargs)

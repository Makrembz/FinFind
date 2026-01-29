"""
Comprehensive Agent Testing Script for FinFind.

Tests each agent individually and identifies improvement opportunities.
"""
import asyncio
import sys
import json
from datetime import datetime
sys.path.insert(0, '.')

from app.agents.orchestrator.coordinator import AgentOrchestrator
from app.agents.config import get_config


class AgentTester:
    """Test harness for FinFind agents."""
    
    def __init__(self):
        self.orchestrator = None
        self.test_results = []
        
    def initialize(self):
        """Initialize the orchestrator and all agents."""
        print("="*70)
        print("FinFind Agent Comprehensive Test Suite")
        print("="*70)
        
        config = get_config()
        print(f"\n📋 Configuration:")
        print(f"   LLM: {config.llm.provider} / {config.llm.model}")
        print(f"   Qdrant: {config.qdrant.url[:50]}...")
        
        self.orchestrator = AgentOrchestrator()
        self.orchestrator.initialize()
        print(f"   ✅ {len(self.orchestrator._agents)} agents initialized")
        
    def record_result(self, test_name: str, passed: bool, details: dict):
        """Record a test result."""
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    async def test_search_agent(self):
        """Test the SearchAgent with various queries."""
        print("\n" + "="*70)
        print("🔍 TESTING: SearchAgent")
        print("="*70)
        
        search_agent = self.orchestrator.get_agent("SearchAgent")
        test_cases = [
            {
                "name": "Category-specific search",
                "query": "Find me a gaming laptop",
                "expected_category": "Laptops",
                "check": lambda r: any("laptop" in str(p).lower() for p in r.get('products', []))
            },
            {
                "name": "Price-constrained search",
                "query": "Show me smartphones under $300",
                "max_expected_price": 300,
                "check": lambda r: all(p.get('price', 999) <= 350 for p in r.get('products', [])[:5]) if r.get('products') else True
            },
            {
                "name": "Feature-based search",
                "query": "Wireless noise-canceling headphones",
                "expected_terms": ["wireless", "headphone", "audio"],
                "check": lambda r: len(r.get('products', [])) > 0
            },
            {
                "name": "Budget + category search",
                "query": "Best camera under $1000",
                "check": lambda r: len(r.get('products', [])) > 0
            }
        ]
        
        for tc in test_cases:
            print(f"\n   📝 Test: {tc['name']}")
            print(f"      Query: '{tc['query']}'")
            
            try:
                result = await self.orchestrator.process_request(
                    input_text=tc['query'],
                    user_id="test_user"
                )
                
                passed = tc['check'](result)
                products = result.get('products', [])
                
                print(f"      Products found: {len(products)}")
                if products:
                    print(f"      Top 3: {[p.get('name', p.get('title', 'Unknown'))[:40] for p in products[:3]]}")
                print(f"      Result: {'✅ PASSED' if passed else '❌ FAILED'}")
                
                self.record_result(f"SearchAgent - {tc['name']}", passed, {
                    "query": tc['query'],
                    "products_count": len(products),
                    "execution_time": result.get('execution_time_ms')
                })
                
            except Exception as e:
                print(f"      ❌ ERROR: {e}")
                self.record_result(f"SearchAgent - {tc['name']}", False, {"error": str(e)})
                
    async def test_recommendation_agent(self):
        """Test the RecommendationAgent."""
        print("\n" + "="*70)
        print("🎯 TESTING: RecommendationAgent")
        print("="*70)
        
        test_cases = [
            {
                "name": "Basic recommendations for user",
                "query": "Give me personalized product recommendations",
                "user_id": "user_001",
            },
            {
                "name": "Category-specific recommendations",
                "query": "Recommend me some electronics based on my preferences",
                "user_id": "user_002",
            },
            {
                "name": "Budget-aware recommendations",
                "query": "What products do you suggest for me? My budget is $500",
                "user_id": "user_003",
            }
        ]
        
        for tc in test_cases:
            print(f"\n   📝 Test: {tc['name']}")
            print(f"      User: {tc['user_id']}")
            
            try:
                result = await self.orchestrator.process_request(
                    input_text=tc['query'],
                    user_id=tc['user_id']
                )
                
                products = result.get('products', [])
                passed = result.get('success', False) and not result.get('errors')
                
                print(f"      Products recommended: {len(products)}")
                print(f"      Agents used: {result.get('agents_used', [])}")
                print(f"      Result: {'✅ PASSED' if passed else '⚠️ PARTIAL' if products else '❌ FAILED'}")
                
                self.record_result(f"RecommendationAgent - {tc['name']}", passed, {
                    "user_id": tc['user_id'],
                    "products_count": len(products),
                    "agents_used": result.get('agents_used', [])
                })
                
            except Exception as e:
                print(f"      ❌ ERROR: {e}")
                self.record_result(f"RecommendationAgent - {tc['name']}", False, {"error": str(e)})
                
    async def test_alternative_agent(self):
        """Test the AlternativeAgent."""
        print("\n" + "="*70)
        print("🔄 TESTING: AlternativeAgent")
        print("="*70)
        
        test_cases = [
            {
                "name": "Find cheaper alternatives",
                "query": "Show me cheaper alternatives to the iPhone 16 Pro",
            },
            {
                "name": "Similar products request",
                "query": "I like the Sony WH-1000XM5 but it's too expensive. What else is similar?",
            },
            {
                "name": "Budget alternative",
                "query": "I want something like a MacBook but under $800",
            }
        ]
        
        for tc in test_cases:
            print(f"\n   📝 Test: {tc['name']}")
            print(f"      Query: '{tc['query'][:60]}...'")
            
            try:
                result = await self.orchestrator.process_request(
                    input_text=tc['query'],
                    user_id="test_user"
                )
                
                products = result.get('products', [])
                output = result.get('output', '')
                passed = result.get('success', False) and (len(products) > 0 or len(output) > 50)
                
                print(f"      Alternatives found: {len(products)}")
                print(f"      Agents used: {result.get('agents_used', [])}")
                print(f"      Result: {'✅ PASSED' if passed else '❌ FAILED'}")
                
                self.record_result(f"AlternativeAgent - {tc['name']}", passed, {
                    "products_count": len(products),
                    "output_length": len(output)
                })
                
            except Exception as e:
                print(f"      ❌ ERROR: {e}")
                self.record_result(f"AlternativeAgent - {tc['name']}", False, {"error": str(e)})
                
    async def test_explainability_agent(self):
        """Test the ExplainabilityAgent."""
        print("\n" + "="*70)
        print("💡 TESTING: ExplainabilityAgent")
        print("="*70)
        
        test_cases = [
            {
                "name": "Explain recommendation reason",
                "query": "Why did you recommend the Sony WH-1000XM5 headphones to me?",
            },
            {
                "name": "Product fit explanation",
                "query": "Explain why the MacBook Air M3 would be a good choice for me",
            },
            {
                "name": "Comparison explanation",
                "query": "How come the Google Pixel 8 is recommended over the iPhone?",
            }
        ]
        
        for tc in test_cases:
            print(f"\n   📝 Test: {tc['name']}")
            print(f"      Query: '{tc['query'][:60]}...'")
            
            try:
                result = await self.orchestrator.process_request(
                    input_text=tc['query'],
                    user_id="test_user"
                )
                
                output = result.get('output', '')
                passed = result.get('success', False) and len(output) > 100
                
                print(f"      Explanation length: {len(output)} chars")
                print(f"      Agents used: {result.get('agents_used', [])}")
                if output:
                    print(f"      Preview: {output[:150]}...")
                print(f"      Result: {'✅ PASSED' if passed else '❌ FAILED'}")
                
                self.record_result(f"ExplainabilityAgent - {tc['name']}", passed, {
                    "output_length": len(output),
                    "agents_used": result.get('agents_used', [])
                })
                
            except Exception as e:
                print(f"      ❌ ERROR: {e}")
                self.record_result(f"ExplainabilityAgent - {tc['name']}", False, {"error": str(e)})
                
    async def test_workflow_orchestration(self):
        """Test multi-agent workflows."""
        print("\n" + "="*70)
        print("🔗 TESTING: Multi-Agent Workflows")
        print("="*70)
        
        test_cases = [
            {
                "name": "Search → Recommend flow",
                "query": "Find me a laptop and recommend the best one for programming",
            },
            {
                "name": "Full pipeline",
                "query": "I need headphones. Find options, recommend the best, and explain why. If too expensive, show alternatives.",
            }
        ]
        
        for tc in test_cases:
            print(f"\n   📝 Test: {tc['name']}")
            print(f"      Query: '{tc['query'][:60]}...'")
            
            try:
                result = await self.orchestrator.process_request(
                    input_text=tc['query'],
                    user_id="test_user"
                )
                
                agents_used = result.get('agents_used', [])
                passed = len(agents_used) >= 1 and result.get('success', False)
                
                print(f"      Agents used: {agents_used}")
                print(f"      Execution time: {result.get('execution_time_ms', 'N/A')}ms")
                print(f"      Result: {'✅ PASSED' if passed else '❌ FAILED'}")
                
                self.record_result(f"Workflow - {tc['name']}", passed, {
                    "agents_used": agents_used,
                    "execution_time": result.get('execution_time_ms')
                })
                
            except Exception as e:
                print(f"      ❌ ERROR: {e}")
                self.record_result(f"Workflow - {tc['name']}", False, {"error": str(e)})
                
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for r in self.test_results if r['passed'])
        total = len(self.test_results)
        
        print(f"\n   Total Tests: {total}")
        print(f"   Passed: {passed} ✅")
        print(f"   Failed: {total - passed} ❌")
        print(f"   Pass Rate: {(passed/total*100):.1f}%")
        
        if total - passed > 0:
            print("\n   Failed Tests:")
            for r in self.test_results:
                if not r['passed']:
                    print(f"      ❌ {r['test']}")
                    if 'error' in r['details']:
                        print(f"         Error: {r['details']['error'][:100]}")
        
        print("\n" + "="*70)
        
    async def run_all_tests(self):
        """Run all agent tests."""
        self.initialize()
        
        await self.test_search_agent()
        await self.test_recommendation_agent()
        await self.test_alternative_agent()
        await self.test_explainability_agent()
        await self.test_workflow_orchestration()
        
        self.print_summary()
        

async def main():
    tester = AgentTester()
    await tester.run_all_tests()
    

if __name__ == "__main__":
    asyncio.run(main())

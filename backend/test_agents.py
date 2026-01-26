"""
Test script to verify agents are working with Groq LLM.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.agents.orchestrator.coordinator import AgentOrchestrator
from app.agents.config import get_config

async def test_agent():
    print("="*60)
    print("Agent + Groq LLM Test")
    print("="*60)
    
    # Check config
    config = get_config()
    print(f"\n1. Configuration:")
    print(f"   LLM Provider: {config.llm.provider}")
    print(f"   LLM Model: {config.llm.model}")
    print(f"   Groq API Key: {'✓ Set' if config.llm.api_key else '✗ NOT SET'}")
    
    if not config.llm.api_key:
        print("\n❌ GROQ_API_KEY not set! Agents will fail.")
        return
    
    # Initialize orchestrator
    print(f"\n2. Initializing Orchestrator...")
    orch = AgentOrchestrator()
    orch.initialize()
    print(f"   ✓ {len(orch._agents)} agents initialized")
    
    for name, agent in orch._agents.items():
        print(f"   - {name}: {len(agent.get_tool_names())} tools")
    
    # Test a simple query
    print(f"\n3. Testing Agent Query (via Groq)...")
    print("   Query: 'Find me a laptop under $500'")
    
    try:
        result = await orch.process_request(
            input_text="Find me a laptop under $500",
            user_id="test_user"
        )
        
        print(f"\n4. Results:")
        print(f"   Success: {result.get('success')}")
        print(f"   Agents Used: {result.get('agents_used', [])}")
        print(f"   Execution Time: {result.get('execution_time_ms', 'N/A')}ms")
        
        if result.get('output'):
            print(f"\n5. Agent Response (first 500 chars):")
            print(f"   {result['output'][:500]}...")
        
        if result.get('products'):
            print(f"\n6. Products Found: {len(result['products'])}")
            for p in result['products'][:3]:
                print(f"   - {p.get('name', 'Unknown')[:50]}: ${p.get('price', 0)}")
        
        if result.get('errors'):
            print(f"\n⚠ Errors: {result['errors']}")
        
        print("\n" + "="*60)
        if result.get('success'):
            print("✓ AGENTS WORKING WITH GROQ LLM!")
        else:
            print("✗ AGENT TEST FAILED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())

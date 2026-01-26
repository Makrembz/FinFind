"""
FinFind Demo Runner

Quick setup script to prepare and run the demo environment.
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_banner():
    """Print the FinFind demo banner."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                    🔍 FinFind Demo Runner                            ║
║                                                                      ║
║              AI-Powered Financial Product Discovery                  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)


def check_environment():
    """Check if required environment variables are set."""
    print("📋 Checking environment...")
    
    required_vars = [
        "GROQ_API_KEY",
        "QDRANT_URL",
        "QDRANT_API_KEY"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("   Please set them in your .env file or environment")
        return False
    
    print("✅ All required environment variables set")
    return True


def check_services():
    """Check if backend and frontend are running."""
    print("\n📡 Checking services...")
    
    import urllib.request
    
    services = {
        "Backend": "http://localhost:8000/health",
        "Frontend": "http://localhost:3000"
    }
    
    all_running = True
    for name, url in services.items():
        try:
            response = urllib.request.urlopen(url, timeout=5)
            if response.status == 200:
                print(f"✅ {name} is running at {url}")
            else:
                print(f"⚠️  {name} returned status {response.status}")
                all_running = False
        except Exception as e:
            print(f"❌ {name} is not running at {url}")
            all_running = False
    
    return all_running


def load_demo_data():
    """Load demo data into the system."""
    print("\n📦 Loading demo data...")
    
    try:
        from demo.demo_data import DEMO_USERS, DEMO_PRODUCTS, export_demo_data_json
        
        # Export to JSON for reference
        export_demo_data_json(str(PROJECT_ROOT / "demo" / "demo_data.json"))
        
        print(f"✅ Demo data exported ({len(DEMO_USERS)} users, {len(DEMO_PRODUCTS)} products)")
        
        # TODO: Load data via API when services are running
        print("ℹ️  To load into running system, use the API endpoints")
        
        return True
    except Exception as e:
        print(f"❌ Failed to load demo data: {e}")
        return False


def print_demo_users():
    """Print information about demo users."""
    print("\n👥 Demo Users:")
    print("─" * 60)
    
    users = [
        ("demo_student_001", "Sarah Chen", "$300-800", "Student"),
        ("demo_professional_001", "Marcus Johnson", "$1,000-2,500", "Professional"),
        ("demo_parent_001", "Jennifer Martinez", "$200-600", "Parent"),
    ]
    
    for user_id, name, budget, persona in users:
        print(f"   {name:<20} | Budget: {budget:<12} | {persona}")
    
    print("─" * 60)


def print_demo_scenarios():
    """Print the demo scenario overview."""
    print("\n🎬 Demo Scenarios:")
    print("─" * 60)
    
    scenarios = [
        ("1", "Vague Intent Search", "Student laptop with budget constraints"),
        ("2", "Multi-Modal Search", "Image upload + voice refinement"),
        ("3", "Recommendations", "Personalized picks with explanations"),
        ("4", "Smart Alternatives", "Out-of-budget handling"),
    ]
    
    for num, name, description in scenarios:
        print(f"   Scenario {num}: {name}")
        print(f"              {description}")
        print()
    
    print("─" * 60)


def print_quick_commands():
    """Print helpful commands for the demo."""
    print("\n⚡ Quick Commands:")
    print("─" * 60)
    print("""
   Start Backend:
   cd backend && python run.py

   Start Frontend:
   cd Frontend && npm run dev

   Docker (All Services):
   docker-compose up -d

   Load Demo Data:
   python demo/demo_data.py

   Run Tests:
   cd backend && pytest tests/ -v
   cd Frontend && npm test
""")
    print("─" * 60)


def print_urls():
    """Print important URLs."""
    print("\n🔗 Important URLs:")
    print("─" * 60)
    print("""
   Local Development:
   • Frontend:  http://localhost:3000
   • Backend:   http://localhost:8000
   • API Docs:  http://localhost:8000/docs

   Production (if deployed):
   • Frontend:  https://finfind-frontend.fly.dev
   • Backend:   https://finfind-backend.fly.dev
""")
    print("─" * 60)


def run_demo_checks():
    """Run all demo preparation checks."""
    print_banner()
    
    results = {
        "environment": check_environment(),
        "demo_data": load_demo_data(),
    }
    
    # Only check services if environment is set up
    if results["environment"]:
        results["services"] = check_services()
    else:
        results["services"] = False
    
    print_demo_users()
    print_demo_scenarios()
    print_quick_commands()
    print_urls()
    
    # Summary
    print("\n📊 Summary:")
    print("─" * 60)
    
    all_good = all(results.values())
    
    for check, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check.replace('_', ' ').title()}")
    
    print("─" * 60)
    
    if all_good:
        print("\n🎉 All systems ready for demo!")
        print("   Open http://localhost:3000 to start")
    else:
        print("\n⚠️  Some checks failed. Please resolve before demo.")
    
    return all_good


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="FinFind Demo Runner")
    parser.add_argument("--check", action="store_true", help="Run demo checks only")
    parser.add_argument("--load-data", action="store_true", help="Load demo data only")
    parser.add_argument("--start", action="store_true", help="Start demo environment")
    
    args = parser.parse_args()
    
    if args.load_data:
        load_demo_data()
    elif args.start:
        print("Starting demo environment...")
        subprocess.run(["docker-compose", "up", "-d"], cwd=PROJECT_ROOT)
    else:
        # Default: run all checks
        success = run_demo_checks()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

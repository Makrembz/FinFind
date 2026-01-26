"""
FinFind Demo Data Loader

Loads seed data for hackathon demo scenarios.
Run this before the demo to ensure consistent data.
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any

# Demo Users with Specific Profiles
DEMO_USERS = [
    {
        "id": "demo_student_001",
        "name": "Sarah Chen",
        "email": "sarah.chen@demo.edu",
        "persona": "college_student",
        "profile": {
            "age_range": "18-24",
            "occupation": "Student",
            "experience_level": "beginner",
            "risk_tolerance": "low",
            "budget_range": {
                "min": 300,
                "max": 800
            },
            "goals": ["coding", "school_projects", "entertainment"],
            "preferences": {
                "value_priority": "high",
                "brand_preference": "flexible",
                "sustainability": "moderate"
            }
        },
        "financial_context": {
            "monthly_income": 1200,
            "savings_goal": 500,
            "discretionary_budget": 200,
            "financial_literacy": "basic"
        },
        "interaction_history": {
            "total_searches": 12,
            "products_viewed": 34,
            "products_saved": 5,
            "average_session_minutes": 8
        }
    },
    {
        "id": "demo_professional_001",
        "name": "Marcus Johnson",
        "email": "marcus.j@demo.tech",
        "persona": "software_engineer",
        "profile": {
            "age_range": "25-34",
            "occupation": "Software Engineer",
            "experience_level": "advanced",
            "risk_tolerance": "medium",
            "budget_range": {
                "min": 1000,
                "max": 2500
            },
            "goals": ["professional_development", "performance", "productivity"],
            "preferences": {
                "value_priority": "medium",
                "brand_preference": "quality_focused",
                "sustainability": "low"
            }
        },
        "financial_context": {
            "monthly_income": 8500,
            "savings_goal": 2000,
            "discretionary_budget": 1500,
            "financial_literacy": "advanced"
        },
        "interaction_history": {
            "total_searches": 45,
            "products_viewed": 128,
            "products_saved": 12,
            "average_session_minutes": 15
        }
    },
    {
        "id": "demo_parent_001",
        "name": "Jennifer Martinez",
        "email": "jen.martinez@demo.family",
        "persona": "budget_conscious_parent",
        "profile": {
            "age_range": "35-44",
            "occupation": "Teacher",
            "experience_level": "intermediate",
            "risk_tolerance": "low",
            "budget_range": {
                "min": 200,
                "max": 600
            },
            "goals": ["family_use", "education", "durability"],
            "preferences": {
                "value_priority": "very_high",
                "brand_preference": "reliable_brands",
                "sustainability": "high"
            }
        },
        "financial_context": {
            "monthly_income": 4200,
            "savings_goal": 800,
            "discretionary_budget": 300,
            "financial_literacy": "intermediate"
        },
        "interaction_history": {
            "total_searches": 28,
            "products_viewed": 76,
            "products_saved": 8,
            "average_session_minutes": 12
        }
    }
]

# Demo Products Catalog
DEMO_PRODUCTS = [
    # Budget Student Laptops
    {
        "id": "laptop_budget_001",
        "name": "ASUS VivoBook 15",
        "category": "laptops",
        "subcategory": "budget",
        "price": 449,
        "description": "Reliable everyday laptop perfect for students and light development work.",
        "features": {
            "processor": "AMD Ryzen 5 5500U",
            "ram": "8GB DDR4",
            "storage": "256GB SSD",
            "display": "15.6\" FHD",
            "battery": "8 hours",
            "weight": "3.97 lbs"
        },
        "ratings": {
            "overall": 4.3,
            "value": 4.6,
            "performance": 3.9,
            "build_quality": 4.1
        },
        "tags": ["student", "budget", "coding", "portable"],
        "suitable_for": ["beginners", "students", "light_coding"],
        "in_stock": True
    },
    {
        "id": "laptop_budget_002",
        "name": "Acer Aspire 5",
        "category": "laptops",
        "subcategory": "budget",
        "price": 549,
        "description": "Great value laptop with solid specs for programming and everyday tasks.",
        "features": {
            "processor": "Intel Core i5-1235U",
            "ram": "16GB DDR4",
            "storage": "512GB SSD",
            "display": "15.6\" FHD IPS",
            "battery": "10 hours",
            "weight": "3.88 lbs"
        },
        "ratings": {
            "overall": 4.4,
            "value": 4.7,
            "performance": 4.2,
            "build_quality": 4.0
        },
        "tags": ["student", "budget", "coding", "16gb_ram"],
        "suitable_for": ["students", "coding", "multitasking"],
        "in_stock": True
    },
    {
        "id": "laptop_budget_003",
        "name": "Lenovo IdeaPad 3",
        "category": "laptops",
        "subcategory": "budget",
        "price": 499,
        "description": "Balanced laptop offering good performance at an affordable price.",
        "features": {
            "processor": "AMD Ryzen 5 7530U",
            "ram": "8GB DDR4",
            "storage": "512GB SSD",
            "display": "15.6\" FHD",
            "battery": "9 hours",
            "weight": "4.19 lbs"
        },
        "ratings": {
            "overall": 4.2,
            "value": 4.5,
            "performance": 4.0,
            "build_quality": 3.9
        },
        "tags": ["student", "budget", "reliable"],
        "suitable_for": ["students", "general_use", "coding"],
        "in_stock": True
    },
    {
        "id": "laptop_midrange_001",
        "name": "HP Pavilion 15",
        "category": "laptops",
        "subcategory": "midrange",
        "price": 699,
        "description": "Solid mid-range laptop for serious coding and development work.",
        "features": {
            "processor": "Intel Core i7-1255U",
            "ram": "16GB DDR4",
            "storage": "512GB SSD",
            "display": "15.6\" FHD IPS",
            "battery": "8.5 hours",
            "weight": "4.03 lbs"
        },
        "ratings": {
            "overall": 4.5,
            "value": 4.4,
            "performance": 4.5,
            "build_quality": 4.3
        },
        "tags": ["development", "coding", "performance"],
        "suitable_for": ["developers", "students", "professionals"],
        "in_stock": True
    },
    {
        "id": "laptop_midrange_002",
        "name": "ASUS ZenBook 14",
        "category": "laptops",
        "subcategory": "midrange",
        "price": 749,
        "description": "Premium ultrabook design with excellent build quality and performance.",
        "features": {
            "processor": "AMD Ryzen 7 7730U",
            "ram": "16GB LPDDR5",
            "storage": "512GB SSD",
            "display": "14\" 2.8K OLED",
            "battery": "12 hours",
            "weight": "2.87 lbs"
        },
        "ratings": {
            "overall": 4.6,
            "value": 4.3,
            "performance": 4.5,
            "build_quality": 4.8
        },
        "tags": ["ultrabook", "premium", "portable", "oled"],
        "suitable_for": ["professionals", "creators", "portable_users"],
        "in_stock": True
    },
    # Video Editing Capable (Budget-ish)
    {
        "id": "laptop_creator_001",
        "name": "ASUS VivoBook Pro 15 OLED",
        "category": "laptops",
        "subcategory": "creator",
        "price": 799,
        "description": "Creator laptop with OLED display and dedicated graphics.",
        "features": {
            "processor": "Intel Core i5-12500H",
            "ram": "16GB DDR5",
            "storage": "512GB SSD",
            "gpu": "NVIDIA RTX 3050",
            "display": "15.6\" OLED",
            "battery": "6 hours",
            "weight": "4.19 lbs"
        },
        "ratings": {
            "overall": 4.4,
            "value": 4.5,
            "performance": 4.3,
            "build_quality": 4.2
        },
        "tags": ["creator", "video_editing", "oled", "gpu"],
        "suitable_for": ["video_editors", "content_creators", "students"],
        "video_editing_score": 7.5,
        "in_stock": True
    },
    {
        "id": "laptop_creator_002",
        "name": "Lenovo IdeaPad Gaming 3",
        "category": "laptops",
        "subcategory": "gaming",
        "price": 699,
        "description": "Budget gaming laptop that doubles as a capable video editing machine.",
        "features": {
            "processor": "AMD Ryzen 5 6600H",
            "ram": "16GB DDR5",
            "storage": "512GB SSD",
            "gpu": "NVIDIA RTX 3050",
            "display": "15.6\" FHD 120Hz",
            "battery": "5 hours",
            "weight": "4.96 lbs"
        },
        "ratings": {
            "overall": 4.3,
            "value": 4.6,
            "performance": 4.4,
            "build_quality": 4.0
        },
        "tags": ["gaming", "video_editing", "gpu", "budget"],
        "suitable_for": ["gamers", "video_editors", "students"],
        "video_editing_score": 7.2,
        "in_stock": True
    },
    # Professional Laptops
    {
        "id": "laptop_pro_001",
        "name": "Dell XPS 15 Developer Edition",
        "category": "laptops",
        "subcategory": "professional",
        "price": 1849,
        "description": "Professional-grade developer laptop with Ubuntu pre-installed.",
        "features": {
            "processor": "Intel Core i7-13700H",
            "ram": "32GB DDR5",
            "storage": "1TB SSD",
            "gpu": "Intel Arc A370M",
            "display": "15.6\" 3.5K OLED",
            "battery": "13 hours",
            "weight": "4.22 lbs"
        },
        "ratings": {
            "overall": 4.8,
            "value": 4.2,
            "performance": 4.9,
            "build_quality": 4.9
        },
        "tags": ["professional", "developer", "linux", "premium"],
        "suitable_for": ["professional_developers", "linux_users", "power_users"],
        "in_stock": True
    },
    {
        "id": "laptop_pro_002",
        "name": "ThinkPad X1 Carbon Gen 11",
        "category": "laptops",
        "subcategory": "professional",
        "price": 1649,
        "description": "Legendary business laptop with excellent keyboard and reliability.",
        "features": {
            "processor": "Intel Core i7-1365U",
            "ram": "32GB LPDDR5",
            "storage": "512GB SSD",
            "display": "14\" 2.8K OLED",
            "battery": "15 hours",
            "weight": "2.48 lbs"
        },
        "ratings": {
            "overall": 4.7,
            "value": 4.0,
            "performance": 4.6,
            "build_quality": 4.9
        },
        "tags": ["business", "professional", "reliable", "lightweight"],
        "suitable_for": ["business_professionals", "developers", "travelers"],
        "in_stock": True
    },
    {
        "id": "laptop_pro_003",
        "name": "MacBook Pro 14\" M3",
        "category": "laptops",
        "subcategory": "professional",
        "price": 1999,
        "description": "Apple's professional laptop with incredible performance and battery life.",
        "features": {
            "processor": "Apple M3 Pro",
            "ram": "18GB Unified",
            "storage": "512GB SSD",
            "display": "14.2\" Liquid Retina XDR",
            "battery": "17 hours",
            "weight": "3.5 lbs"
        },
        "ratings": {
            "overall": 4.9,
            "value": 3.8,
            "performance": 4.9,
            "build_quality": 5.0
        },
        "tags": ["apple", "professional", "premium", "macos"],
        "suitable_for": ["developers", "creatives", "professionals"],
        "in_stock": True
    },
    # Premium/Out of Budget (for Scenario 4)
    {
        "id": "laptop_premium_001",
        "name": "MacBook Pro 16\" M3 Max",
        "category": "laptops",
        "subcategory": "premium",
        "price": 2499,
        "description": "The ultimate creative professional laptop with unmatched performance.",
        "features": {
            "processor": "Apple M3 Max",
            "ram": "36GB Unified",
            "storage": "512GB SSD",
            "display": "16.2\" Liquid Retina XDR",
            "battery": "22 hours",
            "weight": "4.7 lbs"
        },
        "ratings": {
            "overall": 4.9,
            "value": 3.5,
            "performance": 5.0,
            "build_quality": 5.0
        },
        "tags": ["premium", "professional", "video_editing", "creative"],
        "suitable_for": ["video_professionals", "3d_artists", "music_producers"],
        "video_editing_score": 9.5,
        "in_stock": True
    }
]

# Demo Search Queries with Expected Behavior
DEMO_QUERIES = [
    {
        "query": "I need a laptop for coding but I'm on a student budget",
        "expected_user": "demo_student_001",
        "expected_behavior": "Filter to budget range, prioritize coding features",
        "expected_results": ["laptop_budget_002", "laptop_midrange_001", "laptop_budget_003"]
    },
    {
        "query": "MacBook Pro 16 inch for video editing",
        "expected_user": "demo_student_001",
        "expected_behavior": "Detect budget constraint, suggest alternatives",
        "expected_results": ["laptop_creator_001", "laptop_creator_002"],
        "constraint_violation": True
    },
    {
        "query": "best developer laptop with Linux support",
        "expected_user": "demo_professional_001",
        "expected_behavior": "Match professional budget, prioritize dev features",
        "expected_results": ["laptop_pro_001", "laptop_pro_002"]
    }
]

# Demo Interactions for Learning System
DEMO_INTERACTIONS = [
    {
        "user_id": "demo_student_001",
        "interactions": [
            {"type": "search", "query": "cheap laptop for school", "timestamp": "2026-01-20T10:00:00Z"},
            {"type": "view", "product_id": "laptop_budget_001", "duration_seconds": 45},
            {"type": "view", "product_id": "laptop_budget_002", "duration_seconds": 120},
            {"type": "save", "product_id": "laptop_budget_002"},
            {"type": "feedback", "product_id": "laptop_budget_002", "rating": 5, "helpful": True}
        ]
    },
    {
        "user_id": "demo_professional_001",
        "interactions": [
            {"type": "search", "query": "professional developer laptop", "timestamp": "2026-01-22T14:00:00Z"},
            {"type": "view", "product_id": "laptop_pro_001", "duration_seconds": 180},
            {"type": "view", "product_id": "laptop_pro_002", "duration_seconds": 90},
            {"type": "compare", "products": ["laptop_pro_001", "laptop_pro_002"]},
            {"type": "feedback", "product_id": "laptop_pro_001", "rating": 5, "helpful": True}
        ]
    }
]


async def load_demo_users(api_client) -> None:
    """Load demo users into the system."""
    print("Loading demo users...")
    for user in DEMO_USERS:
        try:
            await api_client.post("/users", json=user)
            print(f"  ✓ Loaded user: {user['name']} ({user['id']})")
        except Exception as e:
            print(f"  ✗ Failed to load {user['id']}: {e}")


async def load_demo_products(api_client) -> None:
    """Load demo products into the system."""
    print("Loading demo products...")
    for product in DEMO_PRODUCTS:
        try:
            await api_client.post("/products", json=product)
            print(f"  ✓ Loaded product: {product['name']}")
        except Exception as e:
            print(f"  ✗ Failed to load {product['id']}: {e}")


async def load_demo_interactions(api_client) -> None:
    """Load demo interactions for learning system."""
    print("Loading demo interactions...")
    for user_interactions in DEMO_INTERACTIONS:
        user_id = user_interactions["user_id"]
        for interaction in user_interactions["interactions"]:
            try:
                await api_client.post(
                    f"/learning/interaction",
                    json={"user_id": user_id, **interaction}
                )
            except Exception as e:
                print(f"  ✗ Failed to load interaction: {e}")
        print(f"  ✓ Loaded interactions for: {user_id}")


async def verify_demo_data(api_client) -> bool:
    """Verify demo data is loaded correctly."""
    print("\nVerifying demo data...")
    
    # Check users
    for user in DEMO_USERS:
        try:
            response = await api_client.get(f"/users/{user['id']}/profile")
            if response.status_code == 200:
                print(f"  ✓ User verified: {user['name']}")
            else:
                print(f"  ✗ User missing: {user['id']}")
                return False
        except Exception as e:
            print(f"  ✗ Error checking user: {e}")
            return False
    
    # Check products
    response = await api_client.get("/products", params={"limit": 100})
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Products loaded: {len(data.get('products', []))}")
    else:
        print("  ✗ Failed to verify products")
        return False
    
    print("\n✅ All demo data verified!")
    return True


def export_demo_data_json(output_path: str = "demo/demo_data.json") -> None:
    """Export demo data to JSON file for reference."""
    demo_data = {
        "users": DEMO_USERS,
        "products": DEMO_PRODUCTS,
        "queries": DEMO_QUERIES,
        "interactions": DEMO_INTERACTIONS,
        "generated_at": datetime.utcnow().isoformat()
    }
    
    with open(output_path, "w") as f:
        json.dump(demo_data, f, indent=2)
    
    print(f"Demo data exported to: {output_path}")


if __name__ == "__main__":
    # Export demo data for reference
    export_demo_data_json()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                   FinFind Demo Data Ready                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Demo Users:                                                 ║
║  • demo_student_001 (Sarah Chen) - Budget: $300-800          ║
║  • demo_professional_001 (Marcus Johnson) - Budget: $1k-2.5k ║
║  • demo_parent_001 (Jennifer Martinez) - Budget: $200-600    ║
║                                                              ║
║  Demo Products: 11 laptops across categories                 ║
║  • Budget: 3 products ($449-$549)                            ║
║  • Midrange: 2 products ($699-$749)                          ║
║  • Creator: 2 products ($699-$799)                           ║
║  • Professional: 3 products ($1,649-$1,999)                  ║
║  • Premium: 1 product ($2,499)                               ║
║                                                              ║
║  To load into running system:                                ║
║  python -c "from demo.demo_data import *; asyncio.run(...)"  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

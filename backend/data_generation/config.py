"""
Configuration for FinFind synthetic data generation.

This module contains all configurable parameters for generating realistic
e-commerce data including products, users, reviews, and interactions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from pathlib import Path


@dataclass
class GenerationConfig:
    """Master configuration for data generation."""
    
    # === Volume Settings ===
    num_products: int = 500
    num_users: int = 100
    num_reviews: int = 1200
    num_interactions: int = 2500
    
    # === Randomization ===
    random_seed: int = 42  # For reproducibility
    
    # === Output Settings ===
    output_dir: Path = field(default_factory=lambda: Path("output"))
    
    # === Embedding Settings ===
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_batch_size: int = 64
    text_embedding_dim: int = 384
    generate_embeddings: bool = True
    
    # === Category Distribution (weights must sum to 1.0) ===
    category_weights: Dict[str, float] = field(default_factory=lambda: {
        "Electronics": 0.25,
        "Fashion": 0.20,
        "Home & Kitchen": 0.15,
        "Books & Media": 0.12,
        "Sports & Fitness": 0.13,
        "Beauty & Personal Care": 0.15
    })
    
    # === Price Distributions (per category) ===
    # Format: {"min": float, "max": float, "mean": float, "std": float}
    price_ranges: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "Electronics": {"min": 15, "max": 3000, "mean": 450, "std": 500},
        "Fashion": {"min": 10, "max": 500, "mean": 75, "std": 70},
        "Home & Kitchen": {"min": 8, "max": 1500, "mean": 120, "std": 150},
        "Books & Media": {"min": 5, "max": 100, "mean": 20, "std": 15},
        "Sports & Fitness": {"min": 10, "max": 800, "mean": 100, "std": 120},
        "Beauty & Personal Care": {"min": 5, "max": 200, "mean": 35, "std": 30}
    })
    
    # === Review Distributions ===
    # Rating distribution: probability of each star rating [1, 2, 3, 4, 5]
    rating_distribution: List[float] = field(default_factory=lambda: [0.03, 0.07, 0.20, 0.35, 0.35])
    
    # Sentiment score ranges per rating
    sentiment_ranges: Dict[int, Tuple[float, float]] = field(default_factory=lambda: {
        1: (-1.0, -0.6),
        2: (-0.6, -0.2),
        3: (-0.2, 0.2),
        4: (0.2, 0.6),
        5: (0.6, 1.0)
    })
    
    # Verified purchase probability
    verified_purchase_prob: float = 0.80
    
    # === Interaction Patterns ===
    interaction_weights: Dict[str, float] = field(default_factory=lambda: {
        "search": 0.30,
        "view": 0.35,
        "click": 0.15,
        "add_to_cart": 0.10,
        "purchase": 0.05,
        "wishlist": 0.05
    })
    
    # === User Financial Distributions ===
    budget_personas: Dict[str, Dict] = field(default_factory=lambda: {
        "tight_budget": {"weight": 0.25, "budget_range": (50, 200), "monthly": (100, 300)},
        "moderate": {"weight": 0.40, "budget_range": (200, 800), "monthly": (300, 800)},
        "comfortable": {"weight": 0.25, "budget_range": (800, 2000), "monthly": (800, 2000)},
        "luxury": {"weight": 0.10, "budget_range": (2000, 10000), "monthly": (2000, 5000)}
    })
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Ensure category weights sum to 1.0
        total_weight = sum(self.category_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            # Normalize weights
            self.category_weights = {
                k: v / total_weight for k, v in self.category_weights.items()
            }
        
        # Ensure rating distribution sums to 1.0
        total_rating = sum(self.rating_distribution)
        if abs(total_rating - 1.0) > 0.01:
            self.rating_distribution = [r / total_rating for r in self.rating_distribution]
        
        # Create output directory
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# === Category Hierarchies ===
CATEGORY_HIERARCHY: Dict[str, Dict[str, List[str]]] = {
    "Electronics": {
        "subcategories": [
            "Laptops", "Smartphones", "Tablets", "Headphones", "Speakers",
            "Cameras", "Smartwatches", "Gaming", "Computer Accessories", "TV & Home Theater"
        ],
        "attributes": ["brand", "model", "color", "storage", "screen_size", "battery_life", "connectivity"]
    },
    "Fashion": {
        "subcategories": [
            "Men's Clothing", "Women's Clothing", "Shoes", "Bags & Accessories",
            "Jewelry", "Watches", "Sportswear", "Outerwear"
        ],
        "attributes": ["brand", "color", "size", "material", "style", "season", "fit"]
    },
    "Home & Kitchen": {
        "subcategories": [
            "Furniture", "Kitchen Appliances", "Cookware", "Bedding",
            "Home Decor", "Storage & Organization", "Lighting", "Garden"
        ],
        "attributes": ["brand", "color", "material", "dimensions", "style", "room_type"]
    },
    "Books & Media": {
        "subcategories": [
            "Fiction", "Non-Fiction", "Technical & Programming", "Self-Help",
            "Children's Books", "Audiobooks", "E-Books", "Magazines"
        ],
        "attributes": ["author", "publisher", "pages", "format", "language", "genre"]
    },
    "Sports & Fitness": {
        "subcategories": [
            "Exercise Equipment", "Outdoor Recreation", "Team Sports", "Fitness Accessories",
            "Camping & Hiking", "Cycling", "Water Sports", "Yoga & Pilates"
        ],
        "attributes": ["brand", "sport_type", "skill_level", "material", "weight", "size"]
    },
    "Beauty & Personal Care": {
        "subcategories": [
            "Skincare", "Makeup", "Hair Care", "Fragrances",
            "Personal Hygiene", "Men's Grooming", "Nail Care", "Tools & Accessories"
        ],
        "attributes": ["brand", "skin_type", "ingredients", "scent", "volume", "gender"]
    }
}


# === Brand Data ===
BRANDS_BY_CATEGORY: Dict[str, Dict[str, List[str]]] = {
    "Electronics": {
        "premium": ["Apple", "Sony", "Samsung", "Bose", "Microsoft", "Dell", "LG"],
        "mid_tier": ["Asus", "Lenovo", "HP", "Acer", "JBL", "Logitech", "Canon", "Nikon"],
        "budget": ["Anker", "Xiaomi", "Realme", "TCL", "Hisense", "Onn", "Amazon Basics"]
    },
    "Fashion": {
        "premium": ["Nike", "Adidas", "Levi's", "Ralph Lauren", "Calvin Klein", "Tommy Hilfiger", "Coach"],
        "mid_tier": ["H&M", "Zara", "Gap", "Uniqlo", "Mango", "Banana Republic", "J.Crew"],
        "budget": ["Shein", "Old Navy", "Forever 21", "Primark", "Target Essentials", "Amazon Essentials"]
    },
    "Home & Kitchen": {
        "premium": ["KitchenAid", "Dyson", "Cuisinart", "Le Creuset", "Williams Sonoma", "West Elm"],
        "mid_tier": ["Ninja", "Hamilton Beach", "OXO", "Threshold", "Better Homes", "Rubbermaid"],
        "budget": ["Mainstays", "Room Essentials", "Amazon Basics", "Great Value", "Utopia"]
    },
    "Books & Media": {
        "premium": ["Penguin Random House", "HarperCollins", "Simon & Schuster", "O'Reilly Media"],
        "mid_tier": ["Scholastic", "Wiley", "McGraw Hill", "Hachette", "Macmillan"],
        "budget": ["Dover Publications", "CreateSpace", "Independently Published", "Public Domain"]
    },
    "Sports & Fitness": {
        "premium": ["Nike", "Adidas", "Under Armour", "Lululemon", "Peloton", "Garmin", "The North Face"],
        "mid_tier": ["Reebok", "Puma", "New Balance", "Fitbit", "Coleman", "Schwinn"],
        "budget": ["Champion", "Russell Athletic", "Ozark Trail", "CAP Barbell", "Amazon Basics"]
    },
    "Beauty & Personal Care": {
        "premium": ["Estée Lauder", "Clinique", "La Mer", "Chanel", "Dior", "Tom Ford", "SK-II"],
        "mid_tier": ["L'Oréal", "Neutrogena", "Olay", "Dove", "Nivea", "Garnier", "Maybelline"],
        "budget": ["CeraVe", "The Ordinary", "e.l.f.", "NYX", "Cetaphil", "Suave", "St. Ives"]
    }
}


# === Product Templates ===
# These are combined with Faker data to create realistic product titles and descriptions

PRODUCT_TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    "Electronics": {
        "Laptops": {
            "title_patterns": [
                "{brand} {model} {screen_size}\" Laptop - {processor}, {ram}GB RAM, {storage}GB SSD",
                "{brand} {model} Gaming Laptop - {screen_size}\" {display_type}, {processor}",
                "{brand} {model} Business Laptop - {screen_size}\" FHD, {processor}, {storage}GB"
            ],
            "features": [
                "Fast {processor} processor for seamless multitasking",
                "{ram}GB DDR5 RAM for smooth performance",
                "{storage}GB NVMe SSD for quick boot and load times",
                "{screen_size}\" {display_type} display with vivid colors",
                "Up to {battery_life} hours of battery life",
                "Backlit keyboard for comfortable typing",
                "Built-in HD webcam for video calls",
                "Wi-Fi 6E and Bluetooth 5.3 connectivity"
            ]
        },
        "Smartphones": {
            "title_patterns": [
                "{brand} {model} - {storage}GB, {color}",
                "{brand} {model} 5G Smartphone - {screen_size}\" {display_type}, {storage}GB",
                "{brand} {model} Pro - {camera}MP Camera, {storage}GB, {color}"
            ],
            "features": [
                "Stunning {screen_size}\" {display_type} display",
                "Powerful {processor} chip for flagship performance",
                "{camera}MP advanced camera system",
                "{storage}GB internal storage",
                "All-day {battery_life}mAh battery",
                "5G connectivity for ultra-fast downloads",
                "Water and dust resistant design"
            ]
        },
        "Headphones": {
            "title_patterns": [
                "{brand} {model} Wireless Noise-Canceling Headphones - {color}",
                "{brand} {model} True Wireless Earbuds - {battery_life}h Battery",
                "{brand} {model} Over-Ear Headphones - Hi-Res Audio, {color}"
            ],
            "features": [
                "Industry-leading active noise cancellation",
                "Premium Hi-Res audio with deep bass",
                "Up to {battery_life} hours of listening time",
                "Comfortable over-ear design",
                "Touch controls and voice assistant support",
                "Quick charge - 10 min charge for 5 hours playback",
                "Multipoint connection for seamless device switching"
            ]
        }
    },
    "Fashion": {
        "Men's Clothing": {
            "title_patterns": [
                "{brand} Men's {style} {item_type} - {color}, {material}",
                "{brand} {item_type} for Men - {fit} Fit, {color}",
                "{brand} Men's Classic {item_type} - {material}, {size_range}"
            ],
            "features": [
                "Premium {material} fabric for comfort and durability",
                "{fit} fit for a flattering silhouette",
                "Available in multiple colors and sizes",
                "Machine washable for easy care",
                "Perfect for casual or business casual occasions",
                "Breathable fabric keeps you comfortable all day"
            ]
        },
        "Shoes": {
            "title_patterns": [
                "{brand} Men's {style} {shoe_type} - {color}",
                "{brand} Women's {style} {shoe_type} - {color}, Size {size}",
                "{brand} Unisex {shoe_type} - {material}, {color}"
            ],
            "features": [
                "Cushioned insole for all-day comfort",
                "Durable {material} construction",
                "Non-slip outsole for traction",
                "Breathable design keeps feet cool",
                "Stylish {style} design for any occasion",
                "True to size fit"
            ]
        }
    },
    "Home & Kitchen": {
        "Kitchen Appliances": {
            "title_patterns": [
                "{brand} {capacity} {appliance_type} - {color}, {wattage}W",
                "{brand} {appliance_type} with {feature} - Stainless Steel",
                "{brand} Smart {appliance_type} - {capacity}, WiFi Enabled"
            ],
            "features": [
                "Powerful {wattage}W motor for efficient performance",
                "{capacity} capacity perfect for families",
                "Easy-to-clean stainless steel construction",
                "Multiple preset programs for convenience",
                "Dishwasher-safe removable parts",
                "Compact design fits any kitchen counter"
            ]
        },
        "Furniture": {
            "title_patterns": [
                "{brand} {style} {furniture_type} - {material}, {color}",
                "{brand} {furniture_type} with Storage - {dimensions}",
                "{brand} Modern {furniture_type} - {material} Frame, {color}"
            ],
            "features": [
                "Solid {material} construction for durability",
                "Easy assembly with included hardware",
                "Modern {style} design complements any decor",
                "Dimensions: {dimensions}",
                "Weight capacity: {weight_capacity} lbs",
                "1-year manufacturer warranty"
            ]
        }
    },
    "Books & Media": {
        "Fiction": {
            "title_patterns": [
                "{title} by {author} - {format} Edition",
                "{title}: A Novel by {author}",
                "The {adjective} {noun}: {subtitle} by {author}"
            ],
            "features": [
                "Bestselling {genre} novel",
                "{pages} pages of captivating storytelling",
                "Available in paperback, hardcover, and e-book",
                "Winner of {award}",
                "Over {copies_sold} copies sold worldwide",
                "Now a major motion picture"
            ]
        },
        "Technical & Programming": {
            "title_patterns": [
                "{title}: {subtitle} - {edition} Edition",
                "Learning {technology}: A Practical Guide",
                "{technology} {level}: From {start} to {end}"
            ],
            "features": [
                "Comprehensive coverage of {technology}",
                "Hands-on examples and exercises",
                "Written by industry experts",
                "Includes downloadable code samples",
                "Perfect for {level} developers",
                "Updated for the latest version"
            ]
        }
    },
    "Sports & Fitness": {
        "Exercise Equipment": {
            "title_patterns": [
                "{brand} {equipment_type} - {weight}lb, {color}",
                "{brand} Adjustable {equipment_type} - {weight_range}lb Range",
                "{brand} Home Gym {equipment_type} - Commercial Grade"
            ],
            "features": [
                "Heavy-duty steel construction",
                "Non-slip grip for safety",
                "Compact design for home gyms",
                "Adjustable resistance from {weight_range}",
                "Easy assembly required",
                "Includes workout guide"
            ]
        },
        "Outdoor Recreation": {
            "title_patterns": [
                "{brand} {item_type} - {capacity} Person, {color}",
                "{brand} {item_type} for {activity} - Lightweight, Durable",
                "{brand} Professional {item_type} - {material}"
            ],
            "features": [
                "Lightweight yet durable {material} construction",
                "Weather-resistant design",
                "Easy setup in minutes",
                "Compact for portability",
                "Ideal for {activity}",
                "Includes carrying bag"
            ]
        }
    },
    "Beauty & Personal Care": {
        "Skincare": {
            "title_patterns": [
                "{brand} {product_type} - {volume}oz, {skin_type} Skin",
                "{brand} {ingredient} {product_type} for {concern}",
                "{brand} Daily {product_type} - {benefit}, {volume}ml"
            ],
            "features": [
                "Formulated with {ingredient} for visible results",
                "Suitable for {skin_type} skin types",
                "Dermatologist tested and approved",
                "Paraben-free and cruelty-free",
                "Absorbs quickly without greasy residue",
                "Use daily for best results"
            ]
        },
        "Makeup": {
            "title_patterns": [
                "{brand} {product_type} - {shade}, {finish} Finish",
                "{brand} Long-Lasting {product_type} - {color}",
                "{brand} {product_type} Palette - {num_shades} Shades"
            ],
            "features": [
                "Long-lasting {duration}-hour wear",
                "Highly pigmented for vibrant color",
                "{finish} finish for a flawless look",
                "Easy to blend and build",
                "Cruelty-free and vegan",
                "Suitable for all skin tones"
            ]
        }
    }
}


# === Review Templates ===
REVIEW_TEMPLATES: Dict[int, Dict[str, List[str]]] = {
    5: {
        "openers": [
            "Absolutely love this {product_type}!",
            "Best {product_type} I've ever purchased!",
            "Exceeded all my expectations!",
            "This is exactly what I was looking for!",
            "Five stars isn't enough for this {product_type}!",
            "Amazing quality and value!",
            "Couldn't be happier with my purchase!",
            "This {product_type} is a game changer!"
        ],
        "body": [
            "The {feature1} is incredible and the {feature2} exceeded my expectations.",
            "I've been using this for {duration} and it still works perfectly.",
            "The quality is outstanding - you can tell this is a premium product.",
            "Setup was super easy and it worked right out of the box.",
            "I've recommended this to all my friends and family.",
            "The {feature1} alone makes this worth every penny."
        ],
        "closers": [
            "Highly recommend to everyone!",
            "Would buy again in a heartbeat.",
            "Worth every penny!",
            "Don't hesitate, just buy it!",
            "You won't regret this purchase!",
            "10/10 would recommend!"
        ]
    },
    4: {
        "openers": [
            "Really happy with this purchase.",
            "Great {product_type} overall.",
            "Very satisfied with my {product_type}.",
            "Solid product with minor flaws.",
            "Good value for the price.",
            "Works well for what I need."
        ],
        "body": [
            "The {feature1} works great, though the {feature2} could be slightly better.",
            "For the price point, this delivers excellent value.",
            "I've had this for {duration} and it's holding up well.",
            "Does exactly what it's supposed to do.",
            "Quality is good - not perfect but definitely worth it."
        ],
        "closers": [
            "Would still recommend.",
            "Good value for money.",
            "Happy with my purchase.",
            "Would consider buying again.",
            "Minor issues but overall satisfied."
        ]
    },
    3: {
        "openers": [
            "It's okay, nothing special.",
            "Decent {product_type} for the price.",
            "Mixed feelings about this one.",
            "Average product, does the job.",
            "Not bad, but not great either."
        ],
        "body": [
            "The {feature1} is fine but the {feature2} disappointed me.",
            "It works, but I expected more for this price.",
            "Some features are good, others not so much.",
            "Quality is acceptable but nothing to write home about.",
            "Had some issues initially but it's working now."
        ],
        "closers": [
            "Consider other options before buying.",
            "It's fine if you're on a budget.",
            "Might look for alternatives next time.",
            "Does the job, I guess.",
            "Average overall."
        ]
    },
    2: {
        "openers": [
            "Disappointed with this purchase.",
            "Expected more from this {product_type}.",
            "Not worth the price.",
            "Had issues from the start.",
            "Below my expectations."
        ],
        "body": [
            "The {feature1} barely works and the {feature2} is terrible.",
            "Quality feels cheap and flimsy.",
            "Stopped working properly after {duration}.",
            "Customer service was unhelpful when I had issues.",
            "Does not match the product description."
        ],
        "closers": [
            "Would not recommend.",
            "Save your money for something better.",
            "Looking to return this.",
            "Wish I had read more reviews first.",
            "Can't recommend this to anyone."
        ]
    },
    1: {
        "openers": [
            "Terrible product, avoid at all costs!",
            "Complete waste of money.",
            "Worst {product_type} I've ever bought.",
            "Do NOT buy this!",
            "Absolutely horrible."
        ],
        "body": [
            "Broke after {duration} of use. Total junk.",
            "Nothing about this product works as advertised.",
            "Feels like a cheap knockoff.",
            "Arrived damaged and customer service was useless.",
            "This is either fake or defective."
        ],
        "closers": [
            "Stay far away from this product.",
            "Returning immediately.",
            "One star is too generous.",
            "Biggest regret purchase ever.",
            "Save yourself the headache."
        ]
    }
}


# === User Persona Definitions ===
USER_PERSONAS: Dict[str, Dict[str, Any]] = {
    "student": {
        "weight": 0.20,
        "age_ranges": ["18-24", "25-34"],
        "age_weights": [0.7, 0.3],
        "budget_range": (50, 300),
        "monthly_discretionary": (100, 400),
        "affordability_score_range": (0.2, 0.5),
        "risk_tolerance_weights": {"low": 0.3, "moderate": 0.5, "high": 0.2},
        "spending_style_weights": {"frugal": 0.6, "balanced": 0.35, "impulsive": 0.05},
        "payment_methods": {
            "primary": ["debit_card", "cash"],
            "secondary": ["credit_card", "bnpl"]
        },
        "category_affinities": {
            "Electronics": 0.85,
            "Books & Media": 0.80,
            "Fashion": 0.60,
            "Sports & Fitness": 0.50,
            "Home & Kitchen": 0.30,
            "Beauty & Personal Care": 0.45
        },
        "financial_goals": [
            "save_for_tuition", "build_emergency_fund", "pay_off_student_loans",
            "save_for_graduation_trip", "afford_textbooks", "budget_for_rent"
        ],
        "deal_seeker_prob": 0.85,
        "reviews_importance_range": (0.6, 0.9),
        "brand_loyalty_range": (0.2, 0.5)
    },
    "young_professional": {
        "weight": 0.25,
        "age_ranges": ["25-34", "35-44"],
        "age_weights": [0.7, 0.3],
        "budget_range": (200, 800),
        "monthly_discretionary": (500, 1500),
        "affordability_score_range": (0.4, 0.7),
        "risk_tolerance_weights": {"low": 0.2, "moderate": 0.5, "high": 0.3},
        "spending_style_weights": {"frugal": 0.25, "balanced": 0.50, "impulsive": 0.25},
        "payment_methods": {
            "primary": ["credit_card", "debit_card"],
            "secondary": ["bnpl", "installments"]
        },
        "category_affinities": {
            "Electronics": 0.80,
            "Fashion": 0.75,
            "Home & Kitchen": 0.55,
            "Sports & Fitness": 0.65,
            "Beauty & Personal Care": 0.60,
            "Books & Media": 0.50
        },
        "financial_goals": [
            "save_for_house", "invest_in_retirement", "build_credit",
            "pay_off_debt", "save_for_vacation", "upgrade_lifestyle"
        ],
        "deal_seeker_prob": 0.50,
        "reviews_importance_range": (0.5, 0.8),
        "brand_loyalty_range": (0.4, 0.7)
    },
    "family": {
        "weight": 0.25,
        "age_ranges": ["25-34", "35-44", "45-54"],
        "age_weights": [0.25, 0.50, 0.25],
        "budget_range": (300, 1200),
        "monthly_discretionary": (400, 1200),
        "affordability_score_range": (0.35, 0.65),
        "risk_tolerance_weights": {"low": 0.5, "moderate": 0.4, "high": 0.1},
        "spending_style_weights": {"frugal": 0.40, "balanced": 0.50, "impulsive": 0.10},
        "payment_methods": {
            "primary": ["credit_card", "debit_card"],
            "secondary": ["installments", "bnpl"]
        },
        "category_affinities": {
            "Home & Kitchen": 0.90,
            "Fashion": 0.75,
            "Electronics": 0.65,
            "Books & Media": 0.60,
            "Sports & Fitness": 0.55,
            "Beauty & Personal Care": 0.50
        },
        "financial_goals": [
            "save_for_kids_education", "pay_mortgage", "family_vacation",
            "home_improvement", "emergency_fund", "balance_budget"
        ],
        "deal_seeker_prob": 0.75,
        "reviews_importance_range": (0.7, 0.95),
        "brand_loyalty_range": (0.5, 0.8)
    },
    "affluent": {
        "weight": 0.12,
        "age_ranges": ["35-44", "45-54", "55-64"],
        "age_weights": [0.35, 0.40, 0.25],
        "budget_range": (1000, 5000),
        "monthly_discretionary": (2000, 8000),
        "affordability_score_range": (0.75, 0.95),
        "risk_tolerance_weights": {"low": 0.15, "moderate": 0.45, "high": 0.40},
        "spending_style_weights": {"frugal": 0.10, "balanced": 0.50, "impulsive": 0.40},
        "payment_methods": {
            "primary": ["credit_card"],
            "secondary": ["debit_card", "bank_transfer"]
        },
        "category_affinities": {
            "Electronics": 0.85,
            "Fashion": 0.90,
            "Home & Kitchen": 0.80,
            "Beauty & Personal Care": 0.75,
            "Sports & Fitness": 0.70,
            "Books & Media": 0.55
        },
        "financial_goals": [
            "wealth_management", "luxury_purchases", "investment_growth",
            "estate_planning", "premium_experiences", "philanthropy"
        ],
        "deal_seeker_prob": 0.15,
        "reviews_importance_range": (0.4, 0.7),
        "brand_loyalty_range": (0.6, 0.9)
    },
    "senior": {
        "weight": 0.10,
        "age_ranges": ["55-64", "65+"],
        "age_weights": [0.45, 0.55],
        "budget_range": (200, 800),
        "monthly_discretionary": (300, 1000),
        "affordability_score_range": (0.40, 0.70),
        "risk_tolerance_weights": {"low": 0.6, "moderate": 0.35, "high": 0.05},
        "spending_style_weights": {"frugal": 0.50, "balanced": 0.45, "impulsive": 0.05},
        "payment_methods": {
            "primary": ["credit_card", "debit_card"],
            "secondary": ["cash", "bank_transfer"]
        },
        "category_affinities": {
            "Home & Kitchen": 0.80,
            "Books & Media": 0.75,
            "Beauty & Personal Care": 0.65,
            "Electronics": 0.50,
            "Sports & Fitness": 0.45,
            "Fashion": 0.55
        },
        "financial_goals": [
            "retirement_income", "healthcare_savings", "grandchildren_gifts",
            "home_maintenance", "travel", "hobby_spending"
        ],
        "deal_seeker_prob": 0.60,
        "reviews_importance_range": (0.7, 0.9),
        "brand_loyalty_range": (0.7, 0.95)
    },
    "budget_conscious": {
        "weight": 0.05,
        "age_ranges": ["25-34", "35-44", "45-54"],
        "age_weights": [0.35, 0.40, 0.25],
        "budget_range": (50, 200),
        "monthly_discretionary": (100, 300),
        "affordability_score_range": (0.15, 0.35),
        "risk_tolerance_weights": {"low": 0.7, "moderate": 0.25, "high": 0.05},
        "spending_style_weights": {"frugal": 0.80, "balanced": 0.18, "impulsive": 0.02},
        "payment_methods": {
            "primary": ["debit_card", "cash"],
            "secondary": ["installments", "bnpl"]
        },
        "category_affinities": {
            "Home & Kitchen": 0.70,
            "Fashion": 0.50,
            "Books & Media": 0.60,
            "Beauty & Personal Care": 0.45,
            "Electronics": 0.40,
            "Sports & Fitness": 0.35
        },
        "financial_goals": [
            "debt_repayment", "basic_necessities", "emergency_fund",
            "rent_payment", "utility_bills", "save_any_amount"
        ],
        "deal_seeker_prob": 0.95,
        "reviews_importance_range": (0.8, 0.95),
        "brand_loyalty_range": (0.1, 0.3)
    },
    "luxury_shopper": {
        "weight": 0.03,
        "age_ranges": ["25-34", "35-44", "45-54", "55-64"],
        "age_weights": [0.15, 0.35, 0.35, 0.15],
        "budget_range": (2000, 10000),
        "monthly_discretionary": (5000, 20000),
        "affordability_score_range": (0.85, 1.0),
        "risk_tolerance_weights": {"low": 0.1, "moderate": 0.3, "high": 0.6},
        "spending_style_weights": {"frugal": 0.02, "balanced": 0.28, "impulsive": 0.70},
        "payment_methods": {
            "primary": ["credit_card"],
            "secondary": ["bank_transfer"]
        },
        "category_affinities": {
            "Fashion": 0.95,
            "Beauty & Personal Care": 0.90,
            "Electronics": 0.85,
            "Home & Kitchen": 0.75,
            "Sports & Fitness": 0.60,
            "Books & Media": 0.40
        },
        "financial_goals": [
            "exclusive_experiences", "designer_collection", "premium_quality",
            "status_purchases", "unique_items", "latest_releases"
        ],
        "deal_seeker_prob": 0.05,
        "reviews_importance_range": (0.2, 0.5),
        "brand_loyalty_range": (0.8, 0.98)
    }
}


# === Search Query Templates ===
# Organized by intent type for realistic search generation
SEARCH_QUERY_TEMPLATES: Dict[str, List[str]] = {
    "specific_product": [
        "{brand} {product_type}",
        "{product_type} {color}",
        "{brand} {model}",
        "{category} {brand}",
        "best {product_type} under ${price}",
        "{product_type} with {feature}",
        "{size} {product_type}",
        "new {brand} {product_type}"
    ],
    "vague_intent": [
        "gift for {recipient}",
        "something for {occasion}",
        "need a new {generic_item}",
        "looking for {generic_item}",
        "what's a good {product_type}",
        "{adjective} {generic_item}",
        "ideas for {purpose}",
        "help me find {generic_item}"
    ],
    "budget_focused": [
        "cheap {product_type}",
        "affordable {product_type}",
        "budget {product_type}",
        "{product_type} under ${price}",
        "best value {product_type}",
        "inexpensive {product_type}",
        "low cost {product_type}",
        "deals on {product_type}"
    ],
    "quality_focused": [
        "best {product_type}",
        "top rated {product_type}",
        "premium {product_type}",
        "high quality {product_type}",
        "professional {product_type}",
        "luxury {product_type}",
        "durable {product_type}",
        "best reviewed {product_type}"
    ],
    "category_browse": [
        "{category}",
        "{subcategory}",
        "{category} deals",
        "new in {category}",
        "popular {category}",
        "trending {subcategory}",
        "{category} sale",
        "best sellers {category}"
    ],
    "comparison": [
        "{brand1} vs {brand2}",
        "compare {product_type}",
        "{brand} or {brand2} {product_type}",
        "which {product_type} is better",
        "difference between {product_type}",
        "{product_type} comparison"
    ],
    "feature_specific": [
        "{product_type} with {feature}",
        "wireless {product_type}",
        "waterproof {product_type}",
        "portable {product_type}",
        "rechargeable {product_type}",
        "{color} {product_type}",
        "{material} {product_type}",
        "smart {product_type}"
    ]
}

# Search query fill-in data
SEARCH_FILL_INS: Dict[str, List[str]] = {
    "recipient": [
        "mom", "dad", "wife", "husband", "boyfriend", "girlfriend",
        "teenager", "college student", "grandma", "grandpa", "best friend",
        "coworker", "boss", "teacher", "kids", "baby"
    ],
    "occasion": [
        "birthday", "Christmas", "anniversary", "graduation", "wedding",
        "housewarming", "Mother's Day", "Father's Day", "Valentine's Day",
        "back to school", "new job", "retirement"
    ],
    "generic_item": [
        "laptop", "phone", "headphones", "watch", "bag", "shoes",
        "jacket", "chair", "desk", "camera", "speaker", "tablet",
        "book", "gift", "present", "gadget", "appliance"
    ],
    "adjective": [
        "nice", "good", "cool", "useful", "practical", "trendy",
        "unique", "comfortable", "stylish", "modern", "classic"
    ],
    "purpose": [
        "working from home", "fitness", "cooking", "gaming", "reading",
        "traveling", "studying", "organizing", "decorating", "relaxing"
    ],
    "feature": [
        "long battery", "fast charging", "noise canceling", "Bluetooth",
        "USB-C", "HD camera", "touchscreen", "adjustable", "foldable"
    ]
}


# === Behavioral Patterns ===
# Conversion funnel probabilities
FUNNEL_PROBABILITIES: Dict[str, Dict[str, float]] = {
    # After a search, probability of each next action
    "search": {
        "view": 0.70,      # 70% click on a result
        "search": 0.20,    # 20% refine search
        "abandon": 0.10    # 10% leave
    },
    # After viewing a product
    "view": {
        "view": 0.30,      # 30% view another product
        "add_to_cart": 0.25,  # 25% add to cart
        "wishlist": 0.08,  # 8% add to wishlist
        "search": 0.15,    # 15% go back to search
        "abandon": 0.22    # 22% leave
    },
    # After adding to cart
    "add_to_cart": {
        "purchase": 0.45,  # 45% proceed to purchase
        "view": 0.25,      # 25% continue shopping
        "remove_from_cart": 0.15,  # 15% remove item
        "abandon": 0.15    # 15% abandon cart
    },
    # After adding to wishlist
    "wishlist": {
        "view": 0.40,      # Continue browsing
        "search": 0.30,    # Search more
        "abandon": 0.30    # Leave
    }
}

# Session time patterns (hour weights for interaction generation)
HOURLY_ACTIVITY_WEIGHTS: Dict[int, float] = {
    0: 0.02, 1: 0.01, 2: 0.01, 3: 0.01, 4: 0.01, 5: 0.02,
    6: 0.03, 7: 0.04, 8: 0.05, 9: 0.06, 10: 0.07, 11: 0.07,
    12: 0.08, 13: 0.07, 14: 0.06, 15: 0.06, 16: 0.06, 17: 0.07,
    18: 0.08, 19: 0.09, 20: 0.10, 21: 0.09, 22: 0.07, 23: 0.04
}

# Day of week weights (0=Monday, 6=Sunday)
DAILY_ACTIVITY_WEIGHTS: Dict[int, float] = {
    0: 0.12,  # Monday
    1: 0.13,  # Tuesday
    2: 0.14,  # Wednesday
    3: 0.14,  # Thursday
    4: 0.15,  # Friday
    5: 0.17,  # Saturday
    6: 0.15   # Sunday
}

# Device type by time of day
DEVICE_PREFERENCES: Dict[str, Dict[str, float]] = {
    "morning": {"mobile": 0.50, "desktop": 0.40, "tablet": 0.10},   # 6-12
    "afternoon": {"desktop": 0.55, "mobile": 0.35, "tablet": 0.10}, # 12-18
    "evening": {"mobile": 0.45, "desktop": 0.35, "tablet": 0.20},   # 18-24
    "night": {"mobile": 0.60, "tablet": 0.25, "desktop": 0.15}      # 0-6
}

# Session characteristics
SESSION_CONFIG: Dict[str, Any] = {
    "avg_session_duration_seconds": 480,  # 8 minutes average
    "session_duration_std": 300,
    "min_session_duration": 30,
    "max_session_duration": 3600,  # 1 hour max
    "avg_interactions_per_session": 8,
    "min_interactions_per_session": 1,
    "max_interactions_per_session": 50,
    "time_between_interactions_mean": 45,  # seconds
    "time_between_interactions_std": 30
}


# Default configuration instance
default_config = GenerationConfig()

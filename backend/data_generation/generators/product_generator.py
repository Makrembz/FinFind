"""
Product data generator for FinFind.

Generates realistic e-commerce product data across multiple categories
with proper pricing, attributes, and descriptions.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from faker import Faker
from tqdm import tqdm
import logging

from .base_generator import BaseGenerator
from ..config import (
    GenerationConfig, 
    CATEGORY_HIERARCHY, 
    BRANDS_BY_CATEGORY,
    PRODUCT_TEMPLATES
)
from ..models.product_models import Product, ProductAttributes

logger = logging.getLogger(__name__)
fake = Faker()
Faker.seed(42)


class ProductGenerator(BaseGenerator):
    """Generator for product catalog data."""
    
    def __init__(self, config: Optional[GenerationConfig] = None):
        super().__init__(config)
        self._init_product_data()
    
    def _init_product_data(self) -> None:
        """Initialize product-specific data for generation."""
        # Colors by category
        self.colors = {
            "Electronics": ["Black", "White", "Silver", "Space Gray", "Blue", "Red", "Gold"],
            "Fashion": ["Black", "White", "Navy", "Gray", "Red", "Blue", "Green", "Pink", "Beige", "Brown"],
            "Home & Kitchen": ["White", "Black", "Silver", "Stainless Steel", "Gray", "Wood", "Natural"],
            "Books & Media": ["N/A"],
            "Sports & Fitness": ["Black", "Blue", "Red", "Green", "Orange", "Gray", "White"],
            "Beauty & Personal Care": ["N/A"]
        }
        
        # Sizes
        self.sizes = {
            "Fashion": ["XS", "S", "M", "L", "XL", "XXL"],
            "Shoes": ["6", "7", "8", "9", "10", "11", "12", "13"],
        }
        
        # Materials
        self.materials = {
            "Fashion": ["Cotton", "Polyester", "Wool", "Silk", "Linen", "Leather", "Denim", "Nylon"],
            "Home & Kitchen": ["Wood", "Metal", "Plastic", "Glass", "Ceramic", "Stainless Steel", "Bamboo"],
            "Sports & Fitness": ["Rubber", "Steel", "Neoprene", "Polyester", "Nylon", "Carbon Fiber"]
        }
        
        # Electronics specs
        self.processors = ["Intel Core i5", "Intel Core i7", "Intel Core i9", "AMD Ryzen 5", "AMD Ryzen 7", "Apple M3", "Apple M3 Pro", "Snapdragon 8 Gen 3"]
        self.ram_options = ["8", "16", "32", "64"]
        self.storage_options = ["128", "256", "512", "1000", "2000"]
        self.screen_sizes_laptop = ["13.3", "14", "15.6", "16", "17.3"]
        self.screen_sizes_phone = ["6.1", "6.4", "6.7", "6.8"]
        self.display_types = ["LCD", "OLED", "AMOLED", "Retina", "IPS", "Mini-LED"]
        
        # Book data
        self.book_genres = ["Fiction", "Mystery", "Romance", "Science Fiction", "Fantasy", "Thriller", "Biography", "Self-Help", "Business", "Technology"]
        self.publishers = ["Penguin Random House", "HarperCollins", "Simon & Schuster", "Hachette", "Macmillan", "O'Reilly Media", "Wiley", "McGraw Hill"]
        
        # Beauty data
        self.skin_types = ["All Skin Types", "Oily", "Dry", "Combination", "Sensitive", "Normal"]
        self.beauty_concerns = ["Anti-Aging", "Hydration", "Acne", "Brightening", "Pore Minimizing", "Firming"]
        self.ingredients = ["Hyaluronic Acid", "Vitamin C", "Retinol", "Niacinamide", "Salicylic Acid", "Glycolic Acid", "Peptides", "Ceramides"]
        
        # Stock status weights
        self.stock_weights = [0.70, 0.15, 0.10, 0.05]  # in_stock, low_stock, out_of_stock, preorder
        self.stock_statuses = ["in_stock", "low_stock", "out_of_stock", "preorder"]
    
    def _select_category(self) -> str:
        """Select a category based on configured weights."""
        categories = list(self.config.category_weights.keys())
        weights = list(self.config.category_weights.values())
        return self.weighted_choice(categories, weights)
    
    def _select_subcategory(self, category: str) -> str:
        """Select a subcategory within the given category."""
        subcategories = CATEGORY_HIERARCHY[category]["subcategories"]
        return random.choice(subcategories)
    
    def _select_brand(self, category: str) -> Tuple[str, str]:
        """
        Select a brand and tier for the category.
        
        Returns:
            Tuple of (brand_name, tier)
        """
        brands = BRANDS_BY_CATEGORY.get(category, {})
        if not brands:
            return (fake.company(), "mid_tier")
        
        # Weight toward mid-tier (realistic distribution)
        tier_weights = {"premium": 0.25, "mid_tier": 0.50, "budget": 0.25}
        tier = self.weighted_choice(list(tier_weights.keys()), list(tier_weights.values()))
        
        brand_list = brands.get(tier, brands.get("mid_tier", [fake.company()]))
        return (random.choice(brand_list), tier)
    
    def _generate_price(self, category: str, tier: str) -> Tuple[float, Optional[float]]:
        """
        Generate price based on category and brand tier.
        
        Returns:
            Tuple of (current_price, original_price or None)
        """
        price_config = self.config.price_ranges.get(category, {
            "min": 10, "max": 500, "mean": 100, "std": 80
        })
        
        # Generate base price
        base_price = self.generate_log_normal_price(
            mean=price_config["mean"],
            std=price_config["std"],
            min_val=price_config["min"],
            max_val=price_config["max"]
        )
        
        # Apply tier modifier
        tier_modifiers = {"premium": 1.8, "mid_tier": 1.0, "budget": 0.6}
        base_price *= tier_modifiers.get(tier, 1.0)
        
        # Clamp to category range
        base_price = max(price_config["min"], min(price_config["max"], base_price))
        
        # Adjust to psychological price
        current_price = self.adjust_to_psychological_price(base_price)
        
        # Maybe generate original price (30% chance of discount)
        original_price = None
        if random.random() < 0.30:
            discount_pct = random.uniform(0.10, 0.40)
            original_price = round(current_price / (1 - discount_pct), 2)
            original_price = self.adjust_to_psychological_price(original_price)
        
        return (round(current_price, 2), original_price)
    
    def _generate_payment_options(self, price: float) -> List[str]:
        """Generate appropriate payment options based on price."""
        options = ["credit", "debit"]
        
        if price >= 50:
            if random.random() < 0.7:
                options.append("bnpl")  # Buy Now Pay Later
        
        if price >= 200:
            if random.random() < 0.5:
                options.append("paypal")
        
        if price >= 500:
            if random.random() < 0.6:
                options.append("financing")
        
        if price >= 100 and random.random() < 0.1:
            options.append("crypto")
        
        return options
    
    def _generate_stock_status(self) -> Tuple[str, Optional[int]]:
        """Generate stock status and quantity."""
        status = self.weighted_choice(self.stock_statuses, self.stock_weights)
        
        quantity = None
        if status == "in_stock":
            quantity = random.randint(10, 500)
        elif status == "low_stock":
            quantity = random.randint(1, 9)
        elif status == "preorder":
            quantity = random.randint(50, 200)
        # out_of_stock has no quantity
        
        return (status, quantity)
    
    def _generate_image_url(self, product_id: str, category: str) -> str:
        """Generate a placeholder image URL."""
        # Use picsum.photos with seed for consistent images
        seed = hash(product_id) % 10000
        return f"https://picsum.photos/seed/{seed}/400/400"
    
    def _generate_tags(self, category: str, subcategory: str, 
                       brand: str, attributes: Dict) -> List[str]:
        """Generate relevant tags for the product."""
        tags = [
            category.lower().replace(" & ", "-").replace(" ", "-"),
            subcategory.lower().replace(" ", "-"),
            brand.lower().replace(" ", "-")
        ]
        
        # Add attribute-based tags
        if attributes.get("color") and attributes["color"] != "N/A":
            tags.append(attributes["color"].lower())
        
        if attributes.get("material"):
            tags.append(attributes["material"].lower())
        
        # Add category-specific tags
        category_tags = {
            "Electronics": ["tech", "gadgets", "electronic-devices"],
            "Fashion": ["style", "apparel", "clothing", "fashion-accessories"],
            "Home & Kitchen": ["home-decor", "household", "kitchen-essentials"],
            "Books & Media": ["reading", "books", "literature"],
            "Sports & Fitness": ["fitness", "workout", "sports-equipment", "active-lifestyle"],
            "Beauty & Personal Care": ["beauty", "skincare", "personal-care", "cosmetics"]
        }
        
        tags.extend(random.sample(category_tags.get(category, []), 
                                   min(2, len(category_tags.get(category, [])))))
        
        return list(set(tags))[:10]  # Dedupe and limit
    
    def _generate_electronics_product(self, subcategory: str, brand: str) -> Tuple[str, str, ProductAttributes]:
        """Generate an electronics product."""
        attrs = ProductAttributes(brand=brand)
        
        if subcategory == "Laptops":
            attrs.processor = random.choice(self.processors)
            attrs.ram = random.choice(self.ram_options)
            attrs.storage = random.choice(self.storage_options)
            attrs.screen_size = random.choice(self.screen_sizes_laptop)
            attrs.battery_life = f"{random.randint(6, 18)} hours"
            attrs.color = random.choice(self.colors["Electronics"])
            
            model = fake.bothify(text="??? ####")
            title = f"{brand} {model} {attrs.screen_size}\" Laptop - {attrs.processor}, {attrs.ram}GB RAM, {attrs.storage}GB SSD"
            
            description = f"""Powerful {brand} laptop featuring the latest {attrs.processor} processor 
            for seamless multitasking and demanding applications. Equipped with {attrs.ram}GB DDR5 RAM 
            and a fast {attrs.storage}GB NVMe SSD for quick boot times and ample storage. 
            The stunning {attrs.screen_size}-inch display delivers crisp visuals perfect for work and entertainment. 
            With up to {attrs.battery_life} of battery life, stay productive throughout your day. 
            Features include a backlit keyboard, HD webcam, Wi-Fi 6E, and Bluetooth 5.3 connectivity. 
            Available in {attrs.color}. Perfect for professionals, students, and creators who demand performance and portability."""
            
        elif subcategory == "Smartphones":
            attrs.storage = random.choice(["128", "256", "512"])
            attrs.screen_size = random.choice(self.screen_sizes_phone)
            attrs.color = random.choice(self.colors["Electronics"])
            attrs.battery_life = f"{random.randint(4000, 5500)}mAh"
            camera_mp = random.choice([48, 50, 64, 108, 200])
            
            model = fake.bothify(text="??? ##")
            title = f"{brand} {model} 5G Smartphone - {attrs.screen_size}\" Display, {attrs.storage}GB, {attrs.color}"
            
            description = f"""Experience the next generation of mobile technology with the {brand} {model}. 
            Featuring a stunning {attrs.screen_size}-inch AMOLED display with vibrant colors and deep blacks. 
            Capture every moment with the advanced {camera_mp}MP camera system with AI-enhanced photography. 
            Powered by the latest processor for flagship performance in gaming, streaming, and productivity. 
            {attrs.storage}GB of internal storage keeps all your apps, photos, and media at your fingertips. 
            The {attrs.battery_life} battery with fast charging keeps you going all day. 
            5G connectivity for ultra-fast downloads and streaming. Water and dust resistant design. 
            Available in stunning {attrs.color}."""
            
        elif subcategory in ["Headphones", "Speakers", "Earbuds"]:
            attrs.color = random.choice(self.colors["Electronics"])
            attrs.battery_life = f"{random.randint(20, 60)} hours" if subcategory != "Speakers" else "N/A"
            attrs.connectivity = random.sample(["Bluetooth 5.3", "3.5mm Jack", "USB-C", "Wireless"], k=random.randint(1, 3))
            
            model = fake.bothify(text="???-####")
            
            if subcategory == "Headphones":
                title = f"{brand} {model} Wireless Noise-Canceling Over-Ear Headphones - {attrs.color}"
                description = f"""Immerse yourself in premium sound with {brand} {model} wireless headphones. 
                Industry-leading active noise cancellation blocks out distractions for pure audio enjoyment. 
                Hi-Res audio certification delivers studio-quality sound with deep bass and crystal-clear highs. 
                Up to {attrs.battery_life} of listening time on a single charge - quick charge gives 5 hours from just 10 minutes. 
                Premium memory foam ear cushions provide all-day comfort. Touch controls for easy playback and calls. 
                Multipoint connection lets you switch seamlessly between devices. 
                Foldable design with premium carrying case included. Available in {attrs.color}."""
            elif subcategory == "Speakers":
                watts = random.choice([20, 40, 60, 100, 200])
                title = f"{brand} {model} Bluetooth Speaker - {watts}W, Waterproof, {attrs.color}"
                description = f"""Fill any room with powerful sound from the {brand} {model} Bluetooth speaker. 
                {watts}W of peak power delivers room-filling audio with deep bass and clear mids. 
                IPX7 waterproof rating - perfect for pool parties, beach trips, or bathroom use. 
                Connect via Bluetooth 5.3 or aux cable. Pair two speakers for true stereo sound. 
                Built-in microphone for hands-free calls. Up to 24 hours of playtime. 
                Compact, portable design with built-in handle. Available in {attrs.color}."""
            else:  # Earbuds
                title = f"{brand} {model} True Wireless Earbuds - ANC, {attrs.battery_life} Battery"
                description = f"""Experience wireless freedom with {brand} {model} true wireless earbuds. 
                Active noise cancellation lets you focus on your music or calls without distractions. 
                Premium drivers deliver rich, balanced sound with punchy bass. 
                Up to {attrs.battery_life} total battery life with the charging case. 
                IPX4 sweat and water resistant - perfect for workouts. 
                Touch controls for music, calls, and voice assistant. Wireless charging case included. 
                Three sizes of silicone tips for the perfect fit. Available in {attrs.color}."""
        
        elif subcategory in ["Tablets", "Gaming", "Cameras", "Smartwatches", "TV & Home Theater", "Computer Accessories"]:
            attrs.color = random.choice(self.colors["Electronics"])
            model = fake.bothify(text="??? ####")
            
            if subcategory == "Tablets":
                attrs.screen_size = random.choice(["10.2", "10.9", "11", "12.9"])
                attrs.storage = random.choice(["64", "128", "256", "512"])
                title = f"{brand} {model} Tablet - {attrs.screen_size}\" Display, {attrs.storage}GB, WiFi"
                description = f"""Versatile {brand} tablet perfect for work, entertainment, and creativity. 
                {attrs.screen_size}-inch Retina display with True Tone for comfortable viewing. 
                Powerful chip for smooth performance in apps, games, and multitasking. 
                {attrs.storage}GB storage for all your content. All-day battery life up to 10 hours. 
                Support for keyboard and stylus accessories. WiFi 6 connectivity. 
                Front and rear cameras for video calls and photos. Available in {attrs.color}."""
                
            elif subcategory == "Gaming":
                title = f"{brand} {model} Gaming Controller - Wireless, {attrs.color}"
                description = f"""Take your gaming to the next level with the {brand} {model} controller. 
                Precision analog sticks and triggers for accurate gameplay. 
                Wireless connectivity with ultra-low latency. Ergonomic design for extended play sessions. 
                Customizable buttons and profiles. Vibration feedback for immersive gaming. 
                Up to 40 hours battery life. Compatible with PC, console, and mobile. 
                Available in {attrs.color} with textured grip."""
                
            elif subcategory == "Cameras":
                megapixels = random.choice([24, 26, 33, 45, 61])
                title = f"{brand} {model} Digital Camera - {megapixels}MP, 4K Video"
                description = f"""Capture stunning images with the {brand} {model} {megapixels}MP camera. 
                Full-frame sensor delivers exceptional detail and low-light performance. 
                4K video recording at 60fps for cinematic footage. Advanced autofocus with eye-tracking. 
                5-axis image stabilization for sharp handheld shots. 
                3-inch tilting touchscreen. Weather-sealed body. 
                WiFi and Bluetooth for easy sharing. Perfect for enthusiasts and professionals."""
                
            elif subcategory == "Smartwatches":
                title = f"{brand} {model} Smartwatch - GPS, Heart Rate, {attrs.color}"
                description = f"""Stay connected and healthy with the {brand} {model} smartwatch. 
                Advanced health monitoring including heart rate, SpO2, and sleep tracking. 
                Built-in GPS for accurate workout tracking. Water resistant to 50 meters. 
                Bright always-on display visible in any lighting. Up to 7 days battery life. 
                Receive notifications, calls, and texts on your wrist. 
                100+ workout modes. Customizable watch faces. Available in {attrs.color}."""
                
            elif subcategory == "TV & Home Theater":
                screen_size = random.choice([43, 50, 55, 65, 75, 85])
                title = f'{brand} {screen_size}" 4K Smart TV - HDR, Dolby Atmos'
                description = f"""Transform your living room with the {brand} {screen_size}-inch 4K Smart TV. 
                Crystal-clear 4K UHD resolution with HDR for lifelike picture quality. 
                Dolby Atmos and DTS:X for immersive surround sound. 
                Smart TV platform with all your favorite streaming apps built-in. 
                Voice control with Alexa and Google Assistant. 
                Game mode with low input lag for responsive gaming. 
                Sleek slim design. Multiple HDMI and USB ports."""
                
            else:  # Computer Accessories
                accessory_type = random.choice(["Mechanical Keyboard", "Gaming Mouse", "Monitor Stand", "USB Hub", "Webcam"])
                title = f"{brand} {model} {accessory_type} - {attrs.color}"
                description = f"""Enhance your setup with the {brand} {model} {accessory_type}. 
                Premium build quality with durable materials. 
                Ergonomic design for comfortable extended use. 
                Plug and play setup - works with Windows and Mac. 
                Compact design saves desk space. 
                LED indicators and premium finish. Available in {attrs.color}."""
        
        else:
            # Generic electronics fallback
            title = f"{brand} {subcategory} Device - Premium Quality"
            description = f"High-quality {subcategory.lower()} from {brand}. Features latest technology for optimal performance."
            attrs.color = random.choice(self.colors["Electronics"])
        
        return (title, description.strip(), attrs)
    
    def _generate_fashion_product(self, subcategory: str, brand: str) -> Tuple[str, str, ProductAttributes]:
        """Generate a fashion product."""
        attrs = ProductAttributes(brand=brand)
        attrs.color = random.choice(self.colors["Fashion"])
        attrs.size = random.choice(self.sizes["Fashion"])
        attrs.material = random.choice(self.materials["Fashion"])
        
        styles = ["Casual", "Classic", "Modern", "Vintage", "Athletic", "Formal", "Bohemian"]
        attrs.style = random.choice(styles)
        attrs.fit = random.choice(["Slim", "Regular", "Relaxed", "Oversized"])
        attrs.season = random.choice(["Spring/Summer", "Fall/Winter", "All Season"])
        
        if subcategory == "Men's Clothing":
            item_type = random.choice(["T-Shirt", "Polo Shirt", "Button-Down Shirt", "Jeans", "Chinos", "Sweater", "Hoodie", "Jacket"])
            attrs.gender = "Men"
            title = f"{brand} Men's {attrs.style} {item_type} - {attrs.color}, {attrs.material}"
            description = f"""Elevate your wardrobe with this {brand} men's {item_type}. 
            Crafted from premium {attrs.material} for comfort and durability. 
            {attrs.fit} fit provides a flattering silhouette for all body types. 
            Perfect for {attrs.season.lower()} wear. {attrs.style} design transitions easily from casual to dressed-up occasions. 
            Machine washable for easy care. Available in multiple colors and sizes S-XXL. 
            Pair with jeans or chinos for a complete look. Quality construction with attention to detail."""
            
        elif subcategory == "Women's Clothing":
            item_type = random.choice(["Blouse", "Dress", "Skirt", "Top", "Cardigan", "Pants", "Jumpsuit"])
            attrs.gender = "Women"
            title = f"{brand} Women's {attrs.style} {item_type} - {attrs.color}"
            description = f"""Make a statement with this beautiful {brand} women's {item_type}. 
            Luxurious {attrs.material} fabric drapes beautifully and feels amazing against your skin. 
            {attrs.style} design perfect for any occasion - work, weekend, or evening out. 
            Flattering {attrs.fit} fit suits various body types. Ideal for {attrs.season.lower()}. 
            Easy care - machine wash cold, tumble dry low. 
            Available in sizes XS-XXL. Versatile piece that pairs with your favorite accessories."""
            
        elif subcategory == "Shoes":
            shoe_type = random.choice(["Sneakers", "Boots", "Loafers", "Sandals", "Running Shoes", "Dress Shoes", "Slip-Ons"])
            attrs.size = random.choice(self.sizes["Shoes"])
            attrs.gender = random.choice(["Men", "Women", "Unisex"])
            title = f"{brand} {attrs.gender}'s {attrs.style} {shoe_type} - {attrs.color}"
            description = f"""Step out in style with {brand} {shoe_type}. 
            Premium {attrs.material} upper for durability and breathability. 
            Cushioned insole provides all-day comfort. Non-slip outsole for confident traction. 
            {attrs.style} design complements both casual and smart-casual outfits. 
            True to size fit - order your regular size. 
            Reinforced heel and toe for long-lasting wear. 
            Available in {attrs.color} and multiple sizes."""
            
        elif subcategory == "Bags & Accessories":
            item_type = random.choice(["Backpack", "Tote Bag", "Crossbody Bag", "Wallet", "Belt", "Sunglasses"])
            title = f"{brand} {attrs.style} {item_type} - {attrs.color}"
            description = f"""Complete your look with this {brand} {item_type}. 
            Crafted from premium {attrs.material} for lasting quality. 
            {attrs.style} design works with any outfit. Practical features meet sophisticated style. 
            Multiple compartments keep essentials organized. Quality hardware with secure closures. 
            Perfect size for everyday use. Available in {attrs.color}. 
            Makes an excellent gift for any occasion."""
            
        else:
            # Generic fashion fallback
            title = f"{brand} {subcategory} - {attrs.style} {attrs.color}"
            description = f"Stylish {subcategory.lower()} from {brand}. Quality {attrs.material} construction. {attrs.style} design for {attrs.season}."
        
        return (title, description.strip(), attrs)
    
    def _generate_home_kitchen_product(self, subcategory: str, brand: str) -> Tuple[str, str, ProductAttributes]:
        """Generate a home & kitchen product."""
        attrs = ProductAttributes(brand=brand)
        attrs.color = random.choice(self.colors["Home & Kitchen"])
        attrs.material = random.choice(self.materials["Home & Kitchen"])
        
        if subcategory == "Kitchen Appliances":
            appliance = random.choice(["Blender", "Air Fryer", "Coffee Maker", "Toaster", "Instant Pot", "Stand Mixer", "Food Processor"])
            attrs.wattage = str(random.choice([500, 700, 1000, 1200, 1500]))
            attrs.capacity = random.choice(["4 Cup", "6 Cup", "8 Cup", "5 Quart", "6 Quart"])
            
            title = f"{brand} {appliance} - {attrs.capacity}, {attrs.wattage}W, {attrs.color}"
            description = f"""Transform your kitchen with the {brand} {appliance}. 
            Powerful {attrs.wattage}W motor handles any task with ease. 
            {attrs.capacity} capacity perfect for families and meal prep. 
            Easy-to-clean {attrs.color} finish complements any kitchen decor. 
            Multiple speed settings and preset programs for convenience. 
            Dishwasher-safe removable parts save time on cleanup. 
            Compact design fits easily on your countertop. 
            Includes recipe book with 20+ ideas. 2-year manufacturer warranty."""
            
        elif subcategory == "Cookware":
            item = random.choice(["Frying Pan", "Pot Set", "Baking Sheet", "Dutch Oven", "Knife Set", "Cutting Board Set"])
            attrs.material = random.choice(["Stainless Steel", "Cast Iron", "Non-Stick", "Ceramic", "Carbon Steel"])
            
            title = f"{brand} {item} - {attrs.material}, Professional Grade"
            description = f"""Cook like a pro with the {brand} {item}. 
            Premium {attrs.material} construction for even heat distribution. 
            Oven safe up to 500°F. Compatible with all cooktops including induction. 
            Ergonomic handles stay cool during cooking. 
            Professional-grade durability built to last for years. 
            Easy to clean - dishwasher safe. 
            Perfect for everyday cooking and special occasions. 
            Backed by lifetime warranty."""
            
        elif subcategory == "Furniture":
            furniture = random.choice(["Desk", "Bookshelf", "Coffee Table", "Dining Table", "Office Chair", "Sofa", "Bed Frame"])
            attrs.dimensions = f'{random.randint(24, 72)}"W x {random.randint(18, 36)}"D x {random.randint(24, 48)}"H'
            attrs.style = random.choice(["Modern", "Contemporary", "Traditional", "Industrial", "Scandinavian", "Mid-Century"])
            
            title = f"{brand} {attrs.style} {furniture} - {attrs.material}, {attrs.color}"
            description = f"""Elevate your space with the {brand} {furniture}. 
            {attrs.style} design complements any home decor. 
            Solid {attrs.material} construction ensures lasting durability. 
            Dimensions: {attrs.dimensions}. Weight capacity suitable for everyday use. 
            Easy assembly with included hardware and instructions. 
            Finished in beautiful {attrs.color} to match your style. 
            Perfect addition to living room, bedroom, or home office. 
            1-year manufacturer warranty against defects."""
            
        elif subcategory in ["Bedding", "Home Decor", "Lighting", "Storage & Organization", "Garden"]:
            if subcategory == "Bedding":
                item = random.choice(["Sheet Set", "Comforter", "Pillow Set", "Mattress Topper", "Duvet Cover"])
                attrs.material = random.choice(["Cotton", "Microfiber", "Bamboo", "Linen", "Egyptian Cotton"])
                size = random.choice(["Twin", "Full", "Queen", "King", "California King"])
                title = f"{brand} {item} - {size}, {attrs.material}, {attrs.color}"
                description = f"""Sleep in luxury with the {brand} {item}. 
                Premium {attrs.material} fabric for ultimate softness and breathability. 
                {size} size fits standard mattresses. Deep pockets for secure fit. 
                Available in beautiful {attrs.color} to match your bedroom. 
                Machine washable and gets softer with every wash. 
                OEKO-TEX certified safe. Includes matching pillowcases. 
                Transform your bedroom into a cozy retreat."""
                
            elif subcategory == "Home Decor":
                item = random.choice(["Throw Pillow Set", "Wall Art", "Vase", "Mirror", "Rug", "Curtains"])
                title = f"{brand} {item} - {attrs.style if hasattr(attrs, 'style') else 'Modern'} Design, {attrs.color}"
                description = f"""Add personality to your space with this {brand} {item}. 
                Thoughtfully designed to complement various decor styles. 
                Quality materials and craftsmanship. 
                Available in {attrs.color} to match or accent your room. 
                Perfect for living room, bedroom, or entryway. 
                Makes an excellent housewarming gift. 
                Easy to incorporate into existing decor."""
                
            elif subcategory == "Lighting":
                item = random.choice(["Table Lamp", "Floor Lamp", "Pendant Light", "Desk Lamp", "LED Strip Lights"])
                title = f"{brand} {item} - {attrs.color}, Dimmable"
                description = f"""Illuminate your space with the {brand} {item}. 
                Modern design adds style to any room. 
                Dimmable for adjustable ambiance. Energy-efficient LED technology. 
                Quality {attrs.color} finish. Easy installation with included hardware. 
                Compatible with smart home systems. 
                Perfect for living room, bedroom, or office. 
                2-year manufacturer warranty."""
                
            else:
                title = f"{brand} {subcategory} Product - {attrs.color}"
                description = f"Quality {subcategory.lower()} product from {brand}. Durable construction. Available in {attrs.color}."
        else:
            title = f"{brand} {subcategory} Item - Premium Quality"
            description = f"High-quality {subcategory.lower()} from {brand}. Built to last."
        
        return (title, description.strip(), attrs)
    
    def _generate_books_product(self, subcategory: str, brand: str) -> Tuple[str, str, ProductAttributes]:
        """Generate a books & media product."""
        attrs = ProductAttributes()
        attrs.publisher = brand if brand in self.publishers else random.choice(self.publishers)
        attrs.author = fake.name()
        attrs.pages = random.randint(150, 800)
        attrs.format = random.choice(["Paperback", "Hardcover", "E-Book", "Audiobook"])
        attrs.language = "English"
        
        if subcategory in ["Fiction", "Non-Fiction"]:
            attrs.genre = random.choice(self.book_genres[:5]) if subcategory == "Fiction" else random.choice(self.book_genres[5:])
            
            # Generate book title
            fiction_titles = [
                f"The {fake.word().title()} of {fake.city()}",
                f"{fake.first_name()}'s {fake.word().title()}",
                f"Beyond the {fake.word().title()}",
                f"The Last {fake.word().title()}",
                f"Secrets of {fake.city()}"
            ]
            
            nonfiction_titles = [
                f"The Art of {fake.word().title()}",
                f"How to {fake.word().title()} Your Life",
                f"The {fake.word().title()} Mindset",
                f"Thinking About {fake.word().title()}",
                f"The Power of {fake.word().title()}"
            ]
            
            book_title = random.choice(fiction_titles if subcategory == "Fiction" else nonfiction_titles)
            title = f"{book_title} by {attrs.author} - {attrs.format}"
            
            description = f"""Discover the acclaimed {attrs.genre.lower()} book "{book_title}" by {attrs.author}. 
            This {attrs.pages}-page {attrs.format.lower()} has captivated readers worldwide. 
            A masterfully crafted story that explores themes of human connection and personal growth. 
            Published by {attrs.publisher}. Available in {attrs.format.lower()} format. 
            Perfect for book clubs and avid readers alike. 
            {"Winner of multiple literary awards." if random.random() < 0.3 else ""} 
            Join millions of readers who have been touched by this remarkable work."""
            
        elif subcategory == "Technical & Programming":
            technologies = ["Python", "JavaScript", "React", "Machine Learning", "Data Science", "Cloud Computing", "DevOps", "Kubernetes"]
            tech = random.choice(technologies)
            level = random.choice(["Beginner", "Intermediate", "Advanced"])
            attrs.genre = "Technology"
            
            book_title = random.choice([
                f"Mastering {tech}",
                f"Learning {tech}: A Practical Guide",
                f"{tech} in Action",
                f"Pro {tech}: {level} Techniques",
                f"The Complete {tech} Handbook"
            ])
            
            title = f"{book_title} - {attrs.format}"
            description = f"""Comprehensive guide to {tech} for {level.lower()} developers. 
            {attrs.pages} pages of practical tutorials, examples, and best practices. 
            Written by industry experts with real-world experience. 
            Includes downloadable code samples and exercises. 
            Covers the latest version and modern development practices. 
            Perfect for self-study or classroom use. 
            Published by {attrs.publisher}. {attrs.format} edition."""
            
        elif subcategory == "Self-Help":
            attrs.genre = "Self-Help"
            topics = ["productivity", "happiness", "success", "relationships", "mindfulness", "confidence"]
            topic = random.choice(topics)
            
            book_title = random.choice([
                f"The {topic.title()} Blueprint",
                f"Unlocking Your {topic.title()}",
                f"The Science of {topic.title()}",
                f"7 Principles of {topic.title()}",
                f"Transform Your {topic.title()}"
            ])
            
            title = f"{book_title} by {attrs.author} - {attrs.format}"
            description = f"""Transform your life with "{book_title}" by bestselling author {attrs.author}. 
            Discover proven strategies for improving your {topic} based on cutting-edge research. 
            {attrs.pages} pages of actionable advice and inspiring stories. 
            Includes exercises and worksheets to track your progress. 
            Over {random.randint(100, 500)}K copies sold worldwide. 
            {attrs.format} edition from {attrs.publisher}."""
            
        else:
            book_title = f"The {subcategory} Guide"
            title = f"{book_title} - {attrs.format}"
            description = f"Comprehensive {subcategory.lower()} book. {attrs.pages} pages. Published by {attrs.publisher}."
        
        return (title, description.strip(), attrs)
    
    def _generate_sports_product(self, subcategory: str, brand: str) -> Tuple[str, str, ProductAttributes]:
        """Generate a sports & fitness product."""
        attrs = ProductAttributes(brand=brand)
        attrs.color = random.choice(self.colors["Sports & Fitness"])
        attrs.material = random.choice(self.materials["Sports & Fitness"])
        attrs.skill_level = random.choice(["Beginner", "Intermediate", "Advanced", "All Levels"])
        
        if subcategory == "Exercise Equipment":
            equipment = random.choice(["Dumbbell Set", "Resistance Bands", "Yoga Mat", "Kettlebell", "Pull-Up Bar", "Jump Rope", "Ab Roller"])
            
            if "Dumbbell" in equipment or "Kettlebell" in equipment:
                weight = random.choice([5, 10, 15, 20, 25, 30, 35, 40, 50])
                attrs.weight = f"{weight} lbs"
                title = f"{brand} {equipment} - {attrs.weight}, {attrs.color}"
            else:
                title = f"{brand} {equipment} - Professional Grade, {attrs.color}"
            
            description = f"""Take your fitness to the next level with the {brand} {equipment}. 
            Premium construction built for intense workouts. 
            Suitable for {attrs.skill_level.lower()} fitness enthusiasts. 
            Compact design perfect for home gyms or travel. 
            Ergonomic grip for comfortable, safe exercise. 
            Durable {attrs.material} material built to last. 
            Includes workout guide with exercise ideas. 
            Available in {attrs.color}. 90-day satisfaction guarantee."""
            
        elif subcategory == "Outdoor Recreation":
            item = random.choice(["Tent", "Sleeping Bag", "Backpack", "Camping Chair", "Hiking Poles", "Cooler"])
            capacity = random.choice(["2-Person", "4-Person", "30L", "50L", "65L"])
            attrs.capacity = capacity
            
            title = f"{brand} {item} - {capacity}, Lightweight, {attrs.color}"
            description = f"""Adventure awaits with the {brand} {item}. 
            {capacity} capacity perfect for solo trips or group adventures. 
            Lightweight yet durable {attrs.material} construction. 
            Weather-resistant design handles the elements. 
            Easy setup in minutes - no special tools required. 
            Compact storage with included carry bag. 
            Perfect for camping, hiking, and outdoor adventures. 
            Available in {attrs.color}. 1-year manufacturer warranty."""
            
        elif subcategory == "Fitness Accessories":
            accessory = random.choice(["Gym Bag", "Water Bottle", "Fitness Tracker", "Foam Roller", "Workout Gloves"])
            title = f"{brand} {accessory} - {attrs.color}"
            description = f"""Essential workout gear from {brand}. 
            Premium quality {accessory.lower()} for serious fitness enthusiasts. 
            Durable construction withstands daily use. 
            Thoughtful design with practical features. 
            Comfortable and easy to use. 
            Available in {attrs.color}. 
            Perfect complement to your fitness routine."""
            
        else:
            title = f"{brand} {subcategory} Equipment - {attrs.color}"
            description = f"Quality {subcategory.lower()} gear from {brand}. Perfect for {attrs.skill_level.lower()} athletes."
        
        return (title, description.strip(), attrs)
    
    def _generate_beauty_product(self, subcategory: str, brand: str) -> Tuple[str, str, ProductAttributes]:
        """Generate a beauty & personal care product."""
        attrs = ProductAttributes(brand=brand)
        attrs.skin_type = random.choice(self.skin_types)
        attrs.volume = random.choice(["1 oz", "1.7 oz", "2 oz", "3.4 oz", "8 oz", "16 oz"])
        
        if subcategory == "Skincare":
            product = random.choice(["Moisturizer", "Serum", "Cleanser", "Sunscreen", "Eye Cream", "Toner", "Face Mask"])
            attrs.ingredients = random.sample(self.ingredients, k=random.randint(2, 4))
            concern = random.choice(self.beauty_concerns)
            
            title = f"{brand} {concern} {product} - {attrs.volume}, {attrs.skin_type}"
            description = f"""Transform your skin with {brand} {product}. 
            Formulated with {', '.join(attrs.ingredients)} for visible results. 
            Targets {concern.lower()} concerns effectively. 
            Suitable for {attrs.skin_type.lower()} skin types. 
            Dermatologist tested and approved. 
            Paraben-free, cruelty-free formula. 
            Absorbs quickly without greasy residue. 
            {attrs.volume} bottle with pump dispenser. 
            Use daily for best results. See improvement in 4-8 weeks."""
            
        elif subcategory == "Makeup":
            product = random.choice(["Foundation", "Lipstick", "Mascara", "Eyeshadow Palette", "Blush", "Concealer", "Setting Spray"])
            finish = random.choice(["Matte", "Dewy", "Satin", "Natural", "Radiant"])
            shades = random.choice([12, 18, 24, 36])
            
            if "Palette" in product:
                title = f"{brand} {product} - {shades} Shades, {finish} Finish"
                description = f"""{brand} {product} with {shades} stunning shades. 
                {finish} finish for a flawless look. Highly pigmented for vibrant color payoff. 
                Blendable formula for seamless application. Long-lasting wear up to 12 hours. 
                Mix and match to create endless looks. Includes applicator and mirror. 
                Cruelty-free and vegan. Suitable for all skin tones."""
            else:
                shade = fake.color_name()
                title = f"{brand} {product} - {shade}, {finish} Finish"
                description = f"""Achieve flawless beauty with {brand} {product}. 
                {finish} finish for a professional look. Long-lasting {random.randint(8, 16)}-hour wear. 
                Buildable coverage from light to full. Comfortable, lightweight formula. 
                Available in {shade} and multiple other shades. 
                Dermatologist tested. Cruelty-free and vegan formula."""
                
        elif subcategory == "Hair Care":
            product = random.choice(["Shampoo", "Conditioner", "Hair Mask", "Hair Oil", "Styling Gel", "Heat Protectant"])
            hair_type = random.choice(["All Hair Types", "Dry Hair", "Oily Hair", "Color-Treated", "Curly Hair", "Fine Hair"])
            
            title = f"{brand} {product} for {hair_type} - {attrs.volume}"
            description = f"""Nourish your hair with {brand} {product}. 
            Specially formulated for {hair_type.lower()}. 
            Strengthens and repairs damaged hair. Adds shine and reduces frizz. 
            Sulfate-free and paraben-free formula. 
            Salon-quality results at home. 
            {attrs.volume} bottle. Use as part of your daily hair care routine."""
            
        elif subcategory == "Fragrances":
            scent_family = random.choice(["Floral", "Woody", "Fresh", "Oriental", "Citrus"])
            gender = random.choice(["Women", "Men", "Unisex"])
            attrs.scent = scent_family
            attrs.volume = random.choice(["1 oz", "1.7 oz", "3.4 oz"])
            
            title = f"{brand} Eau de Parfum for {gender} - {scent_family}, {attrs.volume}"
            description = f"""Captivate the senses with {brand} fragrance. 
            {scent_family} scent profile with sophisticated notes. 
            Long-lasting formula stays with you all day. 
            Perfect for {gender.lower()}. Ideal for everyday wear or special occasions. 
            {attrs.volume} spray bottle. Beautifully packaged for gifting. 
            Experience luxury in every spritz."""
            
        else:
            title = f"{brand} {subcategory} Product - {attrs.volume}"
            description = f"Quality {subcategory.lower()} from {brand}. Dermatologist tested."
        
        return (title, description.strip(), attrs)
    
    def _generate_product(self, category: str, subcategory: str) -> Product:
        """Generate a complete product."""
        brand, tier = self._select_brand(category)
        price, original_price = self._generate_price(category, tier)
        stock_status, stock_qty = self._generate_stock_status()
        
        # Generate category-specific content
        generator_map = {
            "Electronics": self._generate_electronics_product,
            "Fashion": self._generate_fashion_product,
            "Home & Kitchen": self._generate_home_kitchen_product,
            "Books & Media": self._generate_books_product,
            "Sports & Fitness": self._generate_sports_product,
            "Beauty & Personal Care": self._generate_beauty_product
        }
        
        generator = generator_map.get(category, self._generate_electronics_product)
        title, description, attrs = generator(subcategory, brand)
        
        product_id = f"prod_{uuid.uuid4()}"
        
        product = Product(
            id=product_id,
            title=title[:500],  # Ensure within limit
            description=description[:5000],
            category=category,
            subcategory=subcategory,
            brand=brand,
            price=price,
            original_price=original_price,
            currency="USD",
            attributes=attrs,
            image_url=self._generate_image_url(product_id, category),
            stock_status=stock_status,
            stock_quantity=stock_qty,
            payment_options=self._generate_payment_options(price),
            tags=self._generate_tags(category, subcategory, brand, attrs.model_dump(exclude_none=True)),
            created_at=fake.date_time_between(start_date="-1y", end_date="now")
        )
        
        return product
    
    def generate(self) -> List[Product]:
        """
        Generate the configured number of products.
        
        Returns:
            List of generated Product objects.
        """
        products = []
        
        logger.info(f"Generating {self.config.num_products} products...")
        
        for _ in tqdm(range(self.config.num_products), desc="Generating products"):
            category = self._select_category()
            subcategory = self._select_subcategory(category)
            
            product = self._generate_product(category, subcategory)
            products.append(product)
        
        # Generate embeddings in batch
        if self.config.generate_embeddings:
            texts = [p.get_embedding_text() for p in products]
            embeddings = self.generate_embeddings(texts)
            
            for product, embedding in zip(products, embeddings):
                product.embedding = embedding
        
        logger.info(f"Generated {len(products)} products successfully")
        return products
    
    def validate(self, products: List[Product]) -> bool:
        """
        Validate generated products.
        
        Args:
            products: List of products to validate.
            
        Returns:
            True if all products are valid.
        """
        logger.info(f"Validating {len(products)} products...")
        
        issues = []
        seen_ids = set()
        
        for i, product in enumerate(products):
            # Check for duplicate IDs
            if product.id in seen_ids:
                issues.append(f"Product {i}: Duplicate ID {product.id}")
            seen_ids.add(product.id)
            
            # Check required fields
            if len(product.title) < 10:
                issues.append(f"Product {i}: Title too short")
            if len(product.description) < 50:
                issues.append(f"Product {i}: Description too short")
            if product.price <= 0:
                issues.append(f"Product {i}: Invalid price {product.price}")
            
            # Check embedding if expected
            if self.config.generate_embeddings and not product.embedding:
                issues.append(f"Product {i}: Missing embedding")
        
        if issues:
            for issue in issues[:10]:  # Show first 10 issues
                logger.warning(issue)
            if len(issues) > 10:
                logger.warning(f"...and {len(issues) - 10} more issues")
            return False
        
        logger.info("All products validated successfully")
        return True


def generate_products(num_products: int = 500, 
                      generate_embeddings: bool = True,
                      random_seed: int = 42) -> List[Product]:
    """
    Convenience function to generate products.
    
    Args:
        num_products: Number of products to generate.
        generate_embeddings: Whether to generate embeddings.
        random_seed: Random seed for reproducibility.
        
    Returns:
        List of generated Product objects.
    """
    config = GenerationConfig(
        num_products=num_products,
        generate_embeddings=generate_embeddings,
        random_seed=random_seed
    )
    
    generator = ProductGenerator(config)
    products = generator.generate()
    generator.validate(products)
    
    return products

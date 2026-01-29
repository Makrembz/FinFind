#!/usr/bin/env python3
"""
Sample Product Data Generator with Real Images

Generates realistic product data for FinFind with real, related product images.
Uses high-quality free image sources that match products perfectly.
"""

import json
import uuid
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any

# Real product images from Unsplash (free, high-quality, product-specific)
# Format: https://images.unsplash.com/photo-{ID}?w=800&q=80

SAMPLE_PRODUCTS: List[Dict[str, Any]] = [
    # ==================== ELECTRONICS - LAPTOPS ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Apple MacBook Pro 14\" M3 Pro - 18GB RAM, 512GB SSD, Space Gray",
        "description": "The Apple MacBook Pro 14-inch with M3 Pro chip delivers exceptional performance for professionals. Featuring an 18GB unified memory and 512GB SSD storage, this laptop handles demanding workflows with ease. The stunning Liquid Retina XDR display offers extreme dynamic range with 1000 nits sustained brightness. Perfect for video editing, 3D rendering, software development, and creative work. Includes MagSafe charging, HDMI port, SD card slot, and up to 17 hours of battery life.",
        "category": "Electronics",
        "subcategory": "Laptops",
        "brand": "Apple",
        "price": 1999.00,
        "original_price": 2199.00,
        "currency": "USD",
        "attributes": {
            "brand": "Apple",
            "model": "MacBook Pro 14 M3 Pro",
            "processor": "Apple M3 Pro",
            "ram": "18GB",
            "storage": "512GB SSD",
            "screen_size": "14.2 inches",
            "battery_life": "17 hours",
            "color": "Space Gray",
            "connectivity": ["WiFi 6E", "Bluetooth 5.3", "Thunderbolt 4"]
        },
        "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 45,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.8,
        "review_count": 2847,
        "tags": ["laptop", "macbook", "apple", "professional", "m3", "creative", "video editing", "programming"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Dell XPS 15 - Intel Core i7-13700H, 32GB RAM, 1TB SSD, OLED Display",
        "description": "The Dell XPS 15 combines stunning design with powerful performance. Equipped with 13th Gen Intel Core i7-13700H processor, 32GB DDR5 RAM, and 1TB NVMe SSD. The 15.6-inch 3.5K OLED display delivers breathtaking visuals with 100% DCI-P3 color accuracy. Features include a CNC machined aluminum chassis, edge-to-edge keyboard, and large precision touchpad. Thunderbolt 4 ports ensure fast connectivity. Ideal for creators, developers, and business professionals.",
        "category": "Electronics",
        "subcategory": "Laptops",
        "brand": "Dell",
        "price": 1849.99,
        "original_price": 2099.99,
        "currency": "USD",
        "attributes": {
            "brand": "Dell",
            "model": "XPS 15 9530",
            "processor": "Intel Core i7-13700H",
            "ram": "32GB DDR5",
            "storage": "1TB NVMe SSD",
            "screen_size": "15.6 inches",
            "battery_life": "13 hours",
            "color": "Platinum Silver",
            "connectivity": ["WiFi 6E", "Bluetooth 5.3", "Thunderbolt 4"]
        },
        "image_url": "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 28,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.6,
        "review_count": 1523,
        "tags": ["laptop", "dell", "xps", "oled", "intel", "ultrabook", "professional", "windows"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Lenovo ThinkPad X1 Carbon Gen 11 - Intel Core i7, 16GB RAM, 512GB SSD",
        "description": "The legendary ThinkPad X1 Carbon continues its legacy of business excellence. Weighing just 2.48 lbs, it features Intel Core i7-1365U vPro processor, 16GB LPDDR5 RAM, and 512GB SSD. The 14-inch 2.8K OLED display with Dolby Vision ensures stunning visuals. Military-grade durability (MIL-STD-810H), fingerprint reader, IR camera for Windows Hello, and renowned ThinkPad keyboard. Perfect for enterprise users and frequent travelers.",
        "category": "Electronics",
        "subcategory": "Laptops",
        "brand": "Lenovo",
        "price": 1649.00,
        "original_price": 1899.00,
        "currency": "USD",
        "attributes": {
            "brand": "Lenovo",
            "model": "ThinkPad X1 Carbon Gen 11",
            "processor": "Intel Core i7-1365U vPro",
            "ram": "16GB LPDDR5",
            "storage": "512GB SSD",
            "screen_size": "14 inches",
            "battery_life": "15 hours",
            "color": "Deep Black",
            "connectivity": ["WiFi 6E", "Bluetooth 5.2", "Thunderbolt 4", "4G LTE"]
        },
        "image_url": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 35,
        "payment_options": ["credit", "debit", "bnpl", "financing"],
        "rating_avg": 4.7,
        "review_count": 1892,
        "tags": ["laptop", "thinkpad", "lenovo", "business", "ultrabook", "lightweight", "enterprise"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "ASUS ROG Zephyrus G14 Gaming Laptop - AMD Ryzen 9, RTX 4060, 16GB RAM",
        "description": "Dominate your games with the ASUS ROG Zephyrus G14. Powered by AMD Ryzen 9 7940HS processor and NVIDIA GeForce RTX 4060 graphics with 8GB VRAM. Features 16GB DDR5 RAM, 1TB PCIe 4.0 SSD, and a stunning 14-inch QHD+ 165Hz display with 100% DCI-P3. The AniMe Matrix LED display on the lid adds unique personalization. Weighs only 3.64 lbs - the most powerful 14-inch gaming laptop available.",
        "category": "Electronics",
        "subcategory": "Laptops",
        "brand": "ASUS",
        "price": 1599.99,
        "original_price": 1799.99,
        "currency": "USD",
        "attributes": {
            "brand": "ASUS",
            "model": "ROG Zephyrus G14 GA402XV",
            "processor": "AMD Ryzen 9 7940HS",
            "gpu": "NVIDIA RTX 4060 8GB",
            "ram": "16GB DDR5",
            "storage": "1TB PCIe 4.0 SSD",
            "screen_size": "14 inches",
            "battery_life": "10 hours",
            "color": "Moonlight White",
            "connectivity": ["WiFi 6E", "Bluetooth 5.2"]
        },
        "image_url": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 22,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.7,
        "review_count": 2156,
        "tags": ["laptop", "gaming", "asus", "rog", "rtx", "amd", "portable gaming", "esports"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "HP Pavilion 15 Budget Laptop - Intel Core i5, 8GB RAM, 256GB SSD",
        "description": "The HP Pavilion 15 offers reliable performance at an affordable price. Features Intel Core i5-1235U processor, 8GB DDR4 RAM, and 256GB SSD. The 15.6-inch Full HD IPS display provides clear visuals for everyday tasks. Includes HP Fast Charge (50% in 45 minutes), dual speakers with Audio by B&O, and a full-size keyboard with numeric keypad. Perfect for students, home office, and everyday computing.",
        "category": "Electronics",
        "subcategory": "Laptops",
        "brand": "HP",
        "price": 549.99,
        "original_price": 699.99,
        "currency": "USD",
        "attributes": {
            "brand": "HP",
            "model": "Pavilion 15-eg3000",
            "processor": "Intel Core i5-1235U",
            "ram": "8GB DDR4",
            "storage": "256GB SSD",
            "screen_size": "15.6 inches",
            "battery_life": "8 hours",
            "color": "Natural Silver",
            "connectivity": ["WiFi 6", "Bluetooth 5.2"]
        },
        "image_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 89,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.3,
        "review_count": 3421,
        "tags": ["laptop", "hp", "budget", "student", "home office", "affordable", "everyday"]
    },

    # ==================== ELECTRONICS - SMARTPHONES ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Apple iPhone 15 Pro Max - 256GB, Natural Titanium, 5G",
        "description": "Experience the most advanced iPhone ever. iPhone 15 Pro Max features the groundbreaking A17 Pro chip, the first 3nm processor in a smartphone. The 6.7-inch Super Retina XDR display with ProMotion offers Always-On capability. Revolutionary 48MP main camera with 5x optical zoom captures stunning photos and 4K60 ProRes video. Titanium design makes it the lightest Pro Max ever. USB-C with USB 3 speeds, Action button, and all-day battery life.",
        "category": "Electronics",
        "subcategory": "Smartphones",
        "brand": "Apple",
        "price": 1199.00,
        "original_price": 1199.00,
        "currency": "USD",
        "attributes": {
            "brand": "Apple",
            "model": "iPhone 15 Pro Max",
            "processor": "A17 Pro",
            "storage": "256GB",
            "screen_size": "6.7 inches",
            "camera": "48MP + 12MP + 12MP",
            "battery_life": "4422mAh",
            "color": "Natural Titanium",
            "connectivity": ["5G", "WiFi 6E", "Bluetooth 5.3", "USB-C", "NFC"]
        },
        "image_url": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 156,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.9,
        "review_count": 8934,
        "tags": ["smartphone", "iphone", "apple", "5g", "pro", "titanium", "camera phone", "flagship"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Samsung Galaxy S24 Ultra - 512GB, Titanium Black, S Pen Included",
        "description": "Meet Galaxy S24 Ultra, the ultimate smartphone with Galaxy AI. Features the powerful Snapdragon 8 Gen 3 processor, 12GB RAM, and 512GB storage. The 6.8-inch Dynamic AMOLED 2X display with anti-reflective coating offers stunning visuals. Revolutionary 200MP camera with advanced Nightography and 100x Space Zoom. Built-in S Pen for productivity. Titanium frame with Gorilla Armor for durability. 7-year OS updates guarantee.",
        "category": "Electronics",
        "subcategory": "Smartphones",
        "brand": "Samsung",
        "price": 1299.99,
        "original_price": 1419.99,
        "currency": "USD",
        "attributes": {
            "brand": "Samsung",
            "model": "Galaxy S24 Ultra",
            "processor": "Snapdragon 8 Gen 3",
            "ram": "12GB",
            "storage": "512GB",
            "screen_size": "6.8 inches",
            "camera": "200MP + 50MP + 12MP + 10MP",
            "battery_life": "5000mAh",
            "color": "Titanium Black",
            "connectivity": ["5G", "WiFi 7", "Bluetooth 5.3", "UWB"]
        },
        "image_url": "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 98,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.7,
        "review_count": 5621,
        "tags": ["smartphone", "samsung", "galaxy", "s pen", "android", "5g", "camera phone", "flagship"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Google Pixel 8 Pro - 256GB, Bay Blue, AI-Powered Camera",
        "description": "Google Pixel 8 Pro brings the best of Google AI to your pocket. Powered by Google Tensor G3 chip custom-designed for AI workloads. Features a 6.7-inch Super Actua LTPO OLED display with 2400 nits peak brightness. The advanced camera system includes a 50MP main sensor with improved Magic Eraser, Best Take, and Audio Magic Eraser. Pro-level video with Video Boost and Night Sight Video. 7 years of OS and security updates.",
        "category": "Electronics",
        "subcategory": "Smartphones",
        "brand": "Google",
        "price": 999.00,
        "original_price": 1049.00,
        "currency": "USD",
        "attributes": {
            "brand": "Google",
            "model": "Pixel 8 Pro",
            "processor": "Google Tensor G3",
            "ram": "12GB",
            "storage": "256GB",
            "screen_size": "6.7 inches",
            "camera": "50MP + 48MP + 48MP",
            "battery_life": "5050mAh",
            "color": "Bay Blue",
            "connectivity": ["5G", "WiFi 7", "Bluetooth 5.3", "UWB"]
        },
        "image_url": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 67,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.6,
        "review_count": 3245,
        "tags": ["smartphone", "pixel", "google", "android", "ai", "camera phone", "pure android"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "OnePlus 12 - 256GB, Silky Black, Hasselblad Camera",
        "description": "OnePlus 12 delivers flagship performance at a competitive price. Equipped with Snapdragon 8 Gen 3, 12GB RAM, and 256GB storage. The 6.82-inch 2K LTPO ProXDR display offers 120Hz refresh rate and 4500 nits peak brightness. Hasselblad-tuned camera system with 50MP main sensor and advanced computational photography. 100W SUPERVOOC charging fills the 5400mAh battery in just 26 minutes. OxygenOS 14 based on Android 14.",
        "category": "Electronics",
        "subcategory": "Smartphones",
        "brand": "OnePlus",
        "price": 799.99,
        "original_price": 899.99,
        "currency": "USD",
        "attributes": {
            "brand": "OnePlus",
            "model": "OnePlus 12",
            "processor": "Snapdragon 8 Gen 3",
            "ram": "12GB",
            "storage": "256GB",
            "screen_size": "6.82 inches",
            "camera": "50MP + 48MP + 64MP",
            "battery_life": "5400mAh",
            "color": "Silky Black",
            "connectivity": ["5G", "WiFi 7", "Bluetooth 5.4"]
        },
        "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 54,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.5,
        "review_count": 1876,
        "tags": ["smartphone", "oneplus", "android", "hasselblad", "fast charging", "flagship killer"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Samsung Galaxy A54 5G - 128GB, Awesome Graphite, Budget Champion",
        "description": "Galaxy A54 5G brings flagship features to an affordable price. Features Exynos 1380 processor, 8GB RAM, and 128GB expandable storage. The 6.4-inch Super AMOLED display with 120Hz refresh rate and 1000 nits brightness delivers smooth, vibrant visuals. 50MP triple camera with OIS captures great photos day and night. IP67 water resistance, 5000mAh battery, and 4 years of OS updates make it exceptional value.",
        "category": "Electronics",
        "subcategory": "Smartphones",
        "brand": "Samsung",
        "price": 349.99,
        "original_price": 449.99,
        "currency": "USD",
        "attributes": {
            "brand": "Samsung",
            "model": "Galaxy A54 5G",
            "processor": "Exynos 1380",
            "ram": "8GB",
            "storage": "128GB",
            "screen_size": "6.4 inches",
            "camera": "50MP + 12MP + 5MP",
            "battery_life": "5000mAh",
            "color": "Awesome Graphite",
            "connectivity": ["5G", "WiFi 6", "Bluetooth 5.3", "NFC"]
        },
        "image_url": "https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 234,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.4,
        "review_count": 6543,
        "tags": ["smartphone", "samsung", "galaxy", "budget", "5g", "mid-range", "value"]
    },

    # ==================== ELECTRONICS - HEADPHONES ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Sony WH-1000XM5 Wireless Noise-Canceling Headphones - Silver",
        "description": "Industry-leading noise cancellation just got better. Sony WH-1000XM5 features two processors controlling 8 microphones for unprecedented noise canceling. 30mm drivers with specialized diaphragm deliver crystal-clear audio with deep bass. Multipoint connection for seamless switching between devices. Speak-to-Chat automatically pauses music when you talk. 30-hour battery life with quick charge (3 min for 3 hours). Ultra-lightweight at just 250g.",
        "category": "Electronics",
        "subcategory": "Headphones",
        "brand": "Sony",
        "price": 348.00,
        "original_price": 399.99,
        "currency": "USD",
        "attributes": {
            "brand": "Sony",
            "model": "WH-1000XM5",
            "color": "Silver",
            "battery_life": "30 hours",
            "driver_size": "30mm",
            "connectivity": ["Bluetooth 5.2", "3.5mm", "USB-C"],
            "noise_canceling": "Yes",
            "weight": "250g"
        },
        "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 78,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.8,
        "review_count": 4521,
        "tags": ["headphones", "sony", "wireless", "noise canceling", "bluetooth", "over-ear", "premium audio"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Apple AirPods Pro (2nd Gen) with USB-C - Active Noise Cancellation",
        "description": "AirPods Pro 2nd generation with USB-C delivers the ultimate wireless earbuds experience. Features 2x more Active Noise Cancellation than the original AirPods Pro. Adaptive Audio dynamically blends Transparency mode and ANC. Conversation Awareness lowers media volume when you speak. Personalized Spatial Audio with dynamic head tracking for immersive sound. Up to 6 hours listening time, 30 hours total with charging case. Now with precision finding for the case.",
        "category": "Electronics",
        "subcategory": "Headphones",
        "brand": "Apple",
        "price": 249.00,
        "original_price": 249.00,
        "currency": "USD",
        "attributes": {
            "brand": "Apple",
            "model": "AirPods Pro 2nd Gen",
            "color": "White",
            "battery_life": "6 hours (30h with case)",
            "connectivity": ["Bluetooth 5.3", "USB-C"],
            "noise_canceling": "Yes",
            "water_resistant": "IPX4"
        },
        "image_url": "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 312,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.7,
        "review_count": 12456,
        "tags": ["earbuds", "airpods", "apple", "wireless", "noise canceling", "true wireless"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Bose QuietComfort Ultra Headphones - Lunar Blue",
        "description": "Bose QuietComfort Ultra Headphones deliver world-class noise cancellation with immersive spatial audio. CustomTune technology personalizes your listening experience. Immersive Audio adds depth to music and movies. Quiet Mode offers full noise cancellation while Aware Mode lets in your surroundings. Premium materials with protein leather cushions and soft headband. 24-hour battery life. Seamlessly switch between 2 connected devices.",
        "category": "Electronics",
        "subcategory": "Headphones",
        "brand": "Bose",
        "price": 429.00,
        "original_price": 429.00,
        "currency": "USD",
        "attributes": {
            "brand": "Bose",
            "model": "QuietComfort Ultra",
            "color": "Lunar Blue",
            "battery_life": "24 hours",
            "connectivity": ["Bluetooth 5.3", "3.5mm", "USB-C"],
            "noise_canceling": "Yes",
            "spatial_audio": "Yes"
        },
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 45,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.6,
        "review_count": 2134,
        "tags": ["headphones", "bose", "wireless", "noise canceling", "spatial audio", "premium"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "JBL Tune 760NC Wireless Over-Ear Headphones - Black",
        "description": "JBL Tune 760NC delivers powerful JBL Pure Bass Sound with Active Noise Cancelling at an affordable price. 40mm drivers provide deep, punchy bass that JBL is famous for. Active Noise Cancelling blocks out distractions for immersive listening. 50-hour battery life (35h with ANC on) means less charging. Lightweight, foldable design for easy portability. Built-in microphone for hands-free calls. Multi-point connection for two devices.",
        "category": "Electronics",
        "subcategory": "Headphones",
        "brand": "JBL",
        "price": 79.95,
        "original_price": 129.95,
        "currency": "USD",
        "attributes": {
            "brand": "JBL",
            "model": "Tune 760NC",
            "color": "Black",
            "battery_life": "50 hours",
            "driver_size": "40mm",
            "connectivity": ["Bluetooth 5.0", "3.5mm"],
            "noise_canceling": "Yes",
            "foldable": "Yes"
        },
        "image_url": "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 189,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.4,
        "review_count": 8765,
        "tags": ["headphones", "jbl", "wireless", "noise canceling", "budget", "bass", "affordable"]
    },

    # ==================== ELECTRONICS - TABLETS ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Apple iPad Pro 12.9\" M2 - 256GB, WiFi, Space Gray",
        "description": "iPad Pro with the M2 chip is the ultimate creative tool. The stunning 12.9-inch Liquid Retina XDR display with ProMotion offers extreme dynamic range and P3 wide color. M2 chip delivers next-level performance with 8-core CPU and 10-core GPU. Works with Apple Pencil (2nd gen) for precise drawing with hover detection. Face ID, USB-C with Thunderbolt, and all-day battery. Stage Manager brings desktop-class multitasking. Perfect for artists, designers, and professionals.",
        "category": "Electronics",
        "subcategory": "Tablets",
        "brand": "Apple",
        "price": 1099.00,
        "original_price": 1199.00,
        "currency": "USD",
        "attributes": {
            "brand": "Apple",
            "model": "iPad Pro 12.9 M2",
            "processor": "Apple M2",
            "storage": "256GB",
            "screen_size": "12.9 inches",
            "display_type": "Liquid Retina XDR",
            "battery_life": "10 hours",
            "color": "Space Gray",
            "connectivity": ["WiFi 6E", "Bluetooth 5.3", "Thunderbolt"]
        },
        "image_url": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 56,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.8,
        "review_count": 3421,
        "tags": ["tablet", "ipad", "apple", "m2", "professional", "creative", "drawing"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Samsung Galaxy Tab S9+ - 256GB, WiFi, Graphite, S Pen Included",
        "description": "Galaxy Tab S9+ combines power and versatility in a premium tablet. Features Snapdragon 8 Gen 2 processor, 12GB RAM, and 256GB storage. The 12.4-inch Dynamic AMOLED 2X display with 120Hz and Vision Booster delivers stunning visuals anywhere. Includes S Pen with near-zero latency for natural writing. IP68 water resistance for peace of mind. DeX mode enables desktop-like productivity. Quad speakers with AKG tuning and Dolby Atmos.",
        "category": "Electronics",
        "subcategory": "Tablets",
        "brand": "Samsung",
        "price": 899.99,
        "original_price": 999.99,
        "currency": "USD",
        "attributes": {
            "brand": "Samsung",
            "model": "Galaxy Tab S9+",
            "processor": "Snapdragon 8 Gen 2",
            "ram": "12GB",
            "storage": "256GB",
            "screen_size": "12.4 inches",
            "display_type": "Dynamic AMOLED 2X",
            "battery_life": "12 hours",
            "color": "Graphite",
            "connectivity": ["WiFi 6E", "Bluetooth 5.3"]
        },
        "image_url": "https://images.unsplash.com/photo-1561154464-82e9adf32764?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 43,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.6,
        "review_count": 1876,
        "tags": ["tablet", "samsung", "galaxy", "s pen", "android", "productivity", "amoled"]
    },

    # ==================== ELECTRONICS - SMARTWATCHES ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Apple Watch Series 9 GPS 45mm - Midnight Aluminum Case with Sport Band",
        "description": "Apple Watch Series 9 is the most powerful Apple Watch yet. The new S9 SiP enables a magical new double tap gesture. Brighter 2000 nit Always-On Retina display. Advanced health features including blood oxygen, ECG, and temperature sensing. Enhanced cycling metrics with automatic detection. Precision Finding for iPhone. Carbon neutral when paired with certain bands. watchOS 10 with redesigned apps and Smart Stack.",
        "category": "Electronics",
        "subcategory": "Smartwatches",
        "brand": "Apple",
        "price": 429.00,
        "original_price": 429.00,
        "currency": "USD",
        "attributes": {
            "brand": "Apple",
            "model": "Watch Series 9",
            "processor": "S9 SiP",
            "case_size": "45mm",
            "display_type": "LTPO OLED",
            "battery_life": "18 hours",
            "color": "Midnight",
            "water_resistant": "50m",
            "connectivity": ["GPS", "Bluetooth 5.3", "WiFi"]
        },
        "image_url": "https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 134,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.8,
        "review_count": 5632,
        "tags": ["smartwatch", "apple watch", "fitness tracker", "health", "gps", "wearable"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Garmin Fenix 7X Solar - Slate Gray with Black Band",
        "description": "Garmin Fenix 7X Solar is built for extreme adventures. Features solar charging that extends battery life up to 37 days in smartwatch mode. 51mm case with rugged design and sapphire crystal lens. Advanced training metrics, maps, and multi-band GPS for precise tracking anywhere. Health monitoring includes heart rate, Pulse Ox, sleep, and HRV status. Preloaded with TopoActive maps, ski resort maps, and golf courses. Built to military standards (MIL-STD-810).",
        "category": "Electronics",
        "subcategory": "Smartwatches",
        "brand": "Garmin",
        "price": 899.99,
        "original_price": 999.99,
        "currency": "USD",
        "attributes": {
            "brand": "Garmin",
            "model": "Fenix 7X Solar",
            "case_size": "51mm",
            "display_type": "MIP",
            "battery_life": "37 days",
            "color": "Slate Gray",
            "water_resistant": "100m",
            "connectivity": ["GPS", "Bluetooth", "WiFi", "ANT+"]
        },
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 28,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.7,
        "review_count": 2134,
        "tags": ["smartwatch", "garmin", "outdoor", "adventure", "solar", "fitness", "gps"]
    },

    # ==================== FASHION - MEN'S CLOTHING ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Levi's 501 Original Fit Men's Jeans - Medium Stonewash, 32x32",
        "description": "The iconic Levi's 501 Original Fit jeans that started it all. Since 1873, these jeans have set the standard for denim. Features the signature button fly, straight leg, and comfortable mid-rise. Made from premium 12.5 oz cotton denim with just the right amount of stretch for all-day comfort. The Medium Stonewash finish offers a classic, versatile look. Sits at waist, regular fit through thigh, straight leg opening.",
        "category": "Fashion",
        "subcategory": "Men's Clothing",
        "brand": "Levi's",
        "price": 69.50,
        "original_price": 79.50,
        "currency": "USD",
        "attributes": {
            "brand": "Levi's",
            "style": "501 Original Fit",
            "color": "Medium Stonewash",
            "material": "99% Cotton, 1% Elastane",
            "fit": "Regular",
            "size": "32x32",
            "gender": "Men"
        },
        "image_url": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 234,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.5,
        "review_count": 15432,
        "tags": ["jeans", "denim", "levis", "501", "classic", "men", "casual"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Ralph Lauren Classic Fit Polo Shirt - Navy Blue, Medium",
        "description": "The quintessential Ralph Lauren polo shirt in a classic fit. Crafted from breathable cotton mesh for all-day comfort. Features the iconic embroidered pony at the left chest. Two-button placket, ribbed polo collar, and short sleeves with ribbed armbands. Tennis tail hem for a polished untucked look. Perfect for casual Fridays, golf, or weekend wear. A timeless wardrobe essential since 1972.",
        "category": "Fashion",
        "subcategory": "Men's Clothing",
        "brand": "Ralph Lauren",
        "price": 98.50,
        "original_price": 110.00,
        "currency": "USD",
        "attributes": {
            "brand": "Ralph Lauren",
            "style": "Classic Fit Polo",
            "color": "Navy Blue",
            "material": "100% Cotton Mesh",
            "fit": "Classic Fit",
            "size": "Medium",
            "gender": "Men"
        },
        "image_url": "https://images.unsplash.com/photo-1625910513413-5fc45d80b400?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 156,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.6,
        "review_count": 8765,
        "tags": ["polo shirt", "ralph lauren", "preppy", "classic", "men", "cotton"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Nike Men's Dri-FIT Training T-Shirt - Black, Large",
        "description": "Push your limits in the Nike Dri-FIT Training T-Shirt. Nike's moisture-wicking Dri-FIT technology keeps you dry and comfortable during intense workouts. Lightweight, breathable fabric with mesh panels for enhanced ventilation. Standard fit for a relaxed, easy feel. Features the iconic Swoosh logo on the chest. Perfect for gym sessions, running, or any athletic activity. Easy care - machine washable.",
        "category": "Fashion",
        "subcategory": "Men's Clothing",
        "brand": "Nike",
        "price": 30.00,
        "original_price": 35.00,
        "currency": "USD",
        "attributes": {
            "brand": "Nike",
            "style": "Dri-FIT Training Tee",
            "color": "Black",
            "material": "100% Polyester",
            "fit": "Standard Fit",
            "size": "Large",
            "gender": "Men"
        },
        "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 423,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.4,
        "review_count": 12543,
        "tags": ["t-shirt", "nike", "athletic", "dri-fit", "workout", "men", "training"]
    },

    # ==================== FASHION - WOMEN'S CLOTHING ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Lululemon Align High-Rise Leggings 25\" - Black, Size 6",
        "description": "The Lululemon Align leggings are a yoga studio staple. Made with buttery-soft, lightweight Nulu fabric that feels like a second skin. High-rise waistband lies flat against your skin for a secure, covered feel. Minimal seams reduce bulk and chafing. Hidden waistband pocket for keys or cards. The 25\" inseam hits just above the ankle. Perfect for yoga, pilates, or lounging. Experience the feel that launched a cult following.",
        "category": "Fashion",
        "subcategory": "Women's Clothing",
        "brand": "Lululemon",
        "price": 98.00,
        "original_price": 98.00,
        "currency": "USD",
        "attributes": {
            "brand": "Lululemon",
            "style": "Align High-Rise",
            "color": "Black",
            "material": "81% Nylon, 19% Lycra (Nulu)",
            "fit": "Tight",
            "size": "6",
            "inseam": "25 inches",
            "gender": "Women"
        },
        "image_url": "https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 178,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.8,
        "review_count": 23456,
        "tags": ["leggings", "lululemon", "yoga", "athleisure", "women", "high waist", "workout"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Zara Satin Midi Dress - Emerald Green, Medium",
        "description": "Make a statement in this elegant Zara Satin Midi Dress. Crafted from luxurious satin fabric with a subtle sheen that catches the light beautifully. Features a V-neckline, adjustable spaghetti straps, and a flattering A-line silhouette. The midi length falls gracefully below the knee. Hidden side zipper for easy dressing. Perfect for date nights, cocktail parties, or special occasions. Pair with heels and statement jewelry for a complete look.",
        "category": "Fashion",
        "subcategory": "Women's Clothing",
        "brand": "Zara",
        "price": 69.90,
        "original_price": 89.90,
        "currency": "USD",
        "attributes": {
            "brand": "Zara",
            "style": "Satin Midi Dress",
            "color": "Emerald Green",
            "material": "100% Polyester Satin",
            "fit": "A-Line",
            "size": "Medium",
            "occasion": "Evening/Cocktail",
            "gender": "Women"
        },
        "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 67,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.3,
        "review_count": 2341,
        "tags": ["dress", "midi dress", "satin", "zara", "evening wear", "women", "elegant"]
    },

    # ==================== FASHION - SHOES ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Nike Air Max 270 Men's Sneakers - Black/White, Size 10",
        "description": "The Nike Air Max 270 delivers unrivaled all-day comfort. Features Nike's largest-ever heel Air unit for plush cushioning with every step. Breathable mesh and synthetic upper provides lightweight support. Stretchy inner sleeve and padded collar for a snug, comfortable fit. Rubber outsole with flex grooves for natural movement. The bold design makes a statement on or off the track. A modern classic in the Air Max lineage.",
        "category": "Fashion",
        "subcategory": "Shoes",
        "brand": "Nike",
        "price": 150.00,
        "original_price": 160.00,
        "currency": "USD",
        "attributes": {
            "brand": "Nike",
            "model": "Air Max 270",
            "color": "Black/White",
            "material": "Mesh/Synthetic",
            "size": "10",
            "gender": "Men",
            "style": "Athletic/Lifestyle"
        },
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 89,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.6,
        "review_count": 18765,
        "tags": ["sneakers", "nike", "air max", "athletic", "lifestyle", "comfortable", "men"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Adidas Ultraboost 23 Running Shoes - Core Black, Men's Size 9.5",
        "description": "Run further and faster with the Adidas Ultraboost 23. Features 20% more BOOST midsole cushioning for incredible energy return with every stride. Primeknit+ upper adapts to your foot's movement for a locked-in fit. Continental Rubber outsole delivers superior grip in wet and dry conditions. Linear Energy Push propulsion system guides your foot for efficient toe-off. The sock-like fit and supportive heel counter provide stability during your run.",
        "category": "Fashion",
        "subcategory": "Shoes",
        "brand": "Adidas",
        "price": 190.00,
        "original_price": 190.00,
        "currency": "USD",
        "attributes": {
            "brand": "Adidas",
            "model": "Ultraboost 23",
            "color": "Core Black",
            "material": "Primeknit+ Upper",
            "size": "9.5",
            "gender": "Men",
            "style": "Running"
        },
        "image_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 67,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.7,
        "review_count": 9432,
        "tags": ["running shoes", "adidas", "ultraboost", "boost", "performance", "athletic", "men"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Dr. Martens 1460 Classic Boots - Black Smooth Leather, Women's Size 8",
        "description": "The iconic Dr. Martens 1460 boot that started a subculture. Crafted from durable Smooth leather with the signature yellow welt stitching. Features the air-cushioned sole for all-day comfort and slip resistance. 8-eye lace-up design with metal eyelets. Goodyear-welted construction ensures durability and repairability. Classic fit that's roomy through the forefoot. Made on the original 1460 last since 1960. Break-in period required for best fit.",
        "category": "Fashion",
        "subcategory": "Shoes",
        "brand": "Dr. Martens",
        "price": 170.00,
        "original_price": 170.00,
        "currency": "USD",
        "attributes": {
            "brand": "Dr. Martens",
            "model": "1460 Original",
            "color": "Black Smooth",
            "material": "Full-grain Leather",
            "size": "8",
            "gender": "Women",
            "style": "Boots"
        },
        "image_url": "https://images.unsplash.com/photo-1608256246200-53e635b5b65f?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 54,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.5,
        "review_count": 12345,
        "tags": ["boots", "dr martens", "leather", "iconic", "women", "combat boots", "classic"]
    },

    # ==================== HOME & KITCHEN - APPLIANCES ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Ninja Foodi 6-in-1 8-Quart 2-Basket Air Fryer - DualZone Technology",
        "description": "The Ninja Foodi DualZone Air Fryer transforms your cooking with two independent baskets. DualZone Technology with Smart Finish feature syncs both zones to finish at the same time. Match Cook lets you duplicate settings across zones for double the capacity. 6 versatile cooking functions: Air Fry, Air Broil, Roast, Bake, Reheat, and Dehydrate. Each basket holds up to 4 lbs of food. Crisps with 75% less fat than deep frying. Easy-clean baskets are dishwasher safe.",
        "category": "Home & Kitchen",
        "subcategory": "Kitchen Appliances",
        "brand": "Ninja",
        "price": 179.99,
        "original_price": 219.99,
        "currency": "USD",
        "attributes": {
            "brand": "Ninja",
            "model": "DZ201 DualZone",
            "capacity": "8 Quarts",
            "wattage": "1690W",
            "color": "Grey/Black",
            "dimensions": "15.8 x 16.7 x 13.1 inches"
        },
        "image_url": "https://images.unsplash.com/photo-1626509653291-18d9a934b9db?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 156,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.7,
        "review_count": 34521,
        "tags": ["air fryer", "ninja", "kitchen appliance", "healthy cooking", "dual basket", "air fry"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "KitchenAid Artisan Series 5-Quart Tilt-Head Stand Mixer - Empire Red",
        "description": "The iconic KitchenAid Artisan Stand Mixer is a baking essential. Powerful 325-watt motor handles heavy, thick batters with ease. 5-quart stainless steel bowl with ergonomic handle. 10 speeds for nearly any mixing task. Includes flat beater, dough hook, and wire whip. Tilt-head design for easy bowl and accessory access. Hub accepts 15+ optional attachments to transform your mixer. Available in 20+ colors to match your kitchen. Made in USA with global materials.",
        "category": "Home & Kitchen",
        "subcategory": "Kitchen Appliances",
        "brand": "KitchenAid",
        "price": 379.99,
        "original_price": 449.99,
        "currency": "USD",
        "attributes": {
            "brand": "KitchenAid",
            "model": "Artisan KSM150PS",
            "capacity": "5 Quarts",
            "wattage": "325W",
            "color": "Empire Red",
            "dimensions": "14 x 8.7 x 14 inches"
        },
        "image_url": "https://images.unsplash.com/photo-1594385208974-2e75f8d7bb48?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 78,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.9,
        "review_count": 45678,
        "tags": ["stand mixer", "kitchenaid", "baking", "kitchen appliance", "mixer", "artisan"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Instant Pot Duo Plus 6-Quart 9-in-1 Electric Pressure Cooker",
        "description": "The Instant Pot Duo Plus is the ultimate kitchen multi-cooker. 9 appliances in 1: pressure cooker, slow cooker, rice cooker, steamer, sauté pan, yogurt maker, sterilizer, sous vide, and warmer. Advanced microprocessor with 15 customizable programs. Whisper-quiet steam release. Easy-seal lid automatically seals when pressurizing. Fingerprint-resistant stainless steel and improved display. 6-quart capacity serves 6-8 people. Quick one-touch cooking for your favorite meals.",
        "category": "Home & Kitchen",
        "subcategory": "Kitchen Appliances",
        "brand": "Instant Pot",
        "price": 89.99,
        "original_price": 119.99,
        "currency": "USD",
        "attributes": {
            "brand": "Instant Pot",
            "model": "Duo Plus",
            "capacity": "6 Quarts",
            "wattage": "1000W",
            "color": "Stainless Steel",
            "dimensions": "13.4 x 12.2 x 12.5 inches"
        },
        "image_url": "https://images.unsplash.com/photo-1585515320310-259814833e62?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 289,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.7,
        "review_count": 156789,
        "tags": ["instant pot", "pressure cooker", "multi cooker", "slow cooker", "kitchen appliance"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Dyson V15 Detect Cordless Vacuum - Yellow/Nickel",
        "description": "The Dyson V15 Detect reveals hidden dust with a precisely-angled laser. Advanced piezo sensor counts and categorizes dust particles, displaying proof of a deep clean on the LCD screen. Powerful Dyson Hyperdymium motor spins at 125,000rpm generating 230 AW of suction. Anti-tangle Hair screw tool removes hair from the brush bar as you clean. Up to 60 minutes of fade-free power. HEPA filtration captures 99.99% of particles. Includes multiple tools for whole-home cleaning.",
        "category": "Home & Kitchen",
        "subcategory": "Kitchen Appliances",
        "brand": "Dyson",
        "price": 749.99,
        "original_price": 749.99,
        "currency": "USD",
        "attributes": {
            "brand": "Dyson",
            "model": "V15 Detect",
            "suction_power": "230 AW",
            "battery_life": "60 minutes",
            "color": "Yellow/Nickel",
            "filtration": "HEPA"
        },
        "image_url": "https://images.unsplash.com/photo-1558317374-067fb5f30001?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 45,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.6,
        "review_count": 8765,
        "tags": ["vacuum", "dyson", "cordless", "laser detect", "hepa", "home cleaning"]
    },

    # ==================== HOME & KITCHEN - FURNITURE ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "West Elm Mid-Century Modern Sofa 80\" - Pebble Weave Oatmeal",
        "description": "The West Elm Mid-Century Modern Sofa brings timeless design to your living room. Inspired by 1950s and 60s design with tapered solid wood legs in Acorn finish. Plush cushions with resilient foam core and fiber wrap for comfort and support. Sustainably sourced kiln-dried wood frame with reinforced joinery. Upholstered in durable Pebble Weave fabric that resists wear and staining. Clean lines and button-free cushions for a contemporary look. Easy assembly required.",
        "category": "Home & Kitchen",
        "subcategory": "Furniture",
        "brand": "West Elm",
        "price": 1499.00,
        "original_price": 1799.00,
        "currency": "USD",
        "attributes": {
            "brand": "West Elm",
            "style": "Mid-Century Modern",
            "color": "Oatmeal",
            "material": "Pebble Weave Fabric, Solid Wood Legs",
            "dimensions": "80 x 35 x 34 inches",
            "room_type": "Living Room"
        },
        "image_url": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 23,
        "payment_options": ["credit", "debit", "bnpl", "financing"],
        "rating_avg": 4.4,
        "review_count": 1234,
        "tags": ["sofa", "mid-century", "modern", "living room", "furniture", "west elm"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "IKEA MALM Queen Bed Frame with 4 Storage Drawers - White",
        "description": "The IKEA MALM bed frame with storage maximizes your bedroom space. Features 4 large integrated drawers for extra storage - perfect for bedding, clothes, or seasonal items. Clean, simple design works with any bedroom decor. Adjustable bed sides for use with mattresses of different thicknesses. 17 slats of layered birch adjust to your body weight. Easy assembly with included tools. Coordinates with other MALM furniture for a cohesive look.",
        "category": "Home & Kitchen",
        "subcategory": "Furniture",
        "brand": "IKEA",
        "price": 349.00,
        "original_price": 399.00,
        "currency": "USD",
        "attributes": {
            "brand": "IKEA",
            "model": "MALM",
            "color": "White",
            "material": "Particleboard, Fiberboard",
            "dimensions": "83.5 x 66.1 x 15 inches",
            "size": "Queen",
            "room_type": "Bedroom"
        },
        "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 67,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.3,
        "review_count": 23456,
        "tags": ["bed frame", "ikea", "malm", "storage", "queen bed", "bedroom", "furniture"]
    },

    # ==================== BOOKS & MEDIA ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Atomic Habits by James Clear - Hardcover",
        "description": "Atomic Habits by James Clear is the #1 New York Times bestseller that reveals the proven framework for building good habits and breaking bad ones. Learn how tiny changes can lead to remarkable results. Clear draws on biology, psychology, and neuroscience to explain how habits work and offers practical strategies for making time for new habits, overcoming lack of motivation, and designing your environment for success. Over 10 million copies sold worldwide.",
        "category": "Books & Media",
        "subcategory": "Non-Fiction",
        "brand": "Avery",
        "price": 19.99,
        "original_price": 27.00,
        "currency": "USD",
        "attributes": {
            "author": "James Clear",
            "publisher": "Avery",
            "pages": 320,
            "format": "Hardcover",
            "language": "English",
            "isbn": "978-0735211292",
            "genre": "Self-Help, Psychology"
        },
        "image_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 534,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.8,
        "review_count": 145678,
        "tags": ["book", "self-help", "habits", "psychology", "bestseller", "productivity"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Python Crash Course, 3rd Edition - Eric Matthes",
        "description": "Python Crash Course is the world's best-selling Python book, now updated for Python 3.11. This fast-paced introduction will have you writing programs, solving problems, and developing applications in no time. Part 1 covers programming basics including variables, lists, classes, and loops. Part 2 puts your knowledge into practice with three projects: an arcade game, data visualizations, and a web app. Perfect for beginners or experienced programmers new to Python.",
        "category": "Books & Media",
        "subcategory": "Technical & Programming",
        "brand": "No Starch Press",
        "price": 35.99,
        "original_price": 45.99,
        "currency": "USD",
        "attributes": {
            "author": "Eric Matthes",
            "publisher": "No Starch Press",
            "pages": 552,
            "format": "Paperback",
            "language": "English",
            "isbn": "978-1718502703",
            "genre": "Programming, Technology"
        },
        "image_url": "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 234,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.7,
        "review_count": 8765,
        "tags": ["book", "programming", "python", "coding", "tech", "beginner", "learning"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Project Hail Mary by Andy Weir - Paperback",
        "description": "From the author of The Martian comes another epic tale of survival. Ryland Grace is the sole survivor on a desperate mission - the only person who can save Earth from extinction. But he doesn't know that yet. He's in space, with no memory of who he is or why he's there. What follows is a gripping adventure filled with science, humor, and heart. A story of friendship across impossible distances and the determination of humanity to survive against all odds.",
        "category": "Books & Media",
        "subcategory": "Fiction",
        "brand": "Ballantine Books",
        "price": 16.99,
        "original_price": 18.00,
        "currency": "USD",
        "attributes": {
            "author": "Andy Weir",
            "publisher": "Ballantine Books",
            "pages": 496,
            "format": "Paperback",
            "language": "English",
            "isbn": "978-0593395561",
            "genre": "Science Fiction, Thriller"
        },
        "image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 345,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.9,
        "review_count": 98765,
        "tags": ["book", "science fiction", "sci-fi", "andy weir", "space", "thriller"]
    },

    # ==================== SPORTS & FITNESS ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Bowflex SelectTech 552 Adjustable Dumbbells - Pair",
        "description": "Bowflex SelectTech 552 replaces 15 sets of weights with one compact design. Each dumbbell adjusts from 5 to 52.5 lbs in 2.5 lb increments up to 25 lbs, then 5 lb increments. Patented dial system lets you switch weights in seconds - simply turn the dial to select your weight and lift. Durable metal plates with molded surrounds for quiet workouts. Compatible with free Bowflex JRNY app for personalized workouts. 2-year warranty. Space-saving design for home gyms.",
        "category": "Sports & Fitness",
        "subcategory": "Exercise Equipment",
        "brand": "Bowflex",
        "price": 429.00,
        "original_price": 549.00,
        "currency": "USD",
        "attributes": {
            "brand": "Bowflex",
            "model": "SelectTech 552",
            "weight_range": "5-52.5 lbs each",
            "material": "Steel, Molded Plates",
            "dimensions": "16.9 x 8 x 9 inches each"
        },
        "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 89,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.7,
        "review_count": 23456,
        "tags": ["dumbbells", "adjustable weights", "bowflex", "home gym", "strength training", "fitness"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Peloton Bike+ - Indoor Exercise Bike with HD Touchscreen",
        "description": "The Peloton Bike+ is the ultimate connected fitness experience. Features a 23.8-inch HD touchscreen that rotates for off-bike workouts. Auto-Resistance automatically adjusts to instructor cues. Apple GymKit integration for seamless Apple Watch pairing. 4-channel rear-facing speakers with 2 front-facing tweeters for immersive sound. Upgraded 3.0 rear stabilizers for extra stability. Access thousands of live and on-demand classes including cycling, strength, yoga, and more.",
        "category": "Sports & Fitness",
        "subcategory": "Exercise Equipment",
        "brand": "Peloton",
        "price": 2495.00,
        "original_price": 2495.00,
        "currency": "USD",
        "attributes": {
            "brand": "Peloton",
            "model": "Bike+",
            "screen_size": "23.8 inches",
            "dimensions": "59 x 22 x 59 inches",
            "weight_capacity": "297 lbs"
        },
        "image_url": "https://images.unsplash.com/photo-1591291621164-2c6367723315?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 34,
        "payment_options": ["credit", "debit", "bnpl", "financing"],
        "rating_avg": 4.6,
        "review_count": 12345,
        "tags": ["exercise bike", "peloton", "indoor cycling", "cardio", "home fitness", "connected fitness"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Manduka PRO Yoga Mat 6mm - Black",
        "description": "The Manduka PRO is the gold standard for yoga mats. Ultra-dense cushioning protects joints during intense practice. Closed-cell surface prevents sweat from seeping in, keeping it hygienic and odor-free. Non-toxic, emissions-free manufacturing with lifetime guarantee. 6mm thickness provides unmatched support. Non-slip fabric-like finish improves with use. 71 x 26 inch size fits most practitioners. Break-in period required - mat will become more grippy over time.",
        "category": "Sports & Fitness",
        "subcategory": "Yoga & Pilates",
        "brand": "Manduka",
        "price": 120.00,
        "original_price": 134.00,
        "currency": "USD",
        "attributes": {
            "brand": "Manduka",
            "model": "PRO",
            "thickness": "6mm",
            "dimensions": "71 x 26 inches",
            "material": "PVC",
            "color": "Black"
        },
        "image_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 234,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.8,
        "review_count": 15678,
        "tags": ["yoga mat", "manduka", "yoga", "pilates", "fitness", "exercise mat"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "The North Face Base Camp Duffel Large - TNF Black",
        "description": "The North Face Base Camp Duffel is built for expeditions and everyday adventures. Durable, water-resistant Base Camp fabric made from recycled materials. Large 95L capacity with D-zip opening for easy access. Padded side handles and adjustable, alpine-cut shoulder straps for versatile carrying. Internal mesh pocket and zippered pocket in lid keep gear organized. Durable, reflective screenprinted logos. Backed by lifetime warranty.",
        "category": "Sports & Fitness",
        "subcategory": "Outdoor Recreation",
        "brand": "The North Face",
        "price": 159.00,
        "original_price": 179.00,
        "currency": "USD",
        "attributes": {
            "brand": "The North Face",
            "model": "Base Camp Duffel L",
            "capacity": "95L",
            "material": "Recycled Polyester",
            "dimensions": "28 x 15 x 15 inches",
            "color": "TNF Black"
        },
        "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 123,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.7,
        "review_count": 8765,
        "tags": ["duffel bag", "north face", "travel", "outdoor", "gym bag", "adventure"]
    },

    # ==================== BEAUTY & PERSONAL CARE ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "La Mer Crème de la Mer Moisturizing Cream - 2 oz",
        "description": "La Mer Crème de la Mer is the legendary moisturizer that started a skincare revolution. At its heart is the Miracle Broth - a cell-renewing elixir that took 12 years to perfect. This ultra-rich cream deeply moisturizes and helps heal dryness, revealing softer, smoother, more radiant skin. Suitable for all skin types, especially dry skin. Gently warm product between fingers and press into skin morning and night. The ultimate luxury in skincare.",
        "category": "Beauty & Personal Care",
        "subcategory": "Skincare",
        "brand": "La Mer",
        "price": 380.00,
        "original_price": 380.00,
        "currency": "USD",
        "attributes": {
            "brand": "La Mer",
            "product_type": "Moisturizing Cream",
            "volume": "2 oz / 60ml",
            "skin_type": "All Skin Types",
            "key_ingredient": "Miracle Broth"
        },
        "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 56,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.6,
        "review_count": 3456,
        "tags": ["moisturizer", "la mer", "luxury skincare", "anti-aging", "hydrating", "cream"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "The Ordinary Hyaluronic Acid 2% + B5 - 30ml",
        "description": "The Ordinary Hyaluronic Acid 2% + B5 delivers powerful hydration at an affordable price. Features low, medium, and high molecular weight hyaluronic acid plus a next-generation HA crosspolymer for multi-depth hydration. Vitamin B5 enhances surface hydration. Water-based, oil-free formula suitable for all skin types. Apply a few drops to face morning and evening before oils and creams. Vegan, cruelty-free, and free from parabens, sulfates, and mineral oil.",
        "category": "Beauty & Personal Care",
        "subcategory": "Skincare",
        "brand": "The Ordinary",
        "price": 8.90,
        "original_price": 8.90,
        "currency": "USD",
        "attributes": {
            "brand": "The Ordinary",
            "product_type": "Serum",
            "volume": "30ml",
            "skin_type": "All Skin Types",
            "key_ingredient": "Hyaluronic Acid, Vitamin B5"
        },
        "image_url": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 567,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.5,
        "review_count": 89765,
        "tags": ["serum", "hyaluronic acid", "the ordinary", "hydrating", "affordable skincare", "budget"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Dyson Airwrap Complete Long Multi-Styler - Nickel/Copper",
        "description": "The Dyson Airwrap multi-styler uses the Coanda effect to curl, wave, smooth, and dry hair with no extreme heat. Long barrel designed for longer hair. Enhanced Coanda airflow for faster, easier styling. Intelligent heat control measures temperature 40+ times per second. Includes 1.2in and 1.6in Airwrap barrels, Coanda smoothing dryer, Firm smoothing brush, Soft smoothing brush, and Round volumizing brush. Presentation case and filter cleaning brush included.",
        "category": "Beauty & Personal Care",
        "subcategory": "Hair Care",
        "brand": "Dyson",
        "price": 599.99,
        "original_price": 599.99,
        "currency": "USD",
        "attributes": {
            "brand": "Dyson",
            "model": "Airwrap Complete Long",
            "color": "Nickel/Copper",
            "heat_settings": "3",
            "attachments": "6 styling attachments"
        },
        "image_url": "https://images.unsplash.com/photo-1522338140262-f46f5913618a?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 45,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.4,
        "review_count": 12345,
        "tags": ["hair styler", "dyson", "airwrap", "curling", "blow dryer", "beauty tools"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Charlotte Tilbury Pillow Talk Lipstick - Matte Revolution",
        "description": "Charlotte Tilbury's iconic Pillow Talk is the world's #1 nude-pink lipstick. The Matte Revolution formula combines 3D pigments, orchid extract, and lipstick tree for bold, buildable color with a soft-focus, matte finish. Square-angled tip allows for precise application without lip liner. Hydrating formula glides on smoothly and wears comfortably for hours. The universally flattering shade complements all skin tones. As seen on countless celebrities and red carpets.",
        "category": "Beauty & Personal Care",
        "subcategory": "Makeup",
        "brand": "Charlotte Tilbury",
        "price": 34.00,
        "original_price": 34.00,
        "currency": "USD",
        "attributes": {
            "brand": "Charlotte Tilbury",
            "product_type": "Lipstick",
            "shade": "Pillow Talk",
            "finish": "Matte",
            "volume": "3.5g"
        },
        "image_url": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 234,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.7,
        "review_count": 45678,
        "tags": ["lipstick", "charlotte tilbury", "pillow talk", "nude pink", "matte", "makeup"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Dior Sauvage Eau de Parfum - 3.4 oz",
        "description": "Dior Sauvage Eau de Parfum is a bold, powerful fragrance inspired by wide-open spaces. Calabrian bergamot and Sichuan pepper create a fresh, spicy opening. Heart notes of lavender and star anise add aromatic depth. Base of Ambroxan, cedar, and vanilla bourbon deliver a warm, addictive trail. Long-lasting sillage that evolves throughout the day. The iconic blue bottle represents the magic hour between day and night. A modern classic for the confident man.",
        "category": "Beauty & Personal Care",
        "subcategory": "Fragrances",
        "brand": "Dior",
        "price": 155.00,
        "original_price": 165.00,
        "currency": "USD",
        "attributes": {
            "brand": "Dior",
            "product_type": "Eau de Parfum",
            "volume": "3.4 oz / 100ml",
            "concentration": "EDP",
            "gender": "Men",
            "scent_family": "Woody, Fresh, Spicy"
        },
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 123,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.8,
        "review_count": 34567,
        "tags": ["fragrance", "cologne", "dior", "sauvage", "mens fragrance", "perfume", "edp"]
    },

    # ==================== ELECTRONICS - CAMERAS ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Sony Alpha a7 IV Mirrorless Camera Body Only",
        "description": "The Sony a7 IV is the perfect hybrid camera for photo and video creators. Features a new 33MP full-frame Exmor R CMOS sensor with BIONZ XR processor. Real-time Eye AF for humans, animals, and birds. 10fps continuous shooting with full AF/AE tracking. 4K 60p video with 10-bit 4:2:2 color and S-Log3 support. 5-axis in-body image stabilization effective up to 5.5 stops. 3.0\" fully articulating touchscreen LCD. Dual card slots (CFexpress Type A / SD UHS-II).",
        "category": "Electronics",
        "subcategory": "Cameras",
        "brand": "Sony",
        "price": 2498.00,
        "original_price": 2498.00,
        "currency": "USD",
        "attributes": {
            "brand": "Sony",
            "model": "Alpha a7 IV",
            "sensor": "33MP Full-Frame",
            "video": "4K 60p",
            "iso_range": "100-51200",
            "stabilization": "5-axis IBIS"
        },
        "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 34,
        "payment_options": ["credit", "debit", "bnpl", "financing"],
        "rating_avg": 4.8,
        "review_count": 2345,
        "tags": ["camera", "mirrorless", "sony", "full frame", "photography", "video", "4k"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "GoPro HERO12 Black - Waterproof Action Camera",
        "description": "GoPro HERO12 Black captures life's best moments in stunning detail. Record 5.3K60 and 4K120 video, or shoot 27MP photos. HyperSmooth 6.0 stabilization eliminates shake for incredibly smooth footage. 10-bit color delivers billion-shade color depth. HDR video and photos with improved dynamic range. Waterproof to 33ft without housing. New Max Lens Mod 2.0 compatibility for ultra-wide 177° FOV. Enduro battery included for extended cold-weather shooting. Rugged and reliable for any adventure.",
        "category": "Electronics",
        "subcategory": "Cameras",
        "brand": "GoPro",
        "price": 399.99,
        "original_price": 449.99,
        "currency": "USD",
        "attributes": {
            "brand": "GoPro",
            "model": "HERO12 Black",
            "video_resolution": "5.3K60, 4K120",
            "photo_resolution": "27MP",
            "waterproof": "33ft / 10m",
            "stabilization": "HyperSmooth 6.0"
        },
        "image_url": "https://images.unsplash.com/photo-1565155785155-33fc8ede33a0?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 156,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.5,
        "review_count": 8765,
        "tags": ["action camera", "gopro", "waterproof", "4k", "adventure", "vlogging", "sports"]
    },

    # ==================== GAMING ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Sony PlayStation 5 Console - Disc Edition",
        "description": "Experience lightning-fast loading with the PS5's ultra-high speed SSD, deeper immersion with haptic feedback, adaptive triggers and 3D Audio, and an all-new generation of incredible PlayStation games. Ray tracing delivers stunning graphics with realistic lighting and shadows. 4K-TV gaming at up to 120fps with support for 120Hz output. HDR technology brings incredible colors and brightness. Includes DualSense wireless controller with innovative features.",
        "category": "Electronics",
        "subcategory": "Gaming",
        "brand": "Sony",
        "price": 499.99,
        "original_price": 499.99,
        "currency": "USD",
        "attributes": {
            "brand": "Sony",
            "model": "PlayStation 5",
            "storage": "825GB SSD",
            "resolution": "Up to 8K",
            "frame_rate": "Up to 120fps",
            "color": "White"
        },
        "image_url": "https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 78,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.9,
        "review_count": 156789,
        "tags": ["gaming console", "playstation", "ps5", "sony", "gaming", "4k", "ray tracing"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Nintendo Switch OLED Model - White",
        "description": "Meet the Nintendo Switch OLED Model with a vibrant 7-inch OLED screen. Play at home on the TV, or pick up and continue playing in tabletop or handheld modes. The upgraded screen offers vivid colors and crisp contrast. Enhanced audio from the system's speakers. Wide adjustable stand for tabletop play. 64GB internal storage (expandable via microSD). Wired LAN port on dock for stable online play. Includes white Joy-Con controllers and dock.",
        "category": "Electronics",
        "subcategory": "Gaming",
        "brand": "Nintendo",
        "price": 349.99,
        "original_price": 349.99,
        "currency": "USD",
        "attributes": {
            "brand": "Nintendo",
            "model": "Switch OLED Model",
            "storage": "64GB",
            "screen_size": "7 inches",
            "display_type": "OLED",
            "color": "White"
        },
        "image_url": "https://images.unsplash.com/photo-1578303512597-81e6cc155b3e?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 123,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.8,
        "review_count": 98765,
        "tags": ["gaming console", "nintendo", "switch", "oled", "portable gaming", "handheld"]
    },

    # ==================== MORE BUDGET OPTIONS ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Anker PowerCore 10000 Portable Charger - Black",
        "description": "The Anker PowerCore 10000 is one of the most compact 10000mAh portable chargers. About the size of a credit card but slightly thicker. PowerIQ and VoltageBoost technologies provide the fastest possible charge for any device. Charges iPhone 15 about 2.5 times, Samsung Galaxy S24 about 2 times. MultiProtect safety system with surge protection, temperature control, and more. USB-A output with 12W max. Includes travel pouch and Micro USB cable.",
        "category": "Electronics",
        "subcategory": "Computer Accessories",
        "brand": "Anker",
        "price": 25.99,
        "original_price": 29.99,
        "currency": "USD",
        "attributes": {
            "brand": "Anker",
            "model": "PowerCore 10000",
            "capacity": "10000mAh",
            "output": "12W USB-A",
            "color": "Black",
            "weight": "6.4 oz"
        },
        "image_url": "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 567,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.6,
        "review_count": 234567,
        "tags": ["power bank", "portable charger", "anker", "budget", "travel", "phone accessories"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "CeraVe Daily Moisturizing Lotion - 12 oz",
        "description": "CeraVe Daily Moisturizing Lotion provides 24-hour hydration with essential ceramides. Developed with dermatologists, this lightweight, oil-free formula contains 3 essential ceramides (1, 3, 6-II) to help restore the skin's natural barrier. Hyaluronic acid helps retain skin's natural moisture. MVE Delivery Technology provides controlled release of ingredients for all-day hydration. Fragrance-free, non-comedogenic, and accepted by the National Eczema Association.",
        "category": "Beauty & Personal Care",
        "subcategory": "Skincare",
        "brand": "CeraVe",
        "price": 15.99,
        "original_price": 18.99,
        "currency": "USD",
        "attributes": {
            "brand": "CeraVe",
            "product_type": "Moisturizing Lotion",
            "volume": "12 oz / 355ml",
            "skin_type": "Normal to Dry",
            "key_ingredient": "Ceramides, Hyaluronic Acid"
        },
        "image_url": "https://images.unsplash.com/photo-1611930022073-b7a4ba5fcccd?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 789,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.7,
        "review_count": 156789,
        "tags": ["moisturizer", "cerave", "ceramides", "budget skincare", "dermatologist recommended"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Amazon Basics Resistance Bands Set - 5 Pack",
        "description": "Amazon Basics 5-piece resistance band set for full-body workouts at home or on the go. Includes 5 color-coded bands with different resistance levels: Extra Light (Yellow), Light (Green), Medium (Red), Heavy (Blue), and Extra Heavy (Black). Made from durable natural latex. Portable and lightweight - includes carrying bag for travel. Great for strength training, physical therapy, yoga, pilates, and stretching. Exercise guide included.",
        "category": "Sports & Fitness",
        "subcategory": "Fitness Accessories",
        "brand": "Amazon Basics",
        "price": 14.99,
        "original_price": 19.99,
        "currency": "USD",
        "attributes": {
            "brand": "Amazon Basics",
            "quantity": "5 bands",
            "material": "Natural Latex",
            "resistance_levels": "Extra Light to Extra Heavy"
        },
        "image_url": "https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 1234,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.4,
        "review_count": 98765,
        "tags": ["resistance bands", "workout", "home gym", "budget", "fitness", "exercise bands"]
    },

    # ==================== BAGS & ACCESSORIES ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Herschel Supply Co. Classic Backpack XL - Black",
        "description": "The Herschel Classic XL is an iconic backpack reimagined for the modern commuter. Increased 26L capacity fits 15\" laptops comfortably. Signature striped fabric liner adds a distinctive touch. Reinforced bottom with extra durability. Front storage pocket with key clip. Padded and fleece-lined 15\" laptop sleeve. Contoured shoulder straps for all-day comfort. Made from durable 600D polyester. Internal media pocket with headphone port.",
        "category": "Fashion",
        "subcategory": "Bags & Accessories",
        "brand": "Herschel Supply Co.",
        "price": 74.99,
        "original_price": 80.00,
        "currency": "USD",
        "attributes": {
            "brand": "Herschel Supply Co.",
            "model": "Classic XL",
            "capacity": "26L",
            "material": "600D Polyester",
            "laptop_size": "15 inches",
            "color": "Black"
        },
        "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 234,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.5,
        "review_count": 23456,
        "tags": ["backpack", "herschel", "laptop bag", "commuter", "school", "travel"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Ray-Ban Wayfarer Classic Sunglasses - Black/Green",
        "description": "The Ray-Ban Wayfarer is the most recognized style in the history of sunglasses. Since its introduction in 1952, the Wayfarer has become a cultural icon. Features classic black acetate frame with G-15 green crystal lenses that provide excellent clarity and comfort. 100% UV protection. 54mm lens width fits most face shapes. Made in Italy with premium materials and craftsmanship. Includes branded case and cleaning cloth.",
        "category": "Fashion",
        "subcategory": "Bags & Accessories",
        "brand": "Ray-Ban",
        "price": 171.00,
        "original_price": 195.00,
        "currency": "USD",
        "attributes": {
            "brand": "Ray-Ban",
            "model": "Wayfarer Classic",
            "lens_color": "Green G-15",
            "frame_color": "Black",
            "lens_width": "54mm",
            "material": "Acetate"
        },
        "image_url": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 189,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.7,
        "review_count": 45678,
        "tags": ["sunglasses", "ray-ban", "wayfarer", "classic", "accessories", "eyewear"]
    },

    # ==================== COFFEE & KITCHEN ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Breville Barista Express Espresso Machine - Stainless Steel",
        "description": "The Breville Barista Express delivers third wave specialty coffee at home. Integrated conical burr grinder grinds beans immediately before extraction for maximum freshness. Optimal water pressure with digital temperature control (PID) for precise espresso. Micro-foam milk texturing for latte art. Includes 54mm portafilter, single and dual wall filter baskets, tamper, and milk jug. Hands-free operation with auto-purge function. Bean hopper holds 1/2 lb.",
        "category": "Home & Kitchen",
        "subcategory": "Kitchen Appliances",
        "brand": "Breville",
        "price": 749.95,
        "original_price": 849.95,
        "currency": "USD",
        "attributes": {
            "brand": "Breville",
            "model": "Barista Express BES870XL",
            "color": "Stainless Steel",
            "pump_pressure": "15 bar",
            "grinder": "Integrated Conical Burr",
            "water_tank": "67 oz"
        },
        "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 45,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.6,
        "review_count": 12345,
        "tags": ["espresso machine", "breville", "coffee maker", "barista", "grinder", "latte"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Le Creuset Signature Enameled Cast Iron Dutch Oven 5.5 Qt - Flame",
        "description": "The Le Creuset Signature Dutch Oven is the ultimate kitchen essential. Superior heat distribution and retention from enameled cast iron. Colorful exterior enamel resists chipping and cracking. Sand-colored interior enamel makes monitoring food easy. Ergonomic handles for secure grip. Tight-fitting lid locks in moisture. Oven safe to 500°F. Suitable for all cooking surfaces including induction. Dishwasher safe but hand wash recommended. 5.5 qt size serves 5-6.",
        "category": "Home & Kitchen",
        "subcategory": "Cookware",
        "brand": "Le Creuset",
        "price": 419.95,
        "original_price": 449.95,
        "currency": "USD",
        "attributes": {
            "brand": "Le Creuset",
            "model": "Signature Round Dutch Oven",
            "capacity": "5.5 Quarts",
            "material": "Enameled Cast Iron",
            "color": "Flame",
            "dimensions": "10.25 inches diameter"
        },
        "image_url": "https://images.unsplash.com/photo-1584990347449-a2d4c89bdee5?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 67,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.9,
        "review_count": 23456,
        "tags": ["dutch oven", "le creuset", "cast iron", "cookware", "kitchen", "braising"]
    },
]


def add_timestamps(products: List[Dict]) -> List[Dict]:
    """Add realistic timestamps to products."""
    now = datetime.utcnow()
    for i, product in enumerate(products):
        # Spread creation dates over the past year
        days_ago = random.randint(1, 365)
        created_at = now - timedelta(days=days_ago)
        product["created_at"] = created_at.isoformat()
        
        # 70% chance of having an update
        if random.random() < 0.7:
            update_days = random.randint(0, days_ago - 1) if days_ago > 1 else 0
            updated_at = now - timedelta(days=update_days)
            product["updated_at"] = updated_at.isoformat()
        else:
            product["updated_at"] = None
            
    return products


def generate_sample_products() -> List[Dict]:
    """Generate and return sample products with timestamps."""
    products = add_timestamps(SAMPLE_PRODUCTS.copy())
    
    # Regenerate unique IDs
    for product in products:
        product["id"] = f"prod_{uuid.uuid4().hex[:12]}"
    
    return products


def save_to_json(products: List[Dict], filename: str = "sample_products.json"):
    """Save products to JSON file."""
    import os
    from pathlib import Path
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    output_dir = script_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / filename
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(products)} products to {output_path}")
    return str(output_path)


def print_summary(products: List[Dict]):
    """Print summary of generated products."""
    print("\n" + "="*60)
    print("SAMPLE PRODUCTS GENERATED")
    print("="*60)
    
    # Count by category
    categories = {}
    for p in products:
        cat = p["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\nTotal Products: {len(products)}")
    print("\nBy Category:")
    for cat, count in sorted(categories.items()):
        print(f"  • {cat}: {count}")
    
    # Price range
    prices = [p["price"] for p in products]
    print(f"\nPrice Range: ${min(prices):.2f} - ${max(prices):.2f}")
    print(f"Average Price: ${sum(prices)/len(prices):.2f}")
    
    # Brands
    brands = set(p["brand"] for p in products)
    print(f"\nUnique Brands: {len(brands)}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    print("Generating sample products with real images...")
    
    products = generate_sample_products()
    print_summary(products)
    
    # Save to JSON
    output_file = save_to_json(products)
    
    print(f"\n✓ Sample data ready!")
    print(f"  File: {output_file}")
    print(f"  Products: {len(products)}")
    print("\nTo upload to Qdrant, run:")
    print("  python -m data_generation.upload_and_verify")

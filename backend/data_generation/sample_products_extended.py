#!/usr/bin/env python3
"""
Extended Sample Product Data Generator - Part 2

More realistic products with real images for FinFind.
"""

import json
import uuid
from datetime import datetime, timedelta, timezone
import random
from typing import List, Dict, Any
from pathlib import Path

EXTENDED_PRODUCTS: List[Dict[str, Any]] = [
    # ==================== ELECTRONICS - MORE LAPTOPS ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Microsoft Surface Laptop 5 15\" - Intel Core i7, 16GB RAM, 512GB SSD, Platinum",
        "description": "The Microsoft Surface Laptop 5 combines elegant design with powerful performance. Features 12th Gen Intel Core i7-1255U processor, 16GB RAM, and 512GB SSD. The stunning 15-inch PixelSense touchscreen display with 3:2 aspect ratio is perfect for productivity. Dolby Atmos speakers and Studio Mics for crystal-clear calls. Windows 11 with seamless Microsoft 365 integration. All-day battery life up to 17 hours. Alcantara palm rest for premium comfort.",
        "category": "Electronics",
        "subcategory": "Laptops",
        "brand": "Microsoft",
        "price": 1499.99,
        "original_price": 1699.99,
        "currency": "USD",
        "attributes": {
            "brand": "Microsoft",
            "model": "Surface Laptop 5",
            "processor": "Intel Core i7-1255U",
            "ram": "16GB",
            "storage": "512GB SSD",
            "screen_size": "15 inches",
            "battery_life": "17 hours",
            "color": "Platinum",
            "connectivity": ["WiFi 6", "Bluetooth 5.1", "USB-C", "USB-A"]
        },
        "image_url": "https://images.unsplash.com/photo-1587614382346-4ec70e388b28?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 42,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.5,
        "review_count": 1876,
        "tags": ["laptop", "microsoft", "surface", "touchscreen", "windows", "ultrabook", "productivity"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Acer Chromebook Spin 714 - Intel Core i5, 8GB RAM, 256GB SSD",
        "description": "The Acer Chromebook Spin 714 is the ultimate Chrome OS productivity machine. Features 12th Gen Intel Core i5-1235U, 8GB RAM, and 256GB SSD. 14-inch WUXGA IPS touchscreen with 360° hinge for laptop, tablet, tent, and display modes. Military-grade durability (MIL-STD 810H). Built-in USI stylus garage. Thunderbolt 4 port for fast data and charging. Up to 10 hours battery life. Google Assistant and fast boot in seconds.",
        "category": "Electronics",
        "subcategory": "Laptops",
        "brand": "Acer",
        "price": 729.00,
        "original_price": 849.00,
        "currency": "USD",
        "attributes": {
            "brand": "Acer",
            "model": "Chromebook Spin 714",
            "processor": "Intel Core i5-1235U",
            "ram": "8GB",
            "storage": "256GB SSD",
            "screen_size": "14 inches",
            "battery_life": "10 hours",
            "color": "Steel Gray",
            "connectivity": ["WiFi 6E", "Bluetooth 5.2", "Thunderbolt 4"]
        },
        "image_url": "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 67,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.4,
        "review_count": 2341,
        "tags": ["chromebook", "acer", "2-in-1", "touchscreen", "convertible", "chrome os"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Razer Blade 15 Gaming Laptop - Intel i9, RTX 4070, 32GB RAM, QHD 240Hz",
        "description": "The Razer Blade 15 is the ultimate gaming laptop for enthusiasts. Powered by Intel Core i9-13950HX and NVIDIA GeForce RTX 4070 with 8GB VRAM. 32GB DDR5 RAM and 1TB PCIe Gen 4 SSD. 15.6-inch QHD 240Hz display with 100% DCI-P3 for buttery-smooth gameplay. CNC aluminum unibody with per-key RGB Chroma lighting. Vapor chamber cooling keeps thermals in check. THX Spatial Audio for immersive sound.",
        "category": "Electronics",
        "subcategory": "Laptops",
        "brand": "Razer",
        "price": 2799.99,
        "original_price": 2999.99,
        "currency": "USD",
        "attributes": {
            "brand": "Razer",
            "model": "Blade 15",
            "processor": "Intel Core i9-13950HX",
            "gpu": "NVIDIA RTX 4070 8GB",
            "ram": "32GB DDR5",
            "storage": "1TB PCIe Gen 4 SSD",
            "screen_size": "15.6 inches",
            "refresh_rate": "240Hz",
            "color": "Black",
            "connectivity": ["WiFi 6E", "Bluetooth 5.3", "Thunderbolt 4"]
        },
        "image_url": "https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 23,
        "payment_options": ["credit", "debit", "bnpl", "financing"],
        "rating_avg": 4.6,
        "review_count": 1234,
        "tags": ["gaming laptop", "razer", "rtx 4070", "high refresh rate", "rgb", "premium gaming"]
    },

    # ==================== ELECTRONICS - MORE SMARTPHONES ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Xiaomi 14 Ultra - 512GB, Black, Leica Camera System",
        "description": "The Xiaomi 14 Ultra represents the pinnacle of mobile photography. Co-engineered with Leica, it features a revolutionary 1-inch main sensor with variable aperture (f/1.63-f/4.0). Quad camera system includes 50MP main, 50MP periscope telephoto (5x), 50MP floating telephoto (3.2x), and 12MP ultrawide. Snapdragon 8 Gen 3 processor, 16GB RAM, 512GB storage. 6.73-inch 2K LTPO AMOLED display with 120Hz. 5000mAh battery with 90W wired and 80W wireless charging.",
        "category": "Electronics",
        "subcategory": "Smartphones",
        "brand": "Xiaomi",
        "price": 1299.00,
        "original_price": 1499.00,
        "currency": "USD",
        "attributes": {
            "brand": "Xiaomi",
            "model": "14 Ultra",
            "processor": "Snapdragon 8 Gen 3",
            "ram": "16GB",
            "storage": "512GB",
            "screen_size": "6.73 inches",
            "camera": "50MP + 50MP + 50MP + 12MP",
            "battery_life": "5000mAh",
            "color": "Black",
            "connectivity": ["5G", "WiFi 7", "Bluetooth 5.4", "NFC"]
        },
        "image_url": "https://images.unsplash.com/photo-1565849904461-04a58ad377e0?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 45,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.7,
        "review_count": 1567,
        "tags": ["smartphone", "xiaomi", "leica", "camera phone", "flagship", "photography"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Nothing Phone (2) - 256GB, Dark Gray, Glyph Interface",
        "description": "Nothing Phone (2) redefines smartphone design with its unique Glyph Interface - 11 LED strips that light up for notifications, charging status, and more. Snapdragon 8+ Gen 1 processor, 12GB RAM, 256GB storage. 6.7-inch LTPO AMOLED display with 120Hz adaptive refresh. 50MP dual camera with Sony sensor and OIS. Clean Nothing OS based on Android for a bloat-free experience. 4700mAh battery with 45W fast charging. Recycled aluminum frame.",
        "category": "Electronics",
        "subcategory": "Smartphones",
        "brand": "Nothing",
        "price": 599.00,
        "original_price": 699.00,
        "currency": "USD",
        "attributes": {
            "brand": "Nothing",
            "model": "Phone (2)",
            "processor": "Snapdragon 8+ Gen 1",
            "ram": "12GB",
            "storage": "256GB",
            "screen_size": "6.7 inches",
            "camera": "50MP + 50MP",
            "battery_life": "4700mAh",
            "color": "Dark Gray",
            "connectivity": ["5G", "WiFi 6E", "Bluetooth 5.3", "NFC"]
        },
        "image_url": "https://images.unsplash.com/photo-1605236453806-6ff36851218e?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 78,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.4,
        "review_count": 3456,
        "tags": ["smartphone", "nothing", "unique design", "led", "glyph", "minimalist"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Motorola Edge 50 Pro - 256GB, Black Beauty, AI Features",
        "description": "Motorola Edge 50 Pro brings premium features at a competitive price. Features Snapdragon 7 Gen 3 processor, 12GB RAM, and 256GB storage. 6.7-inch pOLED display with 144Hz refresh rate and HDR10+. 50MP triple camera with OIS and AI-powered features for stunning photos. 4500mAh battery with incredible 125W TurboPower charging - 0 to 100% in just 19 minutes. 50W wireless charging support. IP68 water and dust resistance. Android 14 with 4 years of updates.",
        "category": "Electronics",
        "subcategory": "Smartphones",
        "brand": "Motorola",
        "price": 499.99,
        "original_price": 599.99,
        "currency": "USD",
        "attributes": {
            "brand": "Motorola",
            "model": "Edge 50 Pro",
            "processor": "Snapdragon 7 Gen 3",
            "ram": "12GB",
            "storage": "256GB",
            "screen_size": "6.7 inches",
            "camera": "50MP + 13MP + 10MP",
            "battery_life": "4500mAh",
            "color": "Black Beauty",
            "connectivity": ["5G", "WiFi 6E", "Bluetooth 5.3", "NFC"]
        },
        "image_url": "https://images.unsplash.com/photo-1574944985070-8f3ebc6b79d2?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 112,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.3,
        "review_count": 2345,
        "tags": ["smartphone", "motorola", "fast charging", "mid-range", "5g", "value"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Google Pixel 8a - 128GB, Bay, Best Value Pixel",
        "description": "Google Pixel 8a brings flagship AI features to an affordable price. Powered by Google Tensor G3 chip with 8GB RAM. 6.1-inch Actua OLED display with 120Hz smooth display. 64MP main camera with Magic Eraser, Photo Unblur, and Best Take. 7 years of OS and security updates - longest support on any phone. Face Unlock and under-display fingerprint. 4492mAh battery with Extreme Battery Saver. IP67 water resistance.",
        "category": "Electronics",
        "subcategory": "Smartphones",
        "brand": "Google",
        "price": 499.00,
        "original_price": 499.00,
        "currency": "USD",
        "attributes": {
            "brand": "Google",
            "model": "Pixel 8a",
            "processor": "Google Tensor G3",
            "ram": "8GB",
            "storage": "128GB",
            "screen_size": "6.1 inches",
            "camera": "64MP + 13MP",
            "battery_life": "4492mAh",
            "color": "Bay",
            "connectivity": ["5G", "WiFi 6E", "Bluetooth 5.3", "NFC"]
        },
        "image_url": "https://images.unsplash.com/photo-1585060544812-6b45742d762f?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 189,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.5,
        "review_count": 4567,
        "tags": ["smartphone", "pixel", "google", "ai", "budget flagship", "value", "camera"]
    },

    # ==================== ELECTRONICS - MORE HEADPHONES & AUDIO ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Sennheiser Momentum 4 Wireless Headphones - Black",
        "description": "Sennheiser Momentum 4 Wireless delivers audiophile-grade sound in a sleek package. 42mm transducers deliver exceptional clarity and deep bass. Adaptive Noise Cancellation adjusts to your environment. 60-hour battery life - the longest in its class. Comfortable leather ear cushions with memory foam. Sound Personalization via Sennheiser Smart Control app. Transparent Hearing mode for awareness. Folds flat for travel with premium case included.",
        "category": "Electronics",
        "subcategory": "Headphones",
        "brand": "Sennheiser",
        "price": 349.95,
        "original_price": 379.95,
        "currency": "USD",
        "attributes": {
            "brand": "Sennheiser",
            "model": "Momentum 4 Wireless",
            "color": "Black",
            "battery_life": "60 hours",
            "driver_size": "42mm",
            "connectivity": ["Bluetooth 5.2", "3.5mm", "USB-C"],
            "noise_canceling": "Yes",
            "weight": "293g"
        },
        "image_url": "https://images.unsplash.com/photo-1545127398-14699f92334b?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 56,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.7,
        "review_count": 2876,
        "tags": ["headphones", "sennheiser", "wireless", "audiophile", "noise canceling", "premium"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Samsung Galaxy Buds3 Pro - Silver, 360 Audio",
        "description": "Galaxy Buds3 Pro delivers an immersive audio experience with intelligent ANC. Dual drivers (10.5mm dynamic + 6.1mm planar) for rich, detailed sound. 360 Audio with head tracking for spatial sound experience. Enhanced ANC with Voice Detect automatically switches to Ambient mode when you speak. Blade Lights for a distinctive look. IPX7 water resistance. Up to 6 hours playback (30 hours with case). Seamless connectivity with Galaxy devices.",
        "category": "Electronics",
        "subcategory": "Headphones",
        "brand": "Samsung",
        "price": 249.99,
        "original_price": 279.99,
        "currency": "USD",
        "attributes": {
            "brand": "Samsung",
            "model": "Galaxy Buds3 Pro",
            "color": "Silver",
            "battery_life": "6 hours (30h with case)",
            "connectivity": ["Bluetooth 5.4"],
            "noise_canceling": "Yes",
            "water_resistant": "IPX7"
        },
        "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 134,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.5,
        "review_count": 3421,
        "tags": ["earbuds", "samsung", "galaxy buds", "true wireless", "anc", "spatial audio"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Sonos Era 300 Smart Speaker - White",
        "description": "Sonos Era 300 is designed from the ground up for spatial audio. Six precisely placed drivers deliver Dolby Atmos Music from above, behind, and in front of you. Advanced processing adapts the sound to your space with Trueplay tuning. Line-in port and Bluetooth for playing from any source. Voice control with Amazon Alexa or Sonos Voice Control. Easy control with capacitive touch. Sustainable design with post-consumer recycled plastics.",
        "category": "Electronics",
        "subcategory": "Speakers",
        "brand": "Sonos",
        "price": 449.00,
        "original_price": 449.00,
        "currency": "USD",
        "attributes": {
            "brand": "Sonos",
            "model": "Era 300",
            "color": "White",
            "drivers": "6",
            "connectivity": ["WiFi", "Bluetooth", "USB-C", "3.5mm"],
            "voice_assistant": "Amazon Alexa, Sonos Voice Control",
            "spatial_audio": "Dolby Atmos"
        },
        "image_url": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 45,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.6,
        "review_count": 1876,
        "tags": ["speaker", "sonos", "smart speaker", "dolby atmos", "spatial audio", "wireless"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Marshall Stanmore III Bluetooth Speaker - Black",
        "description": "Marshall Stanmore III brings legendary Marshall sound to your home. Features 50W Class D amplifier, 15W tweeter, and dual 15W mid-woofers for room-filling sound. Iconic vintage design with brass details and textured vinyl covering. Dynamic Loudness automatically adjusts bass and treble at any volume. Bluetooth 5.2 with aptX HD for high-resolution wireless audio. 3.5mm and RCA inputs. Marshall Bluetooth app for customizable EQ. Made from 70% recycled plastics.",
        "category": "Electronics",
        "subcategory": "Speakers",
        "brand": "Marshall",
        "price": 379.99,
        "original_price": 399.99,
        "currency": "USD",
        "attributes": {
            "brand": "Marshall",
            "model": "Stanmore III",
            "color": "Black",
            "power": "80W total",
            "connectivity": ["Bluetooth 5.2", "3.5mm", "RCA"],
            "dimensions": "13.78 x 7.48 x 6.77 inches"
        },
        "image_url": "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 67,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.7,
        "review_count": 4532,
        "tags": ["speaker", "marshall", "bluetooth", "vintage", "home audio", "rock"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Anker Soundcore Liberty 4 NC Earbuds - Velvet Black",
        "description": "Anker Soundcore Liberty 4 NC delivers premium ANC at an incredible price. 98.5% noise reduction with Adaptive ANC 2.0. LDAC support for Hi-Res Audio wireless. Personalized ANC and sound profile via HearID. 11mm drivers with graphene-coated diaphragms for punchy bass. 8 hours playtime with ANC on (50 hours total with case). 6 mics with AI-enhanced calls. Multipoint connection for seamless device switching. IPX4 water resistance.",
        "category": "Electronics",
        "subcategory": "Headphones",
        "brand": "Anker",
        "price": 99.99,
        "original_price": 149.99,
        "currency": "USD",
        "attributes": {
            "brand": "Anker",
            "model": "Soundcore Liberty 4 NC",
            "color": "Velvet Black",
            "battery_life": "8 hours (50h with case)",
            "connectivity": ["Bluetooth 5.3"],
            "noise_canceling": "Yes",
            "water_resistant": "IPX4"
        },
        "image_url": "https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 234,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.5,
        "review_count": 12345,
        "tags": ["earbuds", "anker", "soundcore", "budget", "anc", "hi-res audio", "value"]
    },

    # ==================== ELECTRONICS - TVs & MONITORS ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "LG C3 65\" OLED 4K Smart TV - evo Gallery Edition",
        "description": "LG C3 OLED delivers perfect blacks and infinite contrast with self-lit OLED pixels. α9 AI Processor Gen6 optimizes picture and sound in real-time. Dolby Vision IQ adjusts picture based on ambient light. Dolby Atmos for immersive audio. Perfect for gaming with 4 HDMI 2.1 ports, 4K@120Hz, VRR, ALLM, and 0.1ms response time. G-SYNC and FreeSync Premium certified. webOS 23 with 300+ streaming apps. Magic Remote with voice control included.",
        "category": "Electronics",
        "subcategory": "TV & Home Theater",
        "brand": "LG",
        "price": 1796.99,
        "original_price": 2099.99,
        "currency": "USD",
        "attributes": {
            "brand": "LG",
            "model": "OLED65C3PUA",
            "screen_size": "65 inches",
            "resolution": "4K UHD",
            "display_type": "OLED",
            "refresh_rate": "120Hz",
            "hdmi_ports": "4 HDMI 2.1",
            "smart_platform": "webOS 23"
        },
        "image_url": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 34,
        "payment_options": ["credit", "debit", "bnpl", "financing"],
        "rating_avg": 4.8,
        "review_count": 5678,
        "tags": ["tv", "oled", "lg", "4k", "smart tv", "gaming tv", "dolby vision"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Samsung 55\" The Frame QLED 4K Smart TV - Charcoal Black",
        "description": "Samsung The Frame transforms into a work of art when not in use. Matte Display with anti-reflection technology for gallery-like viewing. Customizable bezels (sold separately) to match your decor. Art Mode displays over 2000 artworks from famous museums. QLED 4K resolution with Quantum Dot technology for billion+ colors. Motion Sensor and Brightness Sensor for automatic adjustments. Art Store subscription for access to exclusive pieces. Slim fit wall mount included.",
        "category": "Electronics",
        "subcategory": "TV & Home Theater",
        "brand": "Samsung",
        "price": 1297.99,
        "original_price": 1499.99,
        "currency": "USD",
        "attributes": {
            "brand": "Samsung",
            "model": "QN55LS03B",
            "screen_size": "55 inches",
            "resolution": "4K UHD",
            "display_type": "QLED",
            "refresh_rate": "120Hz",
            "hdmi_ports": "4",
            "smart_platform": "Tizen"
        },
        "image_url": "https://images.unsplash.com/photo-1461151304267-38535e780c79?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 45,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.6,
        "review_count": 3456,
        "tags": ["tv", "qled", "samsung", "the frame", "art", "4k", "smart tv", "design"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Dell UltraSharp U2723QE 27\" 4K USB-C Hub Monitor",
        "description": "Dell UltraSharp U2723QE sets new standards for productivity monitors. 27-inch 4K IPS Black panel with 2000:1 contrast ratio - 4x typical IPS. 100% sRGB and 98% DCI-P3 color accuracy with factory calibration (Delta E < 2). USB-C hub with 90W Power Delivery charges your laptop. USB-C/USB-A/HDMI/DP connectivity. Built-in KVM switch for controlling 2 PCs. Adjustable stand with height, tilt, swivel, and pivot. Low blue light and flicker-free for eye comfort.",
        "category": "Electronics",
        "subcategory": "Computer Accessories",
        "brand": "Dell",
        "price": 649.99,
        "original_price": 799.99,
        "currency": "USD",
        "attributes": {
            "brand": "Dell",
            "model": "U2723QE",
            "screen_size": "27 inches",
            "resolution": "4K UHD",
            "panel_type": "IPS Black",
            "refresh_rate": "60Hz",
            "connectivity": ["USB-C 90W", "HDMI", "DisplayPort", "USB Hub"],
            "color_accuracy": "Delta E < 2"
        },
        "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 78,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.7,
        "review_count": 2345,
        "tags": ["monitor", "dell", "4k", "usb-c", "productivity", "color accurate", "ultrasharp"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "ASUS ROG Swift PG27AQDM 27\" OLED Gaming Monitor - 240Hz",
        "description": "ASUS ROG Swift PG27AQDM is the ultimate gaming monitor. 27-inch QHD OLED panel with 240Hz refresh rate and 0.03ms response time. True 10-bit color with 99% DCI-P3 and Delta E < 2. HDR10 with 1000 nits peak brightness. G-SYNC Compatible with NVIDIA Reflex Analyzer. Custom heatsink with graphene film for OLED longevity. Uniform Brightness, OLED Care, and pixel shift features prevent burn-in. ROG gaming design with customizable Aura Sync lighting.",
        "category": "Electronics",
        "subcategory": "Computer Accessories",
        "brand": "ASUS",
        "price": 999.99,
        "original_price": 1099.99,
        "currency": "USD",
        "attributes": {
            "brand": "ASUS",
            "model": "ROG Swift PG27AQDM",
            "screen_size": "27 inches",
            "resolution": "QHD (2560x1440)",
            "panel_type": "OLED",
            "refresh_rate": "240Hz",
            "response_time": "0.03ms",
            "connectivity": ["HDMI 2.0", "DisplayPort 1.4", "USB Hub"]
        },
        "image_url": "https://images.unsplash.com/photo-1616763355603-9755a640a287?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 34,
        "payment_options": ["credit", "debit", "bnpl", "financing"],
        "rating_avg": 4.8,
        "review_count": 1234,
        "tags": ["monitor", "gaming", "oled", "asus", "rog", "240hz", "esports"]
    },

    # ==================== FASHION - MORE CLOTHING ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Patagonia Better Sweater Fleece Jacket - Men's, Industrial Green",
        "description": "Patagonia Better Sweater is the perfect everyday fleece. Made from 100% recycled polyester fleece that looks like wool but is performance-ready. Full-zip front with stand-up collar. Zippered hand-warmer pockets and interior chest pocket. Flat-seam construction reduces bulk and chafing. Hip length for warmth and mobility. Fair Trade Certified sewn. A versatile layer for cool weather, travel, or just looking good.",
        "category": "Fashion",
        "subcategory": "Men's Clothing",
        "brand": "Patagonia",
        "price": 139.00,
        "original_price": 149.00,
        "currency": "USD",
        "attributes": {
            "brand": "Patagonia",
            "style": "Better Sweater",
            "color": "Industrial Green",
            "material": "100% Recycled Polyester Fleece",
            "fit": "Regular",
            "size_range": "XS-XXL",
            "gender": "Men"
        },
        "image_url": "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 123,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.7,
        "review_count": 8765,
        "tags": ["fleece", "patagonia", "jacket", "sustainable", "outdoor", "men", "layer"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Carhartt WIP Detroit Jacket - Hamilton Brown Rigid",
        "description": "Carhartt WIP Detroit Jacket is a streetwear icon. Made from 12 oz organic cotton canvas for durability. Blanket-lined body and quilted nylon sleeves for warmth. Corduroy collar adds classic styling. Dual hand pockets and interior pocket. Snap front closure with adjustable snap cuffs. Regular fit with room for layering. The workwear jacket that became a fashion staple. Import from Carhartt Work In Progress line.",
        "category": "Fashion",
        "subcategory": "Men's Clothing",
        "brand": "Carhartt WIP",
        "price": 225.00,
        "original_price": 245.00,
        "currency": "USD",
        "attributes": {
            "brand": "Carhartt WIP",
            "style": "Detroit Jacket",
            "color": "Hamilton Brown",
            "material": "12 oz Organic Cotton Canvas",
            "fit": "Regular",
            "size_range": "XS-XXL",
            "gender": "Unisex"
        },
        "image_url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 67,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.6,
        "review_count": 3456,
        "tags": ["jacket", "carhartt", "workwear", "streetwear", "canvas", "winter"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Everlane The Perform Legging - Black, Medium",
        "description": "Everlane Perform Legging is designed for studio to street. Made from recycled nylon and spandex with four-way stretch. High-waisted design with hidden pocket at waistband. Moisture-wicking fabric keeps you dry during workouts. Compression fit for support without restriction. Flattering matte finish works for gym or casual wear. Ethically made in Vietnam with radical transparency on pricing. 26\" inseam hits at the ankle.",
        "category": "Fashion",
        "subcategory": "Women's Clothing",
        "brand": "Everlane",
        "price": 58.00,
        "original_price": 68.00,
        "currency": "USD",
        "attributes": {
            "brand": "Everlane",
            "style": "The Perform Legging",
            "color": "Black",
            "material": "58% Recycled Nylon, 42% Spandex",
            "fit": "Compression",
            "size": "Medium",
            "inseam": "26 inches",
            "gender": "Women"
        },
        "image_url": "https://images.unsplash.com/photo-1538805060514-97d9cc17730c?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 189,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.4,
        "review_count": 5678,
        "tags": ["leggings", "everlane", "workout", "sustainable", "women", "athleisure"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Reformation Mia Midi Dress - Champagne, Size 6",
        "description": "Reformation Mia Dress is the perfect date night or special occasion dress. Made from 100% TENCEL Lyocell - a sustainable fabric from renewable wood sources. Flattering V-neckline with adjustable straps. Fitted bodice with A-line skirt falls to mid-calf. Side zipper for easy dressing. Lightweight and breathable for all-day comfort. Reformation uses sustainable practices and offsets carbon emissions. Dry clean recommended.",
        "category": "Fashion",
        "subcategory": "Women's Clothing",
        "brand": "Reformation",
        "price": 218.00,
        "original_price": 248.00,
        "currency": "USD",
        "attributes": {
            "brand": "Reformation",
            "style": "Mia Midi Dress",
            "color": "Champagne",
            "material": "100% TENCEL Lyocell",
            "fit": "Fitted Bodice, A-Line Skirt",
            "size": "6",
            "occasion": "Date Night, Special Occasion",
            "gender": "Women"
        },
        "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 45,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.5,
        "review_count": 2345,
        "tags": ["dress", "reformation", "midi", "sustainable", "women", "special occasion"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Uniqlo Men's Ultra Light Down Jacket - Navy, Large",
        "description": "Uniqlo Ultra Light Down is incredibly warm yet feather-light. Premium 90% down, 10% feather fill provides excellent insulation. Water-repellent outer shell keeps you dry in light rain. Packs into included pouch for easy travel and storage. Stand collar with chin guard prevents zipper rub. Elastic cuffs and hem keep warmth in. Inner pocket and two side pockets. Only 7.8 oz (220g). Essential for travel, layering, or everyday warmth.",
        "category": "Fashion",
        "subcategory": "Men's Clothing",
        "brand": "Uniqlo",
        "price": 69.90,
        "original_price": 79.90,
        "currency": "USD",
        "attributes": {
            "brand": "Uniqlo",
            "style": "Ultra Light Down Jacket",
            "color": "Navy",
            "material": "100% Nylon, 90% Down 10% Feather Fill",
            "fit": "Regular",
            "size": "Large",
            "weight": "7.8 oz",
            "gender": "Men"
        },
        "image_url": "https://images.unsplash.com/photo-1544923246-77307dd628b9?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 345,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.6,
        "review_count": 23456,
        "tags": ["down jacket", "uniqlo", "lightweight", "packable", "men", "travel", "winter"]
    },

    # ==================== FASHION - MORE SHOES ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "New Balance 990v6 - Grey, Men's Size 10",
        "description": "New Balance 990v6 continues the legendary 990 series. Made in USA with premium suede and mesh upper. ENCAP midsole cushioning provides support and durability. Blown rubber outsole for reliable traction. Reflective details for visibility in low light. The classic 'dad shoe' beloved by sneakerheads and everyday wearers alike. Break-in period recommended for best fit. Style # M990GL6.",
        "category": "Fashion",
        "subcategory": "Shoes",
        "brand": "New Balance",
        "price": 199.99,
        "original_price": 199.99,
        "currency": "USD",
        "attributes": {
            "brand": "New Balance",
            "model": "990v6",
            "color": "Grey",
            "material": "Suede/Mesh",
            "size": "10",
            "gender": "Men",
            "style": "Lifestyle/Running"
        },
        "image_url": "https://images.unsplash.com/photo-1539185441755-769473a23570?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 78,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.8,
        "review_count": 6789,
        "tags": ["sneakers", "new balance", "990", "made in usa", "dad shoe", "running", "lifestyle"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Birkenstock Arizona Soft Footbed - Taupe Suede, Women's 38",
        "description": "Birkenstock Arizona is the iconic two-strap sandal with legendary comfort. Soft Footbed provides an extra layer of cushioning foam for plush comfort right out of the box. Contoured footbed made from cork and latex supports your arches and distributes weight evenly. Suede leather upper with adjustable metal buckles. EVA sole for lightweight shock absorption. Made in Germany with over 200 years of shoemaking expertise. Break in naturally for a personalized fit.",
        "category": "Fashion",
        "subcategory": "Shoes",
        "brand": "Birkenstock",
        "price": 150.00,
        "original_price": 160.00,
        "currency": "USD",
        "attributes": {
            "brand": "Birkenstock",
            "model": "Arizona Soft Footbed",
            "color": "Taupe Suede",
            "material": "Suede Leather Upper, Cork Footbed",
            "size": "38 EU (7-7.5 US)",
            "gender": "Women",
            "style": "Sandals"
        },
        "image_url": "https://images.unsplash.com/photo-1603808033192-082d6919d3e1?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 156,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.7,
        "review_count": 34567,
        "tags": ["sandals", "birkenstock", "arizona", "comfort", "women", "summer", "cork"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Allbirds Tree Runners - Kauri Moonlight, Men's Size 11",
        "description": "Allbirds Tree Runners are the world's most comfortable shoes. Made from eucalyptus tree fiber for breathable, lightweight comfort. Allbirds SweetFoam midsole made from sugarcane for cushioned support. Machine washable for easy care - just remove insoles and laces. Carbon-neutral product from sustainable materials. Minimal, clean design goes with everything. No break-in period needed. B Corp certified company committed to sustainability.",
        "category": "Fashion",
        "subcategory": "Shoes",
        "brand": "Allbirds",
        "price": 98.00,
        "original_price": 110.00,
        "currency": "USD",
        "attributes": {
            "brand": "Allbirds",
            "model": "Tree Runners",
            "color": "Kauri Moonlight",
            "material": "Eucalyptus Tree Fiber",
            "size": "11",
            "gender": "Men",
            "style": "Lifestyle"
        },
        "image_url": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 234,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.5,
        "review_count": 12345,
        "tags": ["sneakers", "allbirds", "sustainable", "comfortable", "tree fiber", "eco-friendly"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Converse Chuck Taylor All Star High Top - Black, Unisex M8/W10",
        "description": "Converse Chuck Taylor All Star is the original basketball shoe turned cultural icon. Canvas upper for durability and classic style. Vulcanized rubber sole for flexibility and traction. OrthoLite insole provides cushioning and moisture management. Medial eyelets enhance airflow. Classic All Star patch on ankle. The shoe worn by everyone from basketball legends to rock stars. Style # M9160. True to size.",
        "category": "Fashion",
        "subcategory": "Shoes",
        "brand": "Converse",
        "price": 65.00,
        "original_price": 70.00,
        "currency": "USD",
        "attributes": {
            "brand": "Converse",
            "model": "Chuck Taylor All Star High Top",
            "color": "Black",
            "material": "Canvas",
            "size": "M8/W10",
            "gender": "Unisex",
            "style": "High Top"
        },
        "image_url": "https://images.unsplash.com/photo-1463100099107-aa0980c362e6?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 456,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.6,
        "review_count": 78901,
        "tags": ["sneakers", "converse", "chuck taylor", "classic", "canvas", "iconic", "high top"]
    },

    # ==================== HOME & KITCHEN - MORE ITEMS ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Vitamix A3500 Ascent Series Smart Blender - Brushed Stainless Steel",
        "description": "Vitamix A3500 is the ultimate professional-grade blender. 2.2 peak horsepower motor handles the toughest ingredients. Self-Detect technology automatically adjusts settings for container size. 5 program settings: Smoothies, Hot Soups, Dips & Spreads, Frozen Desserts, Self-Cleaning. Variable speed control and pulse feature. Built-in wireless connectivity with Vitamix Perfect Blend app. Aircraft-grade stainless steel blades with 10-year warranty. Low-profile 64 oz container fits under most cabinets.",
        "category": "Home & Kitchen",
        "subcategory": "Kitchen Appliances",
        "brand": "Vitamix",
        "price": 649.95,
        "original_price": 699.95,
        "currency": "USD",
        "attributes": {
            "brand": "Vitamix",
            "model": "A3500",
            "color": "Brushed Stainless Steel",
            "capacity": "64 oz",
            "motor": "2.2 HP",
            "programs": "5 preset programs"
        },
        "image_url": "https://images.unsplash.com/photo-1570222094114-d054a817e56b?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 56,
        "payment_options": ["credit", "debit", "bnpl", "financing", "paypal"],
        "rating_avg": 4.8,
        "review_count": 5678,
        "tags": ["blender", "vitamix", "professional", "smart appliance", "kitchen", "smoothie"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Staub Cast Iron Cocotte 5.5 Qt - Cherry",
        "description": "Staub Cast Iron Cocotte is a French cooking essential. Heavy-duty enameled cast iron distributes heat evenly and retains it for superior braising and roasting. Self-basting lid with spikes continuously bastes food for moist, flavorful results. Black matte enamel interior develops a natural non-stick coating over time. Compatible with all cooktops including induction. Oven safe to 500°F. Dishwasher safe but hand wash recommended. Made in France.",
        "category": "Home & Kitchen",
        "subcategory": "Cookware",
        "brand": "Staub",
        "price": 379.99,
        "original_price": 429.99,
        "currency": "USD",
        "attributes": {
            "brand": "Staub",
            "model": "Round Cocotte",
            "capacity": "5.5 Quarts",
            "material": "Enameled Cast Iron",
            "color": "Cherry",
            "dimensions": "10.5 inches diameter"
        },
        "image_url": "https://images.unsplash.com/photo-1585837146751-a44118595680?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 45,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.9,
        "review_count": 3456,
        "tags": ["dutch oven", "staub", "cast iron", "french", "cookware", "braising"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Nespresso Vertuo Next Coffee Machine with Aeroccino - Gray",
        "description": "Nespresso Vertuo Next brews perfect coffee at the touch of a button. Centrifusion technology spins capsules at 7000 RPM for optimal extraction. Five cup sizes from espresso to carafe (5, 8, 12, 14, or 18 oz). Barcode technology automatically adjusts brewing parameters for each capsule. 30-second heat-up time. Includes Aeroccino 3 milk frother for lattes and cappuccinos. Made from 54% recycled plastic. Capsule recycling program available.",
        "category": "Home & Kitchen",
        "subcategory": "Kitchen Appliances",
        "brand": "Nespresso",
        "price": 219.00,
        "original_price": 269.00,
        "currency": "USD",
        "attributes": {
            "brand": "Nespresso",
            "model": "Vertuo Next + Aeroccino",
            "color": "Gray",
            "cup_sizes": "5 sizes (5-18 oz)",
            "water_tank": "37 oz",
            "heat_up_time": "30 seconds"
        },
        "image_url": "https://images.unsplash.com/photo-1517487881594-2787fef5ebf7?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 134,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.5,
        "review_count": 8765,
        "tags": ["coffee maker", "nespresso", "espresso", "capsule", "milk frother", "kitchen"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Casper Original Mattress Queen - Medium Firm",
        "description": "The Casper Original Mattress delivers the perfect balance of comfort and support. Three foam layers work together: top layer for pressure relief, middle layer for proper alignment, bottom layer for durable support. Zoned Support provides firmer support under your hips and softer cushioning for shoulders. AirScape perforations promote airflow and temperature regulation. CertiPUR-US certified foams. 100-night trial, 10-year warranty. Ships compressed in a box.",
        "category": "Home & Kitchen",
        "subcategory": "Bedding",
        "brand": "Casper",
        "price": 1095.00,
        "original_price": 1295.00,
        "currency": "USD",
        "attributes": {
            "brand": "Casper",
            "model": "Original Mattress",
            "size": "Queen",
            "firmness": "Medium Firm",
            "thickness": "11 inches",
            "material": "3-Layer Foam"
        },
        "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 78,
        "payment_options": ["credit", "debit", "bnpl", "financing"],
        "rating_avg": 4.4,
        "review_count": 12345,
        "tags": ["mattress", "casper", "bed", "foam", "queen", "sleep", "bedroom"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Article Sven Sofa 88\" - Oxford Blue Velvet",
        "description": "Article Sven Sofa combines Scandinavian design with exceptional comfort. Luxurious Oxford Blue velvet upholstery adds sophistication. Solid oak legs in warm walnut finish. High-density foam cushions with fiber wrap for plush, supportive seating. Removable cushion covers for easy cleaning (dry clean only). Tufted back adds visual interest. 88-inch width seats 3 comfortably. Some assembly required. Direct-to-consumer pricing - no middleman markups.",
        "category": "Home & Kitchen",
        "subcategory": "Furniture",
        "brand": "Article",
        "price": 1299.00,
        "original_price": 1499.00,
        "currency": "USD",
        "attributes": {
            "brand": "Article",
            "model": "Sven Sofa",
            "color": "Oxford Blue",
            "material": "Velvet Upholstery, Solid Oak Legs",
            "dimensions": "88 x 38 x 33 inches",
            "seating_capacity": "3"
        },
        "image_url": "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 23,
        "payment_options": ["credit", "debit", "bnpl", "financing"],
        "rating_avg": 4.6,
        "review_count": 2345,
        "tags": ["sofa", "article", "velvet", "scandinavian", "modern", "living room", "furniture"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Philips Hue White and Color Ambiance Starter Kit - 4 Bulbs + Bridge",
        "description": "Philips Hue Smart Lighting transforms your home with 16 million colors. Kit includes 4 A19 color bulbs and Hue Bridge. Create any ambiance from energizing bright light to relaxing warm tones. Sync lights with music, movies, and games. Voice control with Alexa, Google, and Siri. Set schedules and automations. Geofencing turns lights on/off automatically. Control up to 50 lights with one Bridge. 25,000-hour bulb life. Easy setup via Hue app.",
        "category": "Home & Kitchen",
        "subcategory": "Lighting",
        "brand": "Philips",
        "price": 199.99,
        "original_price": 229.99,
        "currency": "USD",
        "attributes": {
            "brand": "Philips",
            "model": "Hue Starter Kit",
            "bulbs_included": "4 A19 Color Bulbs",
            "bridge_included": "Yes",
            "brightness": "800 lumens each",
            "connectivity": ["Zigbee", "Bluetooth"]
        },
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 167,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.7,
        "review_count": 23456,
        "tags": ["smart lighting", "philips hue", "smart home", "color bulbs", "home automation"]
    },

    # ==================== BOOKS & MEDIA - MORE ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "The Psychology of Money by Morgan Housel - Hardcover",
        "description": "The Psychology of Money explores the strange ways people think about money. Morgan Housel shares 19 short stories exploring the peculiar ways we approach financial decisions. Learn why money isn't about math - it's about behavior. Timeless lessons on wealth, greed, and happiness that apply to everyone regardless of income. Over 3 million copies sold worldwide. A must-read for anyone who wants to understand their own relationship with money.",
        "category": "Books & Media",
        "subcategory": "Non-Fiction",
        "brand": "Harriman House",
        "price": 17.99,
        "original_price": 22.00,
        "currency": "USD",
        "attributes": {
            "author": "Morgan Housel",
            "publisher": "Harriman House",
            "pages": 256,
            "format": "Hardcover",
            "language": "English",
            "isbn": "978-0857197689",
            "genre": "Finance, Psychology"
        },
        "image_url": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 456,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.7,
        "review_count": 67890,
        "tags": ["book", "finance", "psychology", "money", "bestseller", "self-improvement"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Fourth Wing by Rebecca Yarros - Paperback",
        "description": "Fourth Wing is the TikTok phenomenon that launched a fantasy obsession. Twenty-year-old Violet Sorrengail was supposed to enter the Scribe Quadrant. Instead, she's thrust into the deadly world of dragon riders. At the Basgiath War College, the weak die and the dragons decide your fate. Violet must survive brutal training, ruthless enemies, and the most powerful, arrogant wingleader. The first book in the Empyrean series that's impossible to put down.",
        "category": "Books & Media",
        "subcategory": "Fiction",
        "brand": "Red Tower Books",
        "price": 15.99,
        "original_price": 18.99,
        "currency": "USD",
        "attributes": {
            "author": "Rebecca Yarros",
            "publisher": "Red Tower Books",
            "pages": 528,
            "format": "Paperback",
            "language": "English",
            "isbn": "978-1649374042",
            "genre": "Fantasy, Romance"
        },
        "image_url": "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 567,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.6,
        "review_count": 123456,
        "tags": ["book", "fantasy", "romance", "dragons", "tiktok", "booktok", "fiction"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Clean Code by Robert C. Martin - Paperback",
        "description": "Clean Code is essential reading for any software developer. Robert C. Martin presents his revolutionary paradigm for creating better code. Learn the principles, patterns, and practices of writing clean code. Case studies of increasing complexity show how to transform bad code into good code. Topics include meaningful names, functions, comments, formatting, error handling, unit tests, classes, and systems. The definitive guide to writing code that works and is easy to maintain.",
        "category": "Books & Media",
        "subcategory": "Technical & Programming",
        "brand": "Pearson",
        "price": 39.99,
        "original_price": 49.99,
        "currency": "USD",
        "attributes": {
            "author": "Robert C. Martin",
            "publisher": "Pearson",
            "pages": 464,
            "format": "Paperback",
            "language": "English",
            "isbn": "978-0132350884",
            "genre": "Programming, Software Engineering"
        },
        "image_url": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 234,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.7,
        "review_count": 12345,
        "tags": ["book", "programming", "software", "coding", "clean code", "best practices"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Sapiens: A Brief History of Humankind by Yuval Noah Harari - Paperback",
        "description": "Sapiens is a groundbreaking narrative of humanity's creation and evolution. Yuval Noah Harari explores how biology and history have defined us and enhanced our understanding of what it means to be human. From the emergence of Homo sapiens in Africa to the present, discover how we came to believe in gods, nations, and human rights. A thought-provoking exploration of our species that challenges everything you thought you knew. Translated into 65 languages with 25 million copies sold.",
        "category": "Books & Media",
        "subcategory": "Non-Fiction",
        "brand": "Harper Perennial",
        "price": 16.99,
        "original_price": 22.99,
        "currency": "USD",
        "attributes": {
            "author": "Yuval Noah Harari",
            "publisher": "Harper Perennial",
            "pages": 464,
            "format": "Paperback",
            "language": "English",
            "isbn": "978-0062316110",
            "genre": "History, Anthropology"
        },
        "image_url": "https://images.unsplash.com/photo-1550399105-c4db5fb85c18?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 389,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.6,
        "review_count": 98765,
        "tags": ["book", "history", "anthropology", "humanity", "bestseller", "non-fiction"]
    },

    # ==================== SPORTS & FITNESS - MORE ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Theragun PRO Plus - 6th Generation Percussive Therapy Device",
        "description": "Theragun PRO Plus is the most advanced deep tissue massage gun. 6th generation QuietForce Technology is 20% quieter than PRO Gen 5. Proprietary brushless motor delivers up to 60 lbs of force. OLED touchscreen with guided routines via Therabody app. Adjustable arm with 4 positions for hard-to-reach areas. 6 foam attachments for different muscle groups. 150-minute battery life with 2 swappable batteries. Smart Percussive Therapy adapts force based on pressure.",
        "category": "Sports & Fitness",
        "subcategory": "Fitness Accessories",
        "brand": "Therabody",
        "price": 599.00,
        "original_price": 649.00,
        "currency": "USD",
        "attributes": {
            "brand": "Therabody",
            "model": "Theragun PRO Plus",
            "force": "Up to 60 lbs",
            "speeds": "5 speeds",
            "battery_life": "150 minutes",
            "attachments": "6 included"
        },
        "image_url": "https://images.unsplash.com/photo-1616279969862-484a1b1d4e8d?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 67,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.7,
        "review_count": 4567,
        "tags": ["massage gun", "theragun", "recovery", "fitness", "muscle therapy", "percussion"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Garmin Forerunner 265 GPS Running Watch - Black/Aqua",
        "description": "Garmin Forerunner 265 is built for runners who demand data. Bright 1.3\" AMOLED display visible in any lighting. Advanced running dynamics including ground contact time, stride length, and vertical ratio. Training readiness score combines sleep, recovery, and training load. Daily suggested workouts adapt to your fitness level. Race predictor estimates finish times. GPS with multi-band technology for accuracy. Up to 13 days battery in smartwatch mode, 20 hours in GPS mode.",
        "category": "Sports & Fitness",
        "subcategory": "Exercise Equipment",
        "brand": "Garmin",
        "price": 449.99,
        "original_price": 449.99,
        "currency": "USD",
        "attributes": {
            "brand": "Garmin",
            "model": "Forerunner 265",
            "display": "1.3\" AMOLED",
            "battery_life": "13 days smartwatch, 20h GPS",
            "water_resistant": "5 ATM",
            "color": "Black/Aqua"
        },
        "image_url": "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 89,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.8,
        "review_count": 3456,
        "tags": ["running watch", "garmin", "gps", "fitness tracker", "amoled", "training"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "YETI Rambler 26 oz Bottle with Chug Cap - Navy",
        "description": "YETI Rambler 26 oz Bottle keeps drinks cold (or hot) for hours. Double-wall vacuum insulation maintains temperature no matter the conditions. 18/8 stainless steel is puncture and rust resistant. Chug Cap is leakproof and easy to drink from. No Sweat Design means no condensation on the outside. Over-the-nose drinking with wide opening for ice cubes. Dishwasher safe. BPA-free. Built to handle whatever you throw at it - literally.",
        "category": "Sports & Fitness",
        "subcategory": "Outdoor Recreation",
        "brand": "YETI",
        "price": 40.00,
        "original_price": 45.00,
        "currency": "USD",
        "attributes": {
            "brand": "YETI",
            "model": "Rambler 26 oz",
            "capacity": "26 oz",
            "material": "18/8 Stainless Steel",
            "insulation": "Double-Wall Vacuum",
            "color": "Navy"
        },
        "image_url": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 345,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.8,
        "review_count": 23456,
        "tags": ["water bottle", "yeti", "insulated", "stainless steel", "outdoor", "hydration"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "TRX HOME2 System Suspension Trainer",
        "description": "TRX HOME2 is the complete home gym in a bag. Suspension training uses your body weight for hundreds of exercises. Targets every major muscle group with one simple tool. Door anchor and suspension anchor included for home setup. Foam handles with rubber grips for comfort. Adjustable straps with easy-lock carabiner. Includes 8-week workout program guide and access to TRX App with 500+ workouts. Used by military, professional athletes, and fitness enthusiasts worldwide.",
        "category": "Sports & Fitness",
        "subcategory": "Exercise Equipment",
        "brand": "TRX",
        "price": 199.95,
        "original_price": 229.95,
        "currency": "USD",
        "attributes": {
            "brand": "TRX",
            "model": "HOME2 System",
            "weight_capacity": "350 lbs",
            "includes": "Straps, Door Anchor, Suspension Anchor, Bag",
            "material": "Commercial-Grade Nylon"
        },
        "image_url": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 123,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.7,
        "review_count": 8765,
        "tags": ["suspension trainer", "trx", "home gym", "bodyweight", "fitness", "strength training"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Hyperice Hypervolt 2 Pro - Graphite Gray",
        "description": "Hyperice Hypervolt 2 Pro delivers professional-grade percussion therapy. Brushless high-torque motor provides 30% more power than Hypervolt 2. 5 speeds up to 3200 percussions per minute. Interchangeable flat, round, fork, cushion, and bullet heads target different muscle groups. QuietGlide technology for whisper-quiet operation. Pressure sensor with LED feedback shows applied force. Rechargeable lithium-ion battery lasts 3 hours. TSA-approved carry-on size.",
        "category": "Sports & Fitness",
        "subcategory": "Fitness Accessories",
        "brand": "Hyperice",
        "price": 399.00,
        "original_price": 429.00,
        "currency": "USD",
        "attributes": {
            "brand": "Hyperice",
            "model": "Hypervolt 2 Pro",
            "speeds": "5",
            "battery_life": "3 hours",
            "attachments": "5 heads",
            "color": "Graphite Gray"
        },
        "image_url": "https://images.unsplash.com/photo-1620188467120-5042ed1eb5da?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 78,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.6,
        "review_count": 5678,
        "tags": ["massage gun", "hyperice", "recovery", "percussion therapy", "muscle"]
    },

    # ==================== BEAUTY & PERSONAL CARE - MORE ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Sunday Riley Good Genes All-In-One Lactic Acid Treatment - 1.7 oz",
        "description": "Sunday Riley Good Genes is a cult-favorite exfoliating treatment. Purified lactic acid (high-grade AHA) exfoliates dull, pore-clogging dead skin cells. Reveals smoother, fresher, more radiant skin with each use. Licorice brightens the look of dark spots and hyperpigmentation. Lemongrass provides antioxidant protection. Can be used daily or as a weekly mask (leave on 10+ minutes). Safe for all skin types when used as directed. Instant visible results.",
        "category": "Beauty & Personal Care",
        "subcategory": "Skincare",
        "brand": "Sunday Riley",
        "price": 158.00,
        "original_price": 175.00,
        "currency": "USD",
        "attributes": {
            "brand": "Sunday Riley",
            "product_type": "Lactic Acid Treatment",
            "volume": "1.7 oz / 50ml",
            "skin_type": "All Skin Types",
            "key_ingredient": "Lactic Acid, Licorice, Lemongrass"
        },
        "image_url": "https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 89,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.5,
        "review_count": 6789,
        "tags": ["serum", "exfoliant", "lactic acid", "sunday riley", "brightening", "anti-aging"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Olaplex No. 3 Hair Perfector - 3.3 oz",
        "description": "Olaplex No. 3 repairs damaged hair from the inside out. Patented bond-building technology relinks broken disulfide bonds in hair. Reduces breakage and strengthens hair with each use. Not a conditioner - it's a treatment that works on a molecular level. Apply to damp hair, leave on 10+ minutes, then shampoo and condition. Safe for all hair types including color-treated and chemically processed. The at-home treatment that started a hair care revolution.",
        "category": "Beauty & Personal Care",
        "subcategory": "Hair Care",
        "brand": "Olaplex",
        "price": 30.00,
        "original_price": 30.00,
        "currency": "USD",
        "attributes": {
            "brand": "Olaplex",
            "product_type": "Hair Treatment",
            "volume": "3.3 oz / 100ml",
            "hair_type": "All Hair Types",
            "key_ingredient": "Bis-Aminopropyl Diglycol Dimaleate"
        },
        "image_url": "https://images.unsplash.com/photo-1526947425960-945c6e72858f?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 456,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.6,
        "review_count": 89012,
        "tags": ["hair treatment", "olaplex", "bond repair", "damaged hair", "hair care"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "NARS Radiant Creamy Concealer - Vanilla, 0.22 oz",
        "description": "NARS Radiant Creamy Concealer is the #1 selling concealer in the US. Medium-to-buildable coverage with a natural, radiant finish. Multi-action formula hydrates, brightens, and corrects. Peptides help firm and reduce fine lines over time. Color-true shades stay vibrant all day. Built-in applicator for precise application. Covers dark circles, blemishes, and imperfections. Oil-free, non-comedogenic, and dermatologist-tested. 40 shades for every skin tone.",
        "category": "Beauty & Personal Care",
        "subcategory": "Makeup",
        "brand": "NARS",
        "price": 32.00,
        "original_price": 32.00,
        "currency": "USD",
        "attributes": {
            "brand": "NARS",
            "product_type": "Concealer",
            "shade": "Vanilla",
            "finish": "Radiant",
            "volume": "0.22 oz / 6ml",
            "coverage": "Medium to Full"
        },
        "image_url": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 234,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.7,
        "review_count": 34567,
        "tags": ["concealer", "nars", "makeup", "coverage", "radiant", "dark circles"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Paula's Choice 2% BHA Liquid Exfoliant - 4 oz",
        "description": "Paula's Choice 2% BHA Liquid Exfoliant is a game-changer for pores. Salicylic acid (BHA) exfoliates inside pores, reducing blackheads and blemishes. Green tea extract provides antioxidant protection. Lightweight, water-like formula absorbs quickly. Apply with cotton pad after cleansing, no need to rinse. Safe for all skin types, even sensitive and rosacea-prone. Use once or twice daily. The exfoliant that launched a skincare revolution with over 60 million sold.",
        "category": "Beauty & Personal Care",
        "subcategory": "Skincare",
        "brand": "Paula's Choice",
        "price": 35.00,
        "original_price": 37.00,
        "currency": "USD",
        "attributes": {
            "brand": "Paula's Choice",
            "product_type": "BHA Exfoliant",
            "volume": "4 oz / 118ml",
            "skin_type": "All Skin Types",
            "key_ingredient": "2% Salicylic Acid (BHA)"
        },
        "image_url": "https://images.unsplash.com/photo-1617897903246-719242758050?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 567,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.7,
        "review_count": 56789,
        "tags": ["exfoliant", "bha", "paula's choice", "pores", "blackheads", "acne", "skincare"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Chanel Chance Eau Tendre Eau de Parfum - 3.4 oz",
        "description": "Chanel Chance Eau Tendre is a tender, radiant floral fragrance. Opens with a fruity burst of quince and grapefruit. Heart notes of jasmine and hyacinth create a soft, feminine bouquet. Base of white musk, iris, and cedar add warmth and sensuality. The round bottle embodies the unpredictable nature of chance. Long-lasting sillage without being overpowering. The romantic, spontaneous side of CHANCE. Eau de Parfum concentration for enhanced longevity.",
        "category": "Beauty & Personal Care",
        "subcategory": "Fragrances",
        "brand": "Chanel",
        "price": 165.00,
        "original_price": 165.00,
        "currency": "USD",
        "attributes": {
            "brand": "Chanel",
            "product_type": "Eau de Parfum",
            "volume": "3.4 oz / 100ml",
            "concentration": "EDP",
            "gender": "Women",
            "scent_family": "Floral, Fruity"
        },
        "image_url": "https://images.unsplash.com/photo-1541643600914-78b084683601?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 89,
        "payment_options": ["credit", "debit", "bnpl", "paypal"],
        "rating_avg": 4.8,
        "review_count": 12345,
        "tags": ["perfume", "chanel", "chance", "floral", "women's fragrance", "luxury"]
    },

    # ==================== BUDGET OPTIONS ====================
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Anker USB C Charger 65W GaN II - Compact Wall Charger",
        "description": "Anker 65W GaN II Charger is smaller than your standard charger but vastly more powerful. GaN II technology delivers 65W in a compact form factor. Single USB-C port for laptops, tablets, and phones. PowerIQ 3.0 detects device and delivers optimal charge. Charges MacBook Pro 13\" to 50% in 40 minutes. Foldable plug for easy travel. ActiveShield 2.0 monitors temperature 3 million times daily. Multiple safety features protect your devices.",
        "category": "Electronics",
        "subcategory": "Computer Accessories",
        "brand": "Anker",
        "price": 35.99,
        "original_price": 45.99,
        "currency": "USD",
        "attributes": {
            "brand": "Anker",
            "model": "715 Charger",
            "power": "65W",
            "ports": "1 USB-C",
            "technology": "GaN II",
            "foldable_plug": "Yes"
        },
        "image_url": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 678,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.7,
        "review_count": 34567,
        "tags": ["charger", "usb-c", "anker", "gan", "laptop charger", "travel", "compact"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Logitech MX Master 3S Wireless Mouse - Graphite",
        "description": "Logitech MX Master 3S is the ultimate productivity mouse. MagSpeed electromagnetic scrolling - 90% faster, 87% more precise, and near-silent. 8000 DPI track on any surface including glass. Ergonomic shape sculpted for your hand. Quiet Clicks reduce click noise by 90%. App-specific customizations for Adobe, Microsoft, and more. Easy-Switch connects up to 3 devices. USB-C quick charge: 1 minute = 3 hours of use. Works with Logi Options+ software.",
        "category": "Electronics",
        "subcategory": "Computer Accessories",
        "brand": "Logitech",
        "price": 99.99,
        "original_price": 109.99,
        "currency": "USD",
        "attributes": {
            "brand": "Logitech",
            "model": "MX Master 3S",
            "dpi": "8000 DPI",
            "connectivity": ["Bluetooth", "USB Receiver"],
            "battery_life": "70 days",
            "color": "Graphite"
        },
        "image_url": "https://images.unsplash.com/photo-1527814050087-3793815479db?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 345,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.8,
        "review_count": 23456,
        "tags": ["mouse", "logitech", "mx master", "wireless", "productivity", "ergonomic"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "AmazonBasics High-Speed HDMI Cable 6 Feet - 3 Pack",
        "description": "AmazonBasics High-Speed HDMI Cable delivers reliable connectivity at a great price. Supports 4K video at 60Hz, 2160p, 48 bit/px color depth. ARC (Audio Return Channel) for simplified audio setup. 3D and Ethernet capable. Gold-plated connectors resist corrosion. Triple-shielded with polybag for protection. Works with TVs, monitors, gaming consoles, streaming devices, and more. No setup required - plug and play. 3-pack provides cables for multiple devices.",
        "category": "Electronics",
        "subcategory": "Computer Accessories",
        "brand": "Amazon Basics",
        "price": 11.99,
        "original_price": 16.99,
        "currency": "USD",
        "attributes": {
            "brand": "Amazon Basics",
            "length": "6 feet",
            "quantity": "3 pack",
            "resolution": "4K @ 60Hz",
            "features": ["ARC", "3D", "Ethernet"]
        },
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 1234,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.6,
        "review_count": 156789,
        "tags": ["hdmi cable", "amazon basics", "4k", "budget", "cable", "accessories"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "e.l.f. Poreless Putty Primer - 0.74 oz",
        "description": "e.l.f. Poreless Putty Primer creates a flawless, poreless-looking complexion. Squalane-infused formula nourishes and hydrates skin. Putty-like texture smooths over pores and imperfections. Creates the perfect base for makeup application. Lightweight formula won't clog pores. Suitable for all skin types. Vegan and cruelty-free. No need to spend more - this $10 primer rivals high-end competitors. One of the most viral beauty products on TikTok.",
        "category": "Beauty & Personal Care",
        "subcategory": "Makeup",
        "brand": "e.l.f.",
        "price": 10.00,
        "original_price": 10.00,
        "currency": "USD",
        "attributes": {
            "brand": "e.l.f.",
            "product_type": "Primer",
            "volume": "0.74 oz / 21g",
            "skin_type": "All Skin Types",
            "key_ingredient": "Squalane"
        },
        "image_url": "https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 789,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.5,
        "review_count": 67890,
        "tags": ["primer", "elf", "budget makeup", "poreless", "viral", "drugstore"]
    },
    {
        "id": f"prod_{uuid.uuid4().hex[:12]}",
        "title": "Fruit of the Loom Men's Eversoft Cotton T-Shirts 6-Pack - Black",
        "description": "Fruit of the Loom Eversoft Cotton T-Shirts deliver unbeatable comfort and value. 100% ringspun cotton is pre-washed for extra softness. Tag-free neck label eliminates irritation. Lay-flat collar keeps its shape. Reinforced shoulder seams for durability. Moisture-wicking keeps you cool and dry. Classic crew neck design. 6-pack means you always have a fresh tee ready. Perfect for everyday wear, sleep, or workouts. Machine washable.",
        "category": "Fashion",
        "subcategory": "Men's Clothing",
        "brand": "Fruit of the Loom",
        "price": 24.98,
        "original_price": 29.98,
        "currency": "USD",
        "attributes": {
            "brand": "Fruit of the Loom",
            "style": "Eversoft Crew Neck",
            "color": "Black",
            "material": "100% Cotton",
            "fit": "Regular",
            "quantity": "6 pack",
            "gender": "Men"
        },
        "image_url": "https://images.unsplash.com/photo-1562157873-818bc0726f68?w=800&q=80",
        "stock_status": "in_stock",
        "stock_quantity": 567,
        "payment_options": ["credit", "debit", "paypal"],
        "rating_avg": 4.4,
        "review_count": 45678,
        "tags": ["t-shirt", "basics", "cotton", "value pack", "men", "everyday", "budget"]
    },
]


def add_timestamps(products: List[Dict]) -> List[Dict]:
    """Add realistic timestamps to products."""
    now = datetime.now(timezone.utc)
    for product in products:
        days_ago = random.randint(1, 365)
        created_at = now - timedelta(days=days_ago)
        product["created_at"] = created_at.isoformat()
        
        if random.random() < 0.7:
            update_days = random.randint(0, days_ago - 1) if days_ago > 1 else 0
            updated_at = now - timedelta(days=update_days)
            product["updated_at"] = updated_at.isoformat()
        else:
            product["updated_at"] = None
            
    return products


def generate_extended_products() -> List[Dict]:
    """Generate and return extended products with timestamps."""
    products = add_timestamps(EXTENDED_PRODUCTS.copy())
    
    for product in products:
        product["id"] = f"prod_{uuid.uuid4().hex[:12]}"
    
    return products


def merge_with_existing() -> List[Dict]:
    """Merge with existing sample products."""
    script_dir = Path(__file__).parent
    existing_file = script_dir / "output" / "sample_products.json"
    
    # Load existing products
    existing_products = []
    if existing_file.exists():
        with open(existing_file, "r", encoding="utf-8") as f:
            existing_products = json.load(f)
        print(f"Loaded {len(existing_products)} existing products")
    
    # Generate new products
    new_products = generate_extended_products()
    print(f"Generated {len(new_products)} new products")
    
    # Merge
    all_products = existing_products + new_products
    print(f"Total products: {len(all_products)}")
    
    return all_products


def save_to_json(products: List[Dict], filename: str = "sample_products.json"):
    """Save products to JSON file."""
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
    print("EXTENDED PRODUCT COLLECTION")
    print("="*60)
    
    categories = {}
    for p in products:
        cat = p["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\nTotal Products: {len(products)}")
    print("\nBy Category:")
    for cat, count in sorted(categories.items()):
        print(f"  • {cat}: {count}")
    
    prices = [p["price"] for p in products]
    print(f"\nPrice Range: ${min(prices):.2f} - ${max(prices):.2f}")
    print(f"Average Price: ${sum(prices)/len(prices):.2f}")
    
    brands = set(p["brand"] for p in products)
    print(f"\nUnique Brands: {len(brands)}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    print("Generating extended product collection...")
    
    all_products = merge_with_existing()
    print_summary(all_products)
    
    output_file = save_to_json(all_products)
    
    print(f"\n✓ Extended data ready!")
    print(f"  File: {output_file}")
    print(f"  Products: {len(all_products)}")

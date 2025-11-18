"""
O'Brien's Storage Finder
Copyright (c) 2025 John Hibberd
All rights reserved.

This software is proprietary and confidential.
Unauthorized copying, distribution, or use is strictly prohibited.
"""

import os
import re
import difflib
import requests
import sys
import webbrowser
from dotenv import load_dotenv
from collections import defaultdict
import math

load_dotenv()

BASE_URL = "https://clouduk.storman.com"
TOKEN = os.getenv("STORMAN_API_TOKEN")

# Check if TOKEN is set
if not TOKEN:
    import sys
    sys.stderr.write("WARNING: STORMAN_API_TOKEN environment variable is not set!\n")
    sys.stderr.write("Please set STORMAN_API_TOKEN in Render's environment variables.\n")
    sys.stderr.flush()

HEADERS = {
    "Authorization": f"Bearer {TOKEN}" if TOKEN else "Bearer ",
    "Accept": "application/json"
}

FACILITY_CODES = {
    "container": "OBRIC",
    "internal": "OBRIE"
}

# LIVE PRICING SYSTEM - All pricing and availability fetched from API in real-time
# Pricing will be calculated dynamically from API data only
# Weekly prices calculated as: (monthly × 12) ÷ 52
# NO FALLBACK PRICING - System uses only live API data
SITE_PRICING = {}

VALID_SITES = ["wallsend", "boldon", "birtley", "sunderland", "chester-le-street"]

SITE_PREFIXES = {
    "birtley": ["BIR-", "B2-", "B3-"],
    "boldon": ["BOL-", "BOL2-", "BOL3-"],
    "wallsend": ["WAL-", "W-"],
    "sunderland": ["SUN-"],
    "chester-le-street": ["CLS-"]
}

# Enhanced item volumes for UK general public
ITEM_CUBIC_FEET = {
    # Furniture
    "sofa": 50, "2 seater sofa": 35, "3 seater sofa": 50, "4 seater sofa": 60,
    "corner sofa": 70, "sofa bed": 55, "loveseat": 35, "armchair": 10,
    "rocking chair": 12, "recliner chair": 20, "chaise longue": 25, 
    "settee": 50, "couch": 50, "futon": 40,
    
    # Electronics & Appliances
    "television": 10, "tv": 10, "telly": 10, "flat screen": 10,
    "microwave": 8, "fridge": 65, "freezer": 65, "fridge freezer": 65,
    "washing machine": 25, "washer": 25, "dryer": 25, "dishwasher": 25,
    "dish washer": 25, "oven": 15, "cooker": 15, "hob": 5, "extractor": 3,
    "printer": 8, "computer": 5, "laptop": 2, "desktop": 5,
    
    # Beds & Bedroom
    "double bed": 60, "single bed": 40, "king bed": 70, "super king bed": 75,
    "bunk bed": 65, "bed frame": 30, "mattress": 40, "bedside table": 8,
    "wardrobe": 45, "chest of drawers": 20, "dressing table": 25,
    "mirror": 5, "full length mirror": 8,
    
    # Storage & Boxes
    "box": 3, "small box": 1.5, "medium box": 3, "large box": 4.5,
    "extra-large box": 6, "wardrobe box": 10, "mirror box": 5,
    "archive box": 3, "crate": 3, "suitcase": 8, "rucksack": 3,
    "bin": 5, "storage box": 4, "plastic box": 4,
    
    # Tables & Chairs
    "chair": 10, "dining chair": 8, "office chair": 12, "stool": 5,
    "table": 20, "dining table": 30, "coffee table": 15, "side table": 8,
    "kitchen table": 30, "dining table and chairs": 50, "desk": 25,
    "work desk": 25, "office desk": 25,
    
    # Storage Furniture
    "bookcase": 20, "bookshelf": 20, "filing cabinet": 15, "sideboard": 30,
    "buffet": 30, "display cabinet": 25, "tv stand": 15, "tv cabinet": 15,
    
    # Transport
    "bike": 30, "bicycle": 30, "motorbike": 120, "car": 150, "vehicle": 150,
    "scooter": 40, "pushbike": 30, "mountain bike": 35, "quad bike": 100, "atv": 100,
    "jet ski": 80, "jetski": 80,
    
    # Tools & Equipment
    "tools": 3, "tool box": 4, "tool chest": 10, "lawn mower": 15,
    "hedge trimmer": 10, "strimmer": 8, "garden tools": 5, "drill": 2,
    "saw": 3, "hammer": 1, "screwdriver": 1, "wrench": 1,
    
    # Garden & Outdoor
    "garden chair": 8, "garden table": 20, "shed": 60, "garden shed": 60,
    "barbecue": 20, "bbq": 20, "planter": 12, "flower pot": 12,
    "patio furniture": 30, "sun lounger": 15, "umbrella": 5,
    
    # Sports & Leisure
    "surfboard": 12, "surf board": 12, "treadmill": 50, "exercise bike": 40,
    "gym equipment": 30, "weights": 20, "yoga mat": 2, "tent": 15,
    "camping gear": 20, "fishing gear": 10, "golf clubs": 8,
    
    # Books & Media
    "books": 10, "book": 1, "magazines": 5, "dvds": 3, "cds": 2,
    "records": 5, "vinyl": 5, "games": 3, "board games": 5,
    
    # Clothing & Textiles
    "clothes": 15, "clothing": 15, "shoes": 5, "boots": 8, "bags": 3,
    "rug": 10, "carpet": 10, "curtains": 5, "bedding": 8, "towels": 3,
    "duvet": 5, "pillow": 2, "blanket": 4,
    
    # Kitchen & Dining
    "pots": 8, "pans": 8, "crockery": 5, "plates": 3, "cups": 2,
    "glasses": 2, "cutlery": 2, "kitchen utensils": 5, "blender": 3,
    "toaster": 3, "kettle": 2, "coffee machine": 5,
    
    # Miscellaneous
    "ladder": 10, "step ladder": 8, "paint tins": 6, "paint": 6,
    "cleaning supplies": 5, "vacuum cleaner": 8, "iron": 2, "fan": 5,
    "heater": 5, "radiator": 8, "clock": 1, "picture": 2, "frame": 1,
    "ornament": 1, "vase": 2, "plant": 3, "art": 5, "painting": 3
}

# Enhanced aliases for UK variations and common terms
ALIASES = {
    # TV variations
    "tv": "television", "telly": "television", "flat screen": "television",
    "smart tv": "television", "plasma": "television", "lcd": "television",
    
    # Fridge variations
    "fridge": "fridge freezer", "freezer": "fridge freezer", 
    "american fridge": "fridge freezer", "fridgefreezer": "fridge freezer",
    
    # Washing machine variations
    "washer": "washing machine", "washing mashine": "washing machine", 
    "washingmachin": "washing machine", "washing": "washing machine",
    
    # Dishwasher variations
    "dish washer": "dishwasher", "dishwshr": "dishwasher", 
    "dishwasing machine": "dishwasher", "dish": "dishwasher",
    
    # Box variations
    "archive box": "box", "boxes": "box", "crate": "box", "cardboard box": "box",
    "plastic box": "storage box", "storage boxes": "storage box",
    
    # Bookcase variations
    "bookshelf": "bookcase", "book shelf": "bookcase", "book shelv": "bookcase",
    "shelf": "bookcase", "shelves": "bookcase",
    
    # Sofa variations
    "2 seater": "2 seater sofa", "two seater": "2 seater sofa",
    "3 seater": "3 seater sofa", "three seater": "3 seater sofa",
    "4 seater": "4 seater sofa", "four seater": "4 seater sofa", "4seater": "4 seater sofa",
    "corner settee": "corner sofa", "corner": "corner sofa", "sectional": "corner sofa",
    "couch": "3 seater sofa", "settee": "3 seater sofa", "loveseat": "loveseat",
    
    # Chair variations
    "chair": "chair", "chairs": "chair", "arm chair": "armchair",
    "dining chairs": "dining chair", "kitchen chair": "dining chair",
    
    # Table variations
    "table": "table", "tables": "table", "kitchen table": "table",
    "dinning table": "dining table", "dinning table and chairs": "dining table and chairs",
    
    # Bed variations
    "bed": "double bed", "single": "single bed", "double": "double bed",
    "king": "king bed", "super king": "super king bed", "bunk": "bunk bed",
    "twin": "single bed", "queen": "king bed",
    
    # Tool variations
    "toolbox": "tool box", "toolboxes": "tool box", "tool chest": "tool chest",
    "tool kit": "tool box", "tools": "tools",
    
    # Surfboard variations
    "surf board": "surfboard", "surfboards": "surfboard", "surf": "surfboard",
    
    # Garden tool variations
    "mower": "lawn mower", "hedgeclipper": "hedge trimmer", "strimmer": "hedge trimmer",
    "garden mower": "lawn mower", "grass cutter": "lawn mower",
    
    # Shed variations
    "shed storage": "shed", "garden shed": "shed", "storage shed": "shed",
    "workshop": "shed", "garden building": "shed",
    
    # Printer variations
    "printer machine": "printer", "photocopier": "printer", "scanner": "printer",
    
    # Desk variations
    "work desk": "desk", "office desk": "desk", "computer desk": "desk",
    "study desk": "desk", "writing desk": "desk",
    
    # Filing variations
    "filing drawers": "filing cabinet", "file cabinet": "filing cabinet",
    "drawers": "filing cabinet", "filing": "filing cabinet",
    
    # Bookcase variations
    "book shelves": "bookcase", "bookcases": "bookcase", "shelving": "bookcase",
    
    # TV stand variations
    "tv cabinet": "tv stand", "tv stand unit": "tv stand", "tv unit": "tv stand",
    "television stand": "tv stand", "media unit": "tv stand",
    
    # Coffee table variations
    "coffee table": "coffee table", "side table": "coffee table", 
    "end table": "coffee table", "occasional table": "coffee table",
    
    # Rug variations
    "floor rug": "rug", "carpet": "rug", "mat": "rug", "runner": "rug",
    
    # Fan/Heater variations
    "electric fan": "fan", "radiator": "heater", "heater unit": "heater",
    "space heater": "heater", "portable heater": "heater",
    
    # Wardrobe variations
    "ward robe": "wardrobe", "closet": "wardrobe", "built in wardrobe": "wardrobe",
    "fitted wardrobe": "wardrobe", "walk in wardrobe": "wardrobe",
    
    # Sideboard variations
    "side board": "sideboard", "buffet": "sideboard", "credenza": "sideboard",
    
    # Stool variations
    "stools": "stool", "bar stool": "stool", "kitchen stool": "stool",
    
    # BBQ variations
    "bbq": "barbecue", "barbeque": "barbecue", "grill": "barbecue",
    
    # Planter variations
    "flower pot": "planter", "planters": "planter", "plant pot": "planter",
    "garden pot": "planter", "flowerpot": "planter",
    
    # Paint variations
    "paint cans": "paint tins", "paint bucket": "paint tins", "paint": "paint tins",
    "paint pot": "paint tins", "emulsion": "paint tins",
    
    # Ladder variations
    "step ladder": "step ladder", "stepladder": "step ladder", "ladder": "ladder",
    "extension ladder": "ladder", "folding ladder": "step ladder",
    
    # Bike stand variations
    "bike stand": "bicycle stand", "cycle rack": "bicycle stand", 
    "bicycle rack": "bicycle stand", "bike rack": "bicycle stand",
    
    # Treadmill variations
    "gym treadmill": "treadmill", "running machine": "treadmill", 
    "exercise treadmill": "treadmill", "jogging machine": "treadmill",
    
    # Exercise bike variations
    "exercise cycle": "exercise bike", "spinning bike": "exercise bike",
    "stationary bike": "exercise bike", "indoor bike": "exercise bike",
    
    # Common UK terms
    "hoover": "vacuum cleaner", "dustbin": "bin", "rubbish bin": "bin",
    "wheelie bin": "bin", "bin bag": "bin", "rubbish": "bin",
    "poster": "picture", "photo": "picture", "photograph": "picture",
    "cushion": "pillow", "throw": "blanket", "bedspread": "blanket",
    "duvet cover": "duvet", "sheet": "bedding", "bed sheets": "bedding",
    "tea towel": "towels", "bath towel": "towels", "hand towel": "towels",
    "mug": "cups", "cup": "cups", "glass": "glasses", "wine glass": "glasses",
    "fork": "cutlery", "knife": "cutlery", "spoon": "cutlery",
    "saucepan": "pots", "pan": "pans", "frying pan": "pans",
    "plate": "plates", "bowl": "plates", "dish": "plates",
    "clock": "clock", "watch": "clock", "alarm clock": "clock",
    "ornament": "ornament", "decoration": "ornament", "figurine": "ornament",
    "vase": "vase", "flower vase": "vase", "plant pot": "planter",
    "plant": "plant", "house plant": "plant", "indoor plant": "plant",
    "art": "art", "painting": "painting", "drawing": "art", "print": "art"
}

ALIASES = {k: v for k, v in ALIASES.items() if v in ITEM_CUBIC_FEET}

# Prohibited items by storage type
PROHIBITED_ITEMS_CONTAINER = [
    # Highly flammable items (containers only)
    "vapes", "vape", "e-cigarette", "e-cig", "vapour", "vapor",
    "fuel", "petrol", "diesel", "gas", "gasoline", "propane", "butane",
    "flammable", "explosives", "fireworks", "batteries", "lithium",
    "aerosol", "spray", "paint thinner", "solvent", "lighter fluid",
    "white spirit", "turpentine", "acetone", "methanol", "ethanol",
    "kerosene", "paraffin", "lamp oil", "camping fuel", "stove fuel"
]

PROHIBITED_ITEMS_INTERNAL = [
    # Motor vehicles and large items (internal storage only)
    "motorbike", "motorcycle", "car", "vehicle", "van", "truck", "lorry",
    "scooter", "moped", "quad bike", "atv", "golf cart", "dirt bike",
    "go kart", "go-kart", "jet ski", "jetski", "snowmobile", "snow mobile",
    # Food and perishables (internal storage only)
    "food", "perishable", "fresh food", "frozen food", "meat", "fish",
    "dairy", "milk", "cheese", "yogurt", "fruit", "vegetables", "bread",
    "canned food", "tinned food", "pantry items", "groceries",
    # Plants (internal storage only)
    "plant", "plants", "house plant", "indoor plant", "garden plant",
    "flower", "flowers", "tree", "bush", "shrub", "cactus", "succulent",
    "herb", "herbs", "seedling", "sapling", "potted plant"
]

# General prohibited items (both storage types)
PROHIBITED_ITEMS_GENERAL = [
    "tyres", "tires", "animals", "wildlife", "cigarettes", "illegal", 
    "stolen", "drugs", "weapons", "ammunition", "chemicals", "alcohol", 
    "wine", "beer", "spirits", "medication", "medicine", "prescription"
]

def get_facility_code(site, storage_type):
    """Get facility code for site and storage type"""
    facility_codes = {
        "wallsend": {"container": "OBRIC", "internal": "OBRIC"},
        "boldon": {"container": "OBRIC", "internal": "OBRIC"},
        "birtley": {"container": "OBRIC", "internal": "OBRIC"},
        "sunderland": {"container": "OBRIC", "internal": "OBRIE"},
        "chester-le-street": {"container": "OBRIC", "internal": "OBRIC"}
    }
    return facility_codes.get(site.lower(), {}).get(storage_type, "OBRIC")

def get_available_units(facility_code):
    """Get LIVE available units from the API - real-time availability only"""
    if not TOKEN:
        import sys
        sys.stderr.write("ERROR: STORMAN_API_TOKEN is not set. Cannot fetch units from API.\n")
        sys.stderr.flush()
        return []
    
    try:
        res = requests.get(f"{BASE_URL}/api/v1/facility/{facility_code}/units", headers=HEADERS)
        if res.status_code == 200:
            units = res.json()
            # Filter for available units only - API uses 'VACANT' status for available units
            # This ensures only currently available units are shown
            available_units = [unit for unit in units if unit.get('unit_status') == 'VACANT']
            return available_units
    except Exception as e:
        print(f"Error fetching availability: {e}")
    return []

def get_pricing_from_api(site, storage_type):
    """Get LIVE pricing from API and calculate weekly prices dynamically - NO FALLBACK
    This is an online pricing system - all prices fetched in real-time from API only"""
    if not TOKEN:
        import sys
        sys.stderr.write("ERROR: STORMAN_API_TOKEN is not set. Cannot fetch pricing from API.\n")
        sys.stderr.flush()
        return False
    try:
        facility_code = FACILITY_CODES[storage_type]
        res = requests.get(f"{BASE_URL}/api/v1/facility/{facility_code}/units", headers=HEADERS)
        if res.status_code == 200:
            units = res.json()
            
            # Initialize pricing structure for this site/storage type
            if site not in SITE_PRICING:
                SITE_PRICING[site] = {}
            if storage_type not in SITE_PRICING[site]:
                SITE_PRICING[site][storage_type] = {}
            
            # Dictionary to track the cheapest price for each size
            size_pricing = {}
            
            # Process each unit to extract pricing
            for unit in units:
                unit_area = unit.get('unit_area', 0)
                unit_number = unit.get('unit_number', '')
                unit_type = unit.get('unit_type_code', '').lower()
                monthly_price = unit.get('rack_rate', 0)  # API provides rack_rate as monthly price
                
                # Filter by site
                site_matches = False
                if storage_type == "container":
                    # For containers, use unit_number prefixes
                    if site in SITE_PREFIXES:
                        for prefix in SITE_PREFIXES[site]:
                            if unit_number.startswith(prefix):
                                site_matches = True
                                break
                else:  # Internal storage
                    # For internal storage (Sunderland only), don't filter by unit number
                    site_matches = True
                
                if site_matches and monthly_price > 0:
                    # Calculate weekly price using formula: (monthly × 12) ÷ 52
                    weekly_price = round((monthly_price * 12) / 52, 2)
                    
                    # Map unit areas to standard sizes for containers
                    if storage_type == "container":
                        if unit_area == 40 or ('small' in unit_type or '4x10' in unit_type):
                            size_key = 40
                        elif unit_area == 80 or ('med' in unit_type or '10x8' in unit_type):
                            size_key = 80
                        elif unit_area == 160 or ('large' in unit_type or 'lge' in unit_type or '20x8' in unit_type):
                            size_key = 160
                        elif unit_area == 320 or ('xl' in unit_type or '40x8' in unit_type):
                            size_key = 320
                        else:
                            continue
                    else:  # Internal storage
                        # Use the actual unit area for internal storage
                        if unit_area > 0:
                            size_key = unit_area
                        else:
                            continue
                    
                    # Store the cheapest price for each size
                    if size_key not in size_pricing or monthly_price < size_pricing[size_key]['monthly']:
                        size_pricing[size_key] = {"weekly": weekly_price, "monthly": monthly_price}
            
            # Store the cheapest pricing for each size
            SITE_PRICING[site][storage_type] = size_pricing
            
            # Return True if we found pricing, False if no pricing available
            return len(size_pricing) > 0
            
    except Exception as e:
        print(f"Error fetching pricing from API: {e}")
        return False

def get_available_sizes(site, storage_type):
    """Get LIVE available sizes for a specific site and storage type from API
    Returns only sizes that are currently available - no fallback sizes"""
    import sys
    sys.stderr.write(f"DEBUG get_available_sizes: site={site}, storage_type={storage_type}\n")
    sys.stderr.flush()
    
    # First, fetch live pricing from API to populate SITE_PRICING
    api_success = get_pricing_from_api(site, storage_type)
    sys.stderr.write(f"DEBUG get_available_sizes: get_pricing_from_api returned {api_success}\n")
    sys.stderr.flush()
    
    facility_code = FACILITY_CODES[storage_type]
    sys.stderr.write(f"DEBUG get_available_sizes: facility_code={facility_code}\n")
    sys.stderr.flush()
    
    available_units = get_available_units(facility_code)
    sys.stderr.write(f"DEBUG get_available_sizes: get_available_units returned {len(available_units)} units\n")
    sys.stderr.flush()
    
    # Extract sizes from available units
    available_sizes = set()
    for unit in available_units:
        # Use the actual API data structure
        unit_area = unit.get('unit_area', 0)
        unit_number = unit.get('unit_number', '')
        unit_type = unit.get('unit_type_code', '').lower()
        
        # Filter by site
        site_matches = False
        if storage_type == "container":
            # For containers, use unit_number prefixes
            if site in SITE_PREFIXES:
                for prefix in SITE_PREFIXES[site]:
                    if unit_number.startswith(prefix):
                        site_matches = True
                        break
        else:  # Internal storage
            # For internal storage (Sunderland only), don't filter by unit number
            # All OBRIE units are for Sunderland internal storage
            site_matches = True
        
        if site_matches:
            if storage_type == "container":
                # Map unit areas to standard sizes - check both exact match and unit type
                size_mapped = False
                
                # First check unit_area for exact matches
                if unit_area == 40:
                    available_sizes.add(40)
                    size_mapped = True
                elif unit_area == 80:
                    available_sizes.add(80)
                    size_mapped = True
                elif unit_area == 160:
                    available_sizes.add(160)
                    size_mapped = True
                elif unit_area == 320:
                    available_sizes.add(320)
                    size_mapped = True
                
                # If not mapped by area, check unit_type_code
                if not size_mapped:
                    if 'small' in unit_type or '4x10' in unit_type or '4x8' in unit_type:
                        available_sizes.add(40)
                    elif 'med' in unit_type or '10x8' in unit_type or 'medium' in unit_type:
                        available_sizes.add(80)
                    elif 'large' in unit_type or 'lge' in unit_type or '20x8' in unit_type:
                        available_sizes.add(160)
                    elif 'xl' in unit_type or '40x8' in unit_type or 'extra' in unit_type:
                        available_sizes.add(320)
            else:  # Internal storage
                # For internal storage, use the unit_area directly
                if unit_area > 0:
                    available_sizes.add(unit_area)
    
    # Return only live availability from API - no fallback sizes
    result = sorted(list(available_sizes))
    import sys
    sys.stderr.write(f"DEBUG get_available_sizes: returning {result}\n")
    sys.stderr.flush()
    return result

def calculate_size_from_items(items_list):
    total_cuft = 0
    unrecognized_items = []
    
    for entry in items_list:
        entry = entry.strip().lower()
        qty = 1
        item_words = entry.split()
        
        for i, word in enumerate(item_words):
            if word.isdigit():
                qty = int(word)
                item_name = ' '.join(item_words[:i] + item_words[i+1:])
                break
        else:
            item_name = ' '.join(item_words)

        if item_name in ALIASES:
            item_name = ALIASES[item_name]
        else:
            match = difflib.get_close_matches(item_name, ALIASES.keys(), n=1, cutoff=0.8)
            if match:
                item_name = ALIASES[match[0]]

        if item_name in ITEM_CUBIC_FEET:
            total_cuft += ITEM_CUBIC_FEET[item_name] * qty
        else:
            unrecognized_items.append(entry)
    
    size = max(20, round(total_cuft / 6))
    return size, unrecognized_items

def print_welcome():
    print("=" * 70)
    print("🏠 Welcome to O'Brien's Storage Finder! 🏠")
    print("=" * 70)
    print("Find available storage units in real-time across all our locations.")
    print("Get instant pricing and availability for the perfect storage solution.")
    print("=" * 70)

def get_initial_response():
    print("\nLet's find you the perfect storage solution!")
    print("1. Find available storage (recommended)")
    print("2. Account & invoice inquiry")
    print("3. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        if choice in ['1', '2', '3']:
            return choice
        print("Please enter 1, 2, or 3.")

def handle_account_inquiry():
    print("\n" + "=" * 50)
    print("📞 ACCOUNT & INVOICE INQUIRY")
    print("=" * 50)
    print("Please contact us between 8am – 5pm Monday to Friday")
    print("Or please leave your name and number here and we will call you back.")
    print("=" * 50)

def get_storage_site():
    print("\nWhere are you looking to store?")
    print("We have sites in:")
    print("1. Wallsend")
    print("2. Boldon") 
    print("3. Birtley")
    print("4. Sunderland")
    print("5. Chester-le-Street")
    
    site_map = {
        '1': 'wallsend',
        '2': 'boldon', 
        '3': 'birtley',
        '4': 'sunderland',
        '5': 'chester-le-street'
    }
    
    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        if choice in site_map:
            return site_map[choice]
        print("Please enter a number between 1 and 5.")

def get_storage_type(site):
    if site == "sunderland":
        print("\nWhat type of storage are you looking for?")
        print("1. Container storage (outdoor, 24/7 access)")
        print("2. Internal storage (indoor, business hours)")
        
        while True:
            choice = input("\nEnter your choice (1-2): ").strip()
            if choice == '1':
                return 'container'
            elif choice == '2':
                return 'internal'
            print("Please enter 1 or 2.")
    else:
        return 'container'

def get_customer_choice(storage_type):
    print("\nDo you know what size you need, or would you like our recommendation?")
    
    if storage_type == "container":
        print("1. I know what size I need (e.g., 10ft container, 20ft container, 40ft container, or 40sqft, 160sqft)")
    else:  # internal storage
        print("1. I know what size I need (e.g., 25sqft room, 50sqft room, 75sqft room)")
    
    print("2. I need help - recommend based on my items")
    
    while True:
        choice = input("\nEnter your choice (1-2): ").strip()
        if choice in ['1', '2']:
            return choice
        print("Please enter 1 or 2.")

def get_known_size(site, storage_type):
    # Get available sizes from API
    available_sizes = get_available_sizes(site, storage_type)
    
    if not available_sizes:
        print("⚠️  Currently no units available at this site.")
        print("Please contact us directly for availability updates.")
        return None
    
    if storage_type == "container":
        print(f"\nWhat size container do you need?")
        print("You can tell me the size in sqft (e.g., 40, 80, 160, 320) or describe it (e.g., small, medium, large, extra large).")
        print("For container dimensions, you can also say: 10ft, 20ft, or 40ft container.")
        
        while True:
            user_input = input("\nWhat size do you need? ").strip().lower()
            
            # Try to parse numeric input
            try:
                requested_size = int(user_input)
                # Find the closest available size
                closest_size = min(available_sizes, key=lambda x: abs(x - requested_size))
                if closest_size == requested_size:
                    print(f"✅ Perfect! We have {closest_size} sqft containers available.")
                else:
                    print(f"✅ We don't have exactly {requested_size} sqft, but we have {closest_size} sqft available.")
                    confirm = input(f"Would you like the {closest_size} sqft container? (y/n): ").strip().lower()
                    if confirm != 'y':
                        continue
                return closest_size
            except ValueError:
                # Handle descriptive input with enhanced container dimensions
                size_mapping = {
                    # Square footage
                    'small': 40, 's': 40, '4x10': 40, '4ft': 40,
                    'medium': 80, 'med': 80, 'm': 80, '10x8': 80, '8ft': 80,
                    'large': 160, 'l': 160, '20x8': 160,
                    'extra large': 320, 'xl': 320, 'extra': 320, '40x8': 320,
                    # Container dimensions (most common way customers ask)
                    '10ft': 40, '10 foot': 40, '10ft container': 40, '10 foot container': 40,
                    '20ft': 160, '20 foot': 160, '20ft container': 160, '20 foot container': 160,
                    '40ft': 320, '40 foot': 320, '40ft container': 320, '40 foot container': 320,
                    # Additional variations
                    'ten foot': 40, 'ten ft': 40, 'ten foot container': 40,
                    'twenty foot': 160, 'twenty ft': 160, 'twenty foot container': 160,
                    'forty foot': 320, 'forty ft': 320, 'forty foot container': 320
                }
                
                if user_input in size_mapping:
                    requested_size = size_mapping[user_input]
                    closest_size = min(available_sizes, key=lambda x: abs(x - requested_size))
                    if closest_size == requested_size:
                        print(f"✅ Perfect! We have {closest_size} sqft containers available.")
                    else:
                        print(f"✅ We don't have exactly {requested_size} sqft, but we have {closest_size} sqft available.")
                        confirm = input(f"Would you like the {closest_size} sqft container? (y/n): ").strip().lower()
                        if confirm != 'y':
                            continue
                    return closest_size
                else:
                    print("I didn't understand that. Please try again with:")
                    print("• Square footage: '40', '80', '160', '320'")
                    print("• Descriptions: 'small', 'medium', 'large', 'extra large'")
                    print("• Container dimensions: '10ft', '20ft', '40ft'")
    else:  # Internal storage
        print(f"\nWhat size room do you need?")
        print("You can tell me the size in sqft (e.g., 25, 35, 50, 75) and I'll recommend the closest available option.")
        
        while True:
            user_input = input("\nWhat size do you need? ").strip().lower()
            
            # Try to parse numeric input
            try:
                requested_size = int(user_input)
                # Find the closest available size
                closest_size = min(available_sizes, key=lambda x: abs(x - requested_size))
                if closest_size == requested_size:
                    print(f"✅ Perfect! We have {closest_size} sqft rooms available.")
                else:
                    print(f"✅ We don't have exactly {requested_size} sqft, but we have {closest_size} sqft available.")
                    confirm = input(f"Would you like the {closest_size} sqft room? (y/n): ").strip().lower()
                    if confirm != 'y':
                        continue
                return closest_size
            except ValueError:
                print("I didn't understand that. Please try again with a size like '25', '35', '50', '75' etc.")

def display_site_info(site, storage_type):
    print(f"\n{'='*50}")
    print(f"📍 {site.title()} - {storage_type.title()} Storage")
    print(f"{'='*50}")
    
    if storage_type == "container":
        print("🚛 CONVENIENT ACCESS")
        print("• Drive-up containers for easy loading and unloading – no trolleys, lifts, or corridors")
        print("• 24/7 direct access via car, van, or truck")
        print("• Flexible, pay-as-you-go contracts with refundable deposits")
        print("• Fixed pricing for 12 months – guaranteed")
        print()
        print("🔒 SECURITY YOU CAN TRUST")
        print("• 24-hour monitored CCTV")
        if site == "birtley":
            print("• On-site 24-hour Security presence by our Birtley Security team")
        else:
            print("• Monitored by our local security team based in Birtley")
        print("• Gated entry with code access and ANPR")
        print("• Optional insurance and heavy-duty locks available")
        
    else:  # Internal storage (Sunderland)
        print("📦 GOOD LIFT 2M X 2M")
        print()
        print("🎯 YOUR PERSONALISED STORAGE PLAN INCLUDES:")
        print("• Private, Secure Rooms: Tailored to your individual needs")
        print("• Range of Sizes: Affordable options to suit your budget")
        print("• Monthly Billing: No confusing four-week cycles, just simple, straightforward payments")
        print("• Flexible Contracts: Includes refunds for any unused rental or insurance")
        print("• Price Guarantee for 12 Months: No unexpected increases, your price is locked in")
        print("• Professional, Personal Service: You're never just a number to us")
        print("• Free Trolley and Lift Use: Making access easy and efficient")
        print()
        print("🔧 ADDITIONAL SERVICES AVAILABLE:")
        print("• Insurance Options: For added peace of mind")
        print("• Packing Materials: Available on-site for convenience")
        print("• Recommended Removals: Trusted local partners available")
        print("• Out-of-Hours Access: Available on request")
        print("• Collection & Delivery Service: Drop parcels with us for easy collection later")
    
    return True

def display_pricing_info(site, storage_type, available_sizes):
    """Display pricing information after we know the customer's needs"""
    print(f"\n✅ Currently available sizes and pricing:")
    
    if storage_type == "container":
        for size in available_sizes:
            if size == 40:
                if site == "wallsend":
                    print(f"• Small (4ft x 10ft - 40sqft) - £18 a week inc VAT with 2nd month free promotion (£{SITE_PRICING[site]['container'][40]['monthly']} per month)")
                else:
                    print(f"• Small (4ft x 10ft - 40sqft) - £{SITE_PRICING[site]['container'][40]['weekly']} a week inc VAT (£{SITE_PRICING[site]['container'][40]['monthly']} per month)")
            elif size == 80:
                if site == "wallsend":
                    print(f"• Medium (10ft x 8ft - 80sqft) - £18 a week inc VAT with 2nd month free promotion (£{SITE_PRICING[site]['container'][80]['monthly']} per month)")
                else:
                    print(f"• Medium (10ft x 8ft - 80sqft) - £{SITE_PRICING[site]['container'][80]['weekly']} a week inc VAT (£{SITE_PRICING[site]['container'][80]['monthly']} per month)")
            elif size == 160:
                if site == "wallsend":
                    print(f"• Large (20ft x 8ft - 160sqft) - £18 a week inc VAT with 2nd month free promotion (£{SITE_PRICING[site]['container'][160]['monthly']} per month)")
                else:
                    print(f"• Large (20ft x 8ft - 160sqft) - £{SITE_PRICING[site]['container'][160]['weekly']} a week inc VAT (£{SITE_PRICING[site]['container'][160]['monthly']} per month)")
            elif size == 320:
                print(f"• Extra Large (40ft x 8ft - 320sqft) - £{SITE_PRICING[site]['container'][320]['weekly']} a week inc VAT (£{SITE_PRICING[site]['container'][320]['monthly']} per month)")
            
        if site == "wallsend":
            print("\n🎉 SPECIAL OFFER: 2nd month free promotion - equates to £18 per week!")
        
    else:  # Internal storage (Sunderland)
        for size in available_sizes:
            if size in SITE_PRICING['sunderland']['internal']:
                pricing = SITE_PRICING['sunderland']['internal'][size]
                half_weekly = pricing['weekly'] / 2
                half_monthly = pricing['monthly'] / 2
                print(f"• {size} sqft room (8ft tall) - £{half_weekly:.2f} a week inc VAT (£{half_monthly:.2f} per month) for the 1st 2 months, £{pricing['weekly']} a week inc VAT (£{pricing['monthly']} per month) thereafter")
        
        print("🎉 SPECIAL OFFER: First 2 months at half price!")

def get_initial_description():
    """Get initial 1-liner description from user"""
    print("\nCan you give me a rough idea of what you're storing? Just one line is fine.")
    print("Examples: 'boxes and a mattress' or 'a small motorbike and tools'")
    
    description = input("\nWhat are you storing? ").strip()
    return description

def analyze_initial_description(description):
    """Analyze the initial description to extract items and check for issues"""
    items = []
    prohibited_items = []
    vehicle_mentioned = False
    
    # Simple parsing - split by common conjunctions and prepositions
    import re
    # Split by common words that separate items
    parts = re.split(r'\s+(?:and|or|with|plus|including|,\s*|\+)\s+', description.lower())
    
    # Motor vehicle keywords - excluding push bikes/bicycles
    motor_vehicle_keywords = [
        'car', 'motorbike', 'motorcycle', 'vehicle', 'van', 'truck', 'lorry', 'trailer',
        'quad', 'quad bike', 'atv', 'all terrain vehicle', 'dirt bike', 'go kart', 'go-kart',
        'jet ski', 'jetski', 'snowmobile', 'snow mobile', 'moped', 'scooter',
        'petrol', 'gasoline', 'fuel', 'engine', 'motor'
    ]
    
    for part in parts:
        part = part.strip()
        if part:
            # Check for motor vehicles
            for vehicle in motor_vehicle_keywords:
                if vehicle in part:
                    vehicle_mentioned = True
                    break
            
            # Try to extract quantity and item
            # Look for patterns like "2 boxes", "1 sofa", "a mattress", etc.
            quantity_match = re.match(r'(\d+)\s+(.+)', part)
            if quantity_match:
                quantity = int(quantity_match.group(1))
                item = quantity_match.group(2)
                items.append(f"{item} {quantity}")
            else:
                # No quantity specified, assume 1
                items.append(f"{part} 1")
    
    return items, prohibited_items, vehicle_mentioned

def get_items_for_storage():
    print("\n📦 What are you looking to store?")
    print("We need to make sure we're aware of all items.")
    print("Examples: '2 sofas', '1 fridge freezer', '3 boxes', '1 car'")
    print("Type 'done' when you've finished listing your items.")
    
    items = []
    while True:
        item = input(f"\nItem {len(items) + 1}: ").strip()
        if item.lower() == 'done':
            break
        if item:
            items.append(item)
    
    return items

def check_prohibited_items(items, storage_type):
    """Check for prohibited items based on storage type"""
    prohibited_found = []
    
    # Get the appropriate prohibited items list
    if storage_type == "container":
        prohibited_list = PROHIBITED_ITEMS_CONTAINER + PROHIBITED_ITEMS_GENERAL
    else:  # internal
        prohibited_list = PROHIBITED_ITEMS_INTERNAL + PROHIBITED_ITEMS_GENERAL
    
    for item in items:
        item_lower = item.lower()
        for prohibited in prohibited_list:
            if prohibited in item_lower:
                prohibited_found.append(item)
                break
    
    return prohibited_found

def display_contract_info(storage_type):
    print(f"\n📋 CONTRACT INFORMATION")
    print(f"{'='*50}")
    
    if storage_type == "container":
        print("• Monthly renewable contracts")
        print("• Pay monthly in advance")
        print("• £120 deposit (fully refundable)")
        print("• Insurance: £0.99 per £1k per week (advised) - Does not cover vehicles")
        print("• Heavy-duty padlock: £25 (container-specific)")
    else:  # Internal
        print("• Monthly renewable contracts") 
        print("• Pay monthly in advance")
        print("• £50 deposit (fully refundable)")
        print("• Insurance required: £0.99 per £1k per week - Does not cover vehicles")
        print("• Padlock: £9.99")
        print("• Liability: Goods stored at your sole risk")
        print("• Liability limit: £100")

def display_results(site, storage_type, size, items, unrecognized_items, prohibited_items, customer_name):
    print(f"\n{'='*60}")
    print(f"📋 YOUR STORAGE RECOMMENDATION")
    print(f"{'='*60}")
    
    print(f"📍 Location: {site.title()}")
    print(f"🏢 Storage Type: {storage_type.title()}")
    
    if items:  # If they provided items, show the calculation
        print(f"📦 Items: {', '.join(items)}")
        print(f"📏 Estimated Size Needed: {size} sq ft")
    else:  # If they chose a specific size
        print(f"📏 Selected Size: {size} sq ft")
    
    # Get available sizes from API
    available_sizes = get_available_sizes(site, storage_type)
    
    if not available_sizes:
        print("⚠️  Currently no units available at this site.")
        print("Please contact us directly for availability updates.")
        return
    
    # Find suitable size
    suitable_size = None
    
    # If we have items, find the next available size >= required size
    # If we don't have items (multi-step selection), use the exact selected size
    if items:
        for available_size in available_sizes:
            if available_size >= size:
                suitable_size = available_size
                break
    else:
        # Multi-step selection - use the exact selected size if it's available
        if size in available_sizes:
            suitable_size = size
        else:
            # Fallback to finding next available size
            for available_size in available_sizes:
                if available_size >= size:
                    suitable_size = available_size
                    break
    
    if suitable_size:
        # Ensure pricing is fetched - try again if missing
        if site not in SITE_PRICING or storage_type not in SITE_PRICING[site] or suitable_size not in SITE_PRICING[site][storage_type]:
            # Try to fetch pricing again
            get_pricing_from_api(site, storage_type)
        
        # Get pricing for the suitable size
        if site in SITE_PRICING and storage_type in SITE_PRICING[site]:
            if suitable_size in SITE_PRICING[site][storage_type]:
                pricing = SITE_PRICING[site][storage_type][suitable_size]
                
                # Show pricing in a clean format
                print(f"\n✅ RECOMMENDED SOLUTION:")
                if storage_type == "container":
                    if suitable_size == 40:
                        print(f"   Small (4ft x 10ft - 40sqft)")
                    elif suitable_size == 80:
                        print(f"   Medium (10ft x 8ft - 80sqft)")
                    elif suitable_size == 160:
                        print(f"   Large (20ft x 8ft - 160sqft)")
                    elif suitable_size == 320:
                        print(f"   Extra Large (40ft x 8ft - 320sqft)")
                else:
                    print(f"   {suitable_size} sqft room (8ft tall)")
                
                if storage_type == "internal":
                    # Show half-price for first 2 months, then regular price
                    half_weekly = pricing['weekly'] / 2
                    half_monthly = pricing['monthly'] / 2
                    print(f"   💰 £{half_weekly:.2f} per week inc VAT (£{half_monthly:.2f} per month) for the 1st 2 months")
                    print(f"   💰 £{pricing['weekly']} per week inc VAT (£{pricing['monthly']} per month) thereafter")
                elif site == "wallsend" and storage_type == "container" and suitable_size in [40, 80, 160]:
                    # Show £18 per week for Wallsend containers with 2nd month free promotion
                    print(f"   💰 £18 per week inc VAT with 2nd month free promotion")
                    print(f"   💰 £{pricing['monthly']} per month")
                else:
                    print(f"   💰 £{pricing['weekly']} per week inc VAT")
                    print(f"   💰 £{pricing['monthly']} per month")
                
                # Show special offers
                if site == "wallsend" and storage_type == "container" and suitable_size in [40, 80, 160]:
                    print(f"   🎉 SPECIAL: 2nd month free promotion - equates to £18 per week!")
                elif storage_type == "internal":
                    print(f"   🎉 SPECIAL: First 2 months at half price!")
                
            else:
                print(f"⚠️  Size {suitable_size} sq ft available but pricing not available from API")
                print(f"   Please contact us for current pricing: 0191 5372436")
        else:
            print(f"⚠️  Size {suitable_size} sq ft available but pricing not available from API")
            print(f"   Please contact us for current pricing: 0191 5372436")
    else:
        print(f"⚠️  No suitable size available for your needs ({size} sq ft)")
        print("Available sizes:")
        for available_size in available_sizes:
            if site in SITE_PRICING and storage_type in SITE_PRICING[site]:
                if available_size in SITE_PRICING[site][storage_type]:
                    pricing = SITE_PRICING[site][storage_type][available_size]
                    if storage_type == "internal":
                        half_weekly = pricing['weekly'] / 2
                        half_monthly = pricing['monthly'] / 2
                        print(f"   • {available_size} sq ft - £{half_weekly:.2f}/week (£{half_monthly:.2f}/month) for 1st 2 months, £{pricing['weekly']}/week (£{pricing['monthly']}/month) thereafter")
                    elif site == "wallsend" and storage_type == "container" and available_size in [40, 80, 160]:
                        print(f"   • {available_size} sq ft - £18/week with 2nd month free promotion (£{pricing['monthly']}/month)")
                    else:
                        print(f"   • {available_size} sq ft - £{pricing['weekly']}/week (£{pricing['monthly']}/month)")
                else:
                    print(f"   • {available_size} sq ft - pricing not available")
            else:
                print(f"   • {available_size} sq ft")
        print("Please contact us to discuss alternatives.")
    
    if unrecognized_items:
        print(f"\n⚠️  Note: Some items weren't recognized:")
        for item in unrecognized_items:
            print(f"   • {item}")
        print("   (This may affect the size calculation)")
    
    if prohibited_items:
        print(f"\n🚫 WARNING: Some items may be prohibited:")
        for item in prohibited_items:
            print(f"   • {item}")
        print("   Please contact us for clarification.")
    
    # Check for sofa in internal storage
    if storage_type == "internal" and items and any("sofa" in item.lower() for item in items):
        print(f"\n📏 IMPORTANT: The lift is 2m x 2m")
        print("   A typical 3-seater sofa may be too big for the lift.")
        print("   Please measure your sofa before booking.")
    
    print(f"\n{'='*60}")
    print("Ready to book? Choose an option:")
    print("1. 🔗 Book now online")
    print("2. 📞 Call us: 0191 5372436")
    print("3. 📧 Email us: info@obrienselfstorage.co.uk")

    # Get user choice
    booking_choice = input("\nEnter your choice (1-3): ").strip()

    if booking_choice == '1':
        # Provide booking link
        if storage_type == "container":
            print("🔗 Container booking: https://portaluk.storman.com/facility/OBRIC/unit-selection?env=uk")
        else:
            print("🔗 Internal storage booking: https://portaluk.storman.com/facility/OBRIE/unit-selection?env=uk")
        print("Opening booking link...")
        import webbrowser
        if storage_type == "container":
            webbrowser.open("https://portaluk.storman.com/facility/OBRIC/unit-selection?env=uk")
        else:
            webbrowser.open("https://portaluk.storman.com/facility/OBRIE/unit-selection?env=uk")
    elif booking_choice == '2':
        print("📞 Please call us on: 0191 5372436")
        print("We're available Monday-Friday 8am-5pm")
    elif booking_choice == '3':
        print("📧 Please email us at: info@obrienselfstorage.co.uk")
        print("We'll get back to you within 24 hours")
    else:
        print("❌ Invalid choice. Please contact us directly.")
    
    print(f"{'='*60}")

def main():
    print_welcome()
    
    # Capture customer information at the beginning
    print("\n" + "="*60)
    print("📋 CUSTOMER INFORMATION")
    print("="*60)
    customer_name = input("Please enter your name: ").strip()
    customer_phone = input("Please enter your phone number: ").strip()
    customer_email = input("Please enter your email address: ").strip()
    
    # Validate that we have at least a name
    if not customer_name:
        print("❌ Name is required. Please try again.")
        return
    
    print(f"\n✅ Thank you, {customer_name}! Let's find you the perfect storage solution.")
    
    while True:
        prohibited_items_handled = False  # Initialize flag at the start of each loop iteration
        choice = get_initial_response()
        
        if choice == '2':
            handle_account_inquiry()
            continue_choice = input("\nWould you like to find storage instead? (y/n): ").strip().lower()
            if continue_choice != 'y':
                print("\n👋 Thanks for using O'Brien's Storage Finder!")
                print("Have a great day!")
                break
            continue
            
        elif choice == '3':
            print("\n👋 Thanks for using O'Brien's Storage Finder!")
            print("Have a great day!")
            break
        
        # Storage finding - Main focus
        # Find available storage units with real-time pricing and availability
        
        # Stage 1: Get initial description (1-liner)
        initial_description = get_initial_description()
        if not initial_description:
            print("\n❌ No description provided. Please try again.")
            continue
        
        # Analyze the description for items and issues
        initial_items, initial_prohibited, vehicle_mentioned = analyze_initial_description(initial_description)
        
        # Stage 2: Get location
        site = get_storage_site()
        storage_type = get_storage_type(site)
        
        # Check for vehicle storage issues
        if vehicle_mentioned and storage_type == "internal":
            print("\n⚠️  IMPORTANT: Vehicles are not allowed in internal storage rooms.")
            print("   You'll need to use container storage instead.")
            print("   Would you like to switch to container storage?")
            switch_choice = input("   Switch to container? (y/n): ").strip().lower()
            if switch_choice == 'y':
                storage_type = "container"
                prohibited_items_handled = True  # Mark that we've handled vehicle/prohibited items
                print("   ✅ Switched to container storage.")
                
                # Show all available container sites since vehicle requires container storage
                print("\n🔍 Checking available container units across all sites...")
                available_container_sites = []
                
                # Check all sites for available container units
                sites_to_check = ["wallsend", "boldon", "birtley", "sunderland", "chester-le-street"]
                for check_site in sites_to_check:
                    try:
                        # Get available units for containers at this site
                        available_units = get_available_units(get_facility_code(check_site, "container"))
                        
                        # Filter units by site-specific prefixes
                        site_specific_units = []
                        if check_site in SITE_PREFIXES:
                            for unit in available_units:
                                unit_number = unit.get('unit_number', '')
                                for prefix in SITE_PREFIXES[check_site]:
                                    if unit_number.startswith(prefix):
                                        site_specific_units.append(unit)
                                        break
                        
                        if site_specific_units:
                            # Get pricing for this site
                            pricing_success = get_pricing_from_api(check_site, "container")
                            if pricing_success and check_site in SITE_PRICING and "container" in SITE_PRICING[check_site]:
                                available_container_sites.append({
                                    'site': check_site.title(),
                                    'units': site_specific_units,
                                    'pricing': SITE_PRICING[check_site]["container"]
                                })
                    except Exception as e:
                        continue
                
                if available_container_sites:
                    print(f"\n✅ Found {len(available_container_sites)} site(s) with available container units:")
                    print("=" * 50)
                    
                    # Show sites and available sizes
                    print("\n📍 Available Container Sites and Sizes:")
                    for i, site_info in enumerate(available_container_sites, 1):
                        print(f"\n{i}. {site_info['site']} - Container Storage")
                        print("   Available sizes:")
                        
                        # Extract available sizes from the units list
                        available_sizes_set = set()
                        for unit in site_info['units']:
                            unit_area = unit.get('unit_area', 0)
                            unit_type = unit.get('unit_type_code', '').lower()
                            
                            # Map unit areas to standard sizes for containers
                            if unit_area == 40 or ('small' in unit_type or '4x10' in unit_type):
                                available_sizes_set.add(40)
                            elif unit_area == 80 or ('med' in unit_type or '10x8' in unit_type):
                                available_sizes_set.add(80)
                            elif unit_area == 160 or ('large' in unit_type or 'lge' in unit_type or '20x8' in unit_type):
                                available_sizes_set.add(160)
                            elif unit_area == 320 or ('xl' in unit_type or '40x8' in unit_type):
                                available_sizes_set.add(320)
                        
                        # Show sizes with pricing
                        for size in sorted(available_sizes_set):
                            if size in site_info['pricing']:
                                pricing = site_info['pricing'][size]
                                if size == 40:
                                    if site_info['site'].lower() == "wallsend":
                                        print(f"      • Small (4ft x 10ft - 40sqft) - £18/week with 2nd month free promotion")
                                    else:
                                        print(f"      • Small (4ft x 10ft - 40sqft) - £{pricing['weekly']}/week (£{pricing['monthly']}/month)")
                                elif size == 80:
                                    if site_info['site'].lower() == "wallsend":
                                        print(f"      • Medium (10ft x 8ft - 80sqft) - £18/week with 2nd month free promotion")
                                    else:
                                        print(f"      • Medium (10ft x 8ft - 80sqft) - £{pricing['weekly']}/week (£{pricing['monthly']}/month)")
                                elif size == 160:
                                    if site_info['site'].lower() == "wallsend":
                                        print(f"      • Large (20ft x 8ft - 160sqft) - £18/week with 2nd month free promotion")
                                    else:
                                        print(f"      • Large (20ft x 8ft - 160sqft) - £{pricing['weekly']}/week (£{pricing['monthly']}/month)")
                                elif size == 320:
                                    print(f"      • Extra Large (40ft x 8ft - 320sqft) - £{pricing['weekly']}/week (£{pricing['monthly']}/month)")
                    
                    print("\n" + "=" * 50)
                    
                    # Let user pick a site and size
                    print("Please select a site and size:")
                    try:
                        site_choice = int(input("Enter site number: ").strip())
                        if 1 <= site_choice <= len(available_container_sites):
                            selected_site_info = available_container_sites[site_choice - 1]
                            selected_site = selected_site_info['site'].lower()
                            
                            # Update the site and storage_type variables
                            site = selected_site
                            storage_type = "container"
                            
                            # Get available sizes for the selected site
                            available_sizes_set = set()
                            for unit in selected_site_info['units']:
                                unit_area = unit.get('unit_area', 0)
                                unit_type = unit.get('unit_type_code', '').lower()
                                
                                if unit_area == 40 or ('small' in unit_type or '4x10' in unit_type):
                                    available_sizes_set.add(40)
                                elif unit_area == 80 or ('med' in unit_type or '10x8' in unit_type):
                                    available_sizes_set.add(80)
                                elif unit_area == 160 or ('large' in unit_type or 'lge' in unit_type or '20x8' in unit_type):
                                    available_sizes_set.add(160)
                                elif unit_area == 320 or ('xl' in unit_type or '40x8' in unit_type):
                                    available_sizes_set.add(320)
                            
                            # Display site info first
                            display_site_info(site, storage_type)
                            
                            # Add gap between USP and price
                            print("\n" + "=" * 50)
                            
                            # Let user select a specific size
                            print("Please select your preferred unit size:")
                            size_options = sorted(available_sizes_set)
                            for i, size in enumerate(size_options, 1):
                                if size == 40:
                                    print(f"{i}. Small (4ft x 10ft - 40sqft)")
                                elif size == 80:
                                    print(f"{i}. Medium (10ft x 8ft - 80sqft)")
                                elif size == 160:
                                    print(f"{i}. Large (20ft x 8ft - 160sqft)")
                                elif size == 320:
                                    print(f"{i}. Extra Large (40ft x 8ft - 320sqft)")
                            
                            try:
                                size_choice = int(input("\nEnter size number: ").strip())
                                if 1 <= size_choice <= len(size_options):
                                    selected_size = size_options[size_choice - 1]
                                    
                                    # Display actual dimensions based on selected size
                                    if selected_size == 40:
                                        dimensions = "4x8x8"
                                        size_name = "Small"
                                    elif selected_size == 80:
                                        dimensions = "10x8x8"
                                        size_name = "Medium"
                                    elif selected_size == 160:
                                        dimensions = "20x8x8"
                                        size_name = "Large"
                                    elif selected_size == 320:
                                        dimensions = "40x8x8"
                                        size_name = "Extra Large"
                                    
                                    print(f"\n📏 Your selected {size_name} unit dimensions: {dimensions} feet")
                                    print("(Internal dimensions may vary by approximately 8 inches)")
                                    
                                    # Ask if vehicle fits
                                    vehicle_fit = input("\nWould your vehicle fit? (y/n): ").strip().lower()
                                    
                                    if vehicle_fit == 'y':
                                        print(f"\n✅ Perfect! Let's show you the pricing for your {size_name} unit.")
                                        
                                        # Display pricing for the selected size only
                                        print(f"\n✅ Pricing for {size_name} unit ({dimensions}):")
                                        if selected_size == 40:
                                            if site == "wallsend":
                                                print(f"• Small (4ft x 10ft - 40sqft) - £18 a week inc VAT with 2nd month free promotion (£{SITE_PRICING[site]['container'][40]['monthly']} per month)")
                                            else:
                                                print(f"• Small (4ft x 10ft - 40sqft) - £{SITE_PRICING[site]['container'][40]['weekly']} a week inc VAT (£{SITE_PRICING[site]['container'][40]['monthly']} per month)")
                                        elif selected_size == 80:
                                            if site == "wallsend":
                                                print(f"• Medium (10ft x 8ft - 80sqft) - £18 a week inc VAT with 2nd month free promotion (£{SITE_PRICING[site]['container'][80]['monthly']} per month)")
                                            else:
                                                print(f"• Medium (10ft x 8ft - 80sqft) - £{SITE_PRICING[site]['container'][80]['weekly']} a week inc VAT (£{SITE_PRICING[site]['container'][80]['monthly']} per month)")
                                        elif selected_size == 160:
                                            if site == "wallsend":
                                                print(f"• Large (20ft x 8ft - 160sqft) - £18 a week inc VAT with 2nd month free promotion (£{SITE_PRICING[site]['container'][160]['monthly']} per month)")
                                            else:
                                                print(f"• Large (20ft x 8ft - 160sqft) - £{SITE_PRICING[site]['container'][160]['weekly']} a week inc VAT (£{SITE_PRICING[site]['container'][160]['monthly']} per month)")
                                        elif selected_size == 320:
                                            print(f"• Extra Large (40ft x 8ft - 320sqft) - £{SITE_PRICING[site]['container'][320]['weekly']} a week inc VAT (£{SITE_PRICING[site]['container'][320]['monthly']} per month)")
                                        
                                        if site == "wallsend":
                                            print("\n🎉 SPECIAL OFFER: 2nd month free promotion - equates to £18 per week!")
                                        
                                        # Display results with booking options
                                        display_results(site, storage_type, selected_size, [], [], [], customer_name)
                                        
                                        # Ask if they want to re-choose site/size or continue
                                        print(f"\n{'='*60}")
                                        print("What would you like to do next?")
                                        print("1. 🔄 Re-choose site and size")
                                        print("2. ✅ Proceed with current selection")
                                        print("3. 🏠 Start over")
                                        print("4. 👋 Exit")
                                        
                                        next_choice = input("\nEnter your choice (1-4): ").strip()
                                        
                                        if next_choice == '1':
                                            print("\n🔄 Let's help you choose a different site or size.")
                                            print("Would you like to:")
                                            print("1. 📍 Choose a different site")
                                            print("2. 📏 Choose a different size")
                                            print("3. 🔙 Go back to current selection")
                                            
                                            reselect_choice = input("Enter your choice (1-3): ").strip()
                                            
                                            if reselect_choice == '1':
                                                print("\n📍 Let's choose a different site...")
                                                continue  # This will restart the site selection
                                            elif reselect_choice == '2':
                                                print("\n📏 Let's choose a different size...")
                                                # Get available sizes for current site
                                                available_sizes = get_available_sizes(site, storage_type)
                                                if available_sizes:
                                                    print(f"\nAvailable sizes at {site.title()}:")
                                                    for i, available_size in enumerate(available_sizes, 1):
                                                        if storage_type == "container":
                                                            if available_size == 40:
                                                                print(f"{i}. Small (4ft x 10ft - 40sqft)")
                                                            elif available_size == 80:
                                                                print(f"{i}. Medium (10ft x 8ft - 80sqft)")
                                                            elif available_size == 160:
                                                                print(f"{i}. Large (20ft x 8ft - 160sqft)")
                                                            elif available_size == 320:
                                                                print(f"{i}. Extra Large (40ft x 8ft - 320sqft)")
                                                        else:
                                                            print(f"{i}. {available_size} sqft room")
                                                    
                                                    try:
                                                        new_size_choice = int(input("\nEnter size number: ").strip())
                                                        if 1 <= new_size_choice <= len(available_sizes):
                                                            selected_size = available_sizes[new_size_choice - 1]
                                                            print(f"✅ Updated size to {selected_size} sqft")
                                                            continue  # This will restart the results display
                                                        else:
                                                            print("❌ Invalid size choice. Keeping current selection.")
                                                    except ValueError:
                                                        print("❌ Invalid input. Keeping current selection.")
                                                else:
                                                    print("❌ No sizes available at this site.")
                                            elif reselect_choice == '3':
                                                print("✅ Keeping current selection.")
                                            else:
                                                print("❌ Invalid choice. Keeping current selection.")
                                        elif next_choice == '2':
                                            print("✅ Proceeding with current selection.")
                                        elif next_choice == '3':
                                            print("🔄 Starting over...")
                                            continue  # This will restart the main loop
                                        elif next_choice == '4':
                                            print("\n👋 Thanks for using O'Brien's Storage Finder!")
                                            print("Have a great day!")
                                            break
                                        else:
                                            print("❌ Invalid choice. Please try again.")
                                            continue
                                    else:
                                        print("\n❌ No problem! Let's try a different size or site.")
                                        print("Would you like to:")
                                        print("1. Try a larger unit")
                                        print("2. Try a different site")
                                        print("3. Start over")
                                        
                                        retry_choice = input("Enter your choice (1-3): ").strip()
                                        if retry_choice == "1":
                                            continue  # This will restart the size selection
                                        elif retry_choice == "2":
                                            break  # This will restart the site selection
                                        else:
                                            continue  # This will restart the main loop
                                else:
                                    print("❌ Invalid size selection. Please try again.")
                                    continue
                            except ValueError:
                                print("❌ Please enter a valid number.")
                                continue
                        else:
                            print("❌ Invalid selection. Please try again.")
                            continue
                    except ValueError:
                        print("❌ Please enter a valid number.")
                        continue
                else:
                    print("⚠️  No container units currently available at any site.")
                    print("Please contact us directly for availability updates.")
                    continue
            else:
                print("   ❌ Vehicle storage not available in internal rooms.")
                print("   Please contact us for assistance.")
                continue
        
        # Handle special cases (but skip if we've already handled prohibited items)
        if site == "sunderland" and storage_type == "container" and not prohibited_items_handled:
            print("\n⚠️  Sunderland containers currently have a waiting list.")
            print("Please leave your name and number and we'll contact you.")
            name = input("Name: ").strip()
            number = input("Phone number: ").strip()
            print("Thank you! We'll be in touch soon.")
            
            # Offer to show available sites with units
            print("\nWould you like to see other sites with available units?")
            show_alternatives = input("Show available sites? (y/n): ").strip().lower()
            
            if show_alternatives == 'y':
                print("\n🔍 Checking available units across all sites...")
                available_sites = []
                
                # Check all sites for available units
                sites_to_check = ["wallsend", "boldon", "birtley", "sunderland"]
                for check_site in sites_to_check:
                    try:
                        # Get available units for containers at this site
                        available_units = get_available_units(get_facility_code(check_site, "container"))
                        if available_units:
                            # Get pricing for this site
                            pricing_success = get_pricing_from_api(check_site, "container")
                            if pricing_success and check_site in SITE_PRICING and "container" in SITE_PRICING[check_site]:
                                available_sites.append({
                                    'site': check_site.title(),
                                    'units': available_units,
                                    'pricing': SITE_PRICING[check_site]["container"]
                                })
                    except Exception as e:
                        continue
                
                if available_sites:
                    print(f"\n✅ Found {len(available_sites)} site(s) with available container units:")
                    print("=" * 50)
                    
                    # Step 1: Show just sites and available sizes (no pricing yet)
                    print("\n📍 Available Container Sites and Sizes:")
                    for i, site_info in enumerate(available_sites, 1):
                        print(f"\n{i}. {site_info['site']} - Container Storage")
                        print("   Available sizes:")
                        
                        # Extract available sizes from the units list
                        available_sizes_set = set()
                        for unit in site_info['units']:
                            unit_area = unit.get('unit_area', 0)
                            unit_type = unit.get('unit_type_code', '').lower()
                            
                            # Map unit areas to standard sizes for containers
                            if unit_area == 40 or ('small' in unit_type or '4x10' in unit_type):
                                available_sizes_set.add(40)
                            elif unit_area == 80 or ('med' in unit_type or '10x8' in unit_type):
                                available_sizes_set.add(80)
                            elif unit_area == 160 or ('large' in unit_type or 'lge' in unit_type or '20x8' in unit_type):
                                available_sizes_set.add(160)
                            elif unit_area == 320 or ('xl' in unit_type or '40x8' in unit_type):
                                available_sizes_set.add(320)
                        
                        # Show just the sizes (no pricing yet)
                        for size in sorted(available_sizes_set):
                            if size == 40:
                                print(f"      • Small (4ft x 10ft - 40sqft)")
                            elif size == 80:
                                print(f"      • Medium (10ft x 8ft - 80sqft)")
                            elif size == 160:
                                print(f"      • Large (20ft x 8ft - 160sqft)")
                            elif size == 320:
                                print(f"      • Extra Large (40ft x 8ft - 320sqft)")
                    
                    print("\n" + "=" * 50)
                    
                    # Step 2: Let user pick a site and size
                    print("Please select a site and size:")
                    try:
                        site_choice = int(input("Enter site number: ").strip())
                        if 1 <= site_choice <= len(available_sites):
                            selected_site_info = available_sites[site_choice - 1]
                            selected_site = selected_site_info['site'].lower()
                            
                            # Get available sizes for the selected site
                            available_sizes_set = set()
                            for unit in selected_site_info['units']:
                                unit_area = unit.get('unit_area', 0)
                                unit_type = unit.get('unit_type_code', '').lower()
                                
                                if unit_area == 40 or ('small' in unit_type or '4x10' in unit_type):
                                    available_sizes_set.add(40)
                                elif unit_area == 80 or ('med' in unit_type or '10x8' in unit_type):
                                    available_sizes_set.add(80)
                                elif unit_area == 160 or ('large' in unit_type or 'lge' in unit_type or '20x8' in unit_type):
                                    available_sizes_set.add(160)
                                elif unit_area == 320 or ('xl' in unit_type or '40x8' in unit_type):
                                    available_sizes_set.add(320)
                            
                            available_sizes_list = sorted(list(available_sizes_set))
                            
                            print(f"\n📍 {selected_site.title()} - Available Sizes:")
                            for i, size in enumerate(available_sizes_list, 1):
                                if size == 40:
                                    print(f"{i}. Small (4ft x 10ft - 40sqft)")
                                elif size == 80:
                                    print(f"{i}. Medium (10ft x 8ft - 80sqft)")
                                elif size == 160:
                                    print(f"{i}. Large (20ft x 8ft - 160sqft)")
                                elif size == 320:
                                    print(f"{i}. Extra Large (40ft x 8ft - 320sqft)")
                            
                            try:
                                size_choice = int(input("Enter size number: ").strip())
                                if 1 <= size_choice <= len(available_sizes_list):
                                    selected_size = available_sizes_list[size_choice - 1]
                                    site = selected_site
                                    storage_type = "container"  # Update storage type to container
                                    print(f"✅ Selected {selected_site.title()} - {selected_size} sqft")
                                    
                                    # Step 3: Show USPs for the selected site
                                    print("\n" + "=" * 50)
                                    display_site_info(site, "container")
                                    
                                    # Add gap between USP and price
                                    print("\n" + "=" * 50)
                                    
                                    # Display actual dimensions based on selected size
                                    if selected_size == 40:
                                        dimensions = "4x8x8"
                                        size_name = "Small"
                                    elif selected_size == 80:
                                        dimensions = "10x8x8"
                                        size_name = "Medium"
                                    elif selected_size == 160:
                                        dimensions = "20x8x8"
                                        size_name = "Large"
                                    elif selected_size == 320:
                                        dimensions = "40x8x8"
                                        size_name = "Extra Large"
                                    
                                    print(f"\n📏 Your selected {size_name} unit dimensions: {dimensions} feet")
                                    print("(Internal dimensions may vary by approximately 8 inches)")
                                    
                                    # Ask if vehicle fits
                                    vehicle_fit = input("\nWould your vehicle fit? (y/n): ").strip().lower()
                                    
                                    if vehicle_fit == 'y':
                                        print(f"\n✅ Perfect! Let's show you the pricing for your {size_name} unit.")
                                        
                                        # Step 4: Show pricing for the selected size
                                        print(f"\n💰 Pricing for {size_name} unit ({dimensions}):")
                                        if selected_size in selected_site_info['pricing']:
                                            pricing = selected_site_info['pricing'][selected_size]
                                            if site == "wallsend" and selected_size in [40, 80, 160]:
                                                print(f"   💰 £18 per week inc VAT with 2nd month free promotion")
                                                print(f"   💰 £{pricing['monthly']} per month")
                                                print(f"   🎉 SPECIAL: 2nd month free promotion - equates to £18 per week!")
                                            else:
                                                print(f"   💰 £{pricing['weekly']} per week inc VAT")
                                                print(f"   💰 £{pricing['monthly']} per month")
                                        
                                        # Display contract info
                                        display_contract_info(storage_type)
                                        
                                        # Show booking link
                                        print(f"\n🔗 Book now: https://portaluk.storman.com/facility/OBRIC/unit-selection?env=uk")
                                        
                                        # Final summary
                                        print("\n" + "=" * 50)
                                        print("📋 SUMMARY:")
                                        print(f"   Site: {site.title()}")
                                        print(f"   Type: Container Storage")
                                        print(f"   Size: {size_name} ({dimensions})")
                                        print("   Vehicle storage: ✅ Allowed")
                                        print("=" * 50)
                                        print("\n👋 Thanks for using O'Brien's Storage Finder!")
                                        return
                                    else:
                                        print("\n❌ No problem! Let's try a different size or site.")
                                        print("Would you like to:")
                                        print("1. Try a larger unit")
                                        print("2. Try a different site")
                                        print("3. Start over")
                                        
                                        retry_choice = input("Enter your choice (1-3): ").strip()
                                        if retry_choice == "1":
                                            continue  # This will restart the size selection
                                        elif retry_choice == "2":
                                            break  # This will restart the site selection
                                        else:
                                            continue  # This will restart the main loop
                                else:
                                    print("❌ Invalid size choice. Continuing with original flow.")
                            except ValueError:
                                print("❌ Invalid size input. Continuing with original flow.")
                        else:
                            print("❌ Invalid site choice. Continuing with original flow.")
                    except ValueError:
                        print("❌ Invalid site input. Continuing with original flow.")
                else:
                    print("\n❌ No other sites currently have available units.")
                    print("We'll contact you as soon as units become available at Sunderland.")
                    continue
            continue
        
        # Check if units are available (but don't show pricing yet)
        available_sizes = get_available_sizes(site, storage_type)
        if not available_sizes:
            print("⚠️  Currently no units available at this site.")
            print("Please contact us directly for availability updates.")
            continue_choice = input("\nWould you like to check another site? (y/n): ").strip().lower()
            if continue_choice != 'y':
                print("\n👋 Thanks for using O'Brien's Storage Finder!")
                print("Have a great day!")
                break
            continue
        
        # Show site information (features, not pricing)
        display_site_info(site, storage_type)
        
        # Ask if they know what they need or want recommendation
        customer_choice = get_customer_choice(storage_type)
        
        if customer_choice == '1':
            # They know what size they need
            size = get_known_size(site, storage_type)
            if size is None:  # No units available
                continue_choice = input("\nWould you like to check another site? (y/n): ").strip().lower()
                if continue_choice != 'y':
                    print("\n👋 Thanks for using O'Brien's Storage Finder!")
                    print("Have a great day!")
                    break
                continue
            items = []
            unrecognized_items = []
            prohibited_items = []
        else:
            # They need recommendation based on items
            items = get_items_for_storage()
            if not items:
                print("\n❌ No items entered. Please try again.")
                continue
            
            # Calculate size
            size, unrecognized_items = calculate_size_from_items(items)
            
            # Check for prohibited items (only for internal storage)
            if storage_type == "internal":
                prohibited_items = check_prohibited_items(items, storage_type)
            else:
                prohibited_items = []
        
        # Handle prohibited items in internal storage by offering container alternatives
        if storage_type == "internal" and prohibited_items:
            print(f"\n🚫 WARNING: Some items may be prohibited in internal storage:")
            for item in prohibited_items:
                print(f"   • {item}")
            print("\n💡 SOLUTION: Container storage allows these items!")
            print("Would you like to see available container options?")
            
            container_choice = input("Show container alternatives? (y/n): ").strip().lower()
            if container_choice == 'y':
                print("\n🔍 Checking available container units across all sites...")
                available_container_sites = []
                
                # Check all sites for available container units
                sites_to_check = ["wallsend", "boldon", "birtley", "sunderland", "chester-le-street"]
                for check_site in sites_to_check:
                    try:
                        # Get available units for containers at this site
                        available_units = get_available_units(get_facility_code(check_site, "container"))
                        
                        # Filter units by site-specific prefixes
                        site_specific_units = []
                        if check_site in SITE_PREFIXES:
                            for unit in available_units:
                                unit_number = unit.get('unit_number', '')
                                for prefix in SITE_PREFIXES[check_site]:
                                    if unit_number.startswith(prefix):
                                        site_specific_units.append(unit)
                                        break
                        
                        if site_specific_units:
                            # Get pricing for this site
                            pricing_success = get_pricing_from_api(check_site, "container")
                            if pricing_success and check_site in SITE_PRICING and "container" in SITE_PRICING[check_site]:
                                available_container_sites.append({
                                    'site': check_site.title(),
                                    'units': site_specific_units,
                                    'pricing': SITE_PRICING[check_site]["container"]
                                })
                    except Exception as e:
                        print(f"   Error processing {check_site}: {e}")
                        continue
                
                if available_container_sites:
                    print(f"\n✅ Found {len(available_container_sites)} site(s) with available container units:")
                    print("=" * 50)
                    
                    # Show sites and available sizes
                    print("\n📍 Available Container Sites and Sizes:")
                    for i, site_info in enumerate(available_container_sites, 1):
                        print(f"\n{i}. {site_info['site']} - Container Storage")
                        print("   Available sizes:")
                        
                        # Extract available sizes from the units list
                        available_sizes_set = set()
                        for unit in site_info['units']:
                            unit_area = unit.get('unit_area', 0)
                            unit_type = unit.get('unit_type_code', '').lower()
                            
                            # Map unit areas to standard sizes for containers
                            if unit_area == 40 or ('small' in unit_type or '4x10' in unit_type):
                                available_sizes_set.add(40)
                            elif unit_area == 80 or ('med' in unit_type or '10x8' in unit_type):
                                available_sizes_set.add(80)
                            elif unit_area == 160 or ('large' in unit_type or 'lge' in unit_type or '20x8' in unit_type):
                                available_sizes_set.add(160)
                            elif unit_area == 320 or ('xl' in unit_type or '40x8' in unit_type):
                                available_sizes_set.add(320)
                        
                        # Show sizes with pricing
                        for size in sorted(available_sizes_set):
                            if size in site_info['pricing']:
                                pricing = site_info['pricing'][size]
                                if size == 40:
                                    if site_info['site'].lower() == "wallsend":
                                        print(f"      • Small (4ft x 10ft - 40sqft) - £18/week with 2nd month free promotion")
                                    else:
                                        print(f"      • Small (4ft x 10ft - 40sqft) - £{pricing['weekly']}/week (£{pricing['monthly']}/month)")
                                elif size == 80:
                                    if site_info['site'].lower() == "wallsend":
                                        print(f"      • Medium (10ft x 8ft - 80sqft) - £18/week with 2nd month free promotion")
                                    else:
                                        print(f"      • Medium (10ft x 8ft - 80sqft) - £{pricing['weekly']}/week (£{pricing['monthly']}/month)")
                                elif size == 160:
                                    if site_info['site'].lower() == "wallsend":
                                        print(f"      • Large (20ft x 8ft - 160sqft) - £18/week with 2nd month free promotion")
                                    else:
                                        print(f"      • Large (20ft x 8ft - 160sqft) - £{pricing['weekly']}/week (£{pricing['monthly']}/month)")
                                elif size == 320:
                                    print(f"      • Extra Large (40ft x 8ft - 320sqft) - £{pricing['weekly']}/week (£{pricing['monthly']}/month)")
                    
                    print("\n" + "=" * 50)
                    
                    # Let user pick a site and size
                    print("Please select a site and size:")
                    try:
                        site_choice = int(input("Enter site number: ").strip())
                        if 1 <= site_choice <= len(available_container_sites):
                            selected_site_info = available_container_sites[site_choice - 1]
                            selected_site = selected_site_info['site'].lower()
                            
                            # Get available sizes for the selected site
                            available_sizes_set = set()
                            for unit in selected_site_info['units']:
                                unit_area = unit.get('unit_area', 0)
                                unit_type = unit.get('unit_type_code', '').lower()
                                
                                if unit_area == 40 or ('small' in unit_type or '4x10' in unit_type):
                                    available_sizes_set.add(40)
                                elif unit_area == 80 or ('med' in unit_type or '10x8' in unit_type):
                                    available_sizes_set.add(80)
                                elif unit_area == 160 or ('large' in unit_type or 'lge' in unit_type or '20x8' in unit_type):
                                    available_sizes_set.add(160)
                                elif unit_area == 320 or ('xl' in unit_type or '40x8' in unit_type):
                                    available_sizes_set.add(320)
                            
                            available_sizes_list = sorted(list(available_sizes_set))
                            
                            print(f"\n📍 {selected_site.title()} - Available Sizes:")
                            for i, size in enumerate(available_sizes_list, 1):
                                if size == 40:
                                    print(f"{i}. Small (4ft x 10ft - 40sqft)")
                                elif size == 80:
                                    print(f"{i}. Medium (10ft x 8ft - 80sqft)")
                                elif size == 160:
                                    print(f"{i}. Large (20ft x 8ft - 160sqft)")
                                elif size == 320:
                                    print(f"{i}. Extra Large (40ft x 8ft - 320sqft)")
                            
                            try:
                                size_choice = int(input("Enter size number: ").strip())
                                if 1 <= size_choice <= len(available_sizes_list):
                                    selected_size = available_sizes_list[size_choice - 1]
                                    site = selected_site
                                    storage_type = "container"  # Switch to container storage
                                    print(f"✅ Selected {selected_site.title()} - {selected_size} sqft container")
                                    
                                    # Show container USPs
                                    print("\n" + "=" * 50)
                                    display_site_info(site, "container")
                                    
                                    # Show pricing for the selected size
                                    print(f"\n💰 Pricing for {selected_size} sqft container:")
                                    if selected_size in selected_site_info['pricing']:
                                        pricing = selected_site_info['pricing'][selected_size]
                                        if site == "wallsend" and selected_size in [40, 80, 160]:
                                            print(f"   💰 £18 per week inc VAT with 2nd month free promotion")
                                            print(f"   💰 £{pricing['monthly']} per month")
                                            print(f"   🎉 SPECIAL: 2nd month free promotion - equates to £18 per week!")
                                        else:
                                            print(f"   💰 £{pricing['weekly']} per week inc VAT")
                                            print(f"   💰 £{pricing['monthly']} per month")
                                    
                                    # Display results with booking options
                                    display_results(site, storage_type, selected_size, [], [], [], customer_name)
                                    
                                    # Continue with the rest of the flow
                                    print("\n" + "=" * 50)
                                    print("Would you like to proceed with this selection?")
                                    proceed_choice = input("Continue? (y/n): ").strip().lower()
                                    
                                    if proceed_choice != 'y':
                                        print("❌ Returning to main menu.")
                                        continue
                                    
                                    # Set the size and skip item collection since we already have a selection
                                    size = selected_size
                                    items = []
                                    unrecognized_items = []
                                    prohibited_items = []  # Reset since we're now using containers
                                    prohibited_items_handled = True  # Mark that we've handled prohibited items
                                    
                                    # Skip to display results and bypass waiting list logic
                                    display_results(site, storage_type, size, items, unrecognized_items, prohibited_items, customer_name)
                                    display_contract_info(storage_type)
                                    
                                    # Ask if they want to re-choose site/size or continue
                                    print(f"\n{'='*60}")
                                    print("What would you like to do next?")
                                    print("1. 🔄 Re-choose site and size")
                                    print("2. ✅ Proceed with current selection")
                                    print("3. 🏠 Start over")
                                    print("4. 👋 Exit")
                                    
                                    next_choice = input("\nEnter your choice (1-4): ").strip()
                                    
                                    if next_choice == '1':
                                        print("\n🔄 Let's help you choose a different site or size.")
                                        print("Would you like to:")
                                        print("1. 📍 Choose a different site")
                                        print("2. 📏 Choose a different size")
                                        print("3. 🔙 Go back to current selection")
                                        
                                        reselect_choice = input("Enter your choice (1-3): ").strip()
                                        
                                        if reselect_choice == '1':
                                            print("\n📍 Let's choose a different site...")
                                            continue  # This will restart the site selection
                                        elif reselect_choice == '2':
                                            print("\n📏 Let's choose a different size...")
                                            # Get available sizes for current site
                                            available_sizes = get_available_sizes(site, storage_type)
                                            if available_sizes:
                                                print(f"\nAvailable sizes at {site.title()}:")
                                                for i, available_size in enumerate(available_sizes, 1):
                                                    if storage_type == "container":
                                                        if available_size == 40:
                                                            print(f"{i}. Small (4ft x 10ft - 40sqft)")
                                                        elif available_size == 80:
                                                            print(f"{i}. Medium (10ft x 8ft - 80sqft)")
                                                        elif available_size == 160:
                                                            print(f"{i}. Large (20ft x 8ft - 160sqft)")
                                                        elif available_size == 320:
                                                            print(f"{i}. Extra Large (40ft x 8ft - 320sqft)")
                                                    else:
                                                        print(f"{i}. {available_size} sqft room")
                                                
                                                try:
                                                    new_size_choice = int(input("\nEnter size number: ").strip())
                                                    if 1 <= new_size_choice <= len(available_sizes):
                                                        size = available_sizes[new_size_choice - 1]
                                                        print(f"✅ Updated size to {size} sqft")
                                                        continue  # This will restart the results display
                                                    else:
                                                        print("❌ Invalid size choice. Keeping current selection.")
                                                except ValueError:
                                                    print("❌ Invalid input. Keeping current selection.")
                                            else:
                                                print("❌ No sizes available at this site.")
                                        elif reselect_choice == '3':
                                            print("✅ Keeping current selection.")
                                        else:
                                            print("❌ Invalid choice. Keeping current selection.")
                                    elif next_choice == '2':
                                        print("✅ Proceeding with current selection.")
                                    elif next_choice == '3':
                                        print("🔄 Starting over...")
                                        continue  # This will restart the main loop
                                    elif next_choice == '4':
                                        print("\n👋 Thanks for using O'Brien's Storage Finder!")
                                        print("Have a great day!")
                                        break
                                    else:
                                        print("❌ Invalid choice. Please try again.")
                                        continue
                                    
                                    # Ask if they want to continue with another option
                                    continue_choice = input("\nWould you like to check another option? (y/n): ").strip().lower()
                                    if continue_choice != 'y':
                                        print("\n👋 Thanks for using O'Brien's Storage Finder!")
                                        print("Have a great day!")
                                        break
                                    continue
                                else:
                                    print("❌ Invalid size choice. Continuing with original flow.")
                            except ValueError:
                                print("❌ Invalid size input. Continuing with original flow.")
                        else:
                            print("❌ Invalid site choice. Continuing with original flow.")
                    except ValueError:
                        print("❌ Invalid site input. Continuing with original flow.")
                else:
                    print("\n❌ No container units currently available at any site.")
                    print("Please contact us for assistance.")
                    continue
            else:
                print("❌ Prohibited items cannot be stored in internal storage.")
                print("Please contact us for assistance.")
                continue
        
        # Display results with pricing
        display_results(site, storage_type, size, items, unrecognized_items, prohibited_items, customer_name)
        
        # Show contract info
        display_contract_info(storage_type)
        
        # Ask if they want to re-choose site/size or continue
        print(f"\n{'='*60}")
        print("What would you like to do next?")
        print("1. 🔄 Re-choose site and size")
        print("2. ✅ Proceed with current selection")
        print("3. 🏠 Start over")
        print("4. 👋 Exit")
        
        next_choice = input("\nEnter your choice (1-4): ").strip()
        
        if next_choice == '1':
            print("\n🔄 Let's help you choose a different site or size.")
            print("Would you like to:")
            print("1. 📍 Choose a different site")
            print("2. 📏 Choose a different size")
            print("3. 🔙 Go back to current selection")
            
            reselect_choice = input("Enter your choice (1-3): ").strip()
            
            if reselect_choice == '1':
                print("\n📍 Let's choose a different site...")
                continue  # This will restart the site selection
            elif reselect_choice == '2':
                print("\n📏 Let's choose a different size...")
                # Get available sizes for current site
                available_sizes = get_available_sizes(site, storage_type)
                if available_sizes:
                    print(f"\nAvailable sizes at {site.title()}:")
                    for i, available_size in enumerate(available_sizes, 1):
                        if storage_type == "container":
                            if available_size == 40:
                                print(f"{i}. Small (4ft x 10ft - 40sqft)")
                            elif available_size == 80:
                                print(f"{i}. Medium (10ft x 8ft - 80sqft)")
                            elif available_size == 160:
                                print(f"{i}. Large (20ft x 8ft - 160sqft)")
                            elif available_size == 320:
                                print(f"{i}. Extra Large (40ft x 8ft - 320sqft)")
                        else:
                            print(f"{i}. {available_size} sqft room")
                    
                    try:
                        new_size_choice = int(input("\nEnter size number: ").strip())
                        if 1 <= new_size_choice <= len(available_sizes):
                            size = available_sizes[new_size_choice - 1]
                            print(f"✅ Updated size to {size} sqft")
                            continue  # This will restart the results display
                        else:
                            print("❌ Invalid size choice. Keeping current selection.")
                    except ValueError:
                        print("❌ Invalid input. Keeping current selection.")
                else:
                    print("❌ No sizes available at this site.")
            elif reselect_choice == '3':
                print("✅ Keeping current selection.")
            else:
                print("❌ Invalid choice. Keeping current selection.")
        elif next_choice == '2':
            print("✅ Proceeding with current selection.")
        elif next_choice == '3':
            print("🔄 Starting over...")
            continue  # This will restart the main loop
        elif next_choice == '4':
            print("\n👋 Thanks for using O'Brien's Storage Finder!")
            print("Have a great day!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
            continue
        
        # Ask if they want to continue with another option
        continue_choice = input("\nWould you like to check another option? (y/n): ").strip().lower()
        if continue_choice != 'y':
            print("\n👋 Thanks for using O'Brien's Storage Finder!")
            print("Have a great day!")
            break

if __name__ == '__main__':
    main() 
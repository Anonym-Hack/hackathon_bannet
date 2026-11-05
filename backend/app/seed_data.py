import json
import logging
from sqlalchemy.orm import Session

from app.models import User, MaterialListing, BuyerRequest, Inquiry, Message
from app.auth import hash_password
from app.ai_service import rule_based_analyze

logger = logging.getLogger(__name__)

DEMO_LISTINGS = [
    {
        "title": "Industrial Aluminum 6061 CNC Off-Cuts & Shavings",
        "category": "metal",
        "description": "Clean, unmixed aerospace-grade 6061-T6 aluminum billet cut-offs and dry CNC milling turnings. Segregated from cutting fluid and stored in sealed steel bins.",
        "quantity": 12500,
        "unit": "kg",
        "price_type": "fixed",
        "price": 1.85,
        "location": "Chicago, IL",
        "is_hazardous": False,
    },
    {
        "title": "Post-Industrial HDPE Blow Molding Regrind (Natural)",
        "category": "plastic",
        "description": "High-density polyethylene flake regrind derived from clean detergent container production rejects. 0.35 melt index, washed, metal-detected, and packaged in 1,000 kg gaylords.",
        "quantity": 8000,
        "unit": "kg",
        "price_type": "fixed",
        "price": 0.95,
        "location": "Detroit, MI",
        "is_hazardous": False,
    },
    {
        "title": "Recovered Technical Grade Ethanol (92% Purity)",
        "category": "chemical",
        "description": "Distillation-recovered ethanol solvent from botanical extraction facility. Clear liquid suitable for industrial sanitizers, solvent thinning, or parts degreasing. Packed in 200L UN steel drums.",
        "quantity": 4500,
        "unit": "litres",
        "price_type": "fixed",
        "price": 0.80,
        "location": "Indianapolis, IN",
        "is_hazardous": True,
    },
    {
        "title": "Selvedge Raw Denim & Cotton Cutting Scraps",
        "category": "textile",
        "description": "Clean 100% cotton denim apparel manufacturing off-cuts. 12oz to 14oz indigo dyed, unwashed, free from elastane and synthetics. Compressed in 450 kg wire-tied bales.",
        "quantity": 6200,
        "unit": "kg",
        "price_type": "fixed",
        "price": 0.40,
        "location": "Atlanta, GA",
        "is_hazardous": False,
    },
    {
        "title": "Kiln-Dried Pine & Hardwood Sawdust Pelleting Feedstock",
        "category": "wood",
        "description": "Ultra-clean kiln-dried sawdust and planer shavings from high-end architectural millwork. Moisture content < 9%, nail-free, zero adhesives or varnish.",
        "quantity": 25000,
        "unit": "kg",
        "price_type": "free",
        "price": 0.0,
        "location": "Grand Rapids, MI",
        "is_hazardous": False,
    },
    {
        "title": "Crushed Borosilicate Laboratory Glass Cullet",
        "category": "glass",
        "description": "High thermal shock borosilicate glass cullet from glassware plant rejected blanks. Washed and crushed to 10-25mm particle size. High silica content (81%).",
        "quantity": 9000,
        "unit": "kg",
        "price_type": "fixed",
        "price": 0.25,
        "location": "Toledo, OH",
        "is_hazardous": False,
    },
    {
        "title": "Spent Brewer's Grain High-Protein Wet Mash",
        "category": "organic",
        "description": "Fresh spent barley grain mash from craft brewing facility. 28% crude protein on dry basis. High fiber, ideal for cattle feed or bio-methane anaerobic digestion.",
        "quantity": 18000,
        "unit": "kg",
        "price_type": "free",
        "price": 0.0,
        "location": "Milwaukee, WI",
        "is_hazardous": False,
    },
    {
        "title": "Crushed High-Strength Concrete Aggregate (Class 5)",
        "category": "construction",
        "description": "Sieved recycled concrete aggregate (1.5 inch minus) derived from highway barrier and footing demolition. Magnetic rebar separation completed, meets DOT spec.",
        "quantity": 45000,
        "unit": "kg",
        "price_type": "fixed",
        "price": 0.08,
        "location": "Columbus, OH",
        "is_hazardous": False,
    },
    {
        "title": "De-soldered FR-4 Printed Circuit Board (PCB) Scrap",
        "category": "electronic",
        "description": "Populated and trimmed FR-4 motherboard edge scrap and de-soldered panels. Rich in copper tracks with trace gold/silver contacts for certified hydrometallurgical refining.",
        "quantity": 3200,
        "unit": "kg",
        "price_type": "fixed",
        "price": 3.40,
        "location": "Austin, TX",
        "is_hazardous": False,
    },
    {
        "title": "Spent Sulfuric Acid Pickling Liquor (15% H2SO4)",
        "category": "chemical",
        "description": "Concentrated acidic pickling liquor from steel wire drawing line. Contains dissolved ferrous sulfate (FeSO4). Valuable for coagulant synthesis in wastewater treatment.",
        "quantity": 12000,
        "unit": "litres",
        "price_type": "free",
        "price": 0.0,
        "location": "Pittsburgh, PA",
        "is_hazardous": True,
    },
    {
        "title": "Baled Polypropylene (PP) Woven Sacks & Strapping",
        "category": "plastic",
        "description": "Clean white and unprinted PP woven bulk bag scraps (FIBC bags) and baled strapping bands. Dry, UV-treated, ready for agglomeration and extrusion pelletizing.",
        "quantity": 7500,
        "unit": "kg",
        "price_type": "fixed",
        "price": 0.55,
        "location": "Dallas, TX",
        "is_hazardous": False,
    },
    {
        "title": "Structural Grade 50 Steel I-Beam Cut-Offs",
        "category": "metal",
        "description": "Heavy structural steel W-beam end cut pieces from skyscraper fabrication yard. Lengths between 1.2m and 3.5m. Mill test certs available upon request.",
        "quantity": 19000,
        "unit": "kg",
        "price_type": "fixed",
        "price": 0.70,
        "location": "Cleveland, OH",
        "is_hazardous": False,
    },
    {
        "title": "Recycled Gypsum Wallboard Core Powder",
        "category": "construction",
        "description": "Mechanical pulverized gypsum (calcium sulfate dihydrate) recovered from drywall trim scrap. Paper backing separated via air classification. Purity > 93%.",
        "quantity": 14000,
        "unit": "kg",
        "price_type": "fixed",
        "price": 0.12,
        "location": "St. Louis, MO",
        "is_hazardous": False,
    },
    {
        "title": "Sorted Amber Beer & Beverage Glass Cullet",
        "category": "glass",
        "description": "Clean furnace-ready amber glass cullet. Crushed to 15mm nominal size, CSP (ceramic, stone, porcelain) contamination < 15 ppm. High color consistency.",
        "quantity": 22000,
        "unit": "kg",
        "price_type": "fixed",
        "price": 0.18,
        "location": "St. Paul, MN",
        "is_hazardous": False,
    },
    {
        "title": "Coffee Roasting Chaff & Organic Bean Husks",
        "category": "organic",
        "description": "Dry parchment and silverskin chaff collected from industrial cyclone roasters. High potassium content, excellent carbon-to-nitrogen ratio for compost and mycelium cultivation.",
        "quantity": 4800,
        "unit": "kg",
        "price_type": "free",
        "price": 0.0,
        "location": "Seattle, WA",
        "is_hazardous": False,
    },
    {
        "title": "Industrial Wool & Felt Underlay Trim Rolls",
        "category": "textile",
        "description": "Non-woven needle-punched wool/synthetic blended felt off-cuts. High acoustic NRC rating (0.85). Suitable for vehicle dash insulators, architectural acoustic panels.",
        "quantity": 3800,
        "unit": "kg",
        "price_type": "fixed",
        "price": 0.65,
        "location": "Charlotte, NC",
        "is_hazardous": False,
    },
    {
        "title": "Standard Solid Oak & Hardwood Heat-Treated Pallets",
        "category": "wood",
        "description": "48x40 inch GMA grade A wooden pallets. Heat treated (ISPM 15 certified), undamaged deck boards, minimum 1,500 kg static capacity. Stored indoors.",
        "quantity": 650,
        "unit": "units",
        "price_type": "fixed",
        "price": 4.50,
        "location": "Louisville, KY",
        "is_hazardous": False,
    },
    {
        "title": "Clean Copper Scrap Wiring (#1 Bright Wire)",
        "category": "metal",
        "description": "Stripped bare copper electrical wire clippings, unalloyed and un-tinned. Gauge 10 to 4 AWG. 99.9% electrical conductivity standard.",
        "quantity": 2400,
        "unit": "kg",
        "price_type": "fixed",
        "price": 8.20,
        "location": "Phoenix, AZ",
        "is_hazardous": False,
    },
    {
        "title": "Purified Crude Glycerin (80% Biofuel Co-product)",
        "category": "chemical",
        "description": "Technical grade glycerol liquid from biodiesel transesterification. High calorific value (3,800 kcal/kg). Suitable for biogas digester accelerator or dust suppressant.",
        "quantity": 16000,
        "unit": "kg",
        "price_type": "fixed",
        "price": 0.32,
        "location": "Des Moines, IA",
        "is_hazardous": True,
    },
    {
        "title": "Automotive Tier-1 Polycarbonate / ABS Alloy Scrap",
        "category": "plastic",
        "description": "Pre-consumer unpainted PC/ABS blended scrap from automotive instrument cluster sprues. Impact modified, high heat resistance, packed in octabins.",
        "quantity": 5600,
        "unit": "kg",
        "price_type": "fixed",
        "price": 1.40,
        "location": "Detroit, MI",
        "is_hazardous": False,
    },
    {
        "title": "Industrial Foundry Silica Sand Byproduct",
        "category": "other",
        "description": "Thermal-reclaimed green sand casting mold silica sand. Sub-angular grain fineness AFS 55-60. Pre-screened for asphalt binder or clinker manufacturing.",
        "quantity": 35000,
        "unit": "kg",
        "price_type": "free",
        "price": 0.0,
        "location": "Birmingham, AL",
        "is_hazardous": False,
    }
]

DEMO_REQUESTS = [
    {
        "material_name": "HDPE Regrind or Clean Flakes for Pipe Extrusion",
        "category": "plastic",
        "quantity_needed": 10000,
        "unit": "kg",
        "location": "Detroit, MI",
        "use_case": "Manufacturing corrugated drainage pipe and stormwater culverts. Require melt flow index between 0.2 and 0.8.",
    },
    {
        "material_name": "Aerospace or Structural Aluminum 6000/7000 Series Off-Cuts",
        "category": "metal",
        "quantity_needed": 15000,
        "unit": "kg",
        "location": "Chicago, IL",
        "use_case": "Feedstock for induction furnace remelting into architectural extrusion billets.",
    },
    {
        "material_name": "Clean Post-Industrial Cotton Scraps for Acoustic Insulation",
        "category": "textile",
        "quantity_needed": 5000,
        "unit": "kg",
        "location": "Atlanta, GA",
        "use_case": "Need natural fibers for shredding and blending into building soundproofing insulation batts.",
    },
    {
        "material_name": "Dry Hardwood Sawdust or Planer Shavings",
        "category": "wood",
        "quantity_needed": 20000,
        "unit": "kg",
        "location": "Grand Rapids, MI",
        "use_case": "Continuous feedstock for automated biomass wood fuel pellet extrusion line.",
    },
    {
        "material_name": "Technical Grade Ethanol or Isopropanol for Parts Degreasing",
        "category": "chemical",
        "quantity_needed": 3000,
        "unit": "litres",
        "location": "Indianapolis, IN",
        "use_case": "Washing and degreasing stamped metal components in closed-loop ultrasonic wash tanks.",
    },
    {
        "material_name": "Crushed Concrete Base Aggregate for Highway Expansion",
        "category": "construction",
        "quantity_needed": 40000,
        "unit": "kg",
        "location": "Columbus, OH",
        "use_case": "Sub-base stabilization and heavy equipment access road construction.",
    },
    {
        "material_name": "Copper Wire Clippings (#1 or #2 Bare Wire)",
        "category": "metal",
        "quantity_needed": 3000,
        "unit": "kg",
        "location": "Phoenix, AZ",
        "use_case": "Electrolytic refining and casting into electrical busbars and grounding rods.",
    },
    {
        "material_name": "Spent Organic Grain or Food Processing Mash for Biogas",
        "category": "organic",
        "quantity_needed": 15000,
        "unit": "kg",
        "location": "Milwaukee, WI",
        "use_case": "Anaerobic co-digestion feedstock to boost biomethane yields in regional utility facility.",
    }
]

def seed_database_if_empty(db: Session):
    """Checks if database has seed data; populates 2 demo accounts, 21 listings, and 8 requests if empty."""
    listing_count = db.query(MaterialListing).count()
    if listing_count > 0:
        logger.info("Database already seeded with listings. Skipping initial seed.")
        return

    logger.info("Seeding database with demo accounts, listings, and requests...")

    # 1. Ensure Demo Users exist
    supplier = db.query(User).filter(User.email == "supplier@demo.com").first()
    if not supplier:
        supplier = User(
            email="supplier@demo.com",
            hashed_password=hash_password("password123"),
            company_name="Apex EcoMaterials Corp",
            role="Supplier",
            city="Chicago, IL"
        )
        db.add(supplier)

    buyer = db.query(User).filter(User.email == "buyer@demo.com").first()
    if not buyer:
        buyer = User(
            email="buyer@demo.com",
            hashed_password=hash_password("password123"),
            company_name="GreenForge Manufacturing Ltd",
            role="Buyer",
            city="Detroit, MI"
        )
        db.add(buyer)
    db.commit()
    db.refresh(supplier)
    db.refresh(buyer)

    # 2. Seed 21 Material Listings
    created_listings = []
    for item in DEMO_LISTINGS:
        analysis = rule_based_analyze(item["title"], item["description"], item["category"])
        listing = MaterialListing(
            supplier_id=supplier.id,
            title=item["title"],
            description=item["description"],
            category=item["category"],
            quantity=item["quantity"],
            unit=item["unit"],
            price_type=item["price_type"],
            price=item["price"],
            location=item["location"],
            availability_status="available",
            image_url=None,
            ai_material_name=analysis.material_name,
            ai_composition=analysis.composition,
            ai_condition=analysis.condition,
            ai_reuse_applications_json=json.dumps(analysis.reuse_applications),
            ai_target_industries_json=json.dumps(analysis.target_industries),
            ai_handling_notes=analysis.handling_notes,
            ai_sustainability_score=analysis.sustainability_score,
            ai_confidence=analysis.confidence,
            ai_is_demo_mode=True,
            is_hazardous=item.get("is_hazardous", False) or analysis.is_hazardous
        )
        db.add(listing)
        created_listings.append(listing)
    
    db.commit()

    # 3. Seed 8 Buyer Requests
    for req in DEMO_REQUESTS:
        b_req = BuyerRequest(
            buyer_id=buyer.id,
            material_name=req["material_name"],
            category=req["category"],
            quantity_needed=req["quantity_needed"],
            unit=req["unit"],
            location=req["location"],
            use_case=req["use_case"],
            status="open"
        )
        db.add(b_req)
    db.commit()

    # 4. Create an initial sample inquiry and chat message thread between buyer and supplier
    if created_listings:
        sample_listing = created_listings[1]  # HDPE Blow Molding Regrind
        sample_inquiry = Inquiry(
            listing_id=sample_listing.id,
            buyer_id=buyer.id,
            supplier_id=supplier.id,
            subject=f"Inquiry regarding {sample_listing.title}",
            status="open"
        )
        db.add(sample_inquiry)
        db.commit()
        db.refresh(sample_inquiry)

        msg1 = Message(
            inquiry_id=sample_inquiry.id,
            sender_id=buyer.id,
            content="Hello Apex EcoMaterials, we produce corrugated drainage pipes in Detroit and are very interested in your 8,000 kg HDPE natural regrind lot. Can you confirm if melt flow index certificates are available?",
            is_read=True
        )
        msg2 = Message(
            inquiry_id=sample_inquiry.id,
            sender_id=supplier.id,
            content="Hi GreenForge, yes absolutely! The batch has a tested MFI of 0.35 g/10min. We have full COA lab reports ready. We can arrange freight pickup anytime this week.",
            is_read=False
        )
        db.add(msg1)
        db.add(msg2)
        db.commit()

    logger.info("Database seeding complete! 2 accounts, 21 listings, 8 requests, and 1 demo chat thread created.")

import json
import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.schemas import AIAnalysisResult

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "metal", "plastic", "chemical", "textile", "wood", 
    "glass", "organic", "construction", "electronic", "other"
}

HAZARDOUS_KEYWORDS = {
    "acid", "solvent", "chemical", "toxic", "corrosive", "flammable",
    "explosive", "hazardous", "mercury", "lead", "cyanide", "asbestos",
    "spent catalyst", "battery", "caustic", "reactive", "pesticide", "sludge"
}

RULE_DATABASE = {
    "metal": {
        "composition": "High-purity industrial scrap alloy/metal composition",
        "condition": "Sorted scrap grade, clean and ready for smelting or reprocessing",
        "reuse_applications": [
            "Secondary smelting and re-rolling into sheet metal",
            "Feedstock for structural casting and fabrication",
            "Component manufacturing in automotive and aerospace parts",
            "Architectural hardware and reinforcing mesh"
        ],
        "target_industries": [
            "Foundries & Metal Casting",
            "Automotive Manufacturing",
            "Construction & Structural Fabricators",
            "Machining & CNC Job Shops"
        ],
        "handling_notes": "Store in dry covered areas to prevent oxidation. Wear cut-resistant heavy-duty gloves.",
        "sustainability_score": 92,
    },
    "plastic": {
        "composition": "Thermoplastic polymer regrind / production off-cuts",
        "condition": "Post-industrial scrap, de-dusted and uniform pellet or shred size",
        "reuse_applications": [
            "Injection molding for industrial crates and pallets",
            "Compounding with virgin resin for pipe extrusion",
            "Production of automotive interior trim parts",
            "Rotomolding for outdoor containers and construction spacers"
        ],
        "target_industries": [
            "Plastics Compounding & Masterbatch",
            "Packaging & Container Producers",
            "Automotive Component Molders",
            "Consumer Goods Manufacturing"
        ],
        "handling_notes": "Keep free from moisture and oil contamination. Avoid prolonged UV exposure.",
        "sustainability_score": 85,
    },
    "chemical": {
        "composition": "Industrial grade byproduct or recovered solvent mixture",
        "condition": "Filtered liquid or crystalline byproduct in sealed UN-certified drums",
        "reuse_applications": [
            "Industrial degreasing and parts washing feedstock",
            "Secondary solvent extraction in dye/resin manufacturing",
            "pH neutralization agent in wastewater treatment",
            "Raw material synthesis for plasticizers and coatings"
        ],
        "target_industries": [
            "Chemical Processing & Synthesis",
            "Paints, Coatings & Inks",
            "Industrial Wastewater Treatment",
            "Specialty Adhesive Formulation"
        ],
        "handling_notes": "Handle in well-ventilated areas. SDS required. Use chemical-resistant nitriles, eye splash goggles, and grounding for flammables.",
        "sustainability_score": 74,
    },
    "textile": {
        "composition": "Post-industrial spun yarn and fabric off-cuts (natural/synthetic blend)",
        "condition": "Dry, baled textile cuttings sorted by color/composition",
        "reuse_applications": [
            "Acoustic and thermal insulation batts for automotive & building",
            "Heavy-duty cleaning rags and industrial wipes",
            "Fiber reclamation for non-woven geotextiles",
            "Filling material for furniture upholstery and punching bags"
        ],
        "target_industries": [
            "Automotive Acoustic Insulation",
            "Building & Construction Materials",
            "Non-woven & Geotextile Manufacturers",
            "Furniture & Bedding Upholstery"
        ],
        "handling_notes": "Keep in clean, dry covered warehouse away from ignition sources.",
        "sustainability_score": 88,
    },
    "wood": {
        "composition": "Untreated softwood and hardwood off-cuts, pallets, and shavings",
        "condition": "Clean, dry, free of nails, chemical treatments, and adhesives",
        "reuse_applications": [
            "Compressed biomass wood pellets for clean industrial heat",
            "Particleboard and medium-density fiberboard (MDF) manufacturing",
            "Agricultural animal bedding and mulching",
            "Remanufactured Euro-pallets and shipping crates"
        ],
        "target_industries": [
            "Biomass Energy & Heating",
            "Panel & Composite Board Manufacturing",
            "Agriculture & Landscaping Supplies",
            "Logistics & Packaging"
        ],
        "handling_notes": "Store elevated off damp ground. Ensure proper fire suppression in storage areas.",
        "sustainability_score": 90,
    },
    "glass": {
        "composition": "High-purity industrial cullet and flat glass trimmings",
        "condition": "Crushed cullet, color-sorted and de-contaminated",
        "reuse_applications": [
            "Container glass furnace batch feedstock",
            "Glass wool thermal and acoustic insulation",
            "Abrasive blasting media for metal finishing",
            "Reflective bead manufacturing for road markings"
        ],
        "target_industries": [
            "Glass Container & Bottle Producers",
            "Fiberglass & Insulation Manufacturers",
            "Surface Finishing & Sandblasting",
            "Civil Infrastructure & Road Safety"
        ],
        "handling_notes": "Sharp edges. Wear puncture-resistant gloves and protective eyewear during transfer.",
        "sustainability_score": 94,
    },
    "organic": {
        "composition": "Clean agri-food processing byproducts and spent grain/cellulose",
        "condition": "Homogeneous bulk organic cake, low moisture or moisture-stabilized",
        "reuse_applications": [
            "High-protein animal feed supplementation",
            "Anaerobic digestion for biomethane / renewable natural gas",
            "Industrial compost and organic soil conditioner",
            "Cellulose extraction for biodegradable packaging"
        ],
        "target_industries": [
            "Livestock & Animal Feed Formulators",
            "Bioenergy & Biogas Generation",
            "Commercial Composting & Agri-Chemicals",
            "Bio-plastics & Green Packaging"
        ],
        "handling_notes": "Store in temperature-controlled or aerated silos to prevent spontaneous fermentation.",
        "sustainability_score": 89,
    },
    "construction": {
        "composition": "Crushed concrete aggregate, masonry fines, and gypsum wallboard scrap",
        "condition": "Graded aggregate and segregated mineral rubble, free of rebar",
        "reuse_applications": [
            "Sub-base road construction and engineered fill",
            "Recycled aggregate concrete for sidewalks and pavers",
            "Soil stabilization and erosion control rip-rap",
            "Gypsum recovery for new wallboard manufacturing"
        ],
        "target_industries": [
            "Road Infrastructure & Civil Contractors",
            "Precast Concrete & Paver Producers",
            "Gypsum Wallboard Manufacturers",
            "Land Development & Earthmoving"
        ],
        "handling_notes": "Dust hazard during loading/unloading. Use water misting and N95 dust masks.",
        "sustainability_score": 82,
    },
    "electronic": {
        "composition": "De-populated circuit boards, connector pins, and electrical wiring scrap",
        "condition": "Baled or shredded WEEE electronics grade, ready for secondary refining",
        "reuse_applications": [
            "Precious metal recovery (gold, silver, copper, palladium)",
            "Copper wire granulate recycling into new electrical conductors",
            "Secondary aluminum heatsink remelting",
            "Engineered plastic chassis polymer reclamation"
        ],
        "target_industries": [
            "Precious Metal Refineries & Smelters",
            "Cable & Wire Manufacturers",
            "E-Waste Secondary Recyclers",
            "Automotive Electronics Remanufacturers"
        ],
        "handling_notes": "Handle under ESD and environmental controls. Ensure certified chain-of-custody recycling.",
        "sustainability_score": 91,
    },
    "other": {
        "composition": "Composite industrial material byproduct",
        "condition": "Solid reusable manufacturing secondary stream",
        "reuse_applications": [
            "Secondary industrial filler and binder",
            "Refuse-derived fuel (RDF) for cement kiln coprocessing",
            "Sound deadening mats and composite board fillers",
            "Civil engineering embankments"
        ],
        "target_industries": [
            "Cement Kilns & Co-processing",
            "Composite Materials Manufacturing",
            "Industrial Fillers & Extenders",
            "Specialized Waste Upcycling"
        ],
        "handling_notes": "Standard industrial warehouse handling. Review safety data sheet.",
        "sustainability_score": 75,
    }
}

def detect_hazard(text: str) -> bool:
    """Detect if material description contains hazardous indicators."""
    text_lower = text.lower()
    return any(re.search(rf"\b{re.escape(kw)}\b", text_lower) for kw in HAZARDOUS_KEYWORDS)

def rule_based_analyze(title: str, description: str, category_hint: Optional[str] = None) -> AIAnalysisResult:
    """Built-in rule-based analyzer when Gemini API is unavailable or fails."""
    combined_text = f"{title} {description}".lower()
    
    # 1. Determine Category
    category_scores = {cat: 0 for cat in VALID_CATEGORIES}
    matched_category = "other"
    if category_hint and category_hint.lower() in VALID_CATEGORIES and category_hint.lower() != "other":
        matched_category = category_hint.lower()
        category_scores[matched_category] = 3
    else:
        keywords = {
            "metal": ["steel", "iron", "aluminum", "copper", "brass", "scrap", "sheet", "alloy", "tin", "shavings", "pipes", "billet"],
            "plastic": ["plastic", "polyethylene", "hdpe", "ldpe", "pet", "pp", "polypropylene", "pvc", "polymer", "resin", "pellets", "nylon"],
            "chemical": ["chemical", "solvent", "acid", "base", "ethanol", "acetone", "glycol", "lubricant", "oil", "alkali", "reagent", "catalyst"],
            "textile": ["textile", "cotton", "fabric", "denim", "polyester", "yarn", "wool", "cloth", "fiber", "rags", "knitting"],
            "wood": ["wood", "timber", "sawdust", "pallet", "pine", "oak", "plywood", "lumber", "bark", "chips", "shavings"],
            "glass": ["glass", "cullet", "bottles", "silica", "borosilicate", "shards", "plate glass"],
            "organic": ["organic", "spent", "grains", "bagasse", "biomass", "coffee", "husks", "peel", "starch", "food waste", "slurry"],
            "construction": ["concrete", "rubble", "gypsum", "drywall", "asphalt", "bricks", "tiles", "mortar", "aggregate"],
            "electronic": ["electronic", "pcb", "circuit", "e-waste", "wire", "cable", "batteries", "chips", "hardware"]
        }
        for cat, kw_list in keywords.items():
            for kw in kw_list:
                if re.search(rf"\b{re.escape(kw)}\b", combined_text):
                    category_scores[cat] += 1
        
        best_cat = max(category_scores, key=category_scores.get)
        if category_scores[best_cat] > 0:
            matched_category = best_cat

    # 2. Hazard check
    is_hazardous = detect_hazard(combined_text) or (matched_category == "chemical")
    safety_warning = None
    if is_hazardous:
        safety_warning = (
            "⚠️ REGULATORY HAZARD NOTICE: This material exhibits hazardous or regulated characteristics. "
            "Storage, transport, and recycling MUST strictly comply with local environmental regulations, "
            "OSHA/REACH guidelines, and certified waste manifest protocols."
        )

    # 3. Pull from rule database
    cat_data = RULE_DATABASE.get(matched_category, RULE_DATABASE["other"])
    
    material_name = title.strip() if title else f"Recycled {matched_category.capitalize()} Resource"
    if not material_name:
        material_name = f"Industrial {matched_category.capitalize()} Byproduct"

    return AIAnalysisResult(
        material_name=material_name,
        category=matched_category,
        composition=f"Verified industrial grade {matched_category} stream: {cat_data['composition']}",
        condition=cat_data["condition"],
        reuse_applications=cat_data["reuse_applications"],
        target_industries=cat_data["target_industries"],
        handling_notes=cat_data["handling_notes"],
        sustainability_score=cat_data["sustainability_score"],
        confidence="High" if category_scores.get(matched_category, 0) >= 2 else "Medium",
        is_hazardous=is_hazardous,
        safety_warning=safety_warning,
        is_demo_mode=True
    )

def repair_and_validate_ai_json(data: Dict[str, Any], fallback_title: str, fallback_desc: str) -> AIAnalysisResult:
    """Ensure AI response satisfies exact schema rules, repairing missing or invalid items."""
    rule_fallback = rule_based_analyze(fallback_title, fallback_desc)

    material_name = str(data.get("material_name") or fallback_title or "Industrial Resource").strip()
    
    cat = str(data.get("category", "")).lower().strip()
    if cat not in VALID_CATEGORIES:
        cat = rule_fallback.category

    composition = str(data.get("composition") or rule_fallback.composition).strip()
    condition = str(data.get("condition") or rule_fallback.condition).strip()

    # Reuse applications list
    raw_apps = data.get("reuse_applications")
    if isinstance(raw_apps, list) and len(raw_apps) >= 2:
        reuse_applications = [str(x).strip() for x in raw_apps if str(x).strip()][:5]
    else:
        reuse_applications = rule_fallback.reuse_applications

    # Target industries list
    raw_inds = data.get("target_industries")
    if isinstance(raw_inds, list) and len(raw_inds) >= 2:
        target_industries = [str(x).strip() for x in raw_inds if str(x).strip()][:5]
    else:
        target_industries = rule_fallback.target_industries

    handling_notes = str(data.get("handling_notes") or rule_fallback.handling_notes).strip()

    # Sustainability score 0 - 100
    try:
        score = int(data.get("sustainability_score", rule_fallback.sustainability_score))
        score = max(0, min(100, score))
    except Exception:
        score = rule_fallback.sustainability_score

    # Confidence
    conf = str(data.get("confidence", "High")).capitalize()
    if conf not in {"High", "Medium", "Low"}:
        conf = "High"

    is_hazardous = bool(data.get("is_hazardous", False)) or detect_hazard(f"{material_name} {composition} {fallback_desc}")
    safety_warning = None
    if is_hazardous:
        safety_warning = (
            "⚠️ REGULATORY HAZARD NOTICE: This material exhibits hazardous or regulated characteristics. "
            "Storage, transport, and recycling MUST strictly comply with local environmental regulations, "
            "OSHA/REACH guidelines, and certified waste manifest protocols."
        )

    return AIAnalysisResult(
        material_name=material_name,
        category=cat,
        composition=composition,
        condition=condition,
        reuse_applications=reuse_applications,
        target_industries=target_industries,
        handling_notes=handling_notes,
        sustainability_score=score,
        confidence=conf,
        is_hazardous=is_hazardous,
        safety_warning=safety_warning,
        is_demo_mode=False
    )

async def analyze_material(
    title: str,
    description: str,
    image_path: Optional[Path] = None,
    category_hint: Optional[str] = None
) -> AIAnalysisResult:
    """
    Main AI analysis entrypoint.
    Tries Google Gemini API first if GEMINI_API_KEY is configured.
    Smoothly falls back to Demo Rule-Based mode on any failure or missing key.
    """
    if not GEMINI_API_KEY:
        logger.info("No GEMINI_API_KEY found in environment. Using Demo Rule-Based AI analyzer.")
        return rule_based_analyze(title, description, category_hint)

    prompt = f"""
You are the AI Material Assessment Engine for 'ReSource AI', an industrial circular economy exchange.
Analyze the following industrial waste/unused material:
Title: {title}
Description: {description}
Category Hint: {category_hint or 'Unknown'}

Return ONLY a valid JSON object with the following exact schema:
{{
  "material_name": "Specific concise material designation",
  "category": "one of: metal, plastic, chemical, textile, wood, glass, organic, construction, electronic, other",
  "composition": "Detailed technical composition breakdown",
  "condition": "Physical condition summary (e.g. clean sorted regrind, unwashed scrap, surplus virgin)",
  "reuse_applications": ["Application 1", "Application 2", "Application 3", "Application 4"],
  "target_industries": ["Industry 1", "Industry 2", "Industry 3", "Industry 4"],
  "handling_notes": "Key storage, handling, PPE, and transport precautions",
  "sustainability_score": 85,
  "confidence": "High",
  "is_hazardous": false
}}
Strictly return only valid JSON with no conversational preamble or markdown codeblocks outside the JSON.
"""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        model_name = GEMINI_MODEL or "gemini-2.5-flash"

        contents = []
        if image_path and image_path.exists():
            try:
                from PIL import Image
                pil_img = Image.open(image_path)
                contents.append(pil_img)
            except Exception as img_err:
                logger.warning(f"Failed to load image for Gemini: {img_err}")

        contents.append(prompt)

        response = client.models.generate_content(
            model=model_name,
            contents=contents
        )

        response_text = response.text.strip()
        # Clean json backticks if present
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?\n?", "", response_text)
            response_text = re.sub(r"\n?```$", "", response_text)

        parsed_data = json.loads(response_text)
        validated = repair_and_validate_ai_json(parsed_data, title, description)
        return validated

    except Exception as exc:
        logger.warning(f"Gemini API call failed or encountered error: {exc}. Falling back to Demo Rule-Based analyzer.")
        return rule_based_analyze(title, description, category_hint)

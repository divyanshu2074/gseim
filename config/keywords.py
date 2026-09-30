"""Deterministic keyword dictionaries, weights, and negative filters for GSEIM."""

# -------------------------------------------------------------
# Opportunities Taxonomies & Keywords
# -------------------------------------------------------------

CATEGORY_KEYWORDS = {
    "Grant": [
        "grant", "grants", "funding opportunity", "call for proposals",
        "financial assistance", "funding call", "matching grant", "research grant",
        "seed grant", "innovation grant", "r&d grant", "non-dilutive funding",
        "subvention", "subsidy", "equity-free funding"
    ],
    "Accelerator": [
        "accelerator", "acceleration program", "cohort", "accelerator program",
        "demo day", "scaleup program", "growth program", "accelerate",
        "batch", "mentorship program"
    ],
    "Incubator": [
        "incubator", "incubation", "incubation program", "technology business incubator",
        "tbi", "maker space", "venture studio", "co-working incubator",
        "pre-incubation", "academic incubator"
    ],
    "Competition": [
        "competition", "startup challenge", "pitch competition", "hackathon",
        "innovation challenge", "grand challenge", "award", "prize",
        "startup awards", "showcase competition"
    ],
    "Fellowship": [
        "fellowship", "fellow", "entrepreneurship fellowship", "residency",
        "entrepreneur in residence", "eir", "founder fellowship", "fellows cohort"
    ],
    "Investment": [
        "investment", "venture capital", "seed funding", "pre-seed fund",
        "angel network", "syndicate", "capital call", "co-investment",
        "catalytic capital", "equity investment", "convertible note"
    ]
}

# Weighted scoring for Opportunity detection
OPPORTUNITY_WEIGHTS = {
    # High intent terms
    "call for applications": 8,
    "call for proposals": 8,
    "apply now": 6,
    "applications open": 8,
    "applications close": 8,
    "submission deadline": 8,
    "application deadline": 8,
    "cohort": 6,
    "batch": 5,
    "equity-free": 7,
    "non-dilutive": 7,
    "funding up to": 6,
    "grant up to": 6,
    "accelerator program": 7,
    "incubation program": 7,
    "pitch competition": 6,
    "seed fund": 5,
    "startup scheme": 7,
    "technology business incubator": 7,
    
    # Generic positive modifiers
    "startup": 3,
    "startups": 3,
    "founder": 3,
    "founders": 3,
    "entrepreneur": 3,
    "entrepreneurs": 3,
    "innovation": 2,
    "mentorship": 3,
    "prototype": 3,
    "commercialization": 4
}

# Disqualification / Negative Keywords for Opportunities
EXCLUDE_OPPORTUNITIES = [
    "student essay competition",
    "coloring contest",
    "consumer discount",
    "promotional offer",
    "coupon code",
    "high school competition",
    "press release: quarterly earnings",
    "conference ticket sale",
    "freelance gig",
    "real estate lease",
    "used equipment sale"
]

# -------------------------------------------------------------
# Jobs Taxonomies & Keywords
# -------------------------------------------------------------

JOB_FUNCTIONS = {
    "Incubation": [
        "incubation manager", "incubation associate", "incubation director",
        "incubator manager", "incubation lead", "tbi manager", "incubation specialist",
        "head of incubation", "incubation coordinator"
    ],
    "Acceleration": [
        "accelerator manager", "accelerator program manager", "acceleration lead",
        "program manager", "head of programs", "cohort manager", "director of acceleration",
        "startup program manager"
    ],
    "Investment": [
        "investment associate", "investment analyst", "venture capital analyst",
        "vc associate", "investment manager", "principal", "deal flow manager",
        "venture partner", "portfolio associate", "investment director"
    ],
    "Ecosystem": [
        "ecosystem manager", "ecosystem lead", "startup ecosystem manager",
        "startup relations manager", "community manager", "ecosystem director",
        "founder relations", "community lead", "startup community"
    ],
    "Innovation": [
        "innovation manager", "innovation program manager", "open innovation manager",
        "innovation consultant", "director of innovation", "innovation associate",
        "innovation lead", "corporate innovation manager"
    ],
    "Strategy": [
        "strategy manager", "strategy associate", "founder's office",
        "chief of staff", "special projects", "head of strategy", "operations manager"
    ],
    "Partnerships": [
        "partnerships manager", "strategic partnerships", "alliances manager",
        "head of partnerships", "corporate relations manager"
    ],
    "Commercialization": [
        "technology transfer officer", "tto manager", "research commercialization manager",
        "ip manager", "commercialization associate", "licensing officer"
    ]
}

JOB_WEIGHTS = {
    # High-signal Ecosystem Job Titles
    "program manager": 8,
    "incubation manager": 10,
    "accelerator manager": 10,
    "startup program manager": 10,
    "investment associate": 10,
    "venture capital analyst": 10,
    "ecosystem manager": 10,
    "innovation manager": 9,
    "entrepreneurship manager": 9,
    "partnerships manager": 8,
    "startup relations manager": 9,
    "portfolio manager": 8,
    "community manager": 7,
    "founder's office": 9,
    "chief of staff": 8,
    "technology transfer officer": 10,
    "open innovation": 8,
    "deal flow": 9,
    
    # Contextual boosters
    "incubator": 4,
    "accelerator": 4,
    "venture capital": 5,
    "vc fund": 5,
    "startup ecosystem": 5,
    "entrepreneurship centre": 4,
    "angel network": 4,
    "innovation hub": 4,
    "portfolio companies": 4
}

# Negative Job Keywords (Non-ecosystem general tech, sales, corporate jobs)
EXCLUDE_JOBS = [
    "software engineer",
    "frontend developer",
    "backend developer",
    "full stack developer",
    "devops engineer",
    "qa tester",
    "cloud architect",
    "sales executive",
    "accountant",
    "graphic designer",
    "customer support",
    "customer service",
    "warehouse associate",
    "driver",
    "mechanic",
    "cashier",
    "receptionist",
    "telecaller",
    "data entry clerk",
    "security guard"
]

# -------------------------------------------------------------
# Startup Stages & Sectors Taxonomies
# -------------------------------------------------------------

STAGES = [
    "Ideation",
    "Pre-Seed",
    "Seed",
    "Early Stage",
    "Series A",
    "Growth",
    "Scaleup",
    "Any Stage"
]

SECTOR_KEYWORDS = {
    "DeepTech": ["deeptech", "deep tech", "robotics", "quantum", "semiconductor", "photonics"],
    "AI/ML": ["artificial intelligence", "ai", "machine learning", "computer vision", "nlp", "genai"],
    "ClimateTech": ["climatetech", "clean tech", "cleantech", "sustainability", "renewable energy", "carbon", "esg", "circular economy"],
    "AgriTech": ["agritech", "agriculture", "agtech", "food tech", "smart farming"],
    "HealthTech": ["healthtech", "biotech", "life sciences", "medtech", "digital health", "pharma"],
    "FinTech": ["fintech", "financial technology", "insurtech", "payments", "defi", "banking"],
    "EdTech": ["edtech", "education technology", "e-learning", "skills"],
    "SaaS": ["saas", "software as a service", "b2b saas", "enterprise software"],
    "SpaceTech": ["spacetech", "aerospace", "satellite", "geospatial"],
    "Social Impact": ["social innovation", "social enterprise", "livelihood", "inclusion", "impact"]
}

# -------------------------------------------------------------
# Ecosystem Update Keywords
# -------------------------------------------------------------

UPDATE_KEYWORDS = [
    "launches fund", "launched fund", "fund launched",
    "new fund", "new venture fund", "crore fund", "million fund", "billion fund",
    "mou signed", "signs mou", "partnership announced",
    "innovation centre", "innovation center", "centre of excellence", "center of excellence",
    "startup policy", "new policy", "startup mission",
    "research park", "incubation facility", "technology transfer"
]

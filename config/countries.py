"""Country, Region, and Location Taxonomies for GSEIM."""

COUNTRY_REGION_MAP = {
    # South Asia
    "India": "South Asia",
    "Bangladesh": "South Asia",
    "Sri Lanka": "South Asia",
    "Pakistan": "South Asia",
    "Nepal": "South Asia",

    # Southeast Asia
    "Singapore": "Southeast Asia",
    "Indonesia": "Southeast Asia",
    "Malaysia": "Southeast Asia",
    "Thailand": "Southeast Asia",
    "Vietnam": "Southeast Asia",
    "Philippines": "Southeast Asia",

    # North America
    "United States": "North America",
    "USA": "North America",
    "Canada": "North America",
    "Mexico": "North America",

    # Europe
    "United Kingdom": "Europe",
    "UK": "Europe",
    "Germany": "Europe",
    "France": "Europe",
    "Netherlands": "Europe",
    "Sweden": "Europe",
    "Switzerland": "Europe",
    "Estonia": "Europe",
    "Spain": "Europe",
    "Ireland": "Europe",
    "Finland": "Europe",
    "Denmark": "Europe",
    "Norway": "Europe",
    "Belgium": "Europe",
    "Austria": "Europe",
    "Poland": "Europe",
    "Italy": "Europe",
    "European Union": "Europe",

    # Middle East
    "United Arab Emirates": "Middle East",
    "UAE": "Middle East",
    "Saudi Arabia": "Middle East",
    "Qatar": "Middle East",
    "Israel": "Middle East",
    "Bahrain": "Middle East",
    "Oman": "Middle East",

    # East Asia & Oceania
    "Japan": "East Asia",
    "South Korea": "East Asia",
    "Australia": "Oceania",
    "New Zealand": "Oceania",

    # Africa
    "South Africa": "Africa",
    "Kenya": "Africa",
    "Nigeria": "Africa",
    "Rwanda": "Africa",
    "Egypt": "Africa",
    "Ghana": "Africa",

    # Latin America
    "Brazil": "Latin America",
    "Chile": "Latin America",
    "Colombia": "Latin America",
    "Argentina": "Latin America"
}

def get_region_for_country(country: str) -> str:
    """Normalize and lookup region for a given country name."""
    if not country:
        return "Global"
    cleaned = country.strip()
    return COUNTRY_REGION_MAP.get(cleaned, "Global")

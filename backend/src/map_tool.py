# ============================================================================
# COMPREHENSIVE OSM ANALYZER FOR EGYPTIAN NEIGHBORHOODS
# ============================================================================

import httpx
from typing import List, Dict, Any, Optional, Tuple
import math
from collections import Counter
from langchain.tools import tool

OSM_CONFIG = {
    "overpass_url": "https://overpass-api.de/api/interpreter",
    "nominatim_url": "https://nominatim.openstreetmap.org/search",
    "timeout": 45,
    "max_retries": 3
}

# Comprehensive Egyptian neighborhood mappings
EGYPTIAN_NEIGHBORHOODS = {
    # New Cairo Areas - FIXED names
    "benafseg": "Ben Afseg, New Cairo, Cairo Governorate, Egypt",
    "rehab": "Al Rehab City, New Cairo, Cairo Governorate, Egypt", 
    "madinty": "Madinaty, New Cairo, Cairo Governorate, Egypt",
    "katameya": "Katameya, New Cairo, Cairo Governorate, Egypt",
    "sherouk": "El Sherouk City, Cairo Governorate, Egypt",
    
    # 6th October Areas
    "sheikh zayed": "Sheikh Zayed City, Giza Governorate, Egypt",
    "beverly hills": "Beverly Hills, 6th of October City, Giza Governorate, Egypt",
    "gate": "Gate, 6th of October City, Giza Governorate, Egypt",
    "arabella": "Arabella, 6th of October City, Giza Governorate, Egypt",
    
    # Maadi Areas
    "degla": "Degla, Maadi, Cairo Governorate, Egypt",
    "sarabium": "Sarabium, Maadi, Cairo Governorate, Egypt",
    "zahraa": "Zahraa Al Maadi, Cairo Governorate, Egypt",
    
    # Nasr City Areas
    "el nozha": "El Nozha, Nasr City, Cairo Governorate, Egypt",
    "el horreya": "El Horreya, Nasr City, Cairo Governorate, Egypt",
    "hadiq al qubbah": "Hadiq Al Qubbah, Nasr City, Cairo Governorate, Egypt",
    
    # Heliopolis Areas
    "korba": "Korba, Heliopolis, Cairo Governorate, Egypt",
    "cleopatra": "Cleopatra, Heliopolis, Cairo Governorate, Egypt",
    "merghany": "Merghany, Heliopolis, Cairo Governorate, Egypt"
}

# Comprehensive OSM tag mappings for detailed analysis
OSM_ANALYSIS_TAGS = {
    # Traffic & Noise Indicators
    "high_traffic_roads": ["motorway", "trunk", "primary", "secondary"],
    "medium_traffic_roads": ["tertiary", "residential", "unclassified"],
    "low_traffic_roads": ["service", "pedestrian", "footway", "living_street"],
    
    # Amenities & Facilities
    "education": ["school", "college", "university", "kindergarten", "library"],
    "healthcare": ["hospital", "clinic", "pharmacy", "doctor", "dentist"],
    "shopping": ["supermarket", "mall", "convenience", "marketplace", "bakery"],
    "food": ["restaurant", "cafe", "fast_food", "food_court"],
    "recreation": ["park", "garden", "fitness_center", "sports_center", "swimming_pool"],
    "religious": ["mosque", "church", "place_of_worship"],
    "transport": ["bus_station", "train_station", "taxi", "bicycle_parking"],
    "services": ["bank", "atm", "post_office", "police", "fire_station"],
    
    # Quiet & Green Indicators
    "green_spaces": ["park", "garden", "forest", "grass", "recreation_ground"],
    "water_features": ["river", "lake", "pond", "fountain"],
    "quiet_zones": ["cemetery", "grave_yard", "library", "monastery"]
}







class AdvancedNeighborhoodAnalyzer:
    """
    Advanced analyzer for specific Egyptian neighborhoods with detailed metrics
    """
    
    def __init__(self):
        self.config = OSM_CONFIG
    
    def geocode_specific_neighborhood(self, neighborhood: str) -> Optional[Dict]:
        """
        Geocode specific Egyptian neighborhoods with fallbacks
        """
        # Try exact match first
        if neighborhood.lower() in EGYPTIAN_NEIGHBORHOODS:
            exact_location = EGYPTIAN_NEIGHBORHOODS[neighborhood.lower()]
        else:
            # Try partial match
            exact_location = neighborhood
        
        params = {
            'q': exact_location,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'eg',
            'addressdetails': 1
        }
        
        try:
            response = httpx.get(self.config["nominatim_url"], params=params, timeout=15)
            data = response.json()
            
            if data:
                result = data[0]
                bbox = result.get('boundingbox', [])
                
                return {
                    'lat': float(result['lat']),
                    'lng': float(result['lon']),
                    'display_name': result['display_name'],
                    'importance': float(result.get('importance', 0)),
                    'bbox': [float(coord) for coord in bbox] if bbox else None,
                    'type': result.get('type', ''),
                    'class': result.get('class', '')
                }
                
        except Exception as e:
            print(f"Geocoding failed for {neighborhood}: {e}")
        
        return None
    

    def _execute_overpass_query(self, query: str) -> List[Dict]:
     """
     Execute Overpass API query and return results
    """
     try:
        response = httpx.post(
            self.config["overpass_url"],
            data={'data': query},
            timeout=self.config["timeout"]
        )
        response.raise_for_status()
        return response.json().get('elements', [])
     except Exception as e:
        print(f"Overpass query failed: {e}")
        return []
    
    def analyze_neighborhood_comprehensive(self, neighborhood: str, analysis_focus: List[str] = None) -> Dict[str, Any]:
        """
        Comprehensive neighborhood analysis with multiple metrics
        """
        if analysis_focus is None:
            analysis_focus = ["amenities", "traffic", "lifestyle"]
        
        # Geocode the specific neighborhood
        geo_data = self.geocode_specific_neighborhood(neighborhood)
        if not geo_data:
            return {"error": f"Could not find neighborhood: {neighborhood}"}
        
        print(f"🔍 Analyzing {neighborhood} with focus: {analysis_focus}")
        
        # Perform comprehensive OSM queries
        analysis_results = {}
        
        if "amenities" in analysis_focus:
            analysis_results["amenities"] = self._analyze_amenities(geo_data)
        
        if "traffic" in analysis_focus:
            analysis_results["traffic"] = self._analyze_traffic_patterns(geo_data)
        
        if "lifestyle" in analysis_focus:
            analysis_results["lifestyle"] = self._analyze_lifestyle_factors(geo_data)
        
        if "connectivity" in analysis_focus:
            analysis_results["connectivity"] = self._analyze_connectivity(geo_data)
        
        # Calculate overall scores
        overall_scores = self._calculate_comprehensive_scores(analysis_results, analysis_focus)
        
        return {
            "neighborhood": neighborhood,
            "location": geo_data,
            "analysis_focus": analysis_focus,
            "detailed_analysis": analysis_results,
            "scores": overall_scores,
            "recommendations": self._generate_recommendations(analysis_results, overall_scores, analysis_focus)
        }
    
    def _analyze_amenities(self, location: Dict) -> Dict:
        """
        Analyze amenities and facilities in the area
        """
        amenities_query = f"""
        [out:json][timeout:30];
        (
            // Amenities within 1.5km radius
            node["amenity"](around:1500,{location['lat']},{location['lng']});
            way["amenity"](around:1500,{location['lat']},{location['lng']});
            relation["amenity"](around:1500,{location['lat']},{location['lng']});
            
            // Shopping facilities
            node["shop"](around:1500,{location['lat']},{location['lng']});
            way["shop"](around:1500,{location['lat']},{location['lng']});
            
            // Leisure facilities
            node["leisure"](around:1500,{location['lat']},{location['lng']});
            way["leisure"](around:1500,{location['lat']},{location['lng']});
        );
        out body;
        >;
        out skel qt;
        """
        
        amenities_data = self._execute_overpass_query(amenities_query)
        return self._categorize_amenities(amenities_data)
    
    def _analyze_traffic_patterns(self, location: Dict) -> Dict:
        """
        Analyze traffic, roads, and noise indicators
        """
        traffic_query = f"""
        [out:json][timeout:30];
        (
            // All roads within 1km radius
            way["highway"](around:1000,{location['lat']},{location['lng']});
            node["highway"="traffic_signals"](around:1000,{location['lat']},{location['lng']});
        );
        out body;
        >;
        out skel qt;
        """
        
        traffic_data = self._execute_overpass_query(traffic_query)
        return self._analyze_traffic_data(traffic_data)
    
    def _analyze_lifestyle_factors(self, location: Dict) -> Dict:
        """
        Analyze lifestyle factors: green spaces, recreation, etc.
        """
        lifestyle_query = f"""
        [out:json][timeout:30];
        (
            // Green spaces
            way["leisure"](around:1500,{location['lat']},{location['lng']});
            node["leisure"](around:1500,{location['lat']},{location['lng']});
            
            // Natural features
            way["natural"](around:1500,{location['lat']},{location['lng']});
            node["natural"](around:1500,{location['lat']},{location['lng']});
            
            // Water features
            way["water"](around:1500,{location['lat']},{location['lng']});
            node["water"](around:1500,{location['lat']},{location['lng']});
        );
        out body;
        >;
        out skel qt;
        """
        
        lifestyle_data = self._execute_overpass_query(lifestyle_query)
        return self._analyze_lifestyle_data(lifestyle_data)
    
    def _analyze_connectivity(self, location: Dict) -> Dict:
        """
        Analyze transportation and connectivity
        """
        connectivity_query = f"""
        [out:json][timeout:30];
        (
            // Public transport
            node["public_transport"](around:1500,{location['lat']},{location['lng']});
            node["railway"](around:1500,{location['lat']},{location['lng']});
            node["amenity"="bus_station"](around:1500,{location['lat']},{location['lng']});
            
            // Major roads for accessibility
            way["highway"~"motorway|trunk|primary"](around:2000,{location['lat']},{location['lng']});
        );
        out body;
        >;
        out skel qt;
        """
        
        connectivity_data = self._execute_overpass_query(connectivity_query)
        return self._analyze_connectivity_data(connectivity_data)
    




    def _categorize_amenities(self, elements: List[Dict]) -> Dict:
        """Categorize amenities into detailed groups"""
        categories = {
            "education": [], "healthcare": [], "shopping": [], "food": [],
            "recreation": [], "religious": [], "transport": [], "services": []
        }
        
        for element in elements:
            if 'tags' not in element:
                continue
                
            tags = element['tags']
            amenity_type = tags.get('amenity', '')
            shop_type = tags.get('shop', '')
            leisure_type = tags.get('leisure', '')
            name = tags.get('name', 'Unnamed')
            
            amenity_data = {
                'name': name,
                'type': amenity_type or shop_type or leisure_type,
                'lat': element.get('lat'),
                'lon': element.get('lon')
            }
            
            # Categorize based on type
            if amenity_type in OSM_ANALYSIS_TAGS["education"]:
                categories["education"].append(amenity_data)
            elif amenity_type in OSM_ANALYSIS_TAGS["healthcare"]:
                categories["healthcare"].append(amenity_data)
            elif amenity_type in OSM_ANALYSIS_TAGS["food"] or shop_type in ['bakery', 'butcher']:
                categories["food"].append(amenity_data)
            elif amenity_type in OSM_ANALYSIS_TAGS["religious"]:
                categories["religious"].append(amenity_data)
            elif amenity_type in OSM_ANALYSIS_TAGS["transport"]:
                categories["transport"].append(amenity_data)
            elif amenity_type in OSM_ANALYSIS_TAGS["services"]:
                categories["services"].append(amenity_data)
            elif shop_type in OSM_ANALYSIS_TAGS["shopping"] or amenity_type == 'marketplace':
                categories["shopping"].append(amenity_data)
            elif leisure_type in OSM_ANALYSIS_TAGS["recreation"]:
                categories["recreation"].append(amenity_data)
        
        return categories
    
    def _analyze_traffic_data(self, elements: List[Dict]) -> Dict:
        """Analyze traffic patterns and road types"""
        road_counts = Counter()
        total_roads = 0
        
        for element in elements:
            if 'tags' in element:
                highway_type = element['tags'].get('highway', '')
                if highway_type:
                    total_roads += 1
                    if highway_type in OSM_ANALYSIS_TAGS["high_traffic_roads"]:
                        road_counts["high_traffic"] += 1
                    elif highway_type in OSM_ANALYSIS_TAGS["medium_traffic_roads"]:
                        road_counts["medium_traffic"] += 1
                    elif highway_type in OSM_ANALYSIS_TAGS["low_traffic_roads"]:
                        road_counts["low_traffic"] += 1
        
        # Calculate traffic score (lower = quieter)
        if total_roads > 0:
            high_traffic_ratio = road_counts["high_traffic"] / total_roads
            low_traffic_ratio = road_counts["low_traffic"] / total_roads
            traffic_score = max(0, 10 - (high_traffic_ratio * 8) + (low_traffic_ratio * 4))
        else:
            traffic_score = 8.0  # Assume quiet if no roads mapped
        
        return {
            "road_breakdown": dict(road_counts),
            "total_roads": total_roads,
            "traffic_score": round(traffic_score, 1),
            "quietness_indicator": "Very Quiet" if traffic_score >= 8 else 
                                 "Quiet" if traffic_score >= 6 else
                                 "Moderate" if traffic_score >= 4 else "Busy"
        }
    
    def _analyze_lifestyle_data(self, elements: List[Dict]) -> Dict:
        """Analyze lifestyle and quality of life factors"""
        green_spaces = 0
        recreation_facilities = 0
        
        for element in elements:
            if 'tags' in element:
                tags = element['tags']
                leisure_type = tags.get('leisure', '')
                natural_type = tags.get('natural', '')
                
                if leisure_type in ['park', 'garden', 'nature_reserve']:
                    green_spaces += 1
                if leisure_type in ['fitness_center', 'sports_center', 'swimming_pool']:
                    recreation_facilities += 1
        
        # Calculate lifestyle score
        green_score = min(green_spaces / 3 * 5, 5)  # Max 5 points for green spaces
        recreation_score = min(recreation_facilities / 2 * 5, 5)  # Max 5 points for recreation
        lifestyle_score = (green_score + recreation_score) / 10 * 10  # Convert to 0-10 scale
        
        return {
            "green_spaces": green_spaces,
            "recreation_facilities": recreation_facilities,
            "lifestyle_score": round(lifestyle_score, 1),
            "green_rating": "Very Green" if green_spaces >= 3 else 
                          "Moderately Green" if green_spaces >= 1 else "Limited Green"
        }
    
    def _analyze_connectivity_data(self, elements: List[Dict]) -> Dict:
        """Analyze transportation connectivity"""
        transport_nodes = 0
        major_roads = 0
        
        for element in elements:
            if 'tags' in element:
                tags = element['tags']
                if tags.get('public_transport') or tags.get('railway') or tags.get('amenity') == 'bus_station':
                    transport_nodes += 1
                if tags.get('highway') in ['motorway', 'trunk', 'primary']:
                    major_roads += 1
        
        connectivity_score = min((transport_nodes * 3 + major_roads * 2) / 5, 10)
        
        return {
            "transport_nodes": transport_nodes,
            "major_roads": major_roads,
            "connectivity_score": round(connectivity_score, 1),
            "accessibility": "Excellent" if connectivity_score >= 7 else
                           "Good" if connectivity_score >= 5 else
                           "Fair" if connectivity_score >= 3 else "Limited"
        }
    





    def _calculate_comprehensive_scores(self, analysis: Dict, focus_areas: List[str]) -> Dict:
        """Calculate comprehensive neighborhood scores"""
        scores = {}
        
        # Base scores from different analyses
        if "traffic" in analysis:
            scores["quietness"] = analysis["traffic"]["traffic_score"]
        
        if "lifestyle" in analysis:
            scores["lifestyle"] = analysis["lifestyle"]["lifestyle_score"]
        
        if "connectivity" in analysis:
            scores["connectivity"] = analysis["connectivity"]["connectivity_score"]
        
        # Amenity density score
        if "amenities" in analysis:
            total_amenities = sum(len(amenities) for amenities in analysis["amenities"].values())
            amenity_density = min(total_amenities / 20 * 10, 10)  # Normalize to 0-10
            scores["amenities"] = round(amenity_density, 1)
        
        # Overall score weighted by focus areas
        if focus_areas:
            focus_weights = {
                "quiet": 0.4, "amenities": 0.3, "lifestyle": 0.2, "connectivity": 0.1
            }
            
            weighted_score = 0
            for focus in focus_areas:
                weight = focus_weights.get(focus, 0.1)
                if focus == "quiet" and "quietness" in scores:
                    weighted_score += scores["quietness"] * weight
                elif focus in scores:
                    weighted_score += scores[focus] * weight
            
            scores["overall"] = round(weighted_score, 1)
        else:
            # Default weighting
            scores["overall"] = round(
                (scores.get("quietness", 5) * 0.3 + 
                 scores.get("amenities", 5) * 0.3 +
                 scores.get("lifestyle", 5) * 0.2 +
                 scores.get("connectivity", 5) * 0.2), 1
            )
        
        return scores
    
    def _generate_recommendations(self, analysis: Dict, scores: Dict, focus_areas: List[str]) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        overall_score = scores.get("overall", 5)
        
        if overall_score >= 8:
            recommendations.append("🏆 **Excellent choice** - This neighborhood balances amenities with quality of life")
        elif overall_score >= 6:
            recommendations.append("✅ **Good option** - Meets most criteria with some trade-offs")
        else:
            recommendations.append("⚠️ **Consider alternatives** - May not fully meet your needs")
        
        # Focus-specific recommendations
        if "quiet" in focus_areas:
            quiet_score = scores.get("quietness", 5)
            if quiet_score >= 8:
                recommendations.append("🌿 **Very quiet area** - Minimal traffic noise, peaceful environment")
            elif quiet_score >= 6:
                recommendations.append("🔇 **Relatively quiet** - Some traffic but generally peaceful")
            else:
                recommendations.append("🚗 **Busier area** - Expect moderate traffic noise")
        
        if "amenities" in focus_areas:
            amenity_score = scores.get("amenities", 5)
            if amenity_score >= 7:
                recommendations.append("🛍️ **Well-served area** - Good access to shops and services")
            elif amenity_score >= 4:
                recommendations.append("🏪 **Adequate amenities** - Basic services available")
            else:
                recommendations.append("📦 **Limited amenities** - May require travel for shopping")
        
        if "lifestyle" in focus_areas:
            lifestyle_score = scores.get("lifestyle", 5)
            if lifestyle_score >= 7:
                recommendations.append("🌳 **Green & active** - Good parks and recreation options")
            elif lifestyle_score >= 4:
                recommendations.append("🏞️ **Some green spaces** - Limited but available")
            else:
                recommendations.append("🏢 **Urban environment** - Few green/recreation spaces")
        
        return recommendations
    











@tool
def analyze_egyptian_neighborhood_advanced(
    neighborhood: str,
    user_scenario: str = "general",
    specific_needs: List[str] = None
) -> str:
    """
    Advanced neighborhood analysis for specific Egyptian areas with scenario-based focus
    
    Args:
        neighborhood: Specific area (e.g., "benafseg", "rehab", "degla")
        user_scenario: Type of analysis - "quiet", "family", "convenience", "luxury", "budget"
        specific_needs: Additional specific requirements
    
    Returns:
        Detailed neighborhood analysis tailored to user scenario
    """
    analyzer = AdvancedNeighborhoodAnalyzer()
    
    # Map scenarios to analysis focus
    SCENARIO_FOCUS = {
        "quiet": ["traffic", "lifestyle"],
        "family": ["amenities", "lifestyle", "traffic"],
        "convenience": ["amenities", "connectivity"],
        "luxury": ["lifestyle", "amenities"],
        "budget": ["amenities", "connectivity"],
        "general": ["amenities", "traffic", "lifestyle", "connectivity"]
    }
    
    focus_areas = SCENARIO_FOCUS.get(user_scenario, ["amenities", "traffic"])
    
    if specific_needs:
        focus_areas.extend(specific_needs)
    
    # Perform analysis
    result = analyzer.analyze_neighborhood_comprehensive(neighborhood, focus_areas)
    
    if "error" in result:
        return result["error"]
    
    return format_advanced_analysis(result, user_scenario)

def format_advanced_analysis(result: Dict, scenario: str) -> str:
    """Format advanced analysis results"""
    neighborhood = result["neighborhood"]
    scores = result["scores"]
    analysis = result["detailed_analysis"]
    recommendations = result["recommendations"]
    
    response = f"""
## 🏙️ Advanced Neighborhood Analysis: {neighborhood.title()}
### 🎯 Scenario: {scenario.upper()}

### 📊 Overall Score: **{scores['overall']}/10**

### 🔍 Detailed Analysis:
"""
    
    # Traffic/Quietness Analysis
    if "traffic" in analysis:
        traffic_data = analysis["traffic"]
        response += f"""
**🚗 Traffic & Quietness: {traffic_data['quietness_indicator']}**
- Traffic Score: {traffic_data['traffic_score']}/10
- Road Types: {traffic_data['road_breakdown']}
"""
    
    # Amenities Analysis
    if "amenities" in analysis:
        amenities_data = analysis["amenities"]
        response += f"""
**🛍️ Amenities Summary:**
"""
        for category, items in amenities_data.items():
            if items:
                response += f"- {category.title()}: {len(items)} facilities\n"
    
    # Lifestyle Analysis
    if "lifestyle" in analysis:
        lifestyle_data = analysis["lifestyle"]
        response += f"""
**🌿 Lifestyle & Green Spaces: {lifestyle_data['green_rating']}**
- Lifestyle Score: {lifestyle_data['lifestyle_score']}/10
- Green Spaces: {lifestyle_data['green_spaces']}
- Recreation Facilities: {lifestyle_data['recreation_facilities']}
"""
    
    # Connectivity Analysis
    if "connectivity" in analysis:
        connectivity_data = analysis["connectivity"]
        response += f"""
**🚇 Connectivity: {connectivity_data['accessibility']}**
- Connectivity Score: {connectivity_data['connectivity_score']}/10
- Transport Nodes: {connectivity_data['transport_nodes']}
- Major Roads: {connectivity_data['major_roads']}
"""
    
    # Recommendations
    response += f"""
### 💡 Recommendations:
"""
    for rec in recommendations:
        response += f"- {rec}\n"
    
    response += f"""
---

### 🎭 Best For:
{get_scenario_suitability(scores, scenario)}

*📍 Analysis based on OpenStreetMap data - covers {neighborhood.title()} and surrounding 1.5km area*
"""
    
    return response

def get_scenario_suitability(scores: Dict, scenario: str) -> str:
    """Determine suitability for different scenarios"""
    suitability = []
    
    overall = scores.get("overall", 5)
    quietness = scores.get("quietness", 5)
    amenities = scores.get("amenities", 5)
    lifestyle = scores.get("lifestyle", 5)
    
    if scenario == "quiet":
        if quietness >= 7:
            suitability.append("✅ **Perfect for quiet living**")
        elif quietness >= 5:
            suitability.append("⚠️ **Moderately quiet** - some traffic present")
        else:
            suitability.append("❌ **Not ideal for quiet seekers**")
    
    if scenario == "family":
        if amenities >= 6 and quietness >= 6:
            suitability.append("✅ **Great for families** - safe with good amenities")
        elif amenities >= 4 and quietness >= 4:
            suitability.append("⚠️ **Adequate for families** - some compromises needed")
        else:
            suitability.append("❌ **Challenging for families** - limited amenities/safety")
    
    if overall >= 7:
        suitability.append("🌟 **High quality neighborhood**")
    elif overall >= 5:
        suitability.append("💫 **Good standard neighborhood**")
    else:
        suitability.append("🏘️ **Developing neighborhood**")
    
    return "\n".join(suitability)



















# test_osm_analyzer.py

def test_osm_analyzer():
    """
    Test the OpenStreetMap neighborhood analyzer with various Egyptian neighborhoods
    """
    print("🧪 Testing OpenStreetMap Neighborhood Analyzer")
    print("=" * 60)
    
    # Test cases for different scenarios
    test_cases = [
        {
            "neighborhood": "benafseg",
            "scenario": "quiet",
            "description": "Testing quiet area analysis in Benafseg"
        },
        {
            "neighborhood": "rehab", 
            "scenario": "family",
            "description": "Testing family-friendly analysis in Rehab"
        },
        {
            "neighborhood": "degla",
            "scenario": "convenience",
            "description": "Testing convenience analysis in Degla"
        },
        {
            "neighborhood": "sheikh zayed",
            "scenario": "general",
            "description": "Testing general analysis in Sheikh Zayed"
        },
        {
            "neighborhood": "korba",
            "scenario": "luxury", 
            "description": "Testing luxury lifestyle analysis in Korba"
        }
    ]
    
    analyzer = AdvancedNeighborhoodAnalyzer()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['description']}")
        print("-" * 50)
        
        try:
            # First test geocoding
            print(f"📍 Geocoding {test_case['neighborhood']}...")
            geo_data = analyzer.geocode_specific_neighborhood(test_case['neighborhood'])
            
            if not geo_data:
                print(f"❌ Failed to geocode {test_case['neighborhood']}")
                continue
                
            print(f"✅ Found: {geo_data['display_name']}")
            print(f"   Coordinates: {geo_data['lat']:.4f}, {geo_data['lng']:.4f}")
            
            # Test comprehensive analysis
            print(f"🎯 Analyzing for scenario: {test_case['scenario']}...")
            result = analyzer.analyze_neighborhood_comprehensive(
                test_case['neighborhood'], 
                ["amenities", "traffic", "lifestyle"]
            )
            
            if "error" in result:
                print(f"❌ Analysis failed: {result['error']}")
                continue
            
            # Display results
            scores = result['scores']
            analysis = result['detailed_analysis']
            
            print(f"📊 Overall Score: {scores.get('overall', 'N/A')}/10")
            
            if 'amenities' in analysis:
                amenities = analysis['amenities']
                total_amenities = sum(len(items) for items in amenities.values())
                print(f"🛍️  Total amenities found: {total_amenities}")
                for category, items in amenities.items():
                    if items:
                        print(f"   - {category}: {len(items)}")
            
            if 'traffic' in analysis:
                traffic = analysis['traffic']
                print(f"🚗 Traffic score: {traffic['traffic_score']}/10 ({traffic['quietness_indicator']})")
                print(f"   Road breakdown: {traffic['road_breakdown']}")
            
            if 'lifestyle' in analysis:
                lifestyle = analysis['lifestyle']
                print(f"🌿 Lifestyle score: {lifestyle['lifestyle_score']}/10")
                print(f"   Green spaces: {lifestyle['green_spaces']}, Recreation: {lifestyle['recreation_facilities']}")
            
            # Test the tool function
            print(f"\n🛠️ Testing tool function...")
            tool_result = analyze_egyptian_neighborhood_advanced.invoke({
                "neighborhood": test_case['neighborhood'],
                "user_scenario": test_case['scenario']
            })
            
            print("✅ Tool function working!")
            print(f"📝 Result length: {len(tool_result)} characters")
            print(f"📄 First 200 chars: {tool_result[:200]}...")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        print("💤 Waiting 2 seconds before next test...")
        time.sleep(2)  # Be nice to the OSM servers
    
    print("\n" + "=" * 60)
    print("🎉 Testing completed!")

def test_specific_functionality():
    """
    Test specific components of the analyzer
    """
    print("\n🔧 Testing Specific Components")
    print("=" * 50)
    
    analyzer = AdvancedNeighborhoodAnalyzer()
    
    # Test 1: Geocoding
    print("1. Testing Geocoding...")
    neighborhoods_to_test = ["benafseg", "rehab", "degla", "unknown_area"]
    
    for area in neighborhoods_to_test:
        result = analyzer.geocode_specific_neighborhood(area)
        if result:
            print(f"   ✅ {area}: {result['display_name']}")
        else:
            print(f"   ❌ {area}: Not found")
    
    # Test 2: Individual analysis components
    print("\n2. Testing Analysis Components...")
    test_area = "rehab"
    geo_data = analyzer.geocode_specific_neighborhood(test_area)
    
    if geo_data:
        print(f"   Testing amenities analysis...")
        amenities = analyzer._analyze_amenities(geo_data)
        print(f"   ✅ Amenities categories: {list(amenities.keys())}")
        
        print(f"   Testing traffic analysis...")
        traffic = analyzer._analyze_traffic_patterns(geo_data)
        print(f"   ✅ Traffic score: {traffic.get('traffic_score', 'N/A')}")
        
        print(f"   Testing lifestyle analysis...")
        lifestyle = analyzer._analyze_lifestyle_factors(geo_data)
        print(f"   ✅ Lifestyle score: {lifestyle.get('lifestyle_score', 'N/A')}")
    
    # Test 3: Error handling
    print("\n3. Testing Error Handling...")
    invalid_result = analyzer.analyze_neighborhood_comprehensive("invalid_neighborhood_123")
    if "error" in invalid_result:
        print("   ✅ Error handling working correctly")
    else:
        print("   ❌ Error handling failed")

def test_scenario_analysis():
    """
    Test different user scenarios
    """
    print("\n🎭 Testing Different User Scenarios")
    print("=" * 50)
    
    scenarios = [
        ("quiet", "Looking for peaceful area"),
        ("family", "Family with children needs"),
        ("convenience", "Easy access to amenities"), 
        ("luxury", "Upscale lifestyle"),
        ("budget", "Cost-effective living")
    ]
    
    test_neighborhood = "benafseg"
    
    for scenario, description in scenarios:
        print(f"\n🔍 {description}")
        try:
            result = analyze_egyptian_neighborhood_advanced.invoke({
                "neighborhood": test_neighborhood,
                "user_scenario": scenario
            })
            
            # Extract score from result
            import re
            score_match = re.search(r'Overall Score:\s*\*\*(\d+\.?\d*)/10\*\*', result)
            score = score_match.group(1) if score_match else "N/A"
            
            print(f"   ✅ Scenario: {scenario}, Score: {score}/10")
            print(f"   📄 Preview: {result[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")

def performance_test():
    """
    Test performance and response times
    """
    print("\n⏱️ Performance Testing")
    print("=" * 50)
    
    analyzer = AdvancedNeighborhoodAnalyzer()
    test_areas = ["rehab", "degla", "sheikh zayed"]
    
    for area in test_areas:
        print(f"\n⏳ Testing {area}...")
        start_time = time.time()
        
        try:
            result = analyzer.analyze_neighborhood_comprehensive(area)
            end_time = time.time()
            
            if "error" not in result:
                response_time = end_time - start_time
                print(f"   ✅ Analysis completed in {response_time:.2f} seconds")
                print(f"   📊 Overall score: {result['scores'].get('overall', 'N/A')}/10")
            else:
                print(f"   ❌ Analysis failed: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")

if __name__ == "__main__":
    import time
    
    print("🚀 Starting OpenStreetMap Analyzer Tests")
    print("=" * 60)
    
    # Run all tests
    test_osm_analyzer()
    test_specific_functionality() 
    test_scenario_analysis()
    performance_test()
    
    print("\n" + "=" * 60)
    print("🎊 All tests completed!")
    print("\n💡 Next steps:")
    print("1. Check if all neighborhoods were found")
    print("2. Verify analysis scores make sense")
    print("3. Ensure tool functions work without errors")
    print("4. Integrate successful components into your agent")
    









      
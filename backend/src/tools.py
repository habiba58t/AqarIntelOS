from langchain_core.tools import tool, InjectedToolCallId
from typing import Dict, Union, Any, Annotated, Sequence, TypedDict, Literal
from geopy.geocoders import Nominatim
import psycopg2
import requests
@tool
def find_properties_tool(
    place_name: str, 
    radius_km: float = 5, 
    tool_call_id: Annotated[str, InjectedToolCallId] = ""
) -> str:
    """
    Finds up to 5 properties near a given location using PostGIS.
    Returns property name, coordinates, distance, and Google Maps link.
    
    Args:
        place_name: Name of the location to search near (e.g., "German University in Cairo")
        radius_km: Search radius in kilometers (default: 5)
    
    Returns:
        String with property details, distances, and Google Maps links
    """
    print(f"🔍 Searching for properties near: {place_name}")
    print(f"📏 Search radius: {radius_km} km")
    
    try:
        # Geocode the location with Egypt bias
        geolocator = Nominatim(user_agent="real_estate_agent")
        
        # First try: search with ", Egypt" appended
        location = geolocator.geocode(f"{place_name}, Egypt")
        
        # Second try: original name
        if not location:
            print(f"⚠️ First attempt failed, trying without Egypt suffix...")
            location = geolocator.geocode(place_name)
        
        if not location:
            error_msg = f"❌ Couldn't find coordinates for '{place_name}'. Please try a more specific location."
            print(error_msg)
            return error_msg

        lat, lon = location.latitude, location.longitude
        print(f"📍 Found coordinates: {lat}, {lon}")
        print(f"📍 Location: {location.address}")
        
        # Validate it's in Egypt (rough bounds: lat 22-32, lon 25-36)
        if not (22 <= lat <= 32 and 25 <= lon <= 36):
            print(f"⚠️ Warning: Coordinates seem outside Egypt. Found: {location.address}")
            # Try again with explicit Egypt suffix
            location = geolocator.geocode(f"{place_name}, Cairo, Egypt")
            if location and 22 <= location.latitude <= 32 and 25 <= location.longitude <= 36:
                lat, lon = location.latitude, location.longitude
                print(f"✅ Corrected to Egyptian location: {lat}, {lon}")
            else:
                return f"❌ Could not find '{place_name}' in Egypt. Please provide a more specific location in Cairo or Egypt."

        # Connect to database
        try:
            conn = psycopg2.connect(
                "dbname=langgraph_db user=postgres password=123456 host=localhost"
            )
            cur = conn.cursor()
            print("✅ Database connection established")
        except Exception as db_error:
            error_msg = f"❌ Database connection failed: {str(db_error)}"
            print(error_msg)
            return error_msg

        # Query for nearby properties
        # Cast both to geography for consistent type matching
        query = """
        SELECT name, latitude, longitude,
        ST_Distance(
            geom::geography, 
            ST_MakePoint(%s, %s)::geography
        ) AS distance
        FROM properties
        WHERE ST_DWithin(
            geom::geography, 
            ST_MakePoint(%s, %s)::geography, 
            %s
        )
        ORDER BY distance
        LIMIT 5;
        """
        
        print(f"🔍 Executing spatial query...")
        cur.execute(query, (lon, lat, lon, lat, radius_km * 1000))
        results = cur.fetchall()
        print(f"📊 Found {len(results)} properties")
        
        cur.close()
        conn.close()

        if not results:
            msg = f"No properties found within {radius_km}km of {place_name}. Try increasing the search radius."
            print(f"⚠️ {msg}")
            return msg

        # Format response
        response = [f"Found {len(results)} properties near {place_name}:\n"]
        for i, r in enumerate(results, 1):
            name, prop_lat, prop_lon, distance = r
            distance_km = round(distance / 1000, 2)
            maps_link = f"https://www.google.com/maps?q={prop_lat},{prop_lon}"
            response.append(f"{i}. **{name}**")
            response.append(f"   📍 Distance: {distance_km} km away")
            response.append(f"   🗺️ Map: {maps_link}\n")

        result = "\n".join(response)
        print(f"✅ Returning {len(results)} properties")
        return result
        
    except Exception as e:
        error_msg = f"❌ Error in find_properties_tool: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return error_msg
    














@tool
def google_maps_link_tool(
    project_name: str, 
    tool_call_id: Annotated[str, InjectedToolCallId] = ""
) -> str:
    """
    Returns a direct Google Maps link for a property based on its name.
    Looks up the property in the database and retrieves its latitude and longitude.
    
    Args:
        project_name: Name of the property/project to get map link for
    
    Returns:
        Google Maps URL or error message
    """
    print(f"🗺️ Getting map link for: {project_name}")
    
    try:
        # ✅ FIX: Use correct password
        conn = psycopg2.connect(
            "dbname=langgraph_db user=postgres password=123456 host=localhost"
        )
        cur = conn.cursor()
        
        # Query with case-insensitive search
        cur.execute(
            "SELECT name, latitude, longitude FROM properties WHERE name ILIKE %s LIMIT 1;",
            (f"%{project_name}%",)
        )
        result = cur.fetchone()
        cur.close()
        conn.close()

        if not result:
            print(f"⚠️ Property '{project_name}' not found in database")
            return f"❌ Property '{project_name}' not found in database. Please check the spelling."

        name, lat, lon = result
        maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        print(f"✅ Found: {name} at ({lat}, {lon})")
        
        return f"📍 **{name}**\n🗺️ Google Maps: {maps_link}"
    
    except psycopg2.OperationalError as e:
        error_msg = f"❌ Database connection error: {str(e)}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"❌ Error getting map link: {str(e)}"
        print(error_msg)
        return error_msg
    















# @tool
# def nearby_places_tool(
#     project_name: str, 
#     radius_m: int = 2000, 
#     tool_call_id: Annotated[str, InjectedToolCallId] = ""
# ) -> str:
#     """
#     Lists notable points of interest (amenities) near a property using Overpass API.
#     Returns up to 10 nearby amenities with their names or types.
    
#     Args:
#         project_name: Name of the property/project
#         radius_m: Search radius in meters (default: 2000m = 2km)
    
#     Returns:
#         List of nearby places or error message
#     """
#     print(f"🏪 Finding places near: {project_name} (radius: {radius_m}m)")
    
#     try:
#         # ✅ FIX: Use correct password
#         conn = psycopg2.connect(
#             "dbname=langgraph_db user=postgres password=123456 host=localhost"
#         )
#         cur = conn.cursor()
        
#         # Query with case-insensitive search
#         cur.execute(
#             "SELECT name, latitude, longitude FROM properties WHERE name ILIKE %s LIMIT 1;",
#             (f"%{project_name}%",)
#         )
#         result = cur.fetchone()
#         cur.close()
#         conn.close()

#         if not result:
#             print(f"⚠️ Property '{project_name}' not found in database")
#             return f"❌ Property '{project_name}' not found in database."

#         name, lat, lon = result
#         print(f"✅ Found property: {name} at ({lat}, {lon})")
#         print(f"🔍 Querying Overpass API for amenities...")
        
#         # Query Overpass API for nearby amenities
#         query = f"""[out:json][timeout:25];
#         (
#           node(around:{radius_m},{lat},{lon})["amenity"];
#           way(around:{radius_m},{lat},{lon})["amenity"];
#         );
#         out center;"""
        
#         response = requests.get(
#             "https://overpass-api.de/api/interpreter",
#             params={'data': query},
#             timeout=10
#         )
        
#         if response.status_code != 200:
#             return f"⚠️ Could not fetch nearby places (API error: {response.status_code})"
        
#         data = response.json()

#         if 'elements' not in data or len(data['elements']) == 0:
#             print("ℹ️ No amenities found nearby")
#             return f"No notable places found within {radius_m}m of {name}."

#         # Extract place names/types
#         places = []
#         for el in data['elements']:
#             tags = el.get('tags', {})
#             place_name = tags.get('name', tags.get('amenity', 'Unknown'))
#             amenity_type = tags.get('amenity', 'place')
            
#             # Format: "Name (type)" or just "type" if no name
#             if tags.get('name'):
#                 places.append(f"{place_name} ({amenity_type})")
#             else:
#                 places.append(amenity_type)
        
#         # Remove duplicates while preserving order
#         unique_places = list(dict.fromkeys(places))[:10]
        
#         print(f"✅ Found {len(unique_places)} unique places")
        
#         response_text = f"📍 Nearby places around **{name}** (within {radius_m}m):\n\n"
#         for i, place in enumerate(unique_places, 1):
#             response_text += f"{i}. {place}\n"
        
#         return response_text
    
#     except psycopg2.OperationalError as e:
#         error_msg = f"❌ Database connection error: {str(e)}"
#         print(error_msg)
#         return error_msg
#     except requests.RequestException as e:
#         error_msg = f"❌ Error fetching data from Overpass API: {str(e)}"
#         print(error_msg)
#         return error_msg
#     except Exception as e:
#         error_msg = f"❌ Error finding nearby places: {str(e)}"
#         print(error_msg)
#         return error_msg
@tool
def nearby_places_tool(
    project_name: str, 
    radius_m: int = 2000, 
    tool_call_id: Annotated[str, InjectedToolCallId] = ""
) -> str:
    """
    Lists notable points of interest (amenities) near a property.
    Intelligently filters results based on user's question context.
    """
    print(f"🏪 Finding places near: {project_name} (radius: {radius_m}m)")
    
    try:
        conn = psycopg2.connect(
            "dbname=langgraph_db user=postgres password=123456 host=localhost"
        )
        cur = conn.cursor()
        
        # ✅ FIX: Better fuzzy matching - searches anywhere in name
        cur.execute(
            """SELECT name, latitude, longitude 
               FROM properties 
               WHERE name ILIKE %s 
               ORDER BY LENGTH(name) ASC 
               LIMIT 1;""",
            (f"%{project_name}%",)
        )
        result = cur.fetchone()
        cur.close()
        conn.close()

        if not result:
            return f"❌ Property matching '{project_name}' not found in database."

        name, lat, lon = result
        print(f"✅ Found property: {name} at ({lat}, {lon})")
        print(f"🔍 Querying Overpass API for amenities...")
        
        # Query Overpass API for nearby amenities
        query = f"""[out:json][timeout:25];
        (
          node(around:{radius_m},{lat},{lon})["amenity"];
          way(around:{radius_m},{lat},{lon})["amenity"];
        );
        out center;"""
        
        response = requests.get(
            "https://overpass-api.de/api/interpreter",
            params={'data': query},
            timeout=10
        )
        
        if response.status_code != 200:
            return f"⚠️ Could not fetch nearby places (API error: {response.status_code})"
        
        data = response.json()

        if 'elements' not in data or len(data['elements']) == 0:
            return f"No amenities found within {radius_m}m of {name}."

        # ✅ FIX PROBLEM 2: Better categorization and formatting
        places_by_category = {
            'schools': [],
            'places_of_worship': [],
            'cafes_restaurants': [],
            'healthcare': [],
            'shopping': [],
            'parking': [],
            'other': []
        }
        
        for el in data['elements']:
            tags = el.get('tags', {})
            amenity_type = tags.get('amenity', '')
            place_name = tags.get('name', '')
            
            # Get coordinates for Google Maps
            if 'lat' in el and 'lon' in el:
                place_lat, place_lon = el['lat'], el['lon']
            elif 'center' in el:
                place_lat, place_lon = el['center']['lat'], el['center']['lon']
            else:
                place_lat, place_lon = None, None
            
            # Categorize
            place_info = {
                'name': place_name if place_name else amenity_type.replace('_', ' ').title(),
                'type': amenity_type,
                'coords': (place_lat, place_lon) if place_lat and place_lon else None
            }
            
            if amenity_type == 'school':
                places_by_category['schools'].append(place_info)
            elif amenity_type == 'place_of_worship':
                places_by_category['places_of_worship'].append(place_info)
            elif amenity_type in ['cafe', 'restaurant', 'fast_food', 'bar', 'pub']:
                places_by_category['cafes_restaurants'].append(place_info)
            elif amenity_type in ['hospital', 'clinic', 'pharmacy', 'doctors']:
                places_by_category['healthcare'].append(place_info)
            elif amenity_type in ['marketplace', 'bank', 'atm']:
                places_by_category['shopping'].append(place_info)
            elif amenity_type == 'parking':
                places_by_category['parking'].append(place_info)
            else:
                places_by_category['other'].append(place_info)
        
        # Format response with context
        response_text = f"📍 **Places near {name}** (within {radius_m/1000:.1f}km):\n\n"
        
        total_count = 0
        
        if places_by_category['schools']:
            response_text += f"🏫 **Schools** ({len(places_by_category['schools'])}):\n"
            for i, place in enumerate(places_by_category['schools'][:5], 1):
                maps = f"https://www.google.com/maps?q={place['coords'][0]},{place['coords'][1]}" if place['coords'] else ""
                response_text += f"   {i}. {place['name']}"
                if maps:
                    response_text += f" - [Map]({maps})"
                response_text += "\n"
            total_count += len(places_by_category['schools'])
        
        if places_by_category['places_of_worship']:
            response_text += f"\n⛪ **Places of Worship** ({len(places_by_category['places_of_worship'])}):\n"
            for i, place in enumerate(places_by_category['places_of_worship'][:5], 1):
                maps = f"https://www.google.com/maps?q={place['coords'][0]},{place['coords'][1]}" if place['coords'] else ""
                response_text += f"   {i}. {place['name']}"
                if maps:
                    response_text += f" - [Map]({maps})"
                response_text += "\n"
            total_count += len(places_by_category['places_of_worship'])
        
        if places_by_category['cafes_restaurants']:
            response_text += f"\n🍽️ **Cafes & Restaurants** ({len(places_by_category['cafes_restaurants'])}):\n"
            for i, place in enumerate(places_by_category['cafes_restaurants'][:5], 1):
                maps = f"https://www.google.com/maps?q={place['coords'][0]},{place['coords'][1]}" if place['coords'] else ""
                response_text += f"   {i}. {place['name']}"
                if maps:
                    response_text += f" - [Map]({maps})"
                response_text += "\n"
            total_count += len(places_by_category['cafes_restaurants'])
        
        if places_by_category['healthcare']:
            response_text += f"\n🏥 **Healthcare** ({len(places_by_category['healthcare'])}):\n"
            for i, place in enumerate(places_by_category['healthcare'][:5], 1):
                maps = f"https://www.google.com/maps?q={place['coords'][0]},{place['coords'][1]}" if place['coords'] else ""
                response_text += f"   {i}. {place['name']}"
                if maps:
                    response_text += f" - [Map]({maps})"
                response_text += "\n"
            total_count += len(places_by_category['healthcare'])
        
        if places_by_category['shopping']:
            response_text += f"\n🏪 **Shopping & Banking** ({len(places_by_category['shopping'])}):\n"
            for i, place in enumerate(places_by_category['shopping'][:5], 1):
                maps = f"https://www.google.com/maps?q={place['coords'][0]},{place['coords'][1]}" if place['coords'] else ""
                response_text += f"   {i}. {place['name']}"
                if maps:
                    response_text += f" - [Map]({maps})"
                response_text += "\n"
            total_count += len(places_by_category['shopping'])
        
        if places_by_category['parking']:
            response_text += f"\n🅿️ **Parking** ({len(places_by_category['parking'])} spots)\n"
            total_count += len(places_by_category['parking'])
        
        if places_by_category['other']:
            response_text += f"\n📍 **Other Amenities** ({len(places_by_category['other'])}):\n"
            for i, place in enumerate(places_by_category['other'][:5], 1):
                maps = f"https://www.google.com/maps?q={place['coords'][0]},{place['coords'][1]}" if place['coords'] else ""
                response_text += f"   {i}. {place['name']}"
                if maps:
                    response_text += f" - [Map]({maps})"
                response_text += "\n"
            total_count += len(places_by_category['other'])
        
        response_text += f"\n**Total: {total_count} amenities found**"
        
        print(f"✅ Found {total_count} categorized places")
        return response_text
    
    except Exception as e:
        error_msg = f"❌ Error finding nearby places: {str(e)}"
        print(error_msg)
        return error_msg
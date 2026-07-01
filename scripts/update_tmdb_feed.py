import requests
import os
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

def get_rated_movies(auth_token, account_id):
    """Fetch rated movies from TMDB API v4"""
    base_url = "https://api.themoviedb.org/4"
    url = f"{base_url}/account/{account_id}/movie/rated"
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    
    params = {
        "page": 1,
        "sort_by": "created_at.desc"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []
    
    data = response.json()
    return data.get("results", [])

def get_rating_color(rating):
    if rating >= 7:
        return "#2ecc71" # Green
    elif rating >= 5:
        return "#f1c40f" # Yellow/Orange
    else:
        return "#e74c3c" # Red

def generate_rss_feed(movies, output_file="feeds/feed.xml"):
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    
    ET.SubElement(channel, 'title').text = "Divinelink's Ratings"
    ET.SubElement(channel, 'link').text = "https://www.themoviedb.org/"
    ET.SubElement(channel, 'description').text = "Latest movie ratings from Divinelink on TMDB"
    ET.SubElement(channel, 'language').text = "en-us"
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    
    for movie in movies:
        item = ET.SubElement(channel, 'item')
        
        title = movie.get('title', 'Unknown')
        movie_id = movie.get('id', '')
        link = f"https://www.themoviedb.org/movie/{movie_id}"
        
        ET.SubElement(item, 'title').text = title
        ET.SubElement(item, 'link').text = link
        
        # --- Parsing Logic ---
        account_rating = movie.get('account_rating', {})
        
        raw_value = account_rating.get('value', 0)
        try:
            rating = int(float(raw_value))
        except (ValueError, TypeError):
            rating = 0
            
        rated_at_str = account_rating.get('created_at')
        
        overview = movie.get('overview', 'No description available')
        release_date = movie.get('release_date', 'Unknown')
        poster_path = movie.get('poster_path')
        
        poster_url = ""
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        
        color = get_rating_color(rating)
        
        if overview:
            overview = overview.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
        # Build HTML Description with Colored Star
        # Using a span with color on the star character is more reliable than background-color
        description_html = f"""
        <div style="font-family: sans-serif; max-width: 600px;">
            <p style="margin-bottom: 10px;">
                <span style="color: {color}; font-size: 1.5em; font-weight: bold;">★</span> 
                <span style="font-size: 1.2em; font-weight: bold; color: #333;">{rating}/10</span>
                <br/>
                <small style="color: #666;">Release Date: {release_date}</small>
            </p>
        """
        
        if poster_url:
            description_html += f'<img src="{poster_url}" alt="{title}" style="max-width: 200px; border-radius: 5px; margin-top: 10px; display: block;" /><br/>'
            
        description_html += f"<p style='color: #444; line-height: 1.5;'>{overview}</p></div>"
        
        ET.SubElement(item, 'description').text = description_html
        
        if poster_url:
            enclosure = ET.SubElement(item, 'enclosure')
            enclosure.set('url', poster_url)
            enclosure.set('type', 'image/jpeg')
        
        pub_date_text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        if rated_at_str:
            try:
                dt = datetime.fromisoformat(rated_at_str.replace('Z', '+00:00'))
                pub_date_text = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
            except Exception:
                pass
                
        ET.SubElement(item, 'pubDate').text = pub_date_text
        ET.SubElement(item, 'guid').text = link
    
    xml_str = ET.tostring(rss, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding='UTF-8')
    
    with open(output_file, 'wb') as f:
        f.write(pretty_xml)
    
    print(f"RSS feed generated successfully with {len(movies)} movies!")

def main():
    auth_token = os.environ.get('TMDB_AUTH_TOKEN')
    account_id = os.environ.get('TMDB_ACCOUNT_ID')
    
    if not auth_token or not account_id:
        print("Error: TMDB_AUTH_TOKEN and TMDB_ACCOUNT_ID are required")
        exit(1)
    
    print("Fetching rated movies from TMDB V4...")
    movies = get_rated_movies(auth_token, account_id)
    
    if not movies:
        print("No rated movies found or error occurred")
        exit(1)
    
    print(f"Found {len(movies)} rated movies")
    print("Generating RSS feed...")
    generate_rss_feed(movies)

if __name__ == "__main__":
    main()
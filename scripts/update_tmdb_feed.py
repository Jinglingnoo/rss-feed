import requests
import os
from datetime import datetime
from xml.dom import minidom
from lxml import etree as ET
from lxml.etree import CDATA
import xml.dom.minidom as minidom

def get_rated_movies(auth_token, account_id):
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

def generate_rss_feed(movies, output_file="../feeds/feed.xml"):
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    
    ET.SubElement(channel, 'title').text = "Divinelink's Ratings"
    ET.SubElement(channel, 'link').text = "https://www.themoviedb.org/"
    ET.SubElement(channel, 'description').text = "Latest movie ratings from Divinelink"
    ET.SubElement(channel, 'language').text = "en-us"
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    
    for movie in movies:
        item = ET.SubElement(channel, 'item')
        title = movie.get('title', 'Unknown')
        movie_id = movie.get('id', '')
        year = movie.get('release_date', '').split('-')[0] if movie.get('release_date') else ''
        link = f"https://www.themoviedb.org/movie/{movie_id}"
        
        account_rating = movie.get('account_rating', {})
        
        raw_value = account_rating.get('value', 0)
        try:
            rating = float(raw_value)
        except (ValueError, TypeError):
            rating = 0
            
        # Convert rating to stars display
        full_stars = int(rating // 2)
        half_star = 1 if (rating % 2) >= 1 else 0
        empty_stars = 5 - full_stars - half_star
        stars_display = '★' * full_stars + ('½' if half_star else '') + '☆' * empty_stars
        
        rated_at_str = account_rating.get('created_at')
        
        overview = movie.get('overview', 'No description available')
        release_date = movie.get('release_date', 'Unknown')
        poster_path = movie.get('poster_path')
        
        poster_url = ""
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        
        # Format title as: "Title, Year - Stars"
        item_title = f"{title}, {year} - {stars_display}" if year else f"{title} - {stars_display}"
        
        ET.SubElement(item, 'title').text = item_title
        ET.SubElement(item, 'link').text = link
        
        # Build HTML Description with CDATA
        description_html = ""
        if poster_url:
            description_html += f'<img src="{poster_url}" alt="{title}" />\n'
        
        if overview and overview != 'No description available':
            description_html += f'<p>{overview}</p>\n'
        
        watched_date = rated_at_str.split('T')[0] if rated_at_str else 'Unknown'
        description_html += f'<p>Watched on {watched_date}.</p>'
        
        desc_elem = ET.SubElement(item, 'description')
        desc_elem.text = CDATA(description_html)
        
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
        
        # Generate unique GUID
        guid = ET.SubElement(item, 'guid')
        guid.set('isPermaLink', 'false')
        guid.text = f"tmdb-rating-{movie_id}-{rated_at_str or ''}"
    
    xml_str = ET.tostring(rss, encoding='UTF-8', pretty_print=True, xml_declaration=True)
    
    with open(output_file, 'wb') as f:
        f.write(xml_str)
    
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
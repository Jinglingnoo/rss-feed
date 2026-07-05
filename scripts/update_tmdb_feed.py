import requests
import os
import const
import yaml
from datetime import datetime, timezone
from xml.dom import minidom
from lxml import etree as ET
from lxml.etree import CDATA
import xml.dom.minidom as minidom
from pathlib import Path

from models import RssItem, ItemType
from const import _tmdbPosterPath, _tmdbBaseV4Url

OUTPUT_FILE = "../feeds/feed.xml"
CONFIG_PATH = "config.yaml"
TMDB_SECTION_KEY = "tmdb_sections"

def _get_account_movies(endpoint, auth_token, account_id):
    base_url = const._tmdbBaseV4Url 
    url = f"{base_url}/account/{account_id}/movie/{endpoint}"
    
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

def _format_stars(value):
    try:
        rating = float(value)
    except (ValueError, TypeError):
        rating = 0
    full = int(rating // 2)
    half = 1 if (rating % 2) >= 1 else 0
    empty = 5 - full - half
    return '★' * full + ('½' if half else '') + '☆' * empty


def _build_item(movie, item_type: ItemType, user):
    title = movie.get('title', 'Unknown')
    mid = movie.get('id', '')
    year = movie.get('release_date', '').split('-')[0] if movie.get('release_date') else ''
    link = f"https://www.themoviedb.org/movie/{mid}"

    poster_path = movie.get('poster_path')
    poster_url = f"{_tmdbPosterPath}{poster_path}" if poster_path else ""

    if item_type == ItemType.RATED:
        ar = movie.get('account_rating', {})
        stars = _format_stars(ar.get('value', 0))
        date_str = ar.get('created_at')
        extra = f"Watched on {date_str.split('T')[0] if date_str else 'Unknown'}."
        item_title = f"{title}, {year} - {stars}" if year else f"{title} - {stars}"
        guid_text = f"tmdb-{item_type.value}-{mid}-{date_str or ''}"
    elif item_type == ItemType.WATCHLIST:
        date_str = datetime.now(timezone.utc).isoformat()
        extra = f"Added to watchlist from {user}."
        item_title = f"{user} added to watchlist: {title}, {year}" if year else title
        guid_text = f"tmdb-{item_type.value}-{mid}-{user}"
    elif item_type == ItemType.FAVORITES:
        date_str = datetime.now(timezone.utc).isoformat()
        extra = f"Added to favorites from {user}."
        item_title = f"{user} added to favorites: {title}, {year}" if year else title
        guid_text = f"tmdb-{item_type.value}-{mid}-{user}"

    desc_html = ""
    if poster_url:
        desc_html += f'<img src="{poster_url}" alt="{title}" />\n'
    overview = movie.get('overview', '')
    if overview:
        desc_html += f'<p>{overview}</p>\n'
    desc_html += f'<p>{extra}</p>'

    return RssItem(
        type=item_type,
        title=item_title,
        link=link,
        description_html=desc_html,
        pub_date_str=date_str,
        guid_text=guid_text,
        poster_url=poster_url
    )


def _parse_date(date_str):
    if not date_str:
        return datetime.min.replace(tzinfo=timezone.utc)
    
    try:
        clean_str = date_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(clean_str)
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            
        return dt
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)

def load_config():
    config_path = Path(__file__).parent / CONFIG_PATH
    defaults = {TMDB_SECTION_KEY: ["rated"]}
    if not config_path.exists():
        return defaults
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if not config or TMDB_SECTION_KEY not in config:
                return defaults
            sections = config[TMDB_SECTION_KEY]
            if not sections:
                return defaults
            return config
    except Exception as e:
        print(f"Warning: Could not load config: {e}. Using defaults.")
        return defaults

def generate_feed(user, auth_token, account_id):
    print(f"Fetching data from TMDB for {user}...")
    config = load_config()
    sections = config[TMDB_SECTION_KEY]
    
    movies = {}
    for section in sections:
        movies[section] = _get_account_movies(section, auth_token, account_id)

    items = []
    for section in sections:
        for m in movies.get(section, []):
            if section == "rated":
                d = m.get('account_rating', {}).get('created_at')
                date = _parse_date(d)
                item_type = ItemType.RATED
            elif section == "watchlist":
                date = datetime.now(timezone.utc)
                item_type = ItemType.WATCHLIST
            elif section == "favorites":
                date = datetime.now(timezone.utc)
                item_type = ItemType.FAVORITES
            else:
                continue  # Skip unknown sections
        
            items.append((date, _build_item(m, item_type, user)))

    items.sort(key=lambda x: x[0], reverse=True)
    print(f"Processing {len(items)} items...")

    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = f"{user}'s Movie Feed"
    ET.SubElement(channel, 'link').text = "https://www.themoviedb.org/"
    ET.SubElement(channel, 'description').text = f"{user}'s Activity"
    ET.SubElement(channel, 'language').text = "en-US"
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

    for _, item in items:
        elem = ET.SubElement(channel, 'item')
        ET.SubElement(elem, 'title').text = item.title
        ET.SubElement(elem, 'link').text = item.link
        desc = ET.SubElement(elem, 'description')
        desc.text = CDATA(item.description_html)

        pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        if item.pub_date_str:
            try:
                dt = datetime.fromisoformat(item.pub_date_str.replace('Z', '+00:00'))
                pub_date = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
            except Exception:
                pass
        ET.SubElement(elem, 'pubDate').text = pub_date

        if item.poster_url:
            enc = ET.SubElement(elem, 'enclosure')
            enc.set('url', item.poster_url)
            enc.set('type', 'image/jpeg')

        guid = ET.SubElement(elem, 'guid')
        guid.set('isPermaLink', 'false')
        guid.text = item.guid_text

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    xml_str = ET.tostring(rss, encoding='UTF-8', pretty_print=True, xml_declaration=True)
    with open(OUTPUT_FILE, 'wb') as f:
        f.write(xml_str)

    print(f"Done! Feed saved to {OUTPUT_FILE}")

if __name__ == "__main__":
   auth_token = os.environ.get('TMDB_AUTH_TOKEN')
   account_id = os.environ.get('TMDB_ACCOUNT_ID')
   generate_feed("Divinelink", auth_token, account_id)    
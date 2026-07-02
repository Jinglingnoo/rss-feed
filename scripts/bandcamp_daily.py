import requests
import const
from bs4 import BeautifulSoup
from datetime import datetime
import os
import re

URL = const._bandcampDailyUrl
HEADERS = const._bandcampUserAgent

def load_template():
    with open("item.rss", "r", encoding="utf-8") as f:
        return f.read()

def fetch_articles():
    response = requests.get(URL, headers=HEADERS, timeout=15)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    
    # Target the main content area
    post_list = soup.select_one(".post-list, .content-area, main")
    if not post_list:
        post_list = soup
        
    # Find all article links
    links = post_list.select("a[href*='/features/'], a[href*='/lists/'], a[href*='/album-of-the-day/'], a[href*='/best-'], a[href*='/prog-is'], a[href*='/tape-label'], a[href*='/scene-report'], a[href*='/the-side-door'], a[href*='/essential-releases']")
    
    seen_links = set()
    
    for link in links:
        href = link["href"]
        if href in seen_links or not href.startswith("/"):
            continue
            
        if not href.startswith("http"):
            href = f"https://daily.bandcamp.com{href}"
            
        seen_links.add(href)
        
        title = link.get_text(strip=True)
        if not title:
            continue
            
        # Find the parent container to get date and image
        # We go up a few levels to ensure we catch the whole article block
        parent = link.find_parent(["div", "li", "article"])
        if parent:
            parent = parent.find_parent(["div", "li", "article"]) # Go up one more level for safety
        description = title
        pub_date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
        icon = ""
        
        if parent:
            # Extract Date
            text_content = parent.get_text()
            date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2},\s\d{4}', text_content)
            if date_match:
                try:
                    parsed_date = datetime.strptime(date_match.group(0), "%B %d, %Y")
                    pub_date = parsed_date.strftime("%a, %d %b %Y %H:%M:%S +0000")
                except ValueError:
                    pass
            
            # Extract Icon/Image
            # Look for any img tag within the parent container
            img_tag = parent.select_one("img")
            if img_tag:
                # Check data-src first (common for lazy loading), then src
                src = img_tag.get("data-src") or img_tag.get("src")
                
                if src:
                    # Handle protocol-relative URLs (//example.com/image.jpg)
                    if src.startswith("//"):
                        src = "https:" + src
                    # Handle relative URLs (/images/image.jpg)
                    elif src.startswith("/"):
                        src = f"https://daily.bandcamp.com{src}"
                    
                    # Ensure it looks like an image URL
                    if "f4.bcbits.com" in src or ".jpg" in src or ".png" in src:
                        icon = src

        articles.append({
            "title": title,
            "item_link": href,
            "guid": href,
            "links": description,
            "date": pub_date,
            "icon": icon
        })
    
    return articles

def generate_feed(articles, output_file="../feeds/bandcamp_daily.xml"):
    template = load_template()
    items_xml = ""
    
    for article in articles:
         # Build icon HTML only if icon exists
        icon = article.get("icon", "")
        if icon:
            article["icon_html"] = f'<img src="{icon}" style="max-width: 100%; height: auto; display: block; margin-bottom: 10px;" /><br />'
        else:
            article["icon_html"] = ""

        item_content = template
        for key, value in article.items():
            item_content = item_content.replace(f"{{{{{key}}}}}", str(value))
        items_xml += item_content + "\n"

    now = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    full_rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Bandcamp Daily Latest</title>
    <link>{URL}</link>
    <description>Bandcamp Daily</description>
    <lastBuildDate>{now}</lastBuildDate>
    {items_xml}
  </channel>
</rss>"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_rss)
    
    print(f"RSS feed generated: {output_file} ({len(articles)} items)")

if __name__ == "__main__":
    articles = fetch_articles()
    if articles:
        generate_feed(articles)
    else:
        print("No articles found.")
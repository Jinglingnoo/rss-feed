import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime

url = 'https://www.athinorama.gr/cinema/guide/nees_tainies/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

response = requests.get(url, headers=headers)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'html.parser')

fg = FeedGenerator()
fg.title('Athinorama - Νέες Ταινίες')
fg.link(href=url, rel='alternate')
fg.description('Εβδομαδιαίες νέες κυκλοφορίες ταινιών από το athinorama.gr')
fg.language('el')

movies = soup.find_all('h2')

for movie in movies:
    link_tag = movie.find('a')
    if not link_tag or '/cinema/movie/' not in link_tag.get('href', ''):
        continue
        
    title_gr = link_tag.text.strip()
    href = link_tag['href']
    link = f"https://www.athinorama.gr{href}" if href.startswith('/') else href
    
    parent = movie.parent
    synopsis_p = parent.find('p')
    synopsis = synopsis_p.text.strip() if synopsis_p else ""

    tags_div = parent.find('div', class_='tags')
    tags_items = tags_div.find_all('li') if tags_div else []
    
    category = tags_items[0].text.strip() if len(tags_items) > 0 else "Άγνωστο"
    year = tags_items[1].text.strip() if len(tags_items) > 1 else ""
        
    fe = fg.add_entry()
    fe.title(f"{title_gr} | ({year}) - {category}")
    fe.link(href=link)
    fe.description(synopsis)
    fe.category([
        {'term': category},
        {'term': str(year)}
    ])
    fe.guid(link, permalink=True)
    fe.pubDate(datetime.now().astimezone())

fg.rss_file('feeds/athinorama_feed.xml')
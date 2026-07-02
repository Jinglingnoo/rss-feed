import datetime
import const
import random
import email.utils

_process = "rss_aggregator.py"
_user = "unknown user..."
_prefix = f"[{_process}:{_user}]:"

def get_rfc822_date(dt):
    return email.utils.format_datetime(dt)

def extract_item_name_from_url(url):
    try:
        # Split by / and take the last part
        path = url.split("/")[-1]
        # Replace hyphens with spaces and capitalize
        name = path.replace("-", " ").title()
        return name
    except:
        return "Unknown Item"

def createItem(parser, date, link, user):
    item = open("./item.rss").read()
    
    # Extract artist name from URL
    try:
        artist_name = link.split("//")[1].split(".bandcamp.com")[0]
    except:
        artist_name = user

    # Extract item name from URL path
    item_name = extract_item_name_from_url(link)

    # Determine Title based on parser type
    if parser == "following":
        title = f"New follow: {artist_name} (from <b>{user}</b>)"
    elif parser == "release":
        title = f"New release: {item_name}"
    elif parser == "collection":
        title = f"<b>{user}</b> added to collection: {item_name}"
    elif parser == "wishlist":
        title = f"<b>{user}</b> added to wishlist: {item_name}"
    else:
        title = f"{parser.capitalize()} update for <b>{user}</b>"

    rfc_date = get_rfc822_date(date)

    item = item.replace(const._title, title)
    item = item.replace(const._item_link, link)
    item = item.replace(const._guid, f"{parser}-{date.strftime('%Y%m%d%H%M%S')}-{user}-{hash(link)}")
    item = item.replace(const._links, f'<a href="{link}">{link}</a>')
    item = item.replace(const._date, rfc_date)

    print(f"{_prefix} Created item: {title}")
    return item

def run(user, parsers):
    _user = user
    _prefix = f"[{_process}:{_user}]:"
    items = []
    for parser in parsers:
        ssf = open(f"{const._ssf_path}/{parser}_{_user}.ssf")
        ssfLinks = ssf.read().splitlines()
        newSsfLinks = []
        for link in ssfLinks:
            if link.startswith(const._newIndicator):
                newSsfLinks.append(link.replace(const._newIndicator, ""))
        
        if len(newSsfLinks) > 0:
            print(f"{_prefix} Found {len(newSsfLinks)} new items for {parser}")
            for link in newSsfLinks:
                items.append(createItem(parser, datetime.datetime.now(), link, _user))

    if len(items) > 0:
        print(f"{_prefix} updating items.rss with {len(items)} updates for this user")
        itemsrss = open("./items.rss", "a", -1, "utf-8")
        itemsrss.write("\n".join(items))
        itemsrss.write("\n")
        itemsrss.close()
        return True
    else:
        print(f"{_prefix} No updates detected for this user")    
        print(f"{_prefix} Exited successfully")
        return False
    
def createBandcampFridayItem(guidPrefix, date):
    item = open("./item.rss").read()
    gif = const._bandcampFridayGifs[random.randint(0, 2)]
    rfc_date = get_rfc822_date(date)
    
    item = item.replace(const._title, f"<b>It's Bandcamp Friday!</b>")
    item = item.replace(const._item_link, "https://bandcamp.com")
    item = item.replace(const._guid, f"{guidPrefix}-{date.strftime('%Y%m%d%H%M%S')}")
    item = item.replace(const._links, gif)
    item = item.replace(const._date, rfc_date)

    print(f"{_prefix} Created item Bandcamp Friday")
    return item

def addBandcampFridayItem():
    print(f"{_prefix} updating items.rss with bandcamp friday notification")
    itemsrss = open("./items.rss", "a", -1, "utf-8")
    itemsrss.write(createBandcampFridayItem("bandcamp-friday", datetime.datetime.now()))
    itemsrss.write("\n")
    itemsrss.close()
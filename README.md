# rss-feed
Various RSS feeds to share with friends.

## TMDB RSS Feed

Generates an RSS feed from your TMDB account activity.

### Configuration

Edit [`config.yaml`](/scripts/config.yaml) to customize which account sections are included in the feed.

#### Available Options

- `rated` - Movies you've rated
- `watchlist` - Movies on your watchlist
- `favorites` - Your favorite movies

#### Example

```yaml
tmdb_sections:
  - rated
  - watchlist
  # - favorites  # Comment out or delete to disable
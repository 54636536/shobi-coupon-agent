import os
import re
import requests
import feedparser
from datetime import datetime, timedelta, timezone

# Für YouTube später (auskommentiert, bis du den Key hast):
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError

# ---------- EINSTELLUNGEN ----------
# Später, wenn der YouTube-Key da ist, hier eintragen:
# YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', '')
BARK_DEVICE_KEY = os.environ['BARK_DEVICE_KEY']

CODE_PATTERN = re.compile(r'\b(SHOBI\d+|[A-Z]{3,6}\d{1,2}|LOVE\d+|DUFT\d+)\b', re.IGNORECASE)
CONTEXT_WORDS = ['shobi', 'parfum', 'gutschein', 'rabatt', 'coupon', 'code']

SENT_FILE = 'sent_codes.txt'
# ---------- ENDE EINSTELLUNGEN ----------

def load_sent_codes():
    try:
        with open(SENT_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_sent_codes(codes):
    with open(SENT_FILE, 'w') as f:
        for code in sorted(codes):
            f.write(code + '\n')

def send_push(code, source, snippet):
    title = f"Neuer Shobi Code: {code}"
    message = f"Quelle: {source}\n\n{snippet[:200]}"
    url = f"https://api.day.app/{BARK_DEVICE_KEY}/{title}/{message}"
    try:
        requests.get(url)
        print(f"Push gesendet: {code}")
    except Exception as e:
        print(f"Fehler beim Senden: {e}")

def check_rss_feed(name, url, sent_codes):
    """Durchsucht einen RSS-Feed nach neuen Shobi-Codes."""
    print(f"Suche auf {name}...")
    feed = feedparser.parse(url)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    for entry in feed.entries:
        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        if published < cutoff:
            continue
        full_text = entry.title + ' ' + (entry.summary or '')
        matches = CODE_PATTERN.findall(full_text)
        if any(w in full_text.lower() for w in CONTEXT_WORDS):
            for code in matches:
                if code not in sent_codes:
                    send_push(code, name, entry.title)
                    sent_codes.add(code)

# ----- YouTube (später aktivieren, sobald Key da ist) -----
# def check_youtube(sent_codes):
#     if not YOUTUBE_API_KEY:
#         print("YouTube: Kein API-Key gesetzt – überspringe.")
#         return
#     print("Suche auf YouTube...")
#     youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
#     now = datetime.now(timezone.utc)
#     yesterday = (now - timedelta(hours=24)).isoformat() + 'Z'
#
#     try:
#         request = youtube.search().list(
#             q='Shobi Parfumery Coupon OR Gutschein',
#             part='snippet',
#             order='date',
#             maxResults=10,
#             type='video',
#             publishedAfter=yesterday
#         )
#         response = request.execute()
#
#         for item in response.get('items', []):
#             title = item['snippet']['title']
#             description = item['snippet']['description']
#             full_text = title + ' ' + description
#             matches = CODE_PATTERN.findall(full_text)
#             if any(w in full_text.lower() for w in CONTEXT_WORDS):
#                 for code in matches:
#                     if code not in sent_codes:
#                         send_push(code, 'YouTube', full_text)
#                         sent_codes.add(code)
#     except HttpError as e:
#         print(f"YouTube-Fehler: {e}")

if __name__ == '__main__':
    sent = load_sent_codes()
    initial_count = len(sent)

    # Aktive Quellen
    check_rss_feed('mydealz', 'https://www.mydealz.de/feed/search/shobi', sent)
    check_rss_feed('hotukdeals', 'https://www.hotukdeals.com/feed/search/shobi', sent)

    # YouTube später hier entkommentieren:
    # check_youtube(sent)

    if len(sent) > initial_count:
        save_sent_codes(sent)
        print(f"{len(sent) - initial_count} neue Codes gespeichert.")
    else:
        print("Keine neuen Codes gefunden.")

from flask import Flask, send_file
from ics import Calendar, Event
from datetime import datetime
import pytz
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def scrape_wembley_events():
    url = "https://www.wembleystadium.com/events"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    events = []

    # Updated selector to match current website
    event_cards = soup.select(".event-list__item")

    print(f"Found {len(event_cards)} event cards on page.")

    for card in event_cards:
        try:
            title = card.select_one(".event-list__title").text.strip()
            date_str = card.select_one(".event-list__date").text.strip()
            link = card.find("a")["href"]
            link = f"https://www.wembleystadium.com{link}"

            print(f"Parsing event: {title} on {date_str}")

            # Try parsing date string
            dt = datetime.strptime(date_str, "%A %d %B %Y")
            london = pytz.timezone("Europe/London")
            dt = london.localize(dt.replace(hour=19))  # Assume 7 PM

            event = Event()
            event.name = title
            event.begin = dt
            event.duration = {"hours": 3}
            event.description = f"More info: {link}"
            event.location = "Wembley Stadium, London"

            events.append(event)

        except Exception as e:
            print(f"Scraping error: {e}")
            continue

    return events

def generate_calendar():
    cal = Calendar()
    events = scrape_wembley_events()

    print(f"Generating calendar with {len(events)} events.")

    if not events:
        print("⚠️ No events found — double check website or selectors.")

        # Optional: Add a dummy event so .ics isn't empty
        london = pytz.timezone("Europe/London")
        dt = london.localize(datetime.now().replace(hour=19, minute=0))
        dummy = Event()
        dummy.name = "No upcoming events found"
        dummy.begin = dt
        dummy.duration = {"hours": 1}
        dummy.description = "Check back later."
        dummy.location = "Wembley Stadium"
        cal.events.add(dummy)
    else:
        for e in events:
            cal.events.add(e)

    with open("wembley.ics", "w") as f:
        f.writelines(cal)

@app.route("/")
def index():
    return "✅ Wembley Stadium Calendar is live. Visit /calendar.ics to download or subscribe."

@app.route("/calendar.ics")
def serve_calendar():
    generate_calendar()  # Always refresh on request
    return send_file("wembley.ics", as_attachment=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

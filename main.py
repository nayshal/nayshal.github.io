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
    cards = soup.select(".event-list__item")

    for card in cards:
        try:
            title = card.select_one(".event-list__title").text.strip()
            date_str = card.select_one(".event-list__date").text.strip()
            link = card.find("a")["href"]
            dt = datetime.strptime(date_str, "%A %d %B %Y")
            london = pytz.timezone("Europe/London")
            dt = london.localize(dt.replace(hour=19))  # Assume 7 PM

            event = Event()
            event.name = title
            event.begin = dt
            event.duration = {"hours": 3}
            event.description = f"https://www.wembleystadium.com{link}"
            event.location = "Wembley Stadium, London"
            events.append(event)
        except Exception as e:
            print("Error:", e)
            continue

    return events

def generate_calendar():
    cal = Calendar()
    for e in scrape_wembley_events():
        cal.events.add(e)
    with open("wembley.ics", "w") as f:
        f.writelines(cal)

@app.route("/")
def index():
    return "Wembley Calendar is live. Go to /calendar.ics"

@app.route("/calendar.ics")
def serve_calendar():
    generate_calendar()  # Refresh on each request
    return send_file("wembley.ics", as_attachment=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

"""
This script checks for inactive Plex users and sends them an email notification if they have been inactive for a specified number of days.

Usage:
    - Ensure you have the required libraries installed: requests, schedule, smtplib, email, os.
    - Set the environment variables TAUTULLI_API_KEY, SENDER_EMAIL, and SENDER_PASSWORD with your Tautulli API key and email credentials.
    - Schedule this script to run periodically using a scheduler like cron or let it run continuously.

Configuration:
    - TAUTULLI_URL: URL to your Tautulli instance.
    - INACTIVITY_THRESHOLD_DAYS: Number of days of inactivity before a notification is sent.
    - SENDER_EMAIL: Email address used to send notifications.
    - SENDER_PASSWORD: Password for the sender email address.

Example cron job entry to run this script every day at 8:00 AM:
    0 8 * * * /usr/bin/python3 /path/to/useraccess.py

Functions:
    - get_tautulli_data(endpoint, params=None): Fetches data from Tautulli API.
    - check_inactive_users(): Checks for inactive users and sends notifications.
    - send_notification(username, user_email, days_inactive): Sends an email notification to inactive users.
    - main(): Main function to run the script.

"""

import schedule
import time
import smtplib
from email.mime.text import MIMEText
import os

# Configuration
TAUTULLI_URL = "http://your_tautulli_ip:8181/api/v2"
TAUTULLI_API_KEY = os.environ.get("TAUTULLI_API_KEY") #or load from a config file.
INACTIVITY_THRESHOLD_DAYS = 30
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

def get_tautulli_data(endpoint, params=None):
    params = params or {}
    params["apikey"] = TAUTULLI_API_KEY
    url = f"{TAUTULLI_URL}/{endpoint}"
    response = requests.get(url, params=params)
    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    return response.json()["response"]["data"]

def check_inactive_users():
    users = get_tautulli_data("get_users")
    for user in users:
        user_id = user["user_id"]
        username = user["username"]
        watch_history = get_tautulli_data("get_user_watch_history", {"user_id": user_id, "length": 1})
        if watch_history:
          last_watched = watch_history[0]["date"]
          import datetime
          last_watched_date = datetime.datetime.fromtimestamp(last_watched)
          days_since_last_watch = (datetime.datetime.now() - last_watched_date).days

          if days_since_last_watch > INACTIVITY_THRESHOLD_DAYS:
              send_notification(username, user["email"], days_since_last_watch)
        else:
            send_notification(username, user["email"], INACTIVITY_THRESHOLD_DAYS)

def send_notification(username, user_email, days_inactive):
    message = f"Hello {username},\n\nYou have been inactive on Plex for {days_inactive} days. If you do not use Plex soon, your access may be revoked.\n\nThank you."
    msg = MIMEText(message)
    msg["Subject"] = "Plex Inactivity Notice"
    msg["From"] = SENDER_EMAIL
    msg["To"] = user_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"Notification sent to {username} ({user_email})")
    except Exception as e:
        print(f"Error sending notification to {username} ({user_email}): {e}")

def main():
    check_inactive_users()

schedule.every().day.at("08:00").do(main) #runs the script every day at 8:00am.

if __name__ == "__main__":
    main() #run once when the script starts.
    while True:
        schedule.run_pending()
        time.sleep(60)
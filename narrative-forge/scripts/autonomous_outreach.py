import csv
import smtplib
import time
import os
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# --- CONFIG ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
# You will export these as environment variables before running:
# set SENDER_EMAIL=your_email@gmail.com
# set SENDER_APP_PASSWORD=your_app_password

def generate_pitch(name: str, platform: str) -> tuple[str, str]:
    subject = f"High-Margin AI Fulfillment for {platform} clients"
    
    first_name = name.split(" ")[0]
    
    body = f"""Hi {first_name},

I see you’re managing creators at {platform}. I have a local-first AI refinery that converts long-form archives into high-retention clip packs (20 hooks, 20 scripts, titles, and thumbnail prompts per video).

I don’t want to sell to your clients. I want to give you a fulfillment weapon. 

You sell the 'Refinery Pack' for $149 to your roster. You keep $75. I handle the compute and delivery. Zero manual work for either of us.

Interested in a free proof-pack for one of your videos to see the resonance?

Best,
The Refinery Operator"""

    return subject, body

def fire_outreach(csv_path: Path, sender_email: str, sender_pass: str):
    print(f"[*] Initiating Autonomous Outreach Node...")
    
    rows = []
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
            
    print(f"[*] Loaded {len(rows)} targets.")
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender_email, sender_pass)
        print("[*] SMTP Connection Secured.")
    except Exception as e:
        print(f"[🛑] SMTP Login Failed: {e}")
        return

    sent_count = 0
    for row in rows:
        if row['status'] == 'SENT':
            continue
            
        target_name = row['name']
        target_email = row['email']
        platform = row['platform']
        
        subject, body = generate_pitch(target_name, platform)
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = target_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            print(f"[>] Firing on target: {target_email} ({platform})...")
            server.send_message(msg)
            row['status'] = 'SENT'
            sent_count += 1
            # Rate limiting to avoid SMTP spam bans
            time.sleep(3)
        except Exception as e:
            print(f"  [!] Strike failed for {target_email}: {e}")

    server.quit()
    
    # Update state
    fieldnames = ['name', 'email', 'platform', 'reason', 'status']
    with open(csv_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"\n[💎] OUTREACH COMPLETE. {sent_count} rounds fired.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=Path("narrative-forge/outputs/distribution/distributors_email.csv"))
    args = parser.parse_args()

    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_APP_PASSWORD")

    if not sender or not password:
        print("[🛑] ERROR: SENDER_EMAIL and SENDER_APP_PASSWORD environment variables must be set.")
        print("Example (Windows):")
        print("  $env:SENDER_EMAIL='your@gmail.com'")
        print("  $env:SENDER_APP_PASSWORD='abcd efgh ijkl mnop'")
        exit(1)

    fire_outreach(args.csv, sender, password)

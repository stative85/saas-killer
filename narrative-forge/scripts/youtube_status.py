# youtube_status.py
import time
import argparse
import pickle
import os
from googleapiclient.discovery import build

def get_service(token_file):
    if not os.path.exists(token_file):
        print(f"[!] Error: Token file {token_file} missing. Authenticate first.")
        return None
    with open(token_file, "rb") as token:
        creds = pickle.load(token)
    return build("youtube", "v3", credentials=creds)

def poll_status(youtube, video_id):
    print(f"[*] Polling processing status for: {video_id}")
    
    while True:
        request = youtube.videos().list(
            part="processingDetails,status,snippet",
            id=video_id
        )
        response = request.execute()
        
        if not response["items"]:
            print("[!] Video not found.")
            break
            
        item = response["items"][0]
        proc = item.get("processingDetails", {})
        status = proc.get("processingStatus", "unknown")
        
        print(f"  [>] Current Status: {status}")
        
        if status in ["succeeded", "failed"]:
            print(f"[✅] Terminal State Reached: {status}")
            break
            
        time.sleep(30) # Poll every 30 seconds

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--token", default="configs/youtube_token.pickle")
    args = parser.parse_args()
    
    youtube = get_service(args.token)
    if youtube:
        poll_status(youtube, args.id)

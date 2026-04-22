import yt_dlp
import re
from pathlib import Path

def discover_reels(url, browser='firefox'):
    print(f"[*] Ninja infiltrating: {url}")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'cookiesfrombrowser': (browser,),
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    }
    
    reel_ids = set()
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # We use extract_info with download=False to get the page data
            # but we force the 'generic' extractor to avoid the 'Unsupported URL' block
            # or we just fetch the raw HTML if generic fails
            info = ydl.extract_info(url, download=False, process=False)
            
            # If that fails, we do a raw request using ydl's opener
            response = ydl.urlopen(url)
            html = response.read().decode('utf-8', errors='replace')
            
            # Regex to find reel IDs in various FB formats
            # Formats: /reels/123456789/, /watch/?v=123456789, "video_id":"123456789"
            patterns = [
                r'facebook\.com/reels/(\d+)',
                r'/reels/(\d+)',
                r'video_id":"(\d+)"',
                r'watch/\?v=(\d+)',
                r'fb\.watch/(\w+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html)
                for m in matches:
                    reel_ids.add(m)
                    
        except Exception as e:
            print(f"[!] Ninja error: {e}")
            
    return sorted(list(reel_ids))

if __name__ == "__main__":
    profile_url = "https://www.facebook.com/61588493966285/reels/"
    ids = discover_reels(profile_url)
    
    if ids:
        print(f"[+] Discovered {len(ids)} Reel IDs!")
        urls_file = Path("narrative_harvester/urls.txt")
        with open(urls_file, "w") as f:
            for rid in ids:
                f.write(f"https://www.facebook.com/reels/{rid}/\n")
        print(f"[+] Updated {urls_file}")
    else:
        print("[!] No IDs found. Facebook is using heavy encryption or dynamic loading.")

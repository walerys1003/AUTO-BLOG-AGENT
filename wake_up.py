#!/usr/bin/env python3
"""
Wake-up script to ensure application is running before scheduled tasks.
This script pings the application to wake it up if it's sleeping.
"""
import requests
import os
import sys
from datetime import datetime

def wake_up_application():
    """Ping the application to ensure it's awake"""
    # Get the Replit domain
    repl_slug = os.environ.get('REPL_SLUG', 'blog-automation')
    repl_owner = os.environ.get('REPL_OWNER', 'user')
    
    # Try multiple possible URLs
    urls = [
        f"https://{repl_slug}.{repl_owner}.repl.co/",
        f"https://{repl_slug}--{repl_owner}.replit.app/",
        "http://0.0.0.0:5000/",
        "http://localhost:5000/"
    ]
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔔 Wake-up script started")
    
    for url in urls:
        try:
            print(f"Trying to wake up: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code in [200, 302, 401]:  # 401 means app is running but needs auth
                print(f"✅ Application is awake! Status: {response.status_code}")
                print(f"🎯 Scheduler should now run at scheduled times:")
                print(f"   • 06:00 UTC (07:00 PL)")
                print(f"   • 07:00 UTC (08:00 PL)")
                print(f"   • 08:00 UTC (09:00 PL)")
                return True
                
        except requests.exceptions.RequestException as e:
            print(f"Failed to reach {url}: {str(e)}")
            continue
    
    print("⚠️ Could not wake up application from any URL")
    return False

if __name__ == "__main__":
    success = wake_up_application()
    sys.exit(0 if success else 1)

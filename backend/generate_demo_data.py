"""
Script to generate static demo data from Sample1C.wav.

This script:
1. Uploads the sample audio file
2. Waits for processing to complete
3. Fetches the complete results
4. Saves them to demo_data.json for the demo endpoint

Usage:
    python generate_demo_data.py

Requirements:
    - Backend API running (uvicorn app.main:app)
    - Valid user credentials in .env or provided below
    - Sample1C.wav in project root
"""

import asyncio
import json
import time
from pathlib import Path

import httpx

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
AUDIO_FILE_PATH = Path(__file__).parent.parent / "Sample1C.wav"
OUTPUT_JSON_PATH = Path(__file__).parent / "app" / "routers" / "demo_data.json"

# You need to provide valid credentials
# Option 1: Use existing user credentials
EMAIL = "demo@ablepro.com"  # Change this to your test user email
PASSWORD = "demo123456"  # Change this to your test user password

# Option 2: Or set ADMIN_EMAIL/ADMIN_PASSWORD in your .env and use that


async def main():
    """Generate demo data from Sample1C.wav."""
    
    print("🎬 Starting demo data generation...")
    print(f"📁 Audio file: {AUDIO_FILE_PATH}")
    print(f"💾 Output will be saved to: {OUTPUT_JSON_PATH}")
    print()
    
    if not AUDIO_FILE_PATH.exists():
        print(f"❌ Error: Audio file not found at {AUDIO_FILE_PATH}")
        return
    
    async with httpx.AsyncClient(timeout=600.0, follow_redirects=True) as client:
        # Step 1: Login and get access token
        print("🔐 Step 1: Authenticating...")
        try:
            login_response = await client.post(
                f"{API_BASE_URL}/auth/login",
                json={"email": EMAIL, "password": PASSWORD},
            )
            login_response.raise_for_status()
            auth_data = login_response.json()
            access_token = auth_data["tokens"]["access_token"]
            print(f"✅ Authenticated as: {auth_data['user']['email']}")
        except httpx.HTTPStatusError as e:
            print(f"❌ Authentication failed: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            print("\n💡 Tip: Create a user first or update EMAIL/PASSWORD in this script")
            return
        except Exception as e:
            print(f"❌ Error during authentication: {e}")
            return
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Step 2: Upload audio file
        print("\n📤 Step 2: Uploading Sample1C.wav...")
        try:
            with open(AUDIO_FILE_PATH, "rb") as audio_file:
                files = {"file": ("Sample1C.wav", audio_file, "audio/wav")}
                upload_response = await client.post(
                    f"{API_BASE_URL}/audio/upload",
                    files=files,
                    headers=headers,
                )
                upload_response.raise_for_status()
                upload_data = upload_response.json()
                job_id = upload_data["job_id"]
                print(f"✅ Upload successful! Job ID: {job_id}")
        except httpx.HTTPStatusError as e:
            print(f"❌ Upload failed: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            return
        except Exception as e:
            print(f"❌ Error during upload: {e}")
            return
        
        # Step 3: Poll for completion
        print(f"\n⏳ Step 3: Waiting for processing to complete...")
        print("   This may take several minutes depending on audio length...")
        
        max_wait = 600  # 10 minutes max
        start_time = time.time()
        last_stage = None
        
        while (time.time() - start_time) < max_wait:
            try:
                status_response = await client.get(
                    f"{API_BASE_URL}/jobs/{job_id}/status",
                    headers=headers,
                )
                status_response.raise_for_status()
                status_data = status_response.json()
                
                current_status = status_data["status"]
                current_stage = status_data.get("stage")
                progress = status_data.get("progress", 0)
                
                # Print stage updates
                if current_stage != last_stage:
                    print(f"   📊 Stage: {current_stage} ({progress}%)")
                    last_stage = current_stage
                
                if current_status == "completed":
                    print(f"✅ Processing complete! ({int(time.time() - start_time)}s)")
                    break
                elif current_status == "failed":
                    error_msg = status_data.get("error_message", "Unknown error")
                    print(f"❌ Processing failed: {error_msg}")
                    return
                
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                print(f"⚠️  Error checking status: {e}")
                await asyncio.sleep(2)
        else:
            print(f"❌ Timeout: Processing took longer than {max_wait}s")
            return
        
        # Step 4: Fetch complete results
        print("\n📥 Step 4: Fetching complete analysis results...")
        try:
            results_response = await client.get(
                f"{API_BASE_URL}/results/{job_id}",
                headers=headers,
            )
            results_response.raise_for_status()
            results_data = results_response.json()
            print(f"✅ Results fetched successfully!")
            print(f"   📊 Detected speakers: {results_data['detected_speakers']}")
            print(f"   ⏱️  Processing time: {results_data['processing_time_seconds']:.1f}s")
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed to fetch results: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            return
        except Exception as e:
            print(f"❌ Error fetching results: {e}")
            return
        
        # Step 5: Save to JSON file
        print(f"\n💾 Step 5: Saving demo data to {OUTPUT_JSON_PATH.name}...")
        try:
            # Ensure directory exists
            OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with pretty formatting
            with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            file_size = OUTPUT_JSON_PATH.stat().st_size / 1024  # KB
            print(f"✅ Demo data saved! ({file_size:.1f} KB)")
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return
        
        # Summary
        print("\n" + "="*60)
        print("🎉 Demo data generation complete!")
        print("="*60)
        print("\n📋 Summary:")
        print(f"   Audio file: {AUDIO_FILE_PATH.name}")
        print(f"   Job ID: {job_id}")
        print(f"   Speakers: {results_data['detected_speakers']}")
        print(f"   Duration: {results_data['audio']['duration_seconds']:.1f}s")
        print(f"   Atypical speakers: {sum(1 for s in results_data['speakers'] if s.get('prediction', {}).get('atypicality') == 'atypical')}")
        print(f"\n✅ The demo endpoint will now serve real analysis data from Sample1C.wav!")
        print(f"\n🔄 Next step: Restart your backend server to load the new demo data.")


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║          AblePro Demo Data Generator                      ║
║  Processes Sample1C.wav and creates static demo data     ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())

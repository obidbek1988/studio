import time
import requests
import soundfile as sf
import speech_recognition as sr
from playwright.sync_api import sync_playwright

def solve_audio_challenge(bframe):
    print("Clicking audio challenge button...")
    audio_btn = bframe.locator("#recaptcha-audio-button")
    audio_btn.click(force=True)
    time.sleep(3)
    
    # Check if blocked or download link is present
    # If blocked: "Your computer or network may be sending automated queries"
    text_content = bframe.content()
    if "automated queries" in text_content or "blokirovk" in text_content:
        print("Google detected automated queries for audio challenge.")
        return False
        
    # Get download link
    download_link = None
    try:
        download_elem = bframe.locator(".rc-audiochallenge-tdownload-link").first
        if download_elem.count() > 0:
            download_link = download_elem.get_attribute("href")
    except Exception as e:
        print("Error getting audio link:", e)
        
    print("Audio download link:", download_link)
    if not download_link:
        return False
        
    # Download mp3
    resp = requests.get(download_link)
    mp3_path = "5millionsertifikat/challenge.mp3"
    wav_path = "5millionsertifikat/challenge.wav"
    with open(mp3_path, "wb") as f:
        f.write(resp.content)
    print("Saved audio challenge mp3, size:", len(resp.content))
    
    # Convert to wav via soundfile
    data, samplerate = sf.read(mp3_path)
    sf.write(wav_path, data, samplerate)
    print("Converted to wav successfully!")
    
    # Transcribe via speech_recognition
    r = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = r.record(source)
    try:
        text = r.recognize_google(audio_data)
        print("Google Speech recognition solved text:", text)
    except Exception as e:
        print("Speech recognition failed:", e)
        return False
        
    # Fill in response
    resp_input = bframe.locator("#audio-response")
    resp_input.fill(text)
    time.sleep(1)
    
    # Click verify
    verify_btn = bframe.locator("#recaptcha-verify-button")
    verify_btn.click(force=True)
    time.sleep(3)
    return True

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        page.goto("https://omp.aistudy.uz/auth/register", wait_until="domcontentloaded")
        time.sleep(3)
        page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
        
        # Click Metrika
        page.locator("button:has-text('Metrika')").click(force=True)
        time.sleep(2)
        
        anchor_frame = None
        for f in page.frames:
            if "recaptcha" in f.url and "anchor" in f.url:
                anchor_frame = f
                break
                
        if not anchor_frame:
            print("Anchor frame not found!")
            browser.close()
            return
            
        checkbox = anchor_frame.locator("#recaptcha-anchor")
        checkbox.click(force=True)
        time.sleep(4)
        
        is_checked = checkbox.get_attribute("aria-checked")
        print("Aria checked:", is_checked)
        if is_checked == "true":
            print("Directly solved with 1 click!")
        else:
            bframe = None
            for f in page.frames:
                if "recaptcha" in f.url and "bframe" in f.url:
                    bframe = f
                    break
            if bframe:
                solved = solve_audio_challenge(bframe)
                time.sleep(3)
                try:
                    is_checked = anchor_frame.locator("#recaptcha-anchor").get_attribute("aria-checked", timeout=5000)
                    print("After audio solve, aria-checked:", is_checked)
                except Exception as e:
                    print("Could not get aria-checked:", e)
                
        # Get g-recaptcha-response
        token = page.evaluate("document.querySelector('[name=\"g-recaptcha-response\"]')?.value || ''")
        print("g-recaptcha-response token length:", len(token))
        if token:
            print("TOKEN OBTAINED SUCCESSFULLY! Token preview:", token[:50])
            with open("5millionsertifikat/sample_token.txt", "w") as f:
                f.write(token)
                
        browser.close()

if __name__ == "__main__":
    run()

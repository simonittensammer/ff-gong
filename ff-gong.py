import requests
import time
import pygame
import pyttsx3

def list_voices():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for i, voice in enumerate(voices):
        print(f"Voice {i}:")
        print(f"  ID: {voice.id}")
        print(f"  Name: {voice.name}")
        print(f"  Languages: {voice.languages}")
        print()

def fetch_data():
    url = "https://cf-einsaetze.ooelfv.at/webext2/rss/json_2tage.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_fire_brigade(data, target_brigade):
    try:
        if "einsaetze" in data:
            for einsatz_key in data["einsaetze"]:
                einsatz = data["einsaetze"][einsatz_key]["einsatz"]
                feuerwehren = einsatz.get("feuerwehrenarray", {})

                for fw_key in feuerwehren:
                    if feuerwehren[fw_key].get("fwname") == target_brigade:
                        print(f"Match found: {feuerwehren[fw_key].get('fwname')} at {einsatz.get('einsatzort')}")
                        einsatztyp_text = einsatz.get("einsatztyp", {}).get("text", "Einsatztyp not found")
                        einsatzsubtyp_text = einsatz.get("einsatzsubtyp", {}).get("text", "")
                        alarmstufe = einsatz.get("alarmstufe", "Unknown")

                        if einsatzsubtyp_text and einsatzsubtyp_text != einsatztyp_text:
                            combined_text = f"{einsatztyp_text}, {einsatzsubtyp_text}, Alarmstufe {alarmstufe}"
                        else:
                            combined_text = f"{einsatztyp_text}, Alarmstufe {alarmstufe}"

                        return einsatz.get("num1"), combined_text
    except KeyError as e:
        print(f"Key error while processing data: {e}")
    return None, None

def speak_text(text, voice_id=None):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    if voice_id:
        # Use the specified voice
        engine.setProperty('voice', voice_id)
    else:
        # Fallback: Choose the first German voice
        for voice in voices:
            if "de" in voice.id or "german" in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        else:
            print("German voice not found. Using default voice.")
    
    engine.setProperty('rate', 150)  # Adjust speaking rate
    engine.say(text)
    engine.runAndWait()

def main():
    speak_text("Dies ist ein Test.")

    target_brigade = "Feuerwehr/Florian Jeging (33208)"
    alert_sound = "gong.mp3"  # Path to your alert sound file
    interval = 5  # Fetch data every 5 seconds
    alert_counts = {}  # Track the number of alerts per einsatz

    # Initialize pygame mixer
    pygame.mixer.init()

    while True:
        print("Fetching data...")
        data = fetch_data()

        einsatz_num1, alert_text = check_fire_brigade(data, target_brigade)
        if einsatz_num1 and alert_text:
            if einsatz_num1 not in alert_counts:
                alert_counts[einsatz_num1] = 0

            if alert_counts[einsatz_num1] < 3:
                print("Playing alert sound!")
                pygame.mixer.music.load(alert_sound)
                pygame.mixer.music.play()

                # Wait until 1 second before the sound ends to start speaking
                sound_length = pygame.mixer.Sound(alert_sound).get_length()
                time.sleep(max(0, sound_length - 3))

                print(f"Speaking text: {alert_text}")
                speak_text(alert_text)

                # Wait for the remainder of the sound to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)

                alert_counts[einsatz_num1] += 1

        time.sleep(interval)

if __name__ == "__main__":
    main()

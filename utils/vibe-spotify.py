import sys
import subprocess
import os
import argparse
import time
import unicodedata
import re
from gi.repository import GLib
import pydbus

def normalize_string(text):
    if not text:
        return ""
    text = text.replace('ł', 'l').replace('Ł', 'L')
    normalized = unicodedata.normalize('NFKD', text)
    cleaned = "".join(c for c in normalized if not unicodedata.combining(c)).lower()
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

class SpotifyRecorder:
    def __init__(self, target_directory, library_directory=None, skip_cooldown=10):
        self.bus = pydbus.SessionBus()
        self.parec_process = None
        self.ffmpeg_process = None
        self.current_track = None
        self.current_artist = None
        
        self.skip_cooldown = skip_cooldown
        self.last_skip_time = 0
        self.timeout_id = None
        
        self.session_recordings = []
        self.current_recording = None
        
        self.target_dir = os.path.abspath(os.path.expanduser(target_directory))
        os.makedirs(self.target_dir, exist_ok=True)
        
        self.library_dir = None
        if library_directory:
            self.library_dir = os.path.abspath(os.path.expanduser(library_directory))

        try:
            self.spotify = self.bus.get('org.mpris.MediaPlayer2.spotify', '/org/mpris/MediaPlayer2')
            self.spotify.PropertiesChanged.connect(self.on_properties_changed)
            
            # --- Restored Verbose Startup Banner ---
            print("\n==================================================================")
            print("Successfully connected to Spotify via D-Bus!")
            print(f"ACTIVE OUTPUT:   {self.target_dir}")
            if self.library_dir:
                print(f"TRUSTED LIBRARY: {self.library_dir} (Read-Only Safeguard)")
            print(f"SKIP COOLDOWN:   {self.skip_cooldown} seconds")
            print("STATUS:          Idling. Recording starts on the next song change.")
            print("==================================================================\n")
            
        except Exception as e:
            print(f"Error: Could not connect to Spotify. Is it running?\nDetails: {e}")
            sys.exit(1)

    def get_default_monitor_source(self):
        try:
            output = subprocess.check_output(["pactl", "info"], text=True)
            for line in output.splitlines():
                if "Default Sink:" in line:
                    return f"{line.split(':', 1)[1].strip()}.monitor"
        except: return None
        return None

    def on_properties_changed(self, interface, changed_properties, invalidated_properties):
        if 'Metadata' in changed_properties:
            metadata = changed_properties['Metadata']
            title = metadata.get('xesam:title')
            artists = metadata.get('xesam:artist')
            artist = artists[0] if artists else "Unknown Artist"
            
            if title and (title != self.current_track):
                # Restored status logging format
                print(f"\n[Song Change] {artist} - {title}")
                self.handle_track_change(artist, title)

    def handle_track_change(self, artist, title):
        if self.timeout_id is not None:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
            
        self.stop_recording(discard_current=False)
        self.current_track = title
        self.current_artist = artist
        safe_base_name = f"{artist} - {title}".replace("/", "_")
        
        if self.file_already_exists(safe_base_name):
            now = time.time()
            time_since = now - self.last_skip_time
            if time_since >= self.skip_cooldown:
                print(f"   -> [DUPLICATE] Sending D-Bus 'Next' command...")
                self.last_skip_time = now
                self.spotify.Next()
            else:
                remaining = int(self.skip_cooldown - time_since)
                print(f"   -> [DUPLICATE] Cooldown active ({remaining}s left). Scheduling deferred skip...")
                self.timeout_id = GLib.timeout_add_seconds(remaining + 1, self.deferred_skip, artist, title)
            return

        self.start_recording(artist, title, safe_base_name)

    def deferred_skip(self, artist, title):
        if self.current_track == title and self.current_artist == artist:
            print(f"   -> [COOLDOWN EXPIRED] Executing deferred skip for: {artist} - {title}")
            self.last_skip_time = time.time()
            self.spotify.Next()
        self.timeout_id = None
        return False

    def file_already_exists(self, base_name):
        norm_target = normalize_string(base_name)
        dirs = [self.target_dir] + ([self.library_dir] if self.library_dir else [])
        for directory in dirs:
            if not os.path.exists(directory): continue
            for file in os.listdir(directory):
                name_without_ext, _ = os.path.splitext(file)
                if normalize_string(name_without_ext) == norm_target: return True
        return False

    def start_recording(self, artist, title, safe_base_name):
        full_path = os.path.join(self.target_dir, f"{safe_base_name}.mp3")
        monitor = self.get_default_monitor_source()
        if not monitor: return
        
        print(f"   -> Encoding directly to MP3 @ 160kbps...")
        self.current_recording = {"path": full_path, "artist": artist, "title": title, "start_time": time.time()}
        self.parec_process = subprocess.Popen(['parec', '-d', monitor, '--format=s16le', '--rate=44100', '--channels=2'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.ffmpeg_process = subprocess.Popen(['ffmpeg', '-y', '-f', 's16le', '-ar', '44100', '-ac', '2', '-i', 'pipe:0', '-b:a', '160k', full_path], stdin=self.parec_process.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.parec_process.stdout.close()

    def stop_recording(self, discard_current=False):
        if self.parec_process:
            self.parec_process.terminate()
            self.parec_process.wait()
            self.parec_process = None
        if self.ffmpeg_process:
            self.ffmpeg_process.wait()
            self.ffmpeg_process = None

        if self.current_recording:
            if discard_current:
                if os.path.exists(self.current_recording["path"]): os.remove(self.current_recording["path"])
            else:
                self.current_recording["duration"] = time.time() - self.current_recording["start_time"]
                self.session_recordings.append(self.current_recording)
            self.current_recording = None

    def analyze_advertisements(self):
        potential_ads = set()
        for rec in self.session_recordings:
            if rec.get("duration", 0) < 35: potential_ads.add(rec["path"])
        for file in os.listdir(self.target_dir):
            if file.startswith(" -") or file.startswith("-"): potential_ads.add(os.path.join(self.target_dir, file))
        if potential_ads:
            print("\nif the ad list makes sense, here's the commands to remove them:")
            for ad_path in sorted(potential_ads): print(f'rm "{ad_path}"')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir")
    parser.add_argument("-l", "--library-dir")
    parser.add_argument("-c", "--skip-cooldown", type=int, default=10)
    args = parser.parse_args()
        
    recorder = SpotifyRecorder(args.output_dir, args.library_dir, args.skip_cooldown)
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("\nExiting... discarding current partial recording.")
        recorder.stop_recording(discard_current=True)
        recorder.analyze_advertisements()

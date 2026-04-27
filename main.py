import ts3
import requests
import threading
import yt_dlp

TS3_HOST = "127.0.0.1"
TS3_PORT = 10011
TS3_USER = "serveradmin"
TS3_PASS = "password"
TS3_NICK = "ControlBot"
AUDIOBOT_API = "http://127.0.0.1:58913/api/bot/mybot"

YDL_OPTS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_nYou': 'bestaudio',
    'extract_audio': True,
    'audio_format': 'mp3',
}

def download_from_youtube(url):
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
            audio_url = info_dict.get('url', None)
            if not audio_url:
                ydl.download([url])
                print(f"Could not get direct audio stream URL for {url}. Try enabling download and upload.")
                return None
            return audio_url
        except yt_dlp.DownloadError as e:
            print(f"Error downloading from YouTube: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None


def send_to_audiobot(endpoint, method="POST", data=None):
    try:
        url = f"{AUDIOBOT_API}/{endpoint}"
        if method == "POST":
            response = requests.post(url, json=data)
        else:
            response = requests.get(url)
        return response.status_code == 200
    except Exception as e:
        print(f"Error connecting to AudioBot: {e}")
        return False

def command_loop():
    with ts3.query.TS3ServerConnection(f"telnet://{TS3_USER}:{TS3_PASS}@{TS3_HOST}:{TS3_PORT}") as ts:
        ts.exec_("use", sid=1)
        ts.exec_("clientupdate", client_nickname=TS3_NICK)
        ts.register_for_private_messages()

        print("Bot is running and listening for commands...")

        while True:
            event = ts.wait_for_event()
            if event.event == 'notifytextmessage':
                msg = event[0]['msg']
                sender_id = event[0]['invokerid']

                if msg.startswith("!play "):
                    input_url = msg.split(" ", 1)[1]
                    
                    if "youtube.com" in input_url or "youtu.be" in input_url:
                        print(f"Attempting to play YouTube URL: {input_url}")
                        audio_source_url = download_from_youtube(input_url)
                        if audio_source_url:
                            print(f"Extracted audio URL: {audio_source_url}")
                            if send_to_audiobot("play", data={"url": audio_source_url}):
                                ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Playing from YouTube: " + input_url)
                            else:
                                ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Failed to play YouTube audio. Check bot logs.")
                        else:
                            ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Could not process YouTube URL. Make sure it's valid.")
                    else:
                        # اگر URL یوتیوب نبود، مستقیماً به بات ارسال کن (برای فایل‌های صوتی یا لینک‌های مستقیم)
                        if send_to_audiobot("play", data={"url": input_url}):
                            ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Playing: " + input_url)
                        else:
                            ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Failed to play. Check URL and bot status.")


                elif msg == "!next":
                    send_to_audiobot("next")
                    ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Skipped to next track.")

                elif msg == "!stop":
                    send_to_audiobot("stop")
                    ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Stopped.")

                elif msg.startswith("!volume "):
                    try:
                        vol = int(msg.split(" ")[1])
                        if 0 <= vol <= 100: # اطمینان از اینکه ولوم بین 0 تا 100 است
                             if send_to_audiobot("volume", data={"volume": vol}):
                                ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg=f"Volume set to {vol}")
                             else:
                                ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Failed to set volume.")
                        else:
                            ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Volume must be between 0 and 100.")
                    except (ValueError, IndexError):
                        ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Invalid volume. Use: !volume <0-100>")

                elif msg.startswith("!repeat "):
                    mode_parts = msg.split(" ", 1)
                    if len(mode_parts) > 1:
                        mode = mode_parts[1].lower() # off, one, all
                        if mode in ["off", "one", "all"]:
                            if send_to_audiobot("repeat", data={"mode": mode}):
                                ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg=f"Repeat mode set to {mode}")
                            else:
                                ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Failed to set repeat mode.")
                        else:
                            ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Invalid repeat mode. Use 'off', 'one', or 'all'.")
                    else:
                         ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Usage: !repeat <off|one|all>")


                elif msg == "!shuffle": 
                    if send_to_audiobot("shuffle", data={"on": True}):
                        ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Shuffle enabled.")
                    else:
                        ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Failed to enable shuffle.")
                
                elif msg == "!unshuffle":
                     if send_to_audiobot("shuffle", data={"on": False}):
                        ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Shuffle disabled.")
                     else:
                        ts.exec_("sendtextmessage", targetmode=1, target=sender_id, msg="Failed to disable shuffle.")


if __name__ == "__main__":
    try:
        import yt_dlp
    except ImportError:
        print("yt-dlp is not installed. Please install it using: pip install yt-dlp")
        exit(1)
        
    command_loop()

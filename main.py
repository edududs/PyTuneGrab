from pytunegrab.core import YTDownloader

downloader = YTDownloader()
url_da_playlist = "https://music.youtube.com/watch?v=osZU21M9zyM&list=PLLaFpNaeENKMld-bNnsVXNwr-ofOBhEu7"
music_url = "https://music.youtube.com/watch?v=AZ_Hb9B0F58"

downloader.download_audio(music_url)

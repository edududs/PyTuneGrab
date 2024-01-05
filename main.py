from pytunegrab.core import AudioDownload, VideoDownload, convert_to_mp3

audio = AudioDownload()
video = VideoDownload()


# audio.download("https://www.youtube.com/watch?v=5yijULf4Hko")

audio.download_playlist(
    "https://music.youtube.com/watch?v=2fngvQS_PmQ&list=PLLaFpNaeENKPgx955VKNDLpopNvXwLtnA"
)

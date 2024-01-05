import os
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse
import threading
from concurrent.futures import ThreadPoolExecutor
from moviepy.editor import AudioFileClip
from pytube import Playlist, Search, YouTube
from slugify import slugify


def is_valid_url(input_string):
    try:
        result = urlparse(input_string)
        return all(
            [result.scheme, result.netloc]
        )  # Verifica se há esquema e local de rede
    except ValueError:
        return False


def convert_to_mp3(file_path: str | Path) -> Path | str:
    if not isinstance(file_path, Path):
        try:
            file_path = Path(file_path)
        except:
            raise Exception("Caminho inválido")

    if not file_path.exists():
        raise Exception("Arquivo inexistente")

    audio = AudioFileClip(str(file_path))
    if audio:
        mp3_path = str(file_path).replace(".mp4", ".mp3")

        audio.write_audiofile(mp3_path)
        file_path.unlink()

        return mp3_path
    else:
        raise Exception("Nenhum audio encontrado")


class MusicSearcher(ABC):
    @abstractmethod
    def search(self, query):
        pass


class Searcher(MusicSearcher):
    def search(self, query):
        if is_valid_url(query):
            yt = YouTube(query)
            return yt
        else:
            yt = Search(query).results
            if yt:
                return yt[0]
            raise Exception("Nenhum resultado encontrado")


class DownloadStrategy(ABC):
    def __init__(self) -> None:
        self._searcher = Searcher()

    @abstractmethod
    def download(self, search):
        pass


class AudioDownload(DownloadStrategy):
    def download(self, search, out_path=None):
        result = self._searcher.search(search)
        audio = result.streams.get_audio_only()
        self.create_download_directory("downloads")
        if audio:
            if not out_path:
                audio_path = audio.download(
                    r"D:\Eduardo\Projects\RepositorioGit\CriandoModulo\PyTuneGrab\downloads"
                )
            else:
                audio_path = audio.download(out_path)
            title = slugify(result.title)
            new_path = Path(audio_path).parent / f"{title}.mp4"
            os.rename(audio_path, new_path)
            mp3_out_path = convert_to_mp3(new_path)
            return mp3_out_path

    def download_playlist(self, playlist_url, out_path=None):
        playlist = Playlist(playlist_url)
        threads = []
        for video in playlist:
            thread = threading.Thread(target=self.download, args=(video, out_path))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        return playlist
    
    def create_download_directory(self, path):
        os.makedirs(path, exist_ok=True)


class VideoDownload(DownloadStrategy):
    def download(self, search):
        result = self._searcher.search(search)
        video = result.streams.get_highest_resolution()
        if video:
            caminho = video.download()
            return caminho
        raise Exception("Nenhum video encontrado")

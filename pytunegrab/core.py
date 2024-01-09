from __future__ import annotations

import asyncio
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from moviepy.editor import AudioFileClip
from pytube import Playlist, Search, YouTube, Stream
from slugify import slugify


def is_valid_url(input_string: str) -> bool:
    try:
        result = urlparse(input_string)
        return all(
            [result.scheme, result.netloc]
        )  # Verifica se há esquema e local de rede
    except ValueError:
        return False


async def convert_to_mp3(file_path: str | Path) -> Path | str:
    if not isinstance(file_path, Path):
        try:
            file_path = Path(file_path)
        except Exception as e:
            raise e

    if not file_path.exists():
        raise Exception("Arquivo inexistente")

    audio = AudioFileClip(str(file_path))
    if audio:
        mp3_path = str(file_path).replace(".mp4", ".mp3")

        audio.write_audiofile(mp3_path)
        file_path.unlink()

        return mp3_path
    raise Exception("Nenhum audio encontrado")


def slugify_rename(yt_obj, audio_path):
    title = slugify(yt_obj.title)
    new_path = Path(audio_path).parent / f"{title}.mp4"

    shutil.move(audio_path, new_path)
    print(f"Nome do arquivo {yt_obj.title} convertido para {title}")
    return str(new_path)


class MusicSearcher(ABC):
    @abstractmethod
    def search(self, query: str) -> YouTube:
        pass


class Searcher(MusicSearcher):
    def search(self, query: str) -> YouTube:
        if is_valid_url(query):
            yt = YouTube(query)
            return yt

        yt = Search(query).results

        if yt:
            return yt[0]

        raise Exception("Nenhum resultado encontrado")


class DownloadStrategy(ABC):
    def __init__(self) -> None:
        self._searcher = Searcher()
        self._queue_for_download: List[YouTube] = []

    @property
    def playlist(self):
        return self._queue_for_download

    @playlist.setter
    def playlist(self, playlist_url):
        playlist = Playlist(playlist_url)
        for video in playlist:
            self._queue_for_download.append(YouTube(video))

    def create_download_directory(self, path) -> None:
        os.makedirs(path, exist_ok=True)

    def is_playlist_url(self, url):
        try:
            playlist = Playlist(url)
            if playlist.videos:
                return True
        except KeyError:
            return False

    def _download_video_only(
        self, yt_obj: YouTube, out_path=None, do_slugify=True
    ) -> str:
        stream = yt_obj.streams.get_highest_resolution()
        if not stream:
            raise ValueError("Não foi possível pegar o conteúdo do video do YouTube")
        title = yt_obj.title

        return self.handle_download(stream, yt_obj, out_path, title, do_slugify)

    def _download_audio_only(self, yt_obj: YouTube, out_path=None) -> str:
        stream = yt_obj.streams.get_audio_only()
        if not stream:
            raise ValueError("Não foi possível pegar o video do YouTube")
        title = yt_obj.title
        return self.handle_download(stream, yt_obj, out_path, title, do_slugify=True)

    def handle_download(
        self, stream: Stream, yt_obj, out_path, title, do_slugify=True
    ) -> str:
        if not out_path:
            out_path = "downloads"

        audio_path = stream.download(out_path, skip_existing=True)
        print(f"{title} baixado com sucesso!")
        if do_slugify:
            return slugify_rename(yt_obj, audio_path)
        return audio_path

    async def download(self, search, out_path=None, audio_only=False) -> str | list:
        self.create_download_directory("downloads")

        # Verifica se a URL é uma playlist
        if self.is_playlist_url(search):
            all_videos = await self.download_playlist(search, out_path)
            return all_videos

        # Faz a pesquisa do termo e retorna um objeto do YouTube
        result = self._searcher.search(search)

        if audio_only:
            downloaded = self._download_audio_only(result, out_path)
            mp3_out_path = await convert_to_mp3(downloaded)
            return str(mp3_out_path)

        downloaded = self._download_video_only(result, out_path, audio_only)
        return downloaded

    async def download_playlist(
        self, playlist_url, out_path=None, audio_only=False
    ) -> list:
        self.playlist = playlist_url

        async def download_threads(video, semaphore, audio_only=audio_only):
            async with semaphore:
                if audio_only:
                    downladed = await asyncio.to_thread(
                        self._download_audio_only, video, out_path
                    )
                    mp3_out_path = await convert_to_mp3(downladed)
                    return str(mp3_out_path)

                downloaded = await asyncio.to_thread(
                    self._download_video_only, video, out_path, audio_only
                )

                return downloaded

        # Limita o número de downloads e conversões em paralelo com o Semáforo
        max_concurrent_tasks = 4
        semaphore = asyncio.Semaphore(max_concurrent_tasks)

        # Cria uma lista de tarefas para o asyncio.gather e executa-as
        _converted_paths = await asyncio.gather(
            *[download_threads(video, semaphore) for video in self.playlist]
        )
        paths = []
        for path in _converted_paths:
            paths.append(path)

        return paths

    def __str__(self) -> str:
        return self.__class__.__name__


class AudioDownload(DownloadStrategy):
    async def download(self, search, out_path=None, audio_only=True):
        await super().download(search, out_path, audio_only)

    async def download_playlist(self, playlist_url, out_path=None, audio_only=True):
        await super().download_playlist(playlist_url, out_path, audio_only)


class VideoDownload(DownloadStrategy):
    ...


class YTDownloader:
    def download_audio(self, url):
        audio_downloader = AudioDownload()
        asyncio.run(audio_downloader.download(url, audio_only=True))

    def download_video(self, url):
        video_downloader = VideoDownload()
        asyncio.run(video_downloader.download(url))

from __future__ import annotations

import asyncio
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from moviepy.editor import AudioFileClip
from pytube import Playlist, Search, Stream, YouTube
from slugify import slugify


def is_valid_url(input_string: str) -> bool:
    """Determines if the given input string is a valid URL."""
    try:
        result = urlparse(input_string)
        return all(
            [result.scheme, result.netloc]
        )  # Verifica se há esquema e local de rede
    except ValueError:
        return False


def is_playlist_url(url):
    """Determines if the given input string is a playlist URL."""
    try:
        playlist = Playlist(url)
        if playlist.videos:
            return True
        return False
    except KeyError:
        return False


async def convert_to_mp3(file_path: str | Path) -> Path | str:
    """Converts the given file to mp3."""
    if not isinstance(file_path, Path):
        try:
            file_path = Path(file_path)
        except Exception as e:
            raise e

    if not file_path.exists():
        raise Exception("File not found")

    audio = AudioFileClip(str(file_path))
    if audio:
        mp3_path = str(file_path).replace(".mp4", ".mp3")

        audio.write_audiofile(mp3_path)
        file_path.unlink()

        return mp3_path
    raise Exception("No audio found")


def slugify_rename(yt_obj, audio_path):
    """Rename the audio file to the title of the video slugified."""
    title = slugify(yt_obj.title)
    new_path = Path(audio_path).parent / f"{title}.mp4"

    shutil.move(audio_path, new_path)
    print(f"{yt_obj.title} renamed to {title}")
    return str(new_path)


class MusicSearcher(ABC):
    """Abstract class for music searchers."""

    @abstractmethod
    def search(self, query: str) -> YouTube:
        pass


class Searcher(MusicSearcher):
    """Class for searching music on YouTube."""

    def search(self, query: str) -> YouTube:
        if is_valid_url(query):
            yt = YouTube(query)
            return yt

        yt = Search(query).results

        if yt:
            return yt[0]

        raise Exception("No result found")


class DownloadStrategy(ABC):
    """Abstract class for download strategies."""

    def __init__(self) -> None:
        """Initialize the searcher and the queue for download."""
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
        """Create the download directory if it doesn't exist."""
        os.makedirs(path, exist_ok=True)

    def download_video_only(
        self, yt_obj: YouTube, out_path=None, do_slugify=True
    ) -> str:
        """Download the video only."""
        stream = yt_obj.streams.get_highest_resolution()
        if not stream:
            raise ValueError("Unable to get video stream from YouTube")
        title = yt_obj.title

        return self.handle_download(stream, yt_obj, out_path, title, do_slugify)

    def download_audio_only(self, yt_obj: YouTube, out_path=None) -> str:
        """Download the audio only but in the MP4 format."""
        stream = yt_obj.streams.get_audio_only()
        if not stream:
            raise ValueError("Unable to get audio stream from YouTube")
        title = yt_obj.title
        return self.handle_download(stream, yt_obj, out_path, title, do_slugify=True)

    def handle_download(
        self, stream: Stream, yt_obj, out_path, title, do_slugify=True
    ) -> str:
        """
        Handle the download of a video stream.

        Args:
            stream (Stream): The video stream to download.
            yt_obj: The YouTube object associated with the video.
            out_path (str): The output path for the downloaded file.
            title (str): The title of the video.
            do_slugify (bool, optional): Whether to slugify the downloaded file. Defaults to True.

        Returns:
            str: The path to the downloaded file or the slugified file path if do_slugify is True.
        """

        if not out_path:
            out_path = "downloads"

        audio_path = stream.download(out_path, skip_existing=True)
        print(f"{title} downloaded!")
        if do_slugify:
            return slugify_rename(yt_obj, audio_path)
        return audio_path

    @abstractmethod
    async def download(self, search, out_path=None) -> str | list:
        pass

    @abstractmethod
    async def download_playlist(self, playlist_url, out_path=None) -> list:
        pass

    def __str__(self) -> str:
        return self.__class__.__name__


class AudioDownload(DownloadStrategy):
    """Class for downloading a video or a playlist of videos and converting it to mp3."""

    async def download(self, search, out_path=None) -> str | list:
        """
        Downloads a video or playlist from YouTube and converts it to MP3 format.

        Args:
            search (str): The search term or URL of the video or playlist.
            out_path (str, optional): The path to save the downloaded file. Defaults to None.

        Returns:
            str or list: The path to the converted MP3 file if a
            single video is downloaded, or a list of paths if a playlist is downloaded.
        """
        self.create_download_directory("downloads")

        # Verifica se a URL é uma playlist
        if is_playlist_url(search):
            all_videos = await self.download_playlist(search, out_path)
            return all_videos

        # Faz a pesquisa do termo e retorna um objeto do YouTube
        result = self._searcher.search(search)

        # Faz o Download, converte e retorna o caminho do arquivo convertido para mp3
        downloaded = self.download_audio_only(result, out_path)
        mp3_out_path = await convert_to_mp3(downloaded)
        return str(mp3_out_path)

    async def download_playlist(self, playlist_url, out_path=None) -> list:
        """
        Downloads a playlist from YouTube and converts it to MP3 format, using multiple threads.

        Args:
            playlist_url (str): The URL of the playlist to be downloaded.
            out_path (str, optional): The path to save the
            downloaded files. If not specified, the files will be
            saved in the current working directory. Defaults to None.

        Returns:
            list: A list of paths to the downloaded and converted MP3 files.
        """
        self.playlist = playlist_url

        async def download_threads(video, semaphore):
            async with semaphore:
                downladed = await asyncio.to_thread(
                    self.download_audio_only, video, out_path
                )
                mp3_out_path = await convert_to_mp3(downladed)
                return str(mp3_out_path)

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


class VideoDownload(DownloadStrategy):
    """Class for downloading a video or a playlist of videos."""

    async def download(self, search, out_path=None) -> str | list:
        """
        Download a video from YouTube given a search term or URL.

        Args:
            search (str): The search term or URL of the video to download.
            out_path (str, optional): The directory where the downloaded video will be saved.
                                      If not specified, the video
                                      will be saved in the default download directory.

        Returns:
            str or list: The path of the downloaded video file if only one video is downloaded,
                         or a list of paths of the downloaded
                          video files if a playlist is downloaded.
        """
        self.create_download_directory("downloads")

        # Verifica se a URL é uma playlist
        if is_playlist_url(search):
            all_videos = await self.download_playlist(search, out_path)
            return all_videos

        # Faz a pesquisa do termo e retorna um objeto do YouTube
        result = self._searcher.search(search)
        downloaded = self.download_video_only(result, out_path)
        return downloaded

    async def download_playlist(self, playlist_url, out_path=None) -> list:
        """
        Downloads a playlist of videos asynchronously.

        Args:
            playlist_url (str): The URL of the playlist.
            out_path (str, optional): The output path to save the downloaded videos.
                Defaults to None.

        Returns:
            list: A list of paths to the downloaded videos.
        """
        self.playlist = playlist_url

        async def download_threads(video, semaphore):
            async with semaphore:
                downloaded = await asyncio.to_thread(
                    self.download_video_only, video, out_path
                )
                return downloaded

        # Limita o número de downloads e conversões em paralelo com o Semáforo
        max_concurrent_tasks = 4
        semaphore = asyncio.Semaphore(max_concurrent_tasks)

        # Cria uma lista de tarefas para o asyncio.gather e executa-as
        _converted_paths = await asyncio.gather(
            *[download_threads(video, semaphore) for video in self.playlist]
        )
        return _converted_paths


class YTDownloader:
    """
    This class serves as the main interface for downloading videos and audios from YouTube.

    Usage:
    yt_downloader = YTDownloader()
    yt_downloader.download_audio("https://www.youtube.com/watch?v=your_video_id")
    yt_downloader.download_video("https://www.youtube.com/watch?v=your_video_id")

    Methods:
    - download_audio(url: str) -> None: Downloads the audio from the provided YouTube video URL.
    - download_video(url: str) -> None: Downloads the video from the provided YouTube video URL.
   

    Note:
    - This class internally utilizes the AudioDownload and
    VideoDownload classes for downloading and converting videos.
    - Ensure the required dependencies (pytube, moviepy) are installed before using this class.
    """

    def download_audio(self, url):
        audio_downloader = AudioDownload()
        asyncio.run(audio_downloader.download(url))

    def download_video(self, url):
        video_downloader = VideoDownload()
        asyncio.run(video_downloader.download(url))

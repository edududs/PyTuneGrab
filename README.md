# PyTuneGrab

Welcome to the PyTuneGrab documentation! PyTuneGrab is a Python tool designed for downloading and converting YouTube audio and video content. It provides a convenient interface for fetching content, converting videos to MP3 audio, and organizing your media library.

## Main Features
**Audio Download**: Download audio from YouTube videos and convert them to the mp3 format.
**Video Download**: Download videos from YouTube.
**Playlist Handling**: Efficiently download and convert playlists.

## Requirements
- Python 3.7 or higher
- FFmpeg
- PyTube
- MoviePy


## How to Use
1. Install the required libraries:

```bash
pip install pytube moviepy
```
2. Make sure you have installed FFmpeg.

3. Import the relevant classes from PyTuneGrab in your Python script.

4. Create a instance of the desired downloader class.

The download will be done in a folder called "downloads" in the root folder of the directory, if an output path is not provided

Below, we present basic examples of use:

### Downloading and Converting Audio
```python
from pytunegrab.core import YTDownloader

downloader = YTDownloader()

# Download and convert a single video
video_url = "https://www.youtube.com/watch?v=your_video_id"
converted_audio_path = downloader.download_audio(video_url)

print(f"Converted Audio: {video_url} -> {converted_audio_path}")
```

### Downloading and Converting Video
```python

from pytunegrab import YTDownloader

downloader = YTDownloader()

# Download a video
video_url = "https://www.youtube.com/watch?v=your_video_id"
downloaded_video_path = downloader.download_video(video_url)

print(f"Downloaded Video: {video_url} -> {downloaded_video_path}")
```
The script will identify whether it is a playlist or not.

All the downloaders follow a similar pattern. You just need to specify the type of content you want to download, whether audio, video, or a playlist.

### Roadmap
We are committed to expanding the functionalities of this library. Planned future enhancements include:

Improved handling of video resolutions.
Support for additional audio formats.


# Contact
Email: dudulj@live.com

GitHub: edududs

# License
MIT License

Copyright (c) 2023 Eduardo Lima de Jesus

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
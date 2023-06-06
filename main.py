import ffmpeg
import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QWidget,
    QLineEdit, QRadioButton, QComboBox
)
from PyQt6.QtGui import QFont, QPixmap
from pytube import Playlist, YouTube


class YouTubeDownloader(QWidget):
    """Graphical user interface for downloading YouTube audio and videos."""
    def __init__(self):
        super().__init__()

        self.setGeometry(200, 200, 200, 200)
        self.setWindowTitle('YouTube Downloader')

        layout = QVBoxLayout()

        # 1. YouTube Downloader Label
        yt_label = self.create_youtube_label()
        layout.addWidget(yt_label)

        # 2. URL Search
        url_search = self.create_url_search_widgets()
        layout.addLayout(url_search)

        # 3. Video Info
        video_info = self.create_video_info()
        layout.addLayout(video_info)

        # 4. Media Settings
        media_settings = self.create_media_settings()
        layout.addLayout(media_settings)

        self.setLayout(layout)


    def create_youtube_label(self) -> QLabel:
        """Create YouTube Downloader label."""
        label = QLabel('YouTube Downloader')
        label.setFont(QFont('Sanserif', 20))

        return label

    def create_url_search_widgets(self) -> QHBoxLayout:
        """Create widgets to search YouTube URL."""
        layout = QHBoxLayout()
        label = QLabel('URL: ')
        line_edit = QLineEdit()
        btn = QPushButton('Search')

        layout.addWidget(label)
        layout.addWidget(line_edit)
        layout.addWidget(btn)

        return layout
    
    def create_video_info(self) -> QHBoxLayout:
        """Create widgets to display video title and thumbnail."""
        layout = QHBoxLayout()
        title_label = QLabel('Video Title')
        pixmap = QPixmap('./thumbnail.png')
        thumbnail_label = QLabel()
        thumbnail_label.setPixmap(pixmap)

        layout.addWidget(title_label)
        layout.addWidget(thumbnail_label)

        return layout
    
    def create_media_settings(self) -> QHBoxLayout:
        """Create widgets to select the media settings."""
        layout = QHBoxLayout()
        a_rbtn = QRadioButton('Audio (mp3)')
        v_rbtn = QRadioButton('Video (mp4)')
        combo = QComboBox()
        
        layout.addWidget(a_rbtn)
        layout.addWidget(v_rbtn)
        layout.addWidget(combo)

        return layout


def youtube_to_mp3(url, outdir):
    """Download mp3 file from a YouTube url."""
    yt = YouTube(url)
    # stream = yt.streams.filter(abr='160kbps').last()
    stream = yt.streams.filter(only_audio=True).last()
    
    # Download the file
    out_file = stream.download(output_path=outdir)
    # Rename out_file to .mp3
    base, ext = os.path.splitext(out_file)
    new_file = Path(f'{base}.mp3')
    os.rename(out_file, new_file)

    # Check success of download
    if new_file.exists():
        print(f'"{yt.title}" has been successfully downloaded')
    else:
        print(f'ERROR: "{yt.title}" could not be downloaded!')

def youtube_to_mp4(url, outdir):
    """Download mp4 file from a YouTube url."""
    yt = YouTube(url)
    # Download adaptive video
    v_stream = yt.streams.filter(adaptive=True, only_video=True).first()
    v_file = v_stream.download(output_path=outdir, filename='v_file')
    # Download adaptive audio
    a_stream = yt.streams.filter(only_audio=True).last()
    a_file = a_stream.download(output_path=outdir, filename='a_file')

    video = ffmpeg.input(v_file)
    audio = ffmpeg.input(a_file)
    # Combine video and audio
    output_file = outdir + f'{yt.title}.mp4'
    output = ffmpeg.output(video, audio, output_file, vcodec='copy', acodec='copy')
    output.run()

    # Remove a_file and v_file
    if os.path.exists(v_file):
        os.remove(v_file)
    
    if os.path.exists(a_file):
        os.remove(a_file)

def playlist_to_mp3(url, outdir):
    """Download mp3 files from a YouTube playlist url."""
    p = Playlist(url)
    for yt_url in p:
        youtube_to_mp3(yt_url, outdir)


if __name__ == '__main__':
    playlist_url = 'https://www.youtube.com/watch?v=YudHcBIxlYw&list=PLMGwXbxvTnARYX3nP-Boeur4VCJiCoewB'
    url = 'https://www.youtube.com/watch?v=ioNng23DkIM'
    outdir = '/home/Mike/sdcard/Music/'

    # youtube_to_mp3(url, outdir)
    # youtube_to_mp4(url, outdir)
    # playlist_to_mp3(playlist_url, outdir)

    app = QApplication(sys.argv)
    yt = YouTubeDownloader()
    yt.show()
    sys.exit(app.exec())
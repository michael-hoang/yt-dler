import ffmpeg
import os
import requests
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QWidget,
    QLineEdit, QRadioButton, QComboBox, QProgressBar
)
from PyQt6.QtGui import QFont, QColor, QPixmap
from pytube import Playlist, YouTube
from pytube.exceptions import RegexMatchError, VideoUnavailable


class YouTubeDownloader(QWidget):
    """Graphical user interface for downloading YouTube audio and videos."""
    def __init__(self):
        """Initialize the GUI and its attributes."""
        super().__init__()

        # Attributes
        self.youtube = None
        self.url_bar = None
        self.title_label = None
        self.thumbnail_label = None

        # self.setGeometry(200, 200, 300, 300)
        self.setWindowTitle('YouTube Downloader')

        layout = QVBoxLayout()

        # 1. YouTube Downloader Label
        yt_label = self.create_youtube_label()
        layout.addWidget(yt_label)

        # 2. URL Search
        url_search = self.create_url_search_widgets()
        layout.addLayout(url_search)

        # 3. Video Info
        video_info = self.create_video_info_widgets()
        layout.addLayout(video_info)

        # 4. Media Settings
        media_settings = self.create_media_settings_widgets()
        layout.addLayout(media_settings)

        # 5. Output
        output = self.create_output_widgets()
        layout.addLayout(output)

        # 6. Download progress
        dl_progress = self.create_download_progress_widgets()
        layout.addLayout(dl_progress)

        self.setLayout(layout)


    # GUI Creation Methods
    def create_youtube_label(self) -> QLabel:
        """Create YouTube Downloader label."""
        label = QLabel('YouTube Downloader')
        label.setFont(QFont('Sanserif', 20))

        return label

    def create_url_search_widgets(self) -> QHBoxLayout:
        """Create widgets to search YouTube URL."""
        layout = QHBoxLayout()
        label = QLabel('URL:')
        self.url_bar = QLineEdit()
        btn = QPushButton('Search')
        btn.clicked.connect(self.search_url)

        layout.addWidget(label)
        layout.addWidget(self.url_bar)
        layout.addWidget(btn)

        return layout
    
    def create_video_info_widgets(self) -> QHBoxLayout:
        """Create widgets to display video title and thumbnail."""
        layout = QVBoxLayout()
        self.title_label = QLabel('Video Title')
        self.thumbnail_label = QLabel()
        self.display_black_thumbnail()

        layout.addWidget(self.title_label)
        layout.addWidget(self.thumbnail_label)

        return layout
    
    def create_media_settings_widgets(self) -> QHBoxLayout:
        """Create widgets to select the media settings."""
        layout = QHBoxLayout()
        a_rbtn = QRadioButton('Audio (mp3)')
        v_rbtn = QRadioButton('Video (mp4)')
        combo = QComboBox()
        
        layout.addWidget(a_rbtn)
        layout.addWidget(v_rbtn)
        layout.addWidget(combo)

        return layout
    
    def create_output_widgets(self) -> QHBoxLayout:
        """Create widgets to select output folder."""
        layout = QHBoxLayout()
        label = QLabel('Output:')
        line_edit = QLineEdit()
        btn = QPushButton('Browse')

        layout.addWidget(label)
        layout.addWidget(line_edit)
        layout.addWidget(btn)

        return layout

    def create_download_progress_widgets(self) -> QHBoxLayout:
        """Create widgets to display download progress bar and to download media."""
        layout = QHBoxLayout()
        progress = QProgressBar()
        dl_btn = QPushButton('Download')

        layout.addWidget(progress)
        layout.addWidget(dl_btn)

        return layout

    # YouTube Downloader Methods

    def search_url(self) -> YouTube:
        """Create a YouTube object from the inputted URL."""
        # Reset YouTube object
        self.youtube = None
        url = self.url_bar.text()
        try:
            self.youtube = YouTube(url, use_oauth=True, allow_oauth_cache=True)
            self.display_title()
            self.display_thumbnail()
        except (RegexMatchError, VideoUnavailable):
            self.title_label.setText('Search failed.')
            self.display_black_thumbnail()

    def display_title(self):
        """Display the video title."""
        title = self.youtube.title
        self.title_label.setText(title)
    
    def display_thumbnail(self):
        """Display the video thumbnail."""
        thumbnail_url = self.youtube.thumbnail_url
        response = requests.get(thumbnail_url)
        if response.status_code == 200:
            img_data = response.content
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)
            resized_pixmap = pixmap.scaled(360, 202)
            self.thumbnail_label.setPixmap(resized_pixmap)

    def display_black_thumbnail(self):
        """Display a black thumbnail."""
        pixmap = QPixmap(360, 202)
        pixmap.fill(QColor(0, 0, 0))
        self.thumbnail_label.setPixmap(pixmap)




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

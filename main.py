import ffmpeg
import os
import requests
import sys

from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QWidget,
    QLineEdit, QComboBox, QProgressBar, QFileDialog, QCheckBox
)
from PyQt6.QtGui import QFont, QColor, QPixmap
from PyQt6.QtCore import Qt, QThread, QUrl
from pytube import Playlist, YouTube
from pytube.exceptions import RegexMatchError, VideoUnavailable
from urllib.error import URLError


class YouTubeDownloader(QWidget):
    """Graphical user interface for downloading YouTube audio and videos."""
    def __init__(self):
        """Initialize the GUI and its attributes."""
        super().__init__()

        # Attributes
        self.youtube = None
        self.title = None
        self.streams = None
        self.url_bar = None
        self.title_label = None
        self.thumbnail_label = None
        self.playlist_btn = None
        self.format_combo = None
        self.quality_combo = None
        self.a_stream = None
        self.v_streams = {}
        self.output_bar = None
        self.dl_btn = None

        self.setWindowTitle('YouTube Downloader')

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

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
        label = QLabel('▶ YouTube Downloader 🠟')
        label.setFont(QFont('Sanserif', 18, 700))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return label

    def create_url_search_widgets(self) -> QHBoxLayout:
        """Create widgets to search YouTube URL."""
        layout = QHBoxLayout()
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText('Enter YouTube video or playlist URL here')
        btn = QPushButton('Search')
        btn.clicked.connect(self.search_url)

        layout.addWidget(self.url_bar)
        layout.addWidget(btn)

        return layout
    
    def create_video_info_widgets(self) -> QHBoxLayout:
        """Create widgets to display video title and thumbnail."""
        layout = QVBoxLayout()
        self.title_label = QLabel('Liberate those coveted videos!')
        self.thumbnail_label = QLabel()
        self.display_black_thumbnail()

        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.thumbnail_label, alignment=Qt.AlignmentFlag.AlignCenter)

        return layout
    
    def create_media_settings_widgets(self) -> QHBoxLayout:
        """Create widgets to select the media settings."""
        layout = QHBoxLayout()
        
        self.playlist_btn = QCheckBox('Playlist')
        self.playlist_btn.setFixedWidth(70)

        format_layout = QVBoxLayout()
        format_label = QLabel('Format:')
        self.format_combo = QComboBox()
        self.format_combo.setFixedWidth(140)
        self.format_combo.addItems([
            'Audio (.mp3) - Highest',
            'Audio (.webm) - Highest',
            'Video (.mp4)'
        ])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        self.format_combo.setCurrentIndex(-1)
        self.format_combo.currentIndexChanged.connect(self.format_combo_changed)
        self.format_combo.setEnabled(False)
        
        quality_layout = QVBoxLayout()
        quality_label = QLabel('Quality:')
        self.quality_combo = QComboBox()
        self.quality_combo.setFixedWidth(150)
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)
        self.quality_combo.setEnabled(False)
        
        layout.addWidget(self.playlist_btn)
        layout.addLayout(format_layout)
        layout.addLayout(quality_layout)

        return layout
    
    def create_output_widgets(self) -> QHBoxLayout:
        """Create widgets to select output folder."""
        layout = QHBoxLayout()
    
        self.output_bar = QLineEdit()
        self.output_bar.setPlaceholderText('Output directory')
        btn = QPushButton('Browse')
        btn.clicked.connect(self.browser_folder)

        layout.addWidget(self.output_bar)
        layout.addWidget(btn)

        return layout

    def create_download_progress_widgets(self) -> QHBoxLayout:
        """Create widgets to display download progress bar and to download media."""
        layout = QHBoxLayout()
        progress = QProgressBar()
        self.dl_btn = QPushButton('Download')
        self.dl_btn.clicked.connect(self.download)

        layout.addWidget(progress)
        layout.addWidget(self.dl_btn)

        return layout

    # YouTube Downloader Methods

    def search_url(self) -> YouTube:
        """
        Create a YouTube object and initialize available streams from the inputted URL.
        """
        self.reset_attributes()
        url = self.url_bar.text()
        try:
            self.youtube = YouTube(url, use_oauth=True, allow_oauth_cache=True)
            self.streams = self.youtube.streams
            self.display_title()
            self.display_thumbnail()
        except (RegexMatchError, VideoUnavailable, URLError):
            self.title_label.setText('Search failed.')
        else:
            self.format_combo.setEnabled(True)
            if self.format_combo.currentText() == 'Video (.mp4)':
                self.quality_combo.setEnabled(True)
            else:
                self.quality_combo.setEnabled(False)
            self.get_streams()
            self.populate_combobox()

    def display_title(self):
        """Display the video title."""
        self.title = self.youtube.title
        self.title_label.setText(self.title)
    
    def display_thumbnail(self):
        """Display the video thumbnail."""
        thumbnail_url = f'http://img.youtube.com/vi/{self.youtube.video_id}/hqdefault.jpg'
        response = requests.get(thumbnail_url)
        if response.status_code == 200:
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            resized_pixmap = pixmap.scaled(360, 270)
            self.thumbnail_label.setPixmap(resized_pixmap)

    def display_black_thumbnail(self):
        """Display a black thumbnail."""
        pixmap = QPixmap(360, 270)
        pixmap.fill(QColor(0, 0, 0))
        self.thumbnail_label.setPixmap(pixmap)
        
    def get_streams(self):
        """
        Get audio and video streams from the YouTube object.
        """
        # Get highest audio quality stream
        self.a_stream = self.streams.filter(only_audio=True).order_by('bitrate').last()
        self.get_v_streams()

    def get_v_streams(self):
        """Get all of the video streams available for download."""
        v_prog_streams = self.streams.filter(progressive=True).order_by('resolution')
        v_dash_streams = self.streams.filter(progressive=False, only_video=True).order_by('resolution')
       
        for stream in v_prog_streams:
            quality = f'{stream.resolution}, {stream.fps}fps'
            self.v_streams[quality] = {'stream': stream}
            self.v_streams[quality]['progressive'] = True
           
        for stream in v_dash_streams:
            # Remove the last 'p'
            res = stream.resolution[:-1]
            if int(res) > 720:
                quality = f'{stream.resolution}, {stream.fps}fps [{stream.codecs[0]}]'
                self.v_streams[quality] = {'stream': stream}
                self.v_streams[quality]['progressive'] = False

    def populate_combobox(self):
        """Populate the combobox with available video streams."""
        for stream in reversed(self.v_streams):
            self.quality_combo.addItem(stream)

    def format_combo_changed(self):
        """Enable the Quality combobox when Video is selected."""
        if self.format_combo.currentText() == 'Video (.mp4)':
            self.quality_combo.setEnabled(True)
        else:
            self.quality_combo.setEnabled(False)

    def browser_folder(self):
        """Open a folder browsing window."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.output_bar.setText(folder_path)

    def download(self):
        """Download the media file to the output folder."""
        output_folder = self.output_bar.text()
        if os.path.exists(output_folder):
            if not self.playlist_btn.isChecked():
                self.download_single(output_folder)
            else:
                print('checked')
        else:
            pass

    def download_single(self, output_folder: str):
        """Download a single audio or video file."""
        if self.format_combo.currentText() == 'Audio (.mp3) - Highest':
            self.download_mp3(output_folder, mp3=True)
        elif self.format_combo.currentText() == 'Audio (.webm) - Highest':
            self.download_mp3(output_folder)
        elif self.format_combo.currentText() == 'Video (.mp4)':
            quality = self.quality_combo.currentText()
            if not self.v_streams[quality]['progressive']:
                self.download_mp4_dash(output_folder, quality)
            else:
                self.download_mp4_progressive(output_folder, quality)
    
    def download_playlist(self, output_folder: str):
        """Download all audio or video from a playlist."""
        

    def download_mp3(self, output_folder: str, mp3=False) -> str:
        """
        Download audio and convert it to mp3.
        Returns path (str) to the mp3 file.
        """
        audio_file = self.a_stream.download(output_path=output_folder)

        if mp3:
            # Convert audio file to .mp3
            root, ext = os.path.splitext(audio_file)
            mp3_file = Path(f'{root}.mp3')
            os.rename(audio_file, mp3_file)

            return mp3_file

        return audio_file
    
    def download_mp4_progressive(self, output_folder: str, quality: str) -> str:
        """
        Download video in mp4 format.
        Returns path (str) to the mp4 file.
        """
        return self.v_streams[quality]['stream'].download(output_path=output_folder, filename=f'{self.title} ({quality}).mp4')
    
    def download_mp4_dash(self, output_folder: str, quality: str) -> str:
        """
        Download both the video and audio tracks and merge them together with FFmpeg.
        Returns path (str) to the mp4 file.
        """
        v_track = self.v_streams[quality]['stream'].download(output_path=output_folder, filename='.vtemp')
        a_track = self.a_stream.download(output_path=output_folder, filename='.atemp')

        video = ffmpeg.input(v_track)
        audio = ffmpeg.input(a_track)

        # Merge audio to video and write file to output folder
        output_folder = os.path.normpath(output_folder)
        output_file = os.path.join(output_folder, f'{self.title} ({quality}).mp4')
        merged = ffmpeg.output(video, audio, output_file, vcodec='copy', acodec='copy')
        merged.run()

        # Remove .atemp and .vtemp
        if os.path.exists(v_track):
            os.remove(v_track)
        
        if os.path.exists(a_track):
            os.remove(a_track)

    def reset_attributes(self):
        """
        Remove all of the video data currently stored in the YouTubeDownloader object.
        Reset the state of all widgets.
        """
        self.youtube = None
        self.title = None
        self.streams = None
        self.title_label.clear()
        self.display_black_thumbnail()
        self.format_combo.setEnabled(False)
        self.quality_combo.setEnabled(False)
        self.a_stream = None
        self.v_streams = {}
        self.quality_combo.clear()
    

        

def youtube_to_mp3(url, outdir):
    """Download mp3 file from a YouTube url."""
    # Check success of download
    if new_file.exists():
        print(f'"{yt.title}" has been successfully downloaded')
    else:
        print(f'ERROR: "{yt.title}" could not be downloaded!')

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

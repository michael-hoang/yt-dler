import ffmpeg
import os
import requests
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QWidget,
    QLineEdit, QRadioButton, QComboBox, QProgressBar, QFileDialog
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
        self.streams = None
        self.url_bar = None
        self.title_label = None
        self.thumbnail_label = None
        self.a_rbtn = None
        self.v_rbtn = None
        self.combo_box = None
        self.a_stream = None
        self.v_streams = {}
        self.output_bar = None
        self.dl_btn = None

        self.setGeometry(200, 200, 560, 300)
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
        
        self.a_rbtn = QRadioButton('Audio (mp3) - Highest')
        self.a_rbtn.toggled.connect(self.radio_selected)
        self.a_rbtn.setEnabled(False)

        self.v_rbtn = QRadioButton('Video (mp4)')
        self.v_rbtn.toggled.connect(self.radio_selected)
        self.v_rbtn.setEnabled(False)

        self.combo_box = QComboBox()
        self.combo_box.setEnabled(False)
        
        layout.addWidget(self.a_rbtn)
        layout.addWidget(self.v_rbtn)
        layout.addWidget(self.combo_box)

        return layout
    
    def create_output_widgets(self) -> QHBoxLayout:
        """Create widgets to select output folder."""
        layout = QHBoxLayout()
        label = QLabel('Output:')
        self.output_bar = QLineEdit()
        btn = QPushButton('Browse')
        btn.clicked.connect(self.browser_folder)

        layout.addWidget(label)
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
        except (RegexMatchError, VideoUnavailable):
            self.title_label.setText('Search failed.')
        else:
            self.a_rbtn.setEnabled(True)
            self.v_rbtn.setEnabled(True)
            if self.v_rbtn.isChecked():
                self.combo_box.setEnabled(True)
            else:
                self.combo_box.setEnabled(False)
            self.get_streams()
            self.populate_combobox()

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
        
    def get_streams(self):
        """
        Get audio and video streams from the YouTube object.
        """
        # Get highest audio quality stream
        self.a_stream = self.streams.filter(only_audio=True).order_by('bitrate').last()
        self.get_v_streams()

        video_duration = self.youtube.length

    def get_v_streams(self):
        """Get all of the video streams available for download."""
        v_prog_streams = self.streams.filter(progressive=True).order_by('resolution')
        v_dash_streams = self.streams.filter(progressive=False, only_video=True).order_by('resolution')
       
        for stream in v_prog_streams:
            quality = f'{stream.resolution}, {stream.fps}fps'
            self.v_streams[quality] = stream
           
        for stream in v_dash_streams:
            # Remove the last 'p'
            res = stream.resolution[:-1]
            if int(res) > 720:
                quality = f'{stream.resolution}, {stream.fps}fps [{stream.codecs[0]}]'
                self.v_streams[quality] = stream

    def populate_combobox(self):
        """Populate the combobox with available video streams."""
        for stream in reversed(self.v_streams):
            self.combo_box.addItem(stream)

    def radio_selected(self):
        """
        Enable or disable the combobox when the video radiobutton is checked
        or unchecked.
        """
        if self.v_rbtn.isChecked():
            self.combo_box.setEnabled(True)
        else:
            self.combo_box.setEnabled(False)

    def browser_folder(self):
        """Open a folder browsing window."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.output_bar.setText(folder_path)

    def download(self):
        """Download the media file to the output folder."""
        output_folder = self.output_bar.text()
        if os.path.exists(output_folder):
            print('folder exists')

    def reset_attributes(self):
        """
        Remove all of the video data currently stored in the YouTubeDownloader object.
        Reset the state of all widgets.
        """
        self.youtube = None
        self.streams = None
        self.title_label.clear()
        self.display_black_thumbnail()
        self.a_rbtn.setEnabled(False)
        self.v_rbtn.setEnabled(False)
        self.combo_box.setEnabled(False)
        self.a_stream = None
        self.v_streams = {}
        self.combo_box.clear()
    

        



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

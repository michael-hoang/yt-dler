import ffmpeg
import os
from pathlib import Path
from pytube import Playlist, YouTube


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
    playlist_to_mp3(playlist_url, outdir)


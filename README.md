# waveforge-audio-converter-
A python project , it is a audio format converter
Waveforge Audio Converter
A clean, responsive desktop application for converting audio files between multiple formats. Built with Python and powered by FFmpeg, Waveforge provides an intuitive graphical interface for audio format conversion with real-time progress feedback.

Features
Multi-format support: Convert to/from WAV, MP3, FLAC, OGG, OPUS, M4A, AAC, AC3, MP4, and WEBM
Intuitive GUI: Modern desktop interface built with Tkinter, featuring a sleek dark theme with animated background
Non-blocking conversion: Background processing keeps the UI responsive during conversion
Smart defaults: Automatically sets output directory and filename based on your input selection
File browser: Easily select input files and output directories
Status tracking: Real-time progress bar and status messages
Error handling: Clear error messages if conversion fails
Requirements
Python 3.8+
FFmpeg (must be installed and available on your system PATH)
Dependencies listed in requirements.txt
Installation
Clone or download this repository
Install Python dependencies:
pip install -r requirements.txt
Install FFmpeg:
Windows: winget install FFmpeg or download from ffmpeg.org
macOS: brew install ffmpeg
Linux: sudo apt install ffmpeg
Usage
Run the GUI application:
python audio_gui.py
Or use the backend directly from the command line:
python backsend.py song.mp3 --output song.wav
python backsend.py song.wav --output song.mp3 --bitrate 192k
python backsend.py track1.ogg track2.ogg --output-dir converted --format wav
This description covers the key aspects—what it does, its features, requirements, installation, and usage. Feel free to modify it to match your project's specific tone or add any additional information you'd like highlighted!
ENJOY :D

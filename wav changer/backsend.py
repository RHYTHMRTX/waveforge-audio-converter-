"""Audio conversion backend powered by FFmpeg.

Examples:
	python backsend.py song.mp3 --output song.wav
	python backsend.py song.wav --output song.mp3 --bitrate 192k
	python backsend.py track1.ogg track2.ogg --output-dir converted --format wav
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


SUPPORTED_OUTPUT_FORMATS = {
	"aac",
	"ac3",
	"flac",
	"m4a",
	"mp3",
	"mp4",
	"ogg",
	"opus",
	"wav",
	"webm",
}


class ConversionError(RuntimeError):
	"""Raised when an audio conversion cannot be completed."""


def _find_ffmpeg() -> str:
	executable = shutil.which("ffmpeg")
	if executable is None:
		raise ConversionError(
			"FFmpeg was not found. Install it and make sure 'ffmpeg' is on PATH."
		)
	return executable


def _normalise_format(output_format: str) -> str:
	output_format = output_format.lower().lstrip(".")
	if output_format not in SUPPORTED_OUTPUT_FORMATS:
		supported = ", ".join(sorted(SUPPORTED_OUTPUT_FORMATS))
		raise ConversionError(
			f"Unsupported output format '{output_format}'. Supported formats: {supported}."
		)
	return output_format


def convert_file(
	input_path: str | Path,
	output_path: str | Path,
	*,
	sample_rate: int | None = None,
	channels: int | None = None,
	bitrate: str | None = None,
	overwrite: bool = False,
) -> Path:
	"""Convert one audio file and return the resulting path.

	FFmpeg determines the input codec from the file itself, so this works with
	any format supported by the installed FFmpeg build.
	"""
	source = Path(input_path).expanduser()
	destination = Path(output_path).expanduser()

	if not source.is_file():
		raise ConversionError(f"Input file does not exist: {source}")
	if source.resolve() == destination.resolve():
		raise ConversionError("Input and output must be different files.")
	if not destination.suffix:
		raise ConversionError("Output file must have an extension, such as .wav or .mp3.")

	output_format = _normalise_format(destination.suffix)
	destination.parent.mkdir(parents=True, exist_ok=True)

	command = [_find_ffmpeg(), "-hide_banner", "-loglevel", "error"]
	command.append("-y" if overwrite else "-n")
	command.extend(["-i", str(source)])

	if sample_rate is not None:
		command.extend(["-ar", str(sample_rate)])
	if channels is not None:
		command.extend(["-ac", str(channels)])
	if bitrate is not None and output_format != "wav":
		command.extend(["-b:a", bitrate])
	if output_format == "wav":
		command.extend(["-c:a", "pcm_s16le"])

	command.append(str(destination))
	result = subprocess.run(command, capture_output=True, text=True, check=False)
	if result.returncode != 0:
		details = result.stderr.strip() or "FFmpeg returned an unknown error."
		raise ConversionError(details)

	return destination


def build_output_path(source: Path, output_dir: Path, output_format: str) -> Path:
	"""Build a non-colliding-looking output name for batch conversion."""
	return output_dir / f"{source.stem}.{_normalise_format(output_format)}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Convert audio files using FFmpeg.")
	parser.add_argument("inputs", nargs="+", type=Path, help="Input audio file(s).")
	parser.add_argument("-o", "--output", type=Path, help="Output path for one input file.")
	parser.add_argument(
		"--output-dir", type=Path, help="Destination directory when converting multiple files."
	)
	parser.add_argument(
		"-f", "--format", dest="output_format", help="Output format for batch conversion."
	)
	parser.add_argument("--sample-rate", type=int, help="Output sample rate in Hz, e.g. 44100.")
	parser.add_argument("--channels", type=int, choices=(1, 2), help="Output channel count.")
	parser.add_argument("--bitrate", help="Audio bitrate for compressed formats, e.g. 192k.")
	parser.add_argument("-y", "--overwrite", action="store_true", help="Replace existing files.")
	return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
	args = parse_args(argv)
	try:
		if len(args.inputs) == 1 and args.output:
			outputs = [convert_file(
				args.inputs[0],
				args.output,
				sample_rate=args.sample_rate,
				channels=args.channels,
				bitrate=args.bitrate,
				overwrite=args.overwrite,
			)]
		else:
			if args.output:
				raise ConversionError("--output can only be used with one input file.")
			if not args.output_dir or not args.output_format:
				raise ConversionError("Batch conversion requires --output-dir and --format.")
			output_dir = args.output_dir.expanduser()
			outputs = []
			for source in args.inputs:
				destination = build_output_path(source, output_dir, args.output_format)
				outputs.append(convert_file(
					source,
					destination,
					sample_rate=args.sample_rate,
					channels=args.channels,
					bitrate=args.bitrate,
					overwrite=args.overwrite,
				))
	except ConversionError as error:
		print(f"Error: {error}", file=sys.stderr)
		return 1

	for output in outputs:
		print(f"Created: {output}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())

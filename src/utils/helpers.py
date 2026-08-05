import logging
import tempfile as tf
import wave
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import subprocess as sp
import magic
import uuid

_TEMP_DIR: Path = Path(tf.gettempdir())
_DOWNLOAD_DIR: Path = Path.home() / "Downloads"

def select_audio_files() -> list[Path]:
    """Open a native file dialog and return the selected audio/video paths."""
    root = tk.Tk()
    root.withdraw()

    file_paths: tuple[str, ...] = filedialog.askopenfilenames(
        parent=root,
        initialdir=str(Path.home()),
        title="Select Audio Files",
        filetypes=[("Audio Files", ["*.mp3", "*.wav", "*.flac", "*.ogg", "*.m4a", "*.aac", "*.opus", "*.wma"]),
        ("Video", ["*.mp4", "*.mkv", "*.avi", "*.mov", "*.webm", "*.flv", "*.wmv", "*.m4v"]),
        ("Todos los archivos", "*.*"),
        ],
    )
    root.destroy()
    return [Path(file_path) for file_path in file_paths]


def _command_ffmpeg(audio_file: Path, output_file: Path):
    """Build the ffmpeg argument list to convert any audio/video to 16 kHz mono WAV (s16)."""
    command: list[str] = [
        "ffmpeg",
        "-y",
        "-i", str(audio_file),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-sample_fmt", "s16",
        str(output_file),
        ]
    return command

def _is_target_wav_format_stdlib(file_path: Path) -> bool:
    try:

        with wave.open(str(file_path), "rb") as wf:
            return (
                    wf.getframerate() == 16000
                    and wf.getnchannels() == 1
                    and wf.getsampwidth() == 2 # 2 bytes = 16 bits = s16
            )

    except (wave.Error, IOError) as e:
        logging.error("Cannot read WAV header of %s: %s", file_path.name, e)
        return False

    except Exception as e:
        logging.error("Unexpected error reading %s: %s", file_path.name, e)
        return False

def generate_name_audio_file() -> Path:
        """Return a unique temp path of the form <tmpdir>/aud-<9-char-uuid>.wav."""
        unique_id: str = str(uuid.uuid4())[:9]

        file_name: str = f"aud-{unique_id}"

        return _TEMP_DIR / f"{file_name}.wav"

def generate_name_markdown_file()-> str:
    unique_id: str = str(uuid.uuid4())[:9]

    name_file_markdown: str = f"transcription-{unique_id}.md"

    return str(_DOWNLOAD_DIR / name_file_markdown)



def convert_to_wav_16_mono() -> list[Path]:
    """Prompt the user to pick files, convert each to 16 kHz mono WAV, and return the resulting paths."""
    audio_files_converted: list[Path] = []
    # audio_files: list[Path] = select_audio_files()
    audio_files: list[Path] = select_audio_files()


    for af in audio_files:
        try:
            mime: str = magic.from_file(af, mime=True)
        except (FileNotFoundError, PermissionError, OSError, IOError) as e:
            logging.error("Cannot read file %s: %s", af.name, e)
            continue

        except Exception as e:
            logging.error("Unexpected error reading file %s: %s", af, e)
            continue

        if not (mime.startswith("audio/") or mime.startswith("video/")):
            logging.error("Unsupported file type: %s (%s)", mime, af.name)
            continue

        if _is_target_wav_format_stdlib(af):
            logging.info("%s is already in target WAV format (16kHz, mono, 16-bit)", af.name)
            audio_files_converted.append(af)
            continue


        new_name: Path = generate_name_audio_file()

        try:
            sp.run(_command_ffmpeg(af, new_name), check=True)
            logging.info("%s converted into %s", af.name, new_name.name)

        except sp.CalledProcessError as e:
            logging.error("Error converting audio file %s: %s", af.name, e)
            continue

        except FileNotFoundError as e:
            logging.error("ffmpeg not found in PATH — aborting conversion")
            continue

        except PermissionError as e:
            logging.error("")
            continue

        except OSError as e:
            logging.error("I/O error converting %s: %s", af.name, e)
            continue

        except Exception as e:
            logging.error("Unexpected error converting %s: %s", af.name, e)
            continue
        logging.info("Audio file %s | type %s | converted to %s",
                            af.name, mime, new_name.name)

        audio_files_converted.append(new_name)

    return audio_files_converted
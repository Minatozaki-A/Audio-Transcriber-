import noisereduce as nr
import soundfile as sf
# import librosa
import logging
import tempfile as tf
from pathlib import Path
from utils.helpers import generate_name_audio_file



_TEMP_DIR: Path = Path(tf.gettempdir())


def reduce_noise(path_file: Path) -> Path | None:
    output_path: Path = generate_name_audio_file()

    try:
        data, rate = sf.read(path_file)
    except FileNotFoundError as e:
        logging.error("File %s not found: %s", path_file, e)
        return None
    except sf.SoundFileError as e:
        logging.error("Error reading file %s: %s", path_file, e)
        return None


    try:
        if data.ndim >= 2:
            data = data.mean(axis=1)
        reduced_noise = nr.reduce_noise(y=data, sr=rate, thresh_n_mult_nonstationary=2, stationary=False)
    except ValueError as e:
        logging.error("Error processing audio %s: %s", path_file, e)
        return None
    except MemoryError as e:
        logging.error("Out of memory processing %s: %s", path_file, e)
        return None

        # BUG (línea 18): si el audio es multi-canal (no mono), `data` es 2D; noisereduce puede
        # fallar o comportarse mal sin especificar eje/canal. El pipeline asume mono vía ffmpeg.
        # pero ya se procesa en convert_to_wav_16_mono
    try:
        sf.write(str(output_path), reduced_noise, rate)
    except (sf.SoundFileError, OSError, PermissionError) as e:
        logging.error("Error writing file %s: %s", path_file, e)
        return None

    return output_path

    # except FileNotFoundError as e:
        #logging.error("File %s not found: %s", path_file, e)

    #except sf.SoundFileError as e:
        # logging.error("Error reading file %s: %s", path_file, e)

    # except Exception as e:
        # logging.error("Error writing file %s: %s", output_path, e)
        # - logging.exception()
        # BUG (líneas 32-33): el except genérico dice "Error writing file" pero también captura
        # fallos de reduce_noise (y otros no de escritura), lo que oculta la causa real.

    # return None



"""
def audio_normalize(path_file: Path) -> Path | None:

    data, rate = librosa.load(path_file, sr=None)
    audio = librosa.util.normalize(data, norm=1)
    output_path: Path = generate_name_audio_file()

    try:
        sf.write(str(output_path), audio, rate)
    except Exception as e:
        logging.error(f"Error writing file %s: %s", output_path, e)
        return None
"""
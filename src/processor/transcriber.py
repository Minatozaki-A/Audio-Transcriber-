import gc
import torch
import logging
import ctranslate2 as ct2
from contextlib import contextmanager
from faster_whisper import WhisperModel

"""
        # Run on GPU with FP16
        # model = WhisperModel(_MODEL_SIZE, device="cuda", compute_type="float16")

        # or run on GPU with INT8
        # model = WhisperModel(_MODEL_SIZE, device="cuda", compute_type="int8_float16")

        # or run on CPU with INT8
        model = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8")
"""

@contextmanager
def whisper_model(
        model_size: str,
        device: str,
        compute_type: str
    ):
    """Context manager that loads a WhisperModel and guarantees GPU/CPU memory is freed on exit."""
    model = None

    try:
        model = WhisperModel(model_size, device, compute_type)
        logging.info("Model loaded successfully: %s (%s, %s)" % (model_size, device, compute_type))

    except torch.cuda.OutOfMemoryError as e:
        logging.error("CUDA OOM loading model '%s': %s", model_size, e)
        raise

    except (RuntimeError, ValueError, OSError, IOError) as e:
        logging.error("Failed to load model '%s' (device=%s, compute_type=%s): %s",
                      model_size, device, compute_type, e)
        raise

    else:
        try:
            yield model
        except Exception:
            logging.exception("Error during model usage")
            raise

    finally:
        if model is not None:
            del model
            gc.collect()
            logging.info("Model garbage collected")

        if device == "cuda" and torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
                logging.info("CUDA memory cleanup")
            except RuntimeError as e:
                logging.error("Failed to clean CUDA memory: %s", e)


def load_whisper_model():
    try:
        cuda_available = ct2.get_cuda_device_count() > 0
    except Exception:
        cuda_available = False

    if cuda_available:
         try:
             logging.info("Cuda is available: loading model in DGPU with FP16")
             return whisper_model(
                 model_size="medium",
                 device="cuda",
                 compute_type="float16"
             )
         except (RuntimeError,OSError) as e:
             logging.warning("Failed to load model in DGPU with FP16: %s", e)

    logging.info("Loading model in CPU with INT8")
    return whisper_model(
        model_size="small",
        device="cpu",
        compute_type="int8"
    )




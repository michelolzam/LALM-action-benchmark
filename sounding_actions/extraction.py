"""Cut benchmark audio clips out of locally downloaded Ego4D / Ego-Exo4D videos.

Where the source videos live (relative to the download directories created by
the official `ego4d` and `egoexo` downloaders):

    Ego4D      <ego4d_root>/v2/full_scale/<video_uid>.mp4
    Ego-Exo4D  <egoexo4d_root>/takes/<take_name>/ego_preview.mp4

The manifest stores these relative paths in the `source_video` column.
"""
import subprocess
from pathlib import Path
from typing import Union

import soundfile as sf

PathLike = Union[str, Path]


def source_video_path(dataset: str, source_video: str,
                      ego4d_root: PathLike, egoexo4d_root: PathLike) -> Path:
    roots = {'Ego4D': ego4d_root, 'Ego-Exo4D': egoexo4d_root}
    if roots.get(dataset) is None:
        raise ValueError(f'No download directory given for {dataset}')
    return Path(roots[dataset]) / source_video


def extract_clip(video_path: PathLike, clip_path: PathLike, start_sec: float, end_sec: float,
                 overwrite: bool = False) -> None:
    """Write the audio stream of `video_path` between `start_sec` and `end_sec` to FLAC.

    These are the ffmpeg options used to build the benchmark (`-y` and
    `-loglevel` only silence ffmpeg): the audio is not resampled, re-mixed or
    normalised, so the clip keeps the sampling rate (48 kHz) and channel layout
    of the source video. `str()` of the timestamps is passed so that the seek
    positions are identical to the original run.
    """
    clip_path = Path(clip_path)
    if clip_path.exists() and not overwrite:
        return
    clip_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = clip_path.with_name(clip_path.stem + '.partial.flac')

    cmd = [
        'ffmpeg', '-y', '-loglevel', 'error',
        '-ss', str(start_sec),
        '-to', str(end_sec),
        '-i', str(video_path),
        '-q:a', '0',
        '-map', 'a',
        str(tmp_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as err:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeError(f'ffmpeg failed on {video_path}:\n{err.stderr}') from err
    tmp_path.replace(clip_path)  # only complete files end up under the final name


def audio_info(path: PathLike) -> dict:
    info = sf.info(str(path))
    return {'sample_rate': info.samplerate,
            'num_channels': info.channels,
            'num_samples': info.frames}

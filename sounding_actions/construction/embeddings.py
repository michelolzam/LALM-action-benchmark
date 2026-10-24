"""Stage 3: CLAP audio embeddings of the candidate segments.

Model: Microsoft CLAP, 2023 release (`pip install msclap`), which reads audio
at 44.1 kHz in 7 s windows. The preprocessing below mirrors the one used for
the paper so that embeddings are comparable:

  * the audio is resampled to 44.1 kHz;
  * all channels are flattened into one signal (`reshape(-1)`), i.e. the
    channels of stereo clips are concatenated one after the other;
  * signals shorter than 7 s are repeated and truncated to 7 s; longer ones are
    cropped to a random 7 s window.

The random crop makes the embeddings of clips longer than 7 s non-deterministic
across runs. The original run did not fix a seed, so its embeddings cannot be
regenerated exactly; here the crop is drawn from a seeded generator.
"""
import random

import numpy as np
import torch
import torchaudio
from tqdm import tqdm


def load_clap(use_cuda=None):
    from msclap import CLAP
    if use_cuda is None:
        use_cuda = torch.cuda.is_available()
    return CLAP(version='2023', use_cuda=use_cuda)


def preprocess(audio_path, rng, sample_rate=44100, duration_sec=7):
    audio, sr = torchaudio.load(audio_path)
    if sr != sample_rate:
        audio = torchaudio.transforms.Resample(sr, sample_rate)(audio)
    audio = audio.reshape(-1)

    n_samples = duration_sec * sample_rate
    if n_samples >= audio.shape[0]:
        repeats = int(np.ceil(n_samples / audio.shape[0]))
        audio = audio.repeat(repeats)[:n_samples]
    else:
        start = rng.randrange(audio.shape[0] - n_samples)
        audio = audio[start:start + n_samples]
    return audio.float()


def clap_embeddings(audio_paths, clap=None, batch_size=8, seed=0):
    """Return an array of shape (len(audio_paths), 1024)."""
    clap = clap or load_clap()
    device = 'cuda' if clap.use_cuda and torch.cuda.is_available() else 'cpu'
    rng = random.Random(seed)

    embeddings = []
    for i in tqdm(range(0, len(audio_paths), batch_size), desc='CLAP embeddings'):
        batch = [preprocess(p, rng, clap.args.sampling_rate, clap.args.duration)
                 for p in audio_paths[i:i + batch_size]]
        batch = torch.stack(batch).unsqueeze(1).to(device)  # (batch, 1, samples)
        embeddings.append(clap._get_audio_embeddings(batch).cpu().numpy())
    return np.concatenate(embeddings)

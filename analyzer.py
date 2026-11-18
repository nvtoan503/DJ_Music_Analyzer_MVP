"""Audio analysis for DJ Music Analyzer MVP.

Genre suggestions are transparent heuristics, NOT a trained genre model.
"""
from __future__ import annotations

import os
import numpy as np


def _waveform(y: np.ndarray, bins: int = 900) -> list[float]:
    """Lightweight peak envelope for fast drawing in Qt."""
    if y.size == 0:
        return []
    edges = np.linspace(0, len(y), bins + 1, dtype=np.int64)
    return [round(float(np.max(np.abs(y[a:b]))), 4) if b > a else 0.0
            for a, b in zip(edges[:-1], edges[1:])]


def suggest_genre(bpm: float, bass_ratio: float, brightness: float,
                  onset_density: float, dynamic_range: float) -> tuple[str, str]:
    """DJ-oriented rule-of-thumb classification; not objective genre recognition."""
    if bpm <= 0:
        return 'Chưa xác định', 'Không phát hiện được nhịp ổn định'
    # These genres overlap and may be defined differently by different DJs.
    if bpm >= 137 and bass_ratio > 0.22:
        return 'Vinahouse', 'BPM cao và tỷ lệ năng lượng bass lớn'
    if bpm >= 130 and (onset_density > 2.0 or brightness > 2300):
        return 'House Lắc', 'Nhịp nhanh, nhiều onset hoặc phổ âm sáng'
    if 118 <= bpm <= 137 and (dynamic_range > 0.13 or brightness > 1900):
        return 'EDM', 'Nhịp dance và phổ âm hoặc độ tương phản lớn'
    if bpm >= 135:
        return 'House Lắc', 'Nhịp nhanh (ước lượng tạm)'
    return 'EDM', 'Nhãn mặc định cho nhạc điện tử; cần DJ kiểm tra'


def analyze_file(path: str) -> dict:
    # Lazy imports keep startup fast; librosa and dependencies load in worker thread.
    import librosa

    # Downsample + cap length for practical batch analysis. First 180 seconds can
    # miss later style changes; this is an MVP tradeoff.
    y, sr = librosa.load(path, sr=22050, mono=True, duration=180.0)
    if y.size < sr:
        raise ValueError('File âm thanh quá ngắn hoặc không đọc được')
    full_duration = float(librosa.get_duration(path=path))

    # Beat tracking. lib::beat_track can return numpy scalar or ndarray.
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
    tempo, beat_frames = librosa.beat.beat_track(
        onset_envelope=onset_env, sr=sr, hop_length=512, trim=False
    )
    raw_bpm = float(np.ravel(tempo)[0]) if np.size(tempo) else 0.0
    if not np.isfinite(raw_bpm):
        raw_bpm = 0.0
    # Normalize common half-time/double-time ambiguity for dance tracks.
    normalized = raw_bpm
    if 0 < normalized < 95:
        normalized *= 2
    elif normalized > 175:
        normalized /= 2
    bpm = round(normalized, 1)

    # Approximate features for heuristic labeling.
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    frequencies = librosa.fft_frequencies(sr=sr, n_fft=2048)
    bass = float(np.sum(S[frequencies < 180]))
    total = float(np.sum(S)) + 1e-8
    bass_ratio = bass / total
    brightness = float(np.mean(librosa.feature.spectral_centroid(S=S, sr=sr)))
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=512)
    onset_density = float(len(onsets) / (len(y) / sr))
    rms = librosa.feature.rms(y=y)[0]
    dynamic_range = float(np.percentile(rms, 90) - np.percentile(rms, 10))
    genre, why = suggest_genre(bpm, bass_ratio, brightness, onset_density, dynamic_range)

    return {
        'path': os.path.abspath(path),
        'name': os.path.basename(path),
        'duration': round(full_duration, 2),
        'bpm': bpm,
        'raw_bpm': round(raw_bpm, 1),
        'genre': genre,
        'suggested_genre': genre,
        'reason': why,
        'waveform': _waveform(y),
        'analyzed_seconds': round(len(y) / sr, 1),
    }

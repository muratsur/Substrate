"""Convert Kenney 'Impact Sounds' (CC0, kenney.nl, downloaded 2026-10-25) footstep_concrete_000..004.ogg into
Content/Substrate/Audio/FS_Concrete_01..05.wav: mono, leading silence trimmed (keep 5 ms), peak-normalized to -6 dBFS,
10 ms fade-out. Usage: python -I _tools/convert_kenney_footsteps.py <folder with the .ogg files>"""
import sys, os
import numpy as np, soundfile as sf
src = sys.argv[1]
for i in range(5):
    x, sr = sf.read(os.path.join(src, f'footstep_concrete_{i:03d}.ogg'), dtype='float64', always_2d=True)
    x = x.mean(axis=1)
    on = int(np.argmax(np.abs(x) > 0.02 * np.abs(x).max()))
    x = x[max(0, on - int(0.005 * sr)):]
    fade = int(0.01 * sr); x[-fade:] *= np.linspace(1, 0, fade)
    x *= (10 ** (-6 / 20)) / np.abs(x).max()
    spec = np.abs(np.fft.rfft(x)) ** 2; f = np.fft.rfftfreq(len(x), 1 / sr)
    out = f'Content/Substrate/Audio/FS_Concrete_{i + 1:02d}.wav'
    sf.write(out, x, sr, subtype='PCM_16')
    print(out, f'{len(x) / sr * 1000:.0f} ms, {sr} Hz, energy <500 Hz {spec[f < 500].sum() / spec.sum():.0%}, 1-5 kHz {spec[(f >= 1000) & (f <= 5000)].sum() / spec.sum():.0%}')

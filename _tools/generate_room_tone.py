"""Generate a 60 s seamless sewer room tone (the project's three AMB_* loops are one identical water/wading recording).
Low machinery hum (48 Hz + harmonics, slow 20 s beat) over soft brown-ish noise band-limited to ~25-300 Hz, stereo.
Seamless by construction: noise is built in the frequency domain (a periodic signal), and every sine completes a whole
number of cycles in 60 s. Peak -9 dBFS. Writes Content/Substrate/Audio/AMB_RoomTone_Hum.wav (editor auto-imports it)."""
import wave, numpy as np
SR, T = 48000, 60
N = SR * T
rng = np.random.default_rng(7)
t = np.arange(N) / SR
f = np.fft.rfftfreq(N, 1 / SR)
shape = (1 / (f + 20.0)) * (f / (f + 25.0)) / (1 + (f / 300.0) ** 4)   # brown-ish, highpass ~25 Hz, lowpass ~300 Hz
def noise():
    spec = shape * np.exp(2j * np.pi * rng.random(f.size))
    spec[0] = 0
    x = np.fft.irfft(spec, N)
    return x / np.abs(x).max()
common, l, r = noise(), noise(), noise()
def tone(hz, amp):
    assert abs(hz * T - round(hz * T)) < 1e-9, f'{hz} Hz does not loop in {T}s'
    return amp * np.sin(2 * np.pi * hz * t)
hum = tone(48, 1.0) + tone(48.05, 0.6) + tone(96, 0.45) + tone(144, 0.2) + tone(192, 0.08)   # 48 vs 48.05 -> 20 s beat
hum *= 1 + 0.12 * np.sin(2 * np.pi * t / 20)                                                   # 3 slow swells per loop
hum /= np.abs(hum).max()
L = 0.65 * (0.7 * common + 0.3 * l) + 0.35 * hum
R = 0.65 * (0.7 * common + 0.3 * r) + 0.35 * hum
st = np.stack([L, R], axis=1)
st *= (10 ** (-9 / 20)) / np.abs(st).max()
pcm = (st * 32767).astype('<i2')
out = 'Content/Substrate/Audio/AMB_RoomTone_Hum.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
# self-check: the jump across the loop point is no bigger than an ordinary sample-to-sample step
step = np.abs(np.diff(st, axis=0)).max(axis=0)
seam = np.abs(st[0] - st[-1])
print(out, f'{N/SR:.0f}s', 'peak dBFS %.1f' % (20 * np.log10(np.abs(st).max())), 'rms dBFS %.1f' % (20 * np.log10(np.sqrt((st ** 2).mean()))))
print('loop seam jump', seam.round(5), 'vs max normal step', step.round(5))
assert (seam <= step).all()

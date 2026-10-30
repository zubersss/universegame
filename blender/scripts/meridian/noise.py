"""Periodic noise (FFT-filtered white noise): tiles exactly over the array size."""
import numpy as np


def fft_noise(rng, h, w, lo, hi, slope=1.0):
    """Periodic band-limited 2D noise, unit std. lo/hi: wavelength range in px."""
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.rfftfreq(w)[None, :]
    f = np.hypot(fy, fx)
    f[0, 0] = 1.0
    band = (f >= 1.0 / hi) & (f <= 1.0 / lo)
    spec = (rng.standard_normal(f.shape) + 1j * rng.standard_normal(f.shape)) * band / f ** slope
    spec[0, 0] = 0
    n = np.fft.irfft2(spec, s=(h, w))
    return n / (n.std() + 1e-9)


def fft_noise_1d(rng, n, lo, hi, slope=1.0):
    """Periodic band-limited 1D noise of length n, unit std."""
    f = np.fft.rfftfreq(n)
    f[0] = 1.0
    band = (f >= 1.0 / hi) & (f <= 1.0 / lo)
    spec = (rng.standard_normal(f.shape) + 1j * rng.standard_normal(f.shape)) * band / f ** slope
    spec[0] = 0
    x = np.fft.irfft(spec, n=n)
    return x / (x.std() + 1e-9)

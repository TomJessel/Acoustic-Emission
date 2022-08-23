from nptdms import TdmsFile
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import mplcursors
from scipy.stats import kurtosis
import multiprocessing
from functools import partial
import time


def rms(x):
    r = np.sqrt(np.mean(x ** 2))
    return r


class AE:
    def __init__(self, ae_files, pre_amp, fs, testinfo):
        self.files = ae_files
        self.kurt = []
        self.RMS = []
        self.pre_amp = pre_amp
        self.fs = fs
        self._testinfo = testinfo

    @staticmethod
    def volt2db(v):
        v_ref = 1E-4
        db = [20*(np.log10(vin/v_ref)) for vin in v]
        return db

    def fftcalc(self, fno, freqres):
        length = int(self.fs / freqres)
        data = self.readAE(fno)
        if len(data) % length == 0:
            temp = np.reshape(data, (length, -1), order='F')
        else:
            leftover = int(length - np.fmod(len(data), length))
            temp = np.pad(data, (0, leftover), 'constant', constant_values=0)
            temp = np.reshape(temp, (length, -1), order='F')

        win = np.hanning(length)
        win = np.expand_dims(win, axis=-1)
        temp = np.multiply(win, temp)
        sc = len(win) / sum(win)

        fft = np.fft.fft(temp, n=length, axis=0)
        p2 = abs(fft / length)
        p = p2[0:int(np.floor(length / 2)), :]
        p[1:] = p[1:] * 2
        p = np.array(p * sc)
        fft_mean = np.mean(p, axis=1)
        return fft_mean

    def readAE(self, fno):
        test = TdmsFile.read(self.files[fno])
        prop = test.properties
        data = []
        for group in test.groups():
            for channel in group.channels():
                data = channel[:]
        if not data.dtype == float:
            data = (data.astype(np.float) * prop.get('Gain')) + prop.get('Offset')
        if not self.pre_amp.gain == 40:
            if self.pre_amp.gain == 20:
                data = data * 10
            elif self.pre_amp == 60:
                data = data / 10
        return data

    def plotAE(self, fno):
        signal = self.readAE(fno)
        ts = 1 / self.fs
        n = signal.size
        t = np.arange(0, n) * ts
        filename = self.files[fno].partition('_202')[0]
        filename = filename[-8:]
        matplotlib.use("Qt5Agg")
        plt.figure()
        plt.plot(t, signal, linewidth=1)
        plt.title(filename)
        plt.autoscale(enable=True, axis='x', tight=True)
        plt.xlabel('Time (s)')
        plt.ylabel('Voltage (V)')
        mplcursors.cursor(multiple=True)
        plt.show()

    def plotfft(self, fno, freqres=1000):
        p = self.fftcalc(fno, freqres)
        f = np.arange(0, self.fs/2, freqres, dtype=int)

        filename = self.files[fno].partition('_202')[0]
        filename = filename[-8:]
        matplotlib.use('Qt5Agg')
        plt.figure()
        plt.plot(f / 1000, self.volt2db(p), linewidth=0.75)
        plt.title(f'Test No: {self._testinfo.testno} - FFT File {filename[-3:]}')
        plt.autoscale(enable=True, axis='x', tight=True)
        plt.xlabel('Frequency (kHz)')
        plt.ylabel('Amplitude (dB)')
        plt.grid()
        mplcursors.cursor(multiple=True)
        plt.show()
            # todo File 155 showing weird FFT

    def process(self):
        with multiprocessing.Pool() as pool:
            results = np.array(pool.map(self._calc, range(len(self.files))))
        pool.close()

        self.kurt = results[:, 0]
        self.RMS = results[:, 1]

    def _calc(self, fno):
        data = self.readAE(fno)
        r = rms(data)
        k = kurtosis(data, fisher=False)
        print(f'Completed File {fno}...')
        return k, r

    def fftsurf(self, res=1000):

        # todo finish off FFT plotting and calc
        with multiprocessing.Pool() as pool:
            results = pool.map(partial(self.fftcalc, freqres=res), range(len(self.files)))

        f = np.arange(0, self.fs/2, res, dtype=int)
        n = np.arange(0, len(self.files))
        p = self.volt2db(np.array(results))
        p = np.array(p)

        x, y = np.meshgrid(f, n)
        fig = plt.figure()
        ax = fig.add_subplot(projection='3d')
        surf = ax.plot_surface(x, y, p, cmap='jet')
        fig.show()
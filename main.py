#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@File    :   main.py
@Author  :   Tom Jessel
@Contact :   jesselt@cardiff.ac.uk

@Modify Time      @Author    @Version    @Description
------------      -------    --------    -----------
22/08/2022 13:46   tomhj      1.0         Main file
"""
import os

import mplcursors
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy
import seaborn as sns
import mplcursors
from scipy.signal import hilbert

from Experiment import load


def corr_matrix(df: pd.DataFrame, save_fig: bool = True):
    cols = df.columns
    plt.ion()
    fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
    sns.heatmap(df.corr(),
                ax=ax,
                annot=True,
                xticklabels=cols,
                yticklabels=cols,
                vmin=-1,
                vmax=1) \
        .set(title='Correlation Matrix')
    plt.tight_layout()
    plt.show()
    if save_fig:
        path = f'{exp.test_info.dataloc}/Figures'
        png_name = f'{path}/Test {exp.test_info.testno} - Correlation Matrix.png'
        if not os.path.isdir(path) or not os.path.exists(path):
            os.makedirs(path)
        fig.savefig(png_name, dpi=200)
    return df.corr()


def corr_pairplot(df: pd.DataFrame, save_fig: bool = True):
    sns.pairplot(df, height=1.05, aspect=1.85)
    if save_fig:
        path = f'{exp.test_info.dataloc}/Figures'
        png_name = f'{path}/Test {exp.test_info.testno} - Pair Plot.png'
        plt.savefig(png_name, dpi=300)
    plt.show()


def ae_hits(exp: object, s: np.array):
    """
    Convert AE signal into hit data
    :param ex: object: experiement object
    :param s: ndarray: AE signal
    """
    def dbtov(db):
        v_ref = 1E-4
        v = [(10 ** (d / 20)) * v_ref for d in db]
        return v

    # THRESHOLD
    th = 91
    # hit time definition parameters from AEwin
    HDT = 800E-6
    PDT = 200E-6
    HLT = 1000E-6
    MAXD = 1000E-3
    fs = exp.test_info.acquisition[0]
    th_v = dbtov([th])

    abs_sig = np.abs(s)
    th_ind = abs_sig > th_v

    fig, ax = plt.subplots()
    ax.plot(np.arange(0, len(s))*(1/fs), s)
    ax.axhline(y=th_v[0], color='r')
    ax.axhline(y=(-1 * th_v[0]), color='r')
    mplcursors.cursor(multiple=True)
    plt.show()
    # todo finish ae hits attempt
    pass


def envelope_hilbert(s):
    z = hilbert(s)
    inst_amp = np.abs(z)
    fig, ax = plt.subplots(2, 1, sharex=True)
    ax[0].plot(s)
    ax[0].plot(inst_amp, 'r')
    ax[1].plot(inst_amp, 'r')
    plt.show()

    yf = scipy.fft.fft(s)
    xf = scipy.fft.fftfreq(len(s), 1/2000000)
    plt.figure()
    plt.plot(xf, np.abs(yf))
    plt.show()
    # todo investigate enveloping more

if __name__ == '__main__':
    exp = load(file='Test 5')
    sig = exp.ae.readAE(10)[10000000:15000000]
    envelope_hilbert(sig)

    # ae_hits(exp, sig[0:3000000])
    # feat = exp.features.copy()
    # feat.drop([0, 1, 23, 24])
    # c = corr_matrix(feat.drop([0, 1, 23, 24]), save_fig=False)
    # corr_pairplot(feat.drop([0, 1, 23, 24]), save_fig=False)

#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@File    :   config.py
@Author  :   Tom Jessel
@Contact :   jesselt@cardiff.ac.uk

@Modify Time      @Author    @Version    @Description
------------      -------    --------    -----------
22/08/2022 13:46   tomhj      1.0        Config file for constants and paths.
"""

import os
from pathlib import Path

# Paths
# -----------------------------------------------------------------------------
# TODO: Make this a function so it only gets called once
# TODO: Test the paths on both WSL and windows


def config_paths():
    """
    Find directory paths for the project.

    Returns:
        HOME_DIR (pathlib.Path): Home directory for the user.
        BASE_DIR (pathlib.Path): Base directory for all data and code.
        CODE_DIR (pathlib.Path): Code directory.
        TB_DIR (pathlib.Path): Tensorboard directory.
        RMS_DATA_DIR (pathlib.Path): RMS data directory.
    """
    # Home directory from OS and user
    PLATFORM = os.name
    if PLATFORM == 'posix':
        HOME_DIR = Path.home()

    elif PLATFORM == 'nt':
        HOME_DIR = Path.home()
    else:
        raise OSError('OS not supported')

    # Relative paths to other directories

    # Base directory for all data and code
    BASE_DIR = HOME_DIR.joinpath(r'OneDrive - Cardiff University',
                                 r'Documents',
                                 r'PHD',
                                 r'AE',
                                 )
    # Code directory
    CODE_DIR = BASE_DIR.joinpath(r'PYTHON',
                                 r'Acoustic-Emission',
                                 )
    # Tensorboard directory
    TB_DIR = BASE_DIR.joinpath(r'TensorBoard',
                               )
    # RMS data directory
    RMS_DATA_DIR = BASE_DIR.joinpath(r'Testing',
                                     r'RMS',
                                     )
    return HOME_DIR, BASE_DIR, CODE_DIR, TB_DIR, RMS_DATA_DIR

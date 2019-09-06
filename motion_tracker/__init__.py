from matplotlib import pyplot as plt
import numpy as np
import os
from scipy import interpolate, ndimage, spatial
from skvideo import io
from skimage.feature import peak_local_max
from sklearn import cluster
import subprocess
import sys

from PyQt5.QtWidgets import QWidget, QFileDialog, QApplication
from points_GUI import *

from sklearn.exceptions import ConvergenceWarning
import warnings
warnings.filterwarnings("ignore", category=ConvergenceWarning)

colors = [
    'tab:red',
    'tab:green',
    'tab:blue',
    'tab:orange',
    'tab:purple',
]


def print_progress(part, whole):
    prop = float(part)/float(whole)
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%%" % ("="*int(20*prop), 100*prop))
    sys.stdout.flush()


filetypes = [
    ('h264 videos', '*.h264'),
    ('mpeg videos', '*.mpg *.mpeg *.mp4'),
    ('avi videos', '*.avi'),
    ('quicktime videos', '*.mov *.qt'),
    ('all files', '*')
]

# format the filetypes for the pyqt file dialog box
ftypes = []
for (fname, ftype) in filetypes:
    ftypes += [f"{fname} ({ftype})"]
ftypes = ";;".join(ftypes)


def rotate(arr, theta, axis=0):
    """Generate a rotation matrix and rotate input array along a single axis. 
    If only one axis, it will rotate counter-clockwise"""
    # theta = -theta
    rot_matrix = np.array(
        [[np.cos(theta), -np.sin(theta)],
         [np.sin(theta), np.cos(theta)]])
    nx, ny, = np.dot(arr, rot_matrix).T
    nx = np.squeeze(nx)
    ny = np.squeeze(ny)
    return np.array([nx, ny]).T


def save_thumbnail(fn, new_fn=None):
    if new_fn is None:
        ftype = fn.split(".")[-1]
        ftype = f".{ftype}"
        new_fn = fn.replace(ftype, "_thumbnail.jpg")
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-nostats",
        "-i", fn,
        "-vf", "select=gte(n\,100)",
        "-vframes", "1", new_fn
    ]
    subprocess.call(cmd)


class FileSelector(QWidget):
    """Offers a file selection dialog box with filters based on common image filetypes.
    """

    def __init__(self, filetypes=ftypes):
        super().__init__()
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        self.title = 'Select the videos you want to process.'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.filetypes = filetypes
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.openFileNamesDialog()
        self.show()

    def openFileNamesDialog(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        self.files, self.ftype = QFileDialog.getOpenFileNames(
            self,
            "QFileDialog.getOpenFileNames()",
            "",
            self.filetypes,
            options=options)
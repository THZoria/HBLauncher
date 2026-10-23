"""Locate a TrueType font on Linux or Windows."""
import os
from pathlib import Path


def font_path():
    for name in (os.environ.get('HB_FONT'), '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 str(Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / 'segoeui.ttf')):
        if name and Path(name).is_file():
            return name
    raise FileNotFoundError('Set HB_FONT to a TrueType font file')

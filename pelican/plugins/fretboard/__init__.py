import logging
import os
from pelican import signals

logger = logging.getLogger(__name__)
_settings = {}

def _initialized(pelican):
    _settings['CONTENT_PATH'] = pelican.settings.get('PATH', 'content')
    _settings['FRETDROM_CLI'] = pelican.settings.get('FRETDROM_CLI', 'fretdrom')

    img_dir = os.path.join(_settings['CONTENT_PATH'], 'images', 'fretboard')
    os.makedirs(img_dir, exist_ok=True)

    md = pelican.settings.setdefault('MARKDOWN', {})
    md.setdefault('extensions', [])
    ext = 'pelican.plugins.fretboard.preprocessor'
    if ext not in md['extensions']:
        md['extensions'].append(ext)

def register():
    signals.initialized.connect(_initialized)

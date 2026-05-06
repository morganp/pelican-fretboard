from __future__ import annotations
import hashlib, logging, os, re, subprocess, tempfile
from markdown import Extension
from markdown.preprocessors import Preprocessor
from pelican.plugins.fretboard import _settings

logger = logging.getLogger(__name__)

OUTER_FENCE_RE = re.compile(
    r'^(?P<fence>`{4,}|~{4,})[^\n]*\n.*?^(?P=fence)[ \t]*$',
    re.MULTILINE | re.DOTALL
)

FRETDROM_FENCE_RE = re.compile(
    r'^(?P<fence>`{3,}|~{3,})[ \t]*fretdrom[ \t]*\n'
    r'(?P<content>.*?)'
    r'^(?P=fence)[ \t]*$',
    re.MULTILINE | re.DOTALL
)

def _apply_outside_fences(text, func):
    result = []
    last = 0
    for m in OUTER_FENCE_RE.finditer(text):
        result.append(func(text[last:m.start()]))
        result.append(m.group())
        last = m.end()
    result.append(func(text[last:]))
    return ''.join(result)

class FretdromPreprocessor(Preprocessor):
    def run(self, lines):
        text = '\n'.join(lines)
        text = _apply_outside_fences(text, lambda t: FRETDROM_FENCE_RE.sub(self._replace, t))
        return text.split('\n')

    def _replace(self, match):
        return _render_or_cached(match.group('content').strip())

class FretdromExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(FretdromPreprocessor(md), 'fretdrom_block', 27)

def makeExtension(**kwargs):
    return FretdromExtension(**kwargs)

def _render_or_cached(content):
    content_path = _settings.get('CONTENT_PATH', 'content')
    cli = _settings.get('FRETDROM_CLI', 'fretdrom')
    h = hashlib.md5(content.encode()).hexdigest()
    filename = f'fretboard_{h}.svg'
    svg_path = os.path.join(content_path, 'images', 'fretboard', filename)

    if os.path.exists(svg_path):
        return _img_ref(filename)

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json5', delete=False) as f:
            f.write(content)
            tmp_path = f.name
        r = subprocess.run(
            [cli, '-i', tmp_path],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode != 0:
            logger.warning('fretboard: CLI failed: %s', r.stderr.strip())
            return _fallback(content)
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(r.stdout)
        logger.info('fretboard: rendered %s', filename)
        return _img_ref(filename)
    except FileNotFoundError:
        logger.warning('fretboard: fretdrom not found. Install with: npm install -g fretdrom')
        return _fallback(content)
    except subprocess.TimeoutExpired:
        logger.warning('fretboard: timed out')
        return _fallback(content)
    finally:
        if tmp_path:
            try: os.unlink(tmp_path)
            except OSError: pass

def _img_ref(filename):
    return f'![fretboard diagram]({{static}}/images/fretboard/{filename})'

def _fallback(content):
    return f'```json5\n{content}\n```'

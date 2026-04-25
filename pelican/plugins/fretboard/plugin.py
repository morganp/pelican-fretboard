import hashlib
import html
import logging
import os
import re

import yaml
from pelican import signals

try:
    from markdown.preprocessors import Preprocessor
    from markdown.extensions import Extension as MdExtension
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

from . import chord as chord_renderer
from . import scale as scale_renderer
from . import tab as tab_renderer

log = logging.getLogger(__name__)

# Matches ```chord / ```scale / ```tab blocks in raw markdown source
FENCED_RE = re.compile(
    r'^```(chord|scale|tab)[ \t]*\n(.*?)^```[ \t]*$',
    re.MULTILINE | re.DOTALL,
)

# Matches outer fenced blocks with 4+ backticks (used to protect inner code examples)
OUTER_FENCE_RE = re.compile(
    r'^(`{4,})(.*?)^\1[ \t]*$',
    re.MULTILINE | re.DOTALL,
)

# Fallback: matches <pre><code class="language-chord"> in rendered HTML
BLOCK_RE = re.compile(
    r'<pre><code[^>]*class="language-(chord|scale|tab)"[^>]*>(.*?)</code></pre>',
    re.DOTALL,
)

DEFAULT_CACHE_PATH = "content/images/fretboard"
DEFAULT_CACHE_URL = "/images/fretboard"


def _ensure_cache(path):
    os.makedirs(path, exist_ok=True)


def _render(block_type, data, settings):
    colors = settings.get("FRETBOARD_COLORS")
    if block_type == "chord":
        return chord_renderer.render(data, colors)
    if block_type == "scale":
        return scale_renderer.render(data, colors)
    if block_type == "tab":
        return tab_renderer.render(data, colors)
    return None


def _make_replacement(block_type, raw_yaml, cache_path, cache_url, settings):
    block_hash = hashlib.sha256(raw_yaml.encode()).hexdigest()[:16]
    filename = f"fretboard_{block_hash}.svg"
    filepath = os.path.join(cache_path, filename)

    if not os.path.exists(filepath):
        try:
            data = yaml.safe_load(raw_yaml) or {}
            svg = _render(block_type, data, settings)
            if svg:
                with open(filepath, "w", encoding="utf-8") as fh:
                    fh.write(svg)
            else:
                return None
        except Exception as exc:
            log.warning("pelican-fretboard: failed to render %s block: %s", block_type, exc)
            return None

    try:
        data = yaml.safe_load(raw_yaml) or {}
        name = data.get("name", block_type.title() + " diagram")
    except Exception:
        name = block_type.title() + " diagram"

    src = f"{cache_url}/{filename}"
    return (
        f'<figure class="fretboard-diagram fretboard-{block_type}">'
        f'<img src="{src}" alt="{html.escape(name)}" loading="lazy" />'
        f"<figcaption>{html.escape(name)}</figcaption>"
        f"</figure>"
    )


if HAS_MARKDOWN:
    class FretboardPreprocessor(Preprocessor):
        def __init__(self, md, cache_path, cache_url, pelican_settings):
            super().__init__(md)
            self.cache_path = cache_path
            self.cache_url = cache_url
            self.pelican_settings = pelican_settings

        def run(self, lines):
            text = '\n'.join(lines)
            _ensure_cache(self.cache_path)

            # Build a set of character ranges that are inside 4+ backtick fences
            # (code examples) so we don't render those blocks as diagrams
            protected = [(m.start(), m.end()) for m in OUTER_FENCE_RE.finditer(text)]

            def replace(m):
                pos = m.start()
                if any(start <= pos < end for start, end in protected):
                    return m.group(0)
                block_type = m.group(1).lower()
                raw_yaml = m.group(2).strip()
                result = _make_replacement(
                    block_type, raw_yaml,
                    self.cache_path, self.cache_url, self.pelican_settings,
                )
                if result:
                    return '\n' + result + '\n'
                return m.group(0)

            text = FENCED_RE.sub(replace, text)
            return text.split('\n')

    class FretboardMarkdownExtension(MdExtension):
        def __init__(self, cache_path, cache_url, pelican_settings):
            self.cache_path = cache_path
            self.cache_url = cache_url
            self.pelican_settings = pelican_settings
            super().__init__()

        def extendMarkdown(self, md):
            # Priority 175 runs before fenced_code (25) so CodeHilite never sees these blocks
            md.preprocessors.register(
                FretboardPreprocessor(md, self.cache_path, self.cache_url, self.pelican_settings),
                'fretboard',
                175,
            )


def add_markdown_extension(pelican_obj):
    if not HAS_MARKDOWN:
        return
    settings = pelican_obj.settings
    cache_path = settings.get("FRETBOARD_CACHE_PATH", DEFAULT_CACHE_PATH)
    cache_url = settings.get("FRETBOARD_CACHE_URL", DEFAULT_CACHE_URL)

    md_config = settings.setdefault("MARKDOWN", {})
    extensions = md_config.setdefault("extensions", [])

    if not any(isinstance(e, FretboardMarkdownExtension) for e in extensions):
        extensions.append(FretboardMarkdownExtension(cache_path, cache_url, settings))


def process_content(content):
    """Fallback HTML pass for non-Markdown content or renderers that emit language- classes."""
    if not hasattr(content, "_content") or content._content is None:
        return

    settings = getattr(content, "settings", {})
    cache_path = settings.get("FRETBOARD_CACHE_PATH", DEFAULT_CACHE_PATH)
    cache_url = settings.get("FRETBOARD_CACHE_URL", DEFAULT_CACHE_URL)
    _ensure_cache(cache_path)

    def replace(match):
        block_type = match.group(1).lower()
        raw = html.unescape(match.group(2)).strip()
        replacement = _make_replacement(block_type, raw, cache_path, cache_url, settings)
        return replacement if replacement is not None else match.group(0)

    content._content = BLOCK_RE.sub(replace, content._content)


def register():
    if HAS_MARKDOWN:
        signals.initialized.connect(add_markdown_extension)
    signals.content_object_init.connect(process_content)

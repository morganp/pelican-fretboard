import hashlib
import html
import logging
import os
import re

import yaml
from pelican import signals

from . import chord as chord_renderer
from . import scale as scale_renderer
from . import tab as tab_renderer

log = logging.getLogger(__name__)

BLOCK_RE = re.compile(
    r'<pre><code[^>]*class="language-(chord|scale|tab)"[^>]*>(.*?)</code></pre>',
    re.DOTALL,
)

FALLBACK_RE = re.compile(
    r'<pre><code[^>]*>(chord|scale|tab)\n(.*?)</code></pre>',
    re.DOTALL,
)

DEFAULT_CACHE_PATH = "content/images/fretboard"
DEFAULT_CACHE_URL = "/images/fretboard"


def _get_settings(content):
    return getattr(content, "settings", {})


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


def process_content(content):
    if not hasattr(content, "_content") or content._content is None:
        return

    settings = _get_settings(content)
    cache_path = settings.get("FRETBOARD_CACHE_PATH", DEFAULT_CACHE_PATH)
    cache_url = settings.get("FRETBOARD_CACHE_URL", DEFAULT_CACHE_URL)
    _ensure_cache(cache_path)

    def replace(match):
        block_type = match.group(1).lower()
        raw = html.unescape(match.group(2)).strip()
        replacement = _make_replacement(block_type, raw, cache_path, cache_url, settings)
        if replacement is None:
            return match.group(0)
        return replacement

    new_content = BLOCK_RE.sub(replace, content._content)

    if new_content is content._content:
        def replace_fallback(match):
            block_type = match.group(1).lower()
            raw = html.unescape(match.group(2)).strip()
            replacement = _make_replacement(block_type, raw, cache_path, cache_url, settings)
            if replacement is None:
                return match.group(0)
            return replacement
        new_content = FALLBACK_RE.sub(replace_fallback, new_content)

    content._content = new_content


def register():
    signals.content_object_init.connect(process_content)

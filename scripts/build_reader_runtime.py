"""Attach the NDAIB-owned feedback runtime to the existing reader build."""
import html
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path


class ItemParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        item = attrs.get('data-feedback-story-id')
        date = attrs.get('data-feedback-brief-date')
        if item and date:
            self.items.add(date + '|' + item)


def attach_reader_runtime(destination: Path, legacy: Path):
    root = Path(__file__).resolve().parents[1]
    runtime = root / 'migration/reader-runtime'
    parser = ItemParser()
    for page in destination.rglob('*.html'):
        parser.feed(page.read_text())
    watchlist = json.loads((destination / 'data/watchlist.json').read_text())
    registry = {'items': sorted(parser.items), 'topics': sorted(t['topic_id'] for t in watchlist['topics'])}
    if len(registry['items']) < 10:
        raise ValueError('Published item registry is incomplete')
    sidecar = destination.with_name(destination.name + '.runtime')
    shutil.rmtree(sidecar, ignore_errors=True)
    (sidecar / 'server').mkdir(parents=True)
    code = (runtime / 'worker.mjs').read_text()
    code += '\nexport default createReaderWorker(' + json.dumps(registry, separators=(',', ':')) + ');\n'
    (sidecar / 'server/index.js').write_text(code)
    (sidecar / 'registry.json').write_text(json.dumps(registry, indent=2) + '\n')
    shutil.copytree(runtime / 'drizzle', sidecar / 'drizzle')
    (sidecar / 'hosting.json').write_text(json.dumps({'project_id': 'appgprj_6ab087e80a888191abb0f806118aa194', 'd1': 'DB'}, indent=2) + '\n')
    for script in (destination / 'assets/js').glob('*.js'):
        text = script.read_text()
        # All product writes now stay on this Site. Never modify the legacy service.
        text = text.replace('https://daily-ai-brief-ratings.gtome.chatgpt.site/api/', '/api/')
        script.write_text(text)
    # Legacy audience analytics was already inactive on ndaib because its path
    # gate requires /Daily-AI-Brief/. Keep it inactive; no new tracking is added.
    return {'published_items': len(registry['items']), 'watchlist_topics': len(registry['topics']), 'feedback_origin': 'same-origin', 'runtime_sidecar': sidecar.name}


def add_related_coverage(destination: Path, legacy: Path):
    edition = json.loads((legacy / '_data/editions/2026-09-23.json').read_text())
    stories = edition['stories']
    pairs = [[3, 5], [2, 4], [1, 4], [0, 5], [1, 2], [3, 4]]
    for index, story in enumerate(stories):
        page = destination / story['permanent_url'].strip('/') / 'index.html'
        text = page.read_text()
        if 'id="related-coverage"' in text:
            continue
        links = ''.join('<li><a href="' + html.escape(stories[i]['permanent_url'], quote=True) + '">' + html.escape(stories[i]['headline']) + '</a></li>' for i in pairs[index])
        section = '<section id="related-coverage" aria-labelledby="related-coverage-title"><h2 id="related-coverage-title">Related coverage</h2><p>Also in the September 23 brief:</p><ul>' + links + '</ul></section>\n'
        marker = '<div class="story-feedback '
        if marker not in text:
            raise ValueError('Missing story feedback anchor')
        page.write_text(text.replace(marker, section + marker, 1))

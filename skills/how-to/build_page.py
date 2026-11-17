"""Builds a how-to page from the template and the blocks of a topic.

    python -I -X utf8 build_page.py <blocks.js> <page.html>

<blocks.js> – a file with the CONTENT block (together with `model`) and the SCENE
block of the new topic. The script takes template.html next to itself, replaces
only these two blocks and keeps the engine, styles and fonts byte for byte.
Do not write the whole page by hand: without the engine there are no labels,
no step switching, no camera and no clicks.

<page.html> – a full path or just a file name. For a bare name the folder comes
from the HOW_TO_DIR variable, without it – ~/how-to. The script refuses to write
inside a git repository: a finished page is a draft, not part of the code.
"""
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
START = '/* =====================================================================\n   CONTENT'
END = '/* =====================================================================\n   ENGINE'


def fail(msg):
    sys.exit('build_page: ' + msg)


def git_root(path):
    for p in [path, *path.parents]:
        if (p / '.git').exists():
            return p
    return None


def main():
    if len(sys.argv) != 3:
        fail('usage: python -I -X utf8 build_page.py <blocks.js> <page.html>')
    blocks_path = pathlib.Path(sys.argv[1]).expanduser().resolve()
    out = pathlib.Path(sys.argv[2]).expanduser()
    if out.parent == pathlib.Path('.') and not out.is_absolute():
        out = pathlib.Path(os.environ.get('HOW_TO_DIR') or pathlib.Path.home() / 'how-to') / out.name
    out = out.resolve()
    if out.suffix != '.html':
        fail('the page name must end with .html')

    root = git_root(out.parent)
    if root:
        fail(f'{out} is inside the git repository {root}. Save the page outside the repository '
             '(set HOW_TO_DIR or pass a full path).')

    tpl = (HERE / 'template.html').read_text(encoding='utf-8').replace('\r\n', '\n')
    a, b = tpl.find(START), tpl.find(END)
    if a < 0 or b < a:
        fail('template.html block markers not found')

    blocks = blocks_path.read_text(encoding='utf-8').replace('\r\n', '\n').strip('\n')
    for need, what in ((r'\bconst\s+model\s*=', 'const model = v => …'),
                       (r'\bconst\s+CONTENT\s*=', 'const CONTENT = { … }'),
                       (r'\bfunction\s+SCENE\s*\(', 'function SCENE(k) { … }')):
        if not re.search(need, blocks):
            fail(f'{blocks_path.name} has no {what}')
    for bad in ('ENGINE', '<script', '</script', '<html', 'new THREE.WebGLRenderer'):
        if bad in blocks:
            fail(f'{blocks_path.name} contains "{bad}": the blocks file holds only CONTENT and SCENE, '
                 'the engine comes from template.html')

    head = tpl[a:tpl.index('\n', tpl.index('CONTENT', a)) + 1]          # first two marker lines
    blocks = re.sub(r'^/\*\s*=+\s*\n\s*CONTENT.*?\*/[ \t]*\n', '', blocks, flags=re.S)
    page = tpl[:a] + head + '   ===================================================================== */\n' \
        + blocks + '\n\n' + tpl[b:]
    if page[page.find(END):] != tpl[b:]:
        fail('engine block changed while building')

    node = shutil.which('node')
    if node:
        module = page[page.index('<script type="module">') + len('<script type="module">'):page.rindex('</script>')]
        with tempfile.NamedTemporaryFile('w', suffix='.mjs', delete=False, encoding='utf-8') as f:
            f.write(module)
        try:
            r = subprocess.run([node, '--check', f.name], capture_output=True, text=True, encoding='utf-8')
        finally:
            os.unlink(f.name)
        if r.returncode:
            fail('JavaScript syntax error in the blocks:\n' + (r.stderr or r.stdout)[-1500:])

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding='utf-8', newline='\n')
    print(out)
    print(out.as_uri())


if __name__ == '__main__':
    main()

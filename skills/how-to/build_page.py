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

SMOKE = r"""
const __any = (() => { const f = function () {}; const p = new Proxy(f, {
  get: (t, k) => k === Symbol.toPrimitive ? () => 0 : k === Symbol.iterator ? function* () {} : k === 'then' ? undefined : k === 'length' ? 0 : p,
  set: () => true, apply: () => p, construct: () => p, has: () => true, deleteProperty: () => true });
  return p; })();
__ENGINE_NAMES__
const __ids = new Set(), __handles = [], __errs = [];
const k = new Proxy({}, { get: (_, name) => new Proxy(function (...a) {
  if (typeof a[0] === 'string') { __ids.add(a[0]); if (name === 'handle') __handles.push(a[0]); }
  for (const x of a) if (typeof x === 'function') x(__any);
  return __any; }, { get: (t, p) => p === Symbol.toPrimitive ? () => 0 : __any[p], construct: () => __any }) });
const run = (what, fn) => { try { fn(); } catch (e) { __errs.push(`${what}: ${e && e.message || e}`); } };
const raw = {}, v = {};
for (const c of CONTENT.controls || []) raw[c.id] = v[c.id] = c.value ?? c.min ?? 0;
const s = { raw, v, t: 0, dt: 1 / 60, step: 0, mem: {}, dragging: null,
  part: id => __ids.has(id) ? __any : undefined, set: (id, x) => { raw[id] = v[id] = x; } };
let h = {};
run('SCENE', () => { h = SCENE(k) || {}; });
const frames = n => { for (let i = 0; i < n; i++) { s.t += s.dt; run('update', () => h.update?.(s)); } };
const steps = CONTENT.steps || [];
run('model', () => model(raw)); frames(3);
steps.forEach((st, i) => {
  for (const key of ['focus', 'show']) for (const id of st[key] || []) if (!__ids.has(id)) __errs.push(`step ${i + 1} ${key}: no part '${id}' in SCENE`);
  s.step = i; if (st.set) for (const id in st.set) s.set(id, st.set[id]);
  run(`step ${i + 1}`, () => h.step?.(i, s)); run(`done of step ${i + 1}`, () => st.done?.(s)); frames(2);
  for (const id of __ids) { run(`tap ${id}`, () => h.tap?.(id, s)); frames(1); }
  for (const id of __handles) { s.dragging = id; frames(1); s.dragging = null; run(`release ${id}`, () => h.release?.(id, s)); frames(1); }
});
for (const c of CONTENT.controls || []) s.set(c.id, c.type === 'range' ? c.max : 1);
frames(3); run('model', () => model(raw)); steps.forEach((st, i) => run(`done of step ${i + 1}`, () => st.done?.(s)));
run('reset', () => h.reset?.(s)); frames(2);
const __u = [...new Set(__errs)];
if (__u.length) { console.log(__u.slice(0, 10).join('\n')); process.exit(1); }
"""

IDENT = r'[A-Za-z_$][\w$]*'
NL = chr(10)


def engine_names(engine, blocks):
    """Top-level names of the engine and its imports that the blocks may use."""
    names = set()
    for line in engine.split('\n'):
        m = re.match(r'(?:async\s+)?(?:const|let|var|function\*?|class)\s+(.*)', line)
        if not m:
            continue
        rest = m.group(1)
        if line.startswith(('function', 'async', 'class')):
            names.update(re.findall('^' + IDENT, rest))
            continue
        depth, cur = 0, ''
        for ch in rest:
            if ch in '([{':
                depth += 1
            elif ch in ')]}':
                depth -= 1
            elif ch == ';' and depth == 0:
                break
            cur += ch if depth == 0 else ''
        names.update(re.findall(r'(?:^|,)\s*(' + IDENT + r')\s*=', cur))
    declared = set(re.findall(r'\b(?:const|let|var|function|class)\s+(' + IDENT + ')', blocks))
    for d in re.findall(r'\b(?:const|let|var)\s*\{([^}]*)\}', blocks):
        declared.update(re.findall(IDENT, d))
    names -= declared | {'k', 'run', 'raw', 'v', 's', 'h', 'frames', 'steps'}
    return names


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
        imports = set(re.findall(r'import\s+(?:\*\s+as\s+(' + IDENT + r')|\{([^}]*)\})', module))
        names = engine_names(tpl[b:], blocks)
        for star, group in imports:
            names.update([star] if star else re.findall(IDENT, group))
        names -= set(re.findall(r'\b(?:const|let|var|function|class)\s+(' + IDENT + ')', blocks))
        smoke = SMOKE.replace('__ENGINE_NAMES__', NL.join(f'const {n} = __any;' for n in sorted(names)))
        for code, what in ((module, 'syntax'), (blocks + NL + smoke, 'smoke')):
            with tempfile.NamedTemporaryFile('w', suffix='.mjs', delete=False, encoding='utf-8') as f:
                f.write(code)
            try:
                args = [node, '--check', f.name] if what == 'syntax' else [node, f.name]
                r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', timeout=30)
            except subprocess.TimeoutExpired:
                fail('the scene did not finish in 30 seconds during the trial run: look for an endless loop')
            finally:
                os.unlink(f.name)
            if r.returncode and what == 'syntax':
                fail('JavaScript syntax error in the blocks:' + NL + (r.stderr or r.stdout)[-1500:])
            if r.returncode:
                fail('the trial run of the page found errors (every step, every tap and handle):' + NL
                     + (r.stdout or r.stderr)[-1500:] + NL + 'Fix the blocks and build again.')
    else:
        print('build_page: node not found, the page was not checked', file=sys.stderr)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding='utf-8', newline='\n')
    print(out)
    print(out.as_uri())


if __name__ == '__main__':
    main()

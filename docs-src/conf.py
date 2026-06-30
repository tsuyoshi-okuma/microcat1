import sys, os, types, importlib, importlib.abc, importlib.util, re

# micropython と microcat1 を同じ親ディレクトリに clone した前提
# 親ディレクトリ/
#   micropython/
#   microcat1/
#     docs-src/    ← このファイルの場所
MODULES_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__),
                 '../../micropython/ports/rp2/boards/MTX_MICROCAT1/modules')
)

# ── MicroPython 依存モジュールのスタブ ────────────────────
_ppp = types.SimpleNamespace(SEC_NONE=0, SEC_PAP=1, SEC_CHAP=2)
_network = types.ModuleType('network')
_network.PPP = _ppp
sys.modules.setdefault('network', _network)

_machine = types.ModuleType('machine')
for _cls_name in ('Pin', 'Timer', 'UART'):
    _n = _cls_name
    _c = type(_n, (), {
        '__init__': lambda self, *a, **k: None,
        '__repr__': (lambda name: lambda self: f'machine.{name}')(_n),
    })
    setattr(_machine, _n, _c)
_machine.UART.CTS = 1
_machine.UART.RTS = 2
sys.modules.setdefault('machine', _machine)

_mp = types.ModuleType('micropython')
_mp.const = lambda x: x
sys.modules.setdefault('micropython', _mp)

# ── カスタムローダー ──────────────────────────────────────
# Python 3.14 で起きるクラス内 __NAME 定数のネームマングリングを回避しつつ、
# MicroPython ビルトインの const() を注入してモジュールを import する。
_BUILTINS = {'const': lambda x: x}

class _PatchedLoader(importlib.abc.Loader):
    def __init__(self, path):
        self._path = path

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        with open(self._path) as f:
            src = f.read()
        src = re.sub(r'\b(__[A-Z][A-Z0-9_]+)\b', lambda m: m.group(1)[1:], src)
        globs = module.__dict__
        globs.update(_BUILTINS)
        exec(compile(src, self._path, 'exec'), globs)

class _PatchedFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        candidate = os.path.join(MODULES_PATH, fullname + '.py')
        if os.path.exists(candidate):
            spec = importlib.util.spec_from_file_location(fullname, candidate)
            spec.loader = _PatchedLoader(candidate)
            return spec
        return None

sys.meta_path.insert(0, _PatchedFinder())

# ── Sphinx 設定 ───────────────────────────────────────────
project = 'MicroCat.1'
author = 'MechaTracks Co., Ltd.'
extensions = ['sphinx.ext.autodoc']
html_theme = 'sphinx_rtd_theme'

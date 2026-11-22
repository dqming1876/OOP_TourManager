"""Stage only application modules for Wrangler's recursive Python bundler."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / '.wrangler' / 'python-src'
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / 'entry.py', target / 'entry.py')
    backend = target / 'backend'
    if backend.exists():
        shutil.rmtree(backend)
    shutil.copytree(ROOT / 'backend', backend, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))


if __name__ == '__main__':
    main()

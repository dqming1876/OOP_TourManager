"""Run independent mutations in disposable copies; never edit the working tree."""
from pathlib import Path
from tempfile import TemporaryDirectory
from shutil import copytree, ignore_patterns
from subprocess import run
from sys import executable
import re

ROOT = Path(__file__).resolve().parents[1]


def mutations():
    service = (ROOT / 'backend/services.py').read_text()
    for method in ('save_tour', 'set_visibility', 'remove_departure', 'payment_history'):
        pattern = r'(    async def ' + method + r'\([^\n]+\):\n)        self.access.require_role\(ADMIN\)\n'
        changed, count = re.subn(pattern, r'\1', service)
        assert count == 1
        yield method, 'backend/services.py', changed
    cases = [
        ('pending-paid', 'backend/domain.py', 'self.paid and self.status != CONFIRMED', 'self.paid and self.status == CANCELLED'),
        ('capacity-equality', 'backend/repositories.py', 'reserved <= ?', 'reserved < ?'),
        ('expired-today', 'backend/repositories.py', "b.status = 'pending' AND b.day < ?", "b.status = 'pending' AND b.day <= ?"),
        ('completed-today', 'backend/repositories.py', "b.paid = 1 AND b.day < ?", "b.paid = 1 AND b.day <= ?"),
        ('password-minimum', 'backend/services.py', 'text_length(password) < 6', 'text_length(password) < 5'),
        ('login-threshold', 'backend/repositories.py', 'login_attempts.count < 12', 'login_attempts.count < 13'),
        ('d1-trigger-count', 'entry.py', '''result = await self.prepare(sql.rstrip().rstrip(";") + " RETURNING 1 AS changed", values).all()
        return len(result["results"])''', '''result = await self.prepare(sql, values).run()
        return int(result.meta.changes)'''),
    ]
    for name, file, old, new in cases:
        original = (ROOT / file).read_text()
        assert original.count(old) == 1, name
        yield name, file, original.replace(old, new)


def main():
    baseline = run([executable, '-B', '-m', 'unittest', 'discover'], cwd=ROOT, capture_output=True, text=True)
    assert baseline.returncode == 0, baseline.stderr
    total = 0
    for name, file, content in mutations():
        with TemporaryDirectory(prefix='mingo-mutation-') as temp:
            target = Path(temp)
            for folder in ('backend', 'scripts', 'Database', 'tests'):
                copytree(ROOT/folder, target/folder, ignore=ignore_patterns('__pycache__'))
            (target/'entry.py').write_text((ROOT/'entry.py').read_text())
            (target/file).write_text(content)
            result = run([executable, '-B', '-m', 'unittest', 'discover'], cwd=target,
                         capture_output=True, text=True, timeout=60)
            assert result.returncode == 1 and ('FAIL:' in result.stderr or 'ERROR:' in result.stderr), (name, result.stderr)
            assert 'ImportError' not in result.stderr and 'SyntaxError' not in result.stderr, result.stderr
            total += 1
            print(f'{name}: DETECTED', flush=True)
    print(f'{total}/{total} mutations detected. Baseline PASS; working tree unchanged.')


if __name__ == '__main__':
    main()

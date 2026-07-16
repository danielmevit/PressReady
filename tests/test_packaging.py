"""
Guards on the build scripts.

These check things that only bite on a platform we can't run here, which is exactly
why they're worth asserting from the one place that runs everywhere.
"""

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent


def powershell_scripts():
    return sorted(ROOT.glob("packaging/**/*.ps1"))


class TestPowerShellScripts:
    def test_there_are_some(self):
        assert powershell_scripts(), "no .ps1 found — did packaging/ move?"

    @pytest.mark.parametrize("script", powershell_scripts(), ids=lambda p: p.name)
    def test_pure_ascii(self, script):
        """
        Windows PowerShell 5.1 reads a BOM-less .ps1 as ANSI (cp1252), not UTF-8.
        A UTF-8 em-dash then arrives as 'â€”', and that trailing curly quote is a
        string terminator to PowerShell — so one dash in a Write-Host message closes
        the string early, unbalances every brace after it, and the script fails to
        parse before running a single line. It cost a release build to learn.
        """
        raw = script.read_bytes()
        offenders = [
            (i, line.decode("utf-8", "replace"))
            for i, line in enumerate(raw.splitlines(), 1)
            if any(b > 127 for b in line)
        ]
        assert not offenders, (
            f"{script.name} has non-ASCII on line(s) "
            f"{[i for i, _ in offenders]}: PowerShell 5.1 will mis-decode it. "
            f"Use plain ASCII (-- not —, -> not →)."
        )

    @pytest.mark.parametrize("script", powershell_scripts(), ids=lambda p: p.name)
    def test_braces_balance(self, script):
        # Crude, but it catches the shape of the failure above: the em-dash bug
        # showed up as "Missing closing '}'".
        text = script.read_text(encoding="ascii")
        assert text.count("{") == text.count("}"), f"{script.name}: unbalanced braces"

    @pytest.mark.parametrize("script", powershell_scripts(), ids=lambda p: p.name)
    def test_reads_the_version_from_the_one_source(self, script):
        text = script.read_text(encoding="ascii")
        assert "laydown.__version__" in text, (
            f"{script.name} must read the version from laydown/__init__.py, not restate it"
        )


class TestShellScripts:
    @pytest.mark.parametrize(
        "script", sorted(ROOT.glob("packaging/**/*.sh")), ids=lambda p: p.name)
    def test_is_executable_and_strict(self, script):
        text = script.read_text(encoding="utf-8")
        assert text.startswith("#!"), f"{script.name} has no shebang"
        assert "set -euo pipefail" in text, f"{script.name} should fail fast"

"""Deterministic, stratified task selection from the polyglot benchmark."""
from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).parent
BENCH = ROOT / "polyglot-benchmark"


def practice_dir(lang: str) -> Path:
    return BENCH / lang / "exercises" / "practice"


def _rust_std_only(ex: Path) -> bool:
    """True if the Rust exercise declares no external crates (reliably runnable
    offline). Tasks needing rand/counter/etc. add network + dep-resolution noise
    that would corrupt the measurement instrument, so we exclude them."""
    cargo = ex / "Cargo.toml"
    if not cargo.exists():
        return True
    text = cargo.read_text(encoding="utf-8")
    m = re.search(r"\[dependencies\](.*?)(\n\[|\Z)", text, re.DOTALL)
    if not m:
        return True
    deps = [l for l in m.group(1).splitlines() if l.strip() and not l.strip().startswith("#")]
    return not deps


def _rust_whitelist() -> set:
    """Exercise names whose reference example compiled + passed (built by the
    one-off whitelist step). Only sure way to guarantee an offline-clean task."""
    wl = ROOT / "rust_ok.txt"
    if wl.exists():
        return {l.strip() for l in wl.read_text(encoding="utf-8").splitlines() if l.strip()}
    return set()


def select(languages: List[str], n_per_lang: int, seed: int) -> Dict[str, List[Path]]:
    rng = random.Random(seed)
    out: Dict[str, List[Path]] = {}
    for lang in languages:
        pdir = practice_dir(lang)
        exercises = sorted(d for d in pdir.iterdir()
                           if d.is_dir() and (d / ".meta" / "config.json").exists())
        if lang == "rust":
            wl = _rust_whitelist()
            if wl:
                exercises = [e for e in exercises if e.name in wl]
            else:
                exercises = [e for e in exercises if _rust_std_only(e)]
        rng.shuffle(exercises)
        out[lang] = exercises[:n_per_lang]
    return out


if __name__ == "__main__":
    import yaml
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    chosen = select(cfg["languages"], cfg["n_per_lang"], cfg["seed"])
    for lang, exs in chosen.items():
        print(f"{lang} ({len(exs)}): " + ", ".join(e.name for e in exs))

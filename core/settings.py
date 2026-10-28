"""Kopru's settings: one JSON file of plain values. Loading never fails: a missing or unreadable
file gives the defaults, a bad value gives that key's default, and keys Kopru does not know are
dropped. Saving refuses a bad value rather than writing it, and replaces the file in one step.

The crossing look keys are Beamer's (win_app/app_config.py), with the same allowed values, so
its effects and Design page work unchanged. Secrets never live here."""

import json
import os
import tempfile
from pathlib import Path

from core import effects

# tokens.PALETTES' ids; core does not import app modules (app/tests/test_settings_palettes.py
# keeps the two the same).
PALETTE_IDS = ("signal", "colourful", "ocean", "sunset", "mono", "aurora")
SIDES = ("right", "left", "top", "bottom")
ROLES = ("ana", "pc2")
STREAM_PROFILES = ("akici", "dusuk_gecikme")
CODECS = ("auto", "HEVC", "H.264")

DEFAULTS = {
    # How the crossing looks (Beamer's keys).
    "edge_glow": True,
    "glow_style": "glow",
    "glow_colour": "colourful",
    "shortcut_arrival": True,
    "shortcut_arrival_style": "match",
    "effect_length": "normal",
    "effect_size": "medium",
    "effect_pace": 1.0,
    "effect_size_fraction": 0.045,
    "frame_rate": "display",
    # This PC and its link to the other.
    "role": "ana",
    "side": "right",
    "auto_extend": True,
    "resistance_px": 120,
    "stream_profile": "akici",
    "bitrate_kbps": 20000,
    "codec": "auto",
    "grace_reconnect_s": 5,
    "grace_teardown_s": 20,
    "diagnostics": False,
}


def _boolean(value):
    return isinstance(value, bool)


def _whole(low, high):
    return lambda value: isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


def _one_of(choices):
    return lambda value: isinstance(value, str) and value in choices


_RULES = {
    "edge_glow": _boolean,
    "glow_style": _one_of(("glow", "beam") + effects.EFFECT_IDS),
    "glow_colour": _one_of(PALETTE_IDS + effects.PACK_IDS),
    "shortcut_arrival": _boolean,
    "shortcut_arrival_style": _one_of(effects.SWITCH_STYLES),
    "effect_length": _one_of(tuple(value for value, _name in effects.LENGTHS)),
    "effect_size": _one_of(tuple(value for value, _name in effects.SIZES)),
    "effect_pace": lambda value: not isinstance(value, bool) and effects.valid_effect_pace(value),
    "effect_size_fraction": lambda value: not isinstance(value, bool) and effects.valid_effect_size_fraction(value),
    "frame_rate": _one_of(tuple(value for value, _name, _divisor in effects.FRAME_RATES)),
    "role": _one_of(ROLES),
    "side": _one_of(SIDES),
    "auto_extend": _boolean,
    "resistance_px": _whole(0, 2000),
    "stream_profile": _one_of(STREAM_PROFILES),
    "bitrate_kbps": _whole(2000, 150000),
    "codec": _one_of(CODECS),
    "grace_reconnect_s": _whole(1, 60),
    "grace_teardown_s": _whole(2, 600),
    "diagnostics": _boolean,
}


def valid(key, value):
    rule = _RULES.get(key)
    return bool(rule and rule(value))


def load(path):
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    # A hidden style, colour or switch style Beamer saved is shown as its stand-in.
    if {"glow_style", "glow_colour", "shortcut_arrival_style"} & raw.keys():
        style, colour, switch = effects.offered(raw.get("glow_style"), raw.get("glow_colour"),
                                                raw.get("shortcut_arrival_style"))
        raw = dict(raw, glow_style=style, glow_colour=colour, shortcut_arrival_style=switch)
    return {key: raw[key] if key in raw and valid(key, raw[key]) else default
            for key, default in DEFAULTS.items()}


def save(path, values):
    """Write every key of DEFAULTS from `values`; ValueError, and nothing written, if any is bad."""
    bad = [key for key in DEFAULTS if not valid(key, values.get(key))]
    if bad:
        raise ValueError(f"invalid settings: {', '.join(bad)}")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps({key: values[key] for key in DEFAULTS}, indent=2, ensure_ascii=False)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text + "\n")
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise

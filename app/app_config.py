"""The one piece of Beamer's app_config the effects use: a colour id's colours. Kopru's settings
live in core/settings.py."""

import tokens
from core import effects


def palette_colours(colour: str) -> tuple:
    """The colours of a `glow_colour` id: one of today's palettes, else a crossing effect's pack.
    An unknown id is Signal's, as today's glow always drew it."""
    if colour in tokens.PALETTES:
        return tuple(tokens.PALETTES[colour])
    found = effects.pack(colour) if colour in effects.PACK_IDS else None
    return tuple(found[1]) if found else tuple(tokens.PALETTES["signal"])

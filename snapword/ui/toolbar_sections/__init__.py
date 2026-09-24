"""Ordered section implementations; each module owns construction and wiring."""

from .blocks import BlocksSection
from .clear import ClearSection
from .color import ColorSection
from .document import DocumentSection
from .font import FontSection
from .history import HistorySection
from .indent import IndentSection
from .insert import InsertSection
from .lists import ListsSection
from .paragraph import AlignmentSection
from .script import ScriptSection
from .spacing import SpacingSection
from .text import TextSection

SECTIONS = (
    HistorySection,
    FontSection,
    TextSection,
    AlignmentSection,
    ListsSection,
    ColorSection,
    IndentSection,
    SpacingSection,
    InsertSection,
    ScriptSection,
    BlocksSection,
    DocumentSection,
    ClearSection,
)

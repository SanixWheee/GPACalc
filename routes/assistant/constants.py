from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from typing_extensions import Final


NAME: Final[str] = 'GPA Wizard Assistant'
INSTRUCTIONS: Final[str] = '''
You are an AI assistant for a GPA Calculator website. Help users navigate
the website and discuss their grades
'''

FILE_TYPES: Final[Tuple[str, ...]] = ('pdf', 'docx', 'txt')


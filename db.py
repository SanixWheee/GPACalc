import sqlite3
from typing import Optional

from flask import g


def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        g.db = sqlite3.connect('db.sqlite3')

    return g.db


def close_db(exc: Optional[BaseException] = None) -> None:
    if 'db' in g:
        db = g.pop('db')
        db.close()

from __future__ import annotations

import functools
from typing import Any, Callable, ParamSpec, TypeVar

from flask import Blueprint, current_app, request, session, stream_with_context
from flask_login import current_user
from openai.types.beta.assistant_stream_event import ThreadMessageDelta

from .api import client, init_assistant

P = ParamSpec('P')
R = TypeVar('R')


def check_thread(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if 'thread_id' not in session:
            session['thread_id'] = client.beta.threads.create().id
        return func(*args, **kwargs)

    return wrapper


bp = Blueprint('assistant', __name__, url_prefix='/api/assistant')


@bp.route('/create_message', methods=('POST',))
@check_thread
def create_message() -> Any:
    """
    Create a message and get a response from OpenAI

    Methods
    -------
    POST /api/assistant/create_message:
        This is called by the frontend and returns a stream containing the response from OpenAI

        Form Data:
            content: str
    """
    client.beta.threads.messages.create(
        thread_id=session['thread_id'],
        role='user',
        content=request.get_json()['content'],
    )

    @stream_with_context
    def generate():
        with client.beta.threads.runs.create_and_stream(
            thread_id=session['thread_id'],
            assistant_id=current_app.config['ASSISTANT_ID'],
            instructions=f'Please address the user as {current_user.username}',
        ) as stream:
            for event in stream:
                if isinstance(event, ThreadMessageDelta):
                    yield event.data.delta.content[0].text.value

    return generate()  # type: ignore  # stream_with_context seems to be missing an overload

import functools
from queue import Queue
from typing import Any, Callable, TypeVar, ParamSpec, Iterator

from flask import Blueprint, request, session, current_app
from flask_login import current_user
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


class EventHandler(client.beta.assistants.AssistantEventHandler):
    def __init__(self, queue: Queue[str]) -> None:
        self.queue = queue
        self.done = False

    def __iter__(self) -> Iterator[str]:
        while not self.done or not self.queue.empty():
            yield self.queue.get()

    def on_text_created(self, text: str) -> None:
        self.queue.put(text)

    def on_text_delta(self, delta: str, snapshot: str) -> None:
        self.queue.put(delta)

    def on_text_end(self) -> None:
        self.done = True


@check_thread
@bp.route('/create_message', methods=('POST',))
def create_message() -> Any:
    client.beta.threads.messages.create(
        thread_id=session['thread_id'],
        role='user',
        content=request.form['content']
    )

    # get the stream response from OpenAI's api, put the responses in a queue,
    # retrieve messages from the queue and forward it to a new stream to the frontend

    response = Queue()
    with client.beta.threads.runs.create_and_stream(
        thread_id=session['thread_id'],
        assistant_id=current_app.config['ASSISTANT_ID'],
        instructions=f'Please address the user as {current_user.username}',
        event_handler=EventHandler(response)
    ) as stream:
        return (yield from stream)

from __future__ import annotations

import functools
import re
from typing import Any, Callable, ParamSpec, TypeVar

from flask import Blueprint, current_app, request, session, stream_with_context
from flask_login import AnonymousUserMixin, current_user
from openai.types.beta.assistant_stream_event import ThreadMessageDelta, ThreadRunFailed

from .api import client, init_assistant

P = ParamSpec("P")
R = TypeVar("R")


def check_thread(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if "thread_id" not in session:
            session["thread_id"] = client.beta.threads.create(
                messages=[
                    {
                        "role": "assistant",
                        "content": "Welcome to the GPA Wizard interactive chatbot! How may I help you?",
                    }
                ]
            ).id
        return func(*args, **kwargs)

    return wrapper


bp = Blueprint("assistant", __name__, url_prefix="/api/assistant")


@bp.route("/get_messages", methods=("GET",))
@check_thread
def get_messages() -> Any:
    """
    Get all messages in the current thread

    Methods
    -------
    GET /api/assistant/get_messages:
        This is called by the frontend and returns a list of messages in the current thread
    """
    messages = client.beta.threads.messages.list(
        thread_id=session["thread_id"], order="asc"
    )
    return {
        "messages": [
            {"content": message.content[0].text.value, "role": message.role}
            for message in messages
        ]
    }


@bp.route("/create_message", methods=("POST",))
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
        thread_id=session["thread_id"],
        role="user",
        content=request.get_json()["content"],
    )

    # user is not logged in
    if isinstance(current_user, AnonymousUserMixin):
        username = "Guest"
    else:
        username = current_user.username

    @stream_with_context
    def generate():
        with client.beta.threads.runs.create_and_stream(
            thread_id=session["thread_id"],
            assistant_id=current_app.config["ASSISTANT_ID"],
            instructions=f"Please address the user as {username}",
        ) as stream:
            for event in stream:
                if isinstance(event, ThreadMessageDelta):
                    yield event.data.delta.content[0].text.value
                elif isinstance(event, ThreadRunFailed):
                    retry = re.search(
                        r"Please try again in [0-9]+s\.", event.data.last_error.message
                    ).group(0)
                    yield "We are under a high load right now. " + retry

    return generate()  # type: ignore  # stream_with_context seems to be missing an overload

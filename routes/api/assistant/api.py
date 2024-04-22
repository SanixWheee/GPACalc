from __future__ import annotations

import glob
import itertools
import os
from typing import TYPE_CHECKING

import openai

from .constants import FILE_TYPES, INSTRUCTIONS, NAME

if TYPE_CHECKING:
    from openai.types.beta import Assistant


client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def init_assistant() -> Assistant:
    """
    Search for an existing assistant, if it isn't found then create a new one
    """
    assistant = None

    assistants = client.beta.assistants.list()
    for existing_assistant in assistants:
        if (
            existing_assistant.name == NAME
            and existing_assistant.instructions == INSTRUCTIONS
        ):
            assistant = existing_assistant
            break

    if assistant is None:
        assistant = client.beta.assistants.create(
            name=NAME,
            instructions=INSTRUCTIONS,
            tools=[{"type": "file_search"}],
            model="gpt-3.5-turbo-0125",
        )

    vector_store = client.beta.vector_stores.create(name='GPA Calculator')
    file_paths = itertools.chain.from_iterable(glob.glob(f"routes/api/assistant/*.{file_type}") for file_type in FILE_TYPES)
    files = [open(path, "rb") for path in file_paths]

    client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=files
    )

    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )

    return assistant


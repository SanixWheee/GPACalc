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


def get_files() -> list[openai.File]:
    """
    Get the files either from the OpenAI storage, or upload them. Then return them.
    """

    files = list(client.files.list(purpose="assistants"))

    # search for all files in this directory that have a specific file type
    filenames = set(
        itertools.chain.from_iterable(
            glob.glob(f"routes/assistant/*.{file_type}", recursive=True)
            for file_type in FILE_TYPES
        )
    )

    for file in files.copy():
        if file.filename in filenames:
            filenames.remove(file.filename)
            files.remove(file)  # remove known files from list

    # delete unknown files
    for file in files:
        client.files.delete(file_id=file.id)

    if len(filenames) == 0:
        # no files left to add
        return files

    for filename in filenames:
        with open(filename, "rb") as f:
            client.files.create(purpose="assistants", file=f)

    # the second time, all files should be uploaded and this function will return early
    return get_files()


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
            tools=[{"type": "retrieval"}],
            model="gpt-3.5-turbo-0125",
        )

    files = get_files()
    # check if the files attached to the assistant are different from the ones we have
    if (
        set(client.beta.assistants.retrieve(assistant_id=assistant.id).file_ids)
        != get_files()
    ):
        client.beta.assistants.update(
            assistant_id=assistant.id, file_ids=[file.id for file in files]
        )

    return assistant


init_assistant()

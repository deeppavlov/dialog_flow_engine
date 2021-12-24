"""
Responses
---------------------------
Functions that work with responses.
"""
import random
from .core.context import Context
from .core.actor import Actor


def choice(responses: list):
    """
    Function wrapper that takes the list of responses as an input,
    and returns handler which outputs a response randomly chosen from that list.
    """

    def choice_response_handler(ctx: Context, actor: Actor, *args, **kwargs):
        return random.choice(responses)

    return choice_response_handler

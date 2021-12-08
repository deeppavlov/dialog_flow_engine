"""
Conditions
---------------------------
This file contains functions that set the basic conditions for use in scenarios.
"""
from typing import Callable, Pattern, Union, Any
import logging
import re

from pydantic import validate_arguments

from dff.core.types import NodeLabel2Type

from .core.actor import Actor
from .core.context import Context

logger = logging.getLogger(__name__)


@validate_arguments
def exact_match(match: Any, *args, **kwargs) -> Callable:
    """
    Returns function handler. This handler returns True only if the last user phrase is exactly the same as the `match`.

    Parameters
    ----------

    match: Any
        the variable of the same type as last_request field of `Context`
    """

    def exact_match_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        request = ctx.last_request
        return match == request

    return exact_match_condition_handler


@validate_arguments
def regexp(pattern: Union[str, Pattern], flags: Union[int, re.RegexFlag] = 0, *args, **kwargs) -> Callable:
    """
    Returns function handler. This handler returns True only if the last user phrase contains `pattern` with `flags`.

    Parameters
    ----------

    `pattern`: Union[str, Pattern]
        the RegExp pattern

    flags: Union[int, re.RegexFlag] = 0
         flags for this pattern
    """
    pattern = re.compile(pattern, flags)

    def regexp_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        request = ctx.last_request
        return bool(pattern.search(request))

    return regexp_condition_handler


@validate_arguments
def check_cond_seq(cond_seq: list):
    """
    Checks if the list consists only of Callables.

    Parameters
    ----------

    cond_seq: []
        list of conditions to check
    """
    for cond in cond_seq:
        if not isinstance(cond, Callable):
            raise TypeError(f"{cond_seq=} has to consist of callable objects")


_any = any
""" _any is an alias for any. """
_all = all
""" _all is an alias for all. """


@validate_arguments
def aggregate(cond_seq: list, aggregate_func: Callable = _any, *args, **kwargs) -> Callable:
    """
    Aggregates multiple functions into one. Returns function handler.

    Parameters
    ----------

    cond_seq: []
        list of conditions to check
    aggregate_func: Callable = _any
        function to aggregate conditions
    """
    check_cond_seq(cond_seq)

    def aggregate_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        try:
            return bool(aggregate_func([cond(ctx, actor, *args, **kwargs) for cond in cond_seq]))
        except Exception as exc:
            logger.error(f"Exception {exc} for {cond_seq=}, {aggregate_func=} and {ctx.last_request=}", exc_info=exc)

    return aggregate_condition_handler


@validate_arguments
def any(cond_seq: list, *args, **kwargs) -> Callable:
    """
    Function that return function handler. This handler returns True if any function from the list is True.

    Parameters
    ----------
    cond_seq: []
        list of conditions to check
    """
    _agg = aggregate(cond_seq, _any)

    def any_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        return _agg(ctx, actor, *args, **kwargs)

    return any_condition_handler


@validate_arguments
def all(cond_seq: list, *args, **kwargs) -> Callable:
    """
    Function that return function handler. This handler returns True only if all functions from the list are True.

    Parameters
    ----------
    cond_seq: []
        list of conditions to check
    """
    _agg = aggregate(cond_seq, _all)

    def all_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        return _agg(ctx, actor, *args, **kwargs)

    return all_condition_handler


@validate_arguments
def negation(condition: Callable, *args, **kwargs) -> Callable:
    """
    Returns function handler. This handler returns negation of the condition: False if condition and True if not condition

    Parameters
    ----------
    condition: Callable
    """

    def negation_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        return not condition(ctx, actor, *args, **kwargs)

    return negation_condition_handler


@validate_arguments
def has_last_labels(
    flow_labels: list[str] = [], labels: list[NodeLabel2Type] = [], last_n_indexes: int = 1, *args, **kwargs
) -> Callable:
    """
    Function returns condition handler.
    This handler returns True if any label from last `last_n_indexes` context labels is in the `flow_labels` list or in the `labels` list.

    Parameters
    ----------
    flow_labels: []
        list of labels to check.Every label has type `str`. Is empty if not set.
    labels: []
        list of labels that correspond to the nodes. Is empty is not set.
    last_n_indexes: 1
        number of last utterances to check.
    """

    def has_last_labels_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        label = list(ctx.labels.values())[-last_n_indexes:]
        for label in list(ctx.labels.values())[-last_n_indexes:]:
            label = label if label else (None, None)
            if label[0] in flow_labels or label in labels:
                return True
        return False

    return has_last_labels_condition_handler


@validate_arguments
def true(*args, **kwargs) -> Callable:
    """
    Returns function handler. This handler always returns True.
    """

    def true_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        return True

    return true_handler


@validate_arguments
def false(*args, **kwargs) -> Callable:
    """
    Returns function handler. This handler always returns False.
    """

    def false_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        return False

    return false_handler


# aliases
agg = aggregate
""" agg is an alias for aggregate. """
neg = negation
""" neg is an alias for negation. """

"""
Context
---------------------------
Data structure which is used for the context storage.
It provides a convenient interface for working with data:
adding data, data serialization, type checking etc.

"""
import logging
from functools import partial
from uuid import UUID, uuid4

from typing import Any, Optional, Union, Dict, Type, Callable

from pydantic import BaseModel, validate_arguments, Field, validator
from pydantic.json import custom_pydantic_encoder

from .types import NodeLabel2Type, ModuleName

logger = logging.getLogger(__name__)

Context = BaseModel
Node = BaseModel


@validate_arguments
def sort_dict_keys(dictionary: dict) -> dict:
    """
    Sorting of keys in the `dictionary`.
    It is nesessary to do it after the deserialization: keys deserialize in a random order.
    """
    return {key: dictionary[key] for key in sorted(dictionary)}


@validate_arguments
def get_last_index(dictionary: dict) -> int:
    """
    Obtaining of the last index from the `dictionary`, functions returns `-1` if the `dict` is empty.
    """
    indices = list(dictionary)
    return indices[-1] if indices else -1


class Context(BaseModel):
    """
    The structure which is used for the storage of data about the dialog context.

    Parameters
    ----------

    id : Union[UUID, int, str]
        `id` is the unique context identifier.
        By default, the `id` which is randomly generated using `uuid4` is used.
        `id` can be used to trace the user behaviour,
        e.g while collecting the statistical data.

    labels : dict[int, :py:const:`~df_engine.core.types.NodeLabel2Type`]
        `labels` stores the history of all passed `labels`:

        * key - `id` of the turn
        * value - `label` on this turn

    requests : dict[int, Any]
        `requests` stores the history of all `requests` received by the agent

        * key - `id` of the turn
        * value - `request` on this turn

    responses : dict[int, Any]
        `responses` stores the history of all agent `responses`

        * key - `id` of the turn
        * value - `response` on this turn

    misc : dict[str, Any]
        `misc` stores any custom data, the engine doesn't use this dictionary by default,
        so storage of any data won't reflect on the work on the internal Dialog Flow Engine functions.

        * key - arbitrary data name
        * value - arbitrary data

    validation : bool
        `validation` is a flag that signals that :py:class:`~df_engine.core.actor.Actor`,
        while being initialized, checks the :py:class:`~df_engine.core.script.Script`.
        The functions that can give not validable data
        while being validated must use this flag to take the validation mode into account.
        Otherwise the validation will not be passed.

    framework_states : dict[:py:const:`~df_engine.core.types.ModuleName`, dict[str, Any]]
        `framework_states` is used for addons states or for :py:class:`~df_engine.core.actor.Actor`'s states.
        :py:class:`~df_engine.core.actor.Actor` records all its intermediate conditions into the `framework_states`.
        After :py:class:`~df_engine.core.context.Context` processing is finished,
        :py:class:`~df_engine.core.actor.Actor` resets `framework_states` and
        returns :py:class:`~df_engine.core.context.Context`.

        * key - temporary variable name
        * value - temporary variable data

    """

    id: Union[UUID, int, str] = Field(default_factory=uuid4)
    labels: dict[int, NodeLabel2Type] = {}
    requests: dict[int, Any] = {}
    responses: dict[int, Any] = {}
    misc: dict[str, Any] = {}
    validation: bool = False
    framework_states: dict[ModuleName, dict[str, Any]] = {}

    # validators
    _sort_labels = validator("labels", allow_reuse=True)(sort_dict_keys)
    _sort_requests = validator("requests", allow_reuse=True)(sort_dict_keys)
    _sort_responses = validator("responses", allow_reuse=True)(sort_dict_keys)

    _custom_encoders: Dict[Type[Any], Callable[[Any], Any]] = {}

    @classmethod
    def cast(cls, ctx: Union[Context, dict, str] = {}, *args, **kwargs) -> Context:
        """
        Transforms different data types to the objects of :py:class:`~df_engine.core.context.Context` class.

        Parameters
        ----------
        ctx : Union[Context, dict, str]
            Different data types, that are used to initialize object of :py:class:`~df_engine.core.context.Context`
            type. The empty object of :py:class:`~df_engine.core.context.Context` type is created if no data are given.

        Returns
        -------
        Context
            Object of :py:class:`~df_engine.core.context.Context` type that is initialized by the input data
        """
        if not ctx:
            ctx = Context(*args, **kwargs)
        elif isinstance(ctx, dict):
            ctx = Context.parse_obj(ctx)
        elif isinstance(ctx, str):
            ctx = Context.parse_raw(ctx)
        elif not issubclass(type(ctx), Context):
            raise ValueError(
                f"context expected as sub class of Context class or object of dict/str(json) type, but got {ctx}"
            )
        return ctx

    @classmethod
    def add_json_encoder(cls, t: Type[Any], encoder: Callable[[Any], Any]):
        cls._custom_encoders[t] = encoder

    def json(self, **kwargs) -> str:
        if 'encoder' in kwargs:
            return super().json(**kwargs)
        else:
            if self.__config__.json_encoders:
                encoders = {**self._custom_encoders, **self.__config__.json_encoders}
            else:
                encoders = self._custom_encoders

            encoder_fn = partial(custom_pydantic_encoder, encoders)
            return super().json(encoder=encoder_fn, **kwargs)

    @validate_arguments
    def add_request(self, request: Any):
        """
        Adds to the context the next `request`, that is correspondent to the next turn.
        The addition is happening in the `requests`, and `new_index = last_index + 1`

        Parameters
        ----------
        request : Any
            `request` that we need to add to the context
        """
        last_index = get_last_index(self.requests)
        self.requests[last_index + 1] = request

    @validate_arguments
    def add_response(self, response: Any):
        """
        Adds to the context the next `response`, that is correspondent to the next turn.
        The addition is happening in the `responses`, and `new_index = last_index + 1`

        Parameters
        ----------
        response : Any
            `response` that we need to add to the context
        """
        last_index = get_last_index(self.responses)
        self.responses[last_index + 1] = response

    @validate_arguments
    def add_label(self, label: NodeLabel2Type):
        """
        Adds to the context the next :py:const:`label <df_engine.core.types.NodeLabel2Type>`,
        that is correspondent to the next turn.
        The addition is happening in the `labels`, and `new_index = last_index + 1`

        Parameters
        ----------
        label : :py:const:`~df_engine.core.types.NodeLabel2Type`
            `label` that we need to add to the context
        """
        last_index = get_last_index(self.labels)
        self.labels[last_index + 1] = label

    @validate_arguments
    def clear(self, hold_last_n_indices: int, field_names: list[str] = ["requests", "responses", "labels"]):
        """
        Deletes all recordings from the `requests`/`responses`/`labels` except for
        the last N turns according to the `hold_last_n_indices`.
        If`field_names` contains `misc` field, `misc` field is fully cleared,

        Parameters
        ----------
        hold_last_n_indices : int
            number of last turns that remein under clearing
        field_names : list[str]
             properties of :py:class:`~df_engine.core.context.Context` we need to clear
        """
        if "requests" in field_names:
            for index in list(self.requests)[:-hold_last_n_indices]:
                del self.requests[index]
        if "responses" in field_names:
            for index in list(self.responses)[:-hold_last_n_indices]:
                del self.responses[index]
        if "misc" in field_names:
            self.misc.clear()
        if "labels" in field_names:
            for index in list(self.labels)[:-hold_last_n_indices]:
                del self.labels[index]
        if "framework_states" in field_names:
            self.framework_states.clear()

    @property
    def last_label(self) -> Optional[NodeLabel2Type]:
        """
        Returns the last :py:const:`~df_engine.core.types.NodeLabel2Type` of
        the :py:class:`~df_engine.core.context.Context`.
        Returns `None` if `labels` is empty
        """
        last_index = get_last_index(self.labels)
        return self.labels.get(last_index)

    @property
    def last_response(self) -> Optional[Any]:
        """
        Returns the last `response` of the current :py:class:`~df_engine.core.context.Context`.
        Returns `None if `responses` is empty
        """
        last_index = get_last_index(self.responses)
        return self.responses.get(last_index)

    @property
    def last_request(self) -> Optional[Any]:
        """
        Returns the last `request` of the current :py:class:`~df_engine.core.context.Context`.
        Returns `None if `requests` is empty
        """
        last_index = get_last_index(self.requests)
        return self.requests.get(last_index)

    @property
    def current_node(self) -> Optional[Node]:
        """
        Returns current :py:class:`~df_engine.core.script.Node`.
        """
        actor = self.framework_states.get("actor", {})
        node = (
            actor.get("processed_node")
            or actor.get("pre_response_processed_node")
            or actor.get("next_node")
            or actor.get("pre_transitions_processed_node")
            or actor.get("previous_node")
        )
        if node is None:
            logger.warning(
                "The `current_node` exists when an actor is running between `ActorStage.GET_PREVIOUS_NODE`"
                " and `ActorStage.FINISH_TURN`"
            )

        return node

    @validate_arguments
    def overwrite_current_node_in_processing(self, processed_node: Node):
        """
        Overwrites the current node with a processed node. This method only works in processing functions.

        Parameters
        ----------
        processed_node : :py:class:`~df_engine.core.script.Node`.
            `node` that we need to overwrite current node.
        """
        is_processing = self.framework_states.get("actor", {}).get("processed_node")
        if is_processing:
            self.framework_states["actor"]["processed_node"] = processed_node
        else:
            logger.warning(
                f"The `{self.overwrite_current_node_in_processing.__name__}` "
                "function can only be run during processing functions."
            )


Context.update_forward_refs()

"""
Context
---------------------------
Структура данных, которая используется для хранения контекста.
Предаставляет удомный интерфейс работы с данными: добавлени данных,
сериализация, проверка типов и т.д.
"""
import logging
from uuid import UUID, uuid4

from typing import ForwardRef
from typing import Any, Optional, Union

from pydantic import BaseModel, validate_arguments, Field, validator
from .types import NodeLabel2Type


logger = logging.getLogger(__name__)

Context = ForwardRef("Context")


@validate_arguments
def sort_dict_keys(dictionary: dict) -> dict:
    """
    Сортировка ключей в словаре. Это необходимо делать после десериализвации.
    Т.к. десерализироваться ключи могут в случайном порядке.
    """
    return {key: dictionary[key] for key in sorted(dictionary)}


@validate_arguments
def get_last_index(dictionary: dict) -> int:
    """
    Получение последнего индекса из `dict`, если `dict` пустой возвращается `-1`.
    """
    indexes = list(dictionary)
    return indexes[-1] if indexes else -1


class Context(BaseModel):
    """
    Структура, которая используется для хранения данных о контексте диалога.

    Parameters
    ----------
    id : Union[UUID, int, str]
        `id` это уикальный идентификатор контекста, поумолчанию используется
        случайно сгенеренный `id` с помощью `uuid4`.
        `id` может использоваться для отслеживания поведения отдельного пользоватателя
        например при сборе статистики.

    labels : dict[int, NodeLabel2Type]
        `labels` хранит историю всех пройденных `labels`:
        * ключ - `id` терна
        * значение - `label` на этом терне

    requests : dict[int, Any]
        `requests` хранит историю всех `requests` - полученных агентом запросов:
        * ключ - `id` терна
        * значение - `request` на этом терне

    responses : dict[int, Any]
        `responses` хранит историю всех `responses` - ответо агента:
        * ключ - `id` терна
        * значение - `response` на этом терне

    misc : dict[str, Any]
        `misc` хранит произвольные данные, этот дикт не используется самими фреймворком,
        поэтому хранение любых данных не будет отражаться на логике работы внутренних функций Dialog Flow Framework
        * ключ - название произвольных данных
        * значение - произвольные данные

    validation : bool
        `validation` - это флаг, который сигнализирует о том, что `Actor` выполняет проверку `Plot`, проверка выполняется при инициализании `Actor`.
        Tе функции, которые во время вализации могут давать не валидируемые значения, должны использовать этот флаг, чтобы учитывать режим валидации
        иначе валидация не будет пройдена.

    actor_state : dict[str, Any]
        `actor_state` или `a_s` используется каждый раз при обработке `Context`. В `actor_state` записывает все промежуточные состояния `Actor`.
        После того, как обработка `Context` заканчивается, `Actor` очищает `actor_state`  и возвращает `Context`.
        * ключ - название временных переменных
        * значение - данные временных переменных

    """

    id: Union[UUID, int, str] = Field(default_factory=uuid4)
    labels: dict[int, NodeLabel2Type] = {}
    requests: dict[int, Any] = {}
    responses: dict[int, Any] = {}
    misc: dict[str, Any] = {}
    validation: bool = False
    actor_state: dict[str, Any] = {}

    # validators
    _sort_labels = validator("labels", allow_reuse=True)(sort_dict_keys)
    _sort_requests = validator("requests", allow_reuse=True)(sort_dict_keys)
    _sort_responses = validator("responses", allow_reuse=True)(sort_dict_keys)

    @classmethod
    def cast(
        cls,
        ctx: Union[Context, dict, str] = {},
        *args,
        **kwargs,
    ) -> Context:
        """
        Преобразует разные типы данных в объект класса `Context`

        Parameters
        ----------
        ctx : Union[Context, dict, str]
            Разные типы данных, которые используются для инициалиации объекта типа `Context`
            Если данных не подается создается пустой объект типа `Context`.

        Returns
        -------
        Context
            инициализированный входными данными объект типа `Context`
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

    @validate_arguments
    def add_request(self, request: Any):
        """
        Добавляет в контекст следующий `request`, который соответствует следующему терну.
        Добавление происходит в `requests`, при этом `new_index = last_index + 1`

        Parameters
        ----------
        request : Any
            `request` который надо добавить к контексту
        """
        last_index = get_last_index(self.requests)
        self.requests[last_index + 1] = request

    @validate_arguments
    def add_response(self, response: Any):
        """
        Добавляет в контекст следующий `response`, который соответствует следующему терну.
        Добавление происходит в `responses`, при этом `new_index = last_index + 1`

        Parameters
        ----------
        response : Any
            `response` который надо добавить к контексту
        """
        last_index = get_last_index(self.responses)
        self.responses[last_index + 1] = response

    @validate_arguments
    def add_label(self, label: NodeLabel2Type):
        """
        Добавляет в контекст следующий `label`, который соответствует следующему терну.
        Добавление происходит в `labels`, при этом `new_index = last_index + 1`

        Parameters
        ----------
        label : NodeLabel2Type
            `label` который надо добавить к контексту
        """
        last_index = get_last_index(self.labels)
        self.labels[last_index + 1] = label

    @validate_arguments
    def clear(self, hold_last_n_indexes: int, field_names: list[str] = ["requests", "responses", "labels"]):
        """
        Удаляет все записи из `requests`/`responses`/`labels` кроме последних N тернов в соответствии с `hold_last_n_indexes`. Если `field_names` содержит поле `misc`, тогда оно очищается полностью.

        Parameters
        ----------
        hold_last_n_indexes : int
            задает количество тернов с конца, которое останется после очистки
        field_names : list[str]
            свойства `Context`. которые надо будет очистить
        """
        if "requests" in field_names:
            for index in list(self.requests)[:-hold_last_n_indexes]:
                del self.requests[index]
        if "responses" in field_names:
            for index in list(self.responses)[:-hold_last_n_indexes]:
                del self.responses[index]
        if "mics" in field_names:
            self.misc.clear()
        if "labels" in field_names:
            for index in list(self.labels)[:-hold_last_n_indexes]:
                del self.labels[index]

    @property
    def last_label(self) -> Optional[NodeLabel2Type]:
        """
        Возвращает последний `label` текущего `Context`

        Returns
        -------
        Optional[NodeLabel2Type]
            если `labels` пустой возвращает `None`
        """
        last_index = get_last_index(self.labels)
        return self.labels.get(last_index)

    @property
    def last_response(self) -> Optional[Any]:
        """
        Возвращает последний `response` текущего `Context`

        Returns
        -------
        Optional[Any]
            если `responses` пустой возвращает `None`
        """
        last_index = get_last_index(self.responses)
        return self.responses.get(last_index)

    @property
    def last_request(self) -> Optional[Any]:
        """
        Возвращает последний `request` текущего `Context`

        Returns
        -------
        Optional[Any]
            если `requests` пустой возвращает `None`
        """
        last_index = get_last_index(self.requests)
        return self.requests.get(last_index)

    @property
    def a_s(self) -> dict[str, Any]:
        """
        Alias или сокращенная запись `actor_state`
        """
        return self.actor_state


Context.update_forward_refs()

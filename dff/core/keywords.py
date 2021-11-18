"""
Keywords
---------------------------
Ключевые слова используются для описания сенария диалога.
"""
from enum import Enum, auto


class Keywords(Enum):
    """
    Keywords used to define the dialog script (plot).
    При описании сценария используется тип данных `dict`.
    `Enums` этого класса используются как ключи в этом `dict`.
    По разным ключам лежат разные типы значений преднозначенные для разных целей.

    Enums:
    GLOBAL : keyword is used to define a global node.
    Значение, которое лежит по ключу `GLOBAL`  имеет тип `dict` с ключевыми словами:
    `{TRANSITIONS:..., RESPONSE:..., PROCESSING:..., MISC:...}`
    There can only be one global node in a script (plot).

    The global node is defined at the flow level as opposed to regular nodes.
    Глобальная нода позволяет определять глобальные значения по умолчнию для всех нод

    LOCAL : ключевое слово, которое определяет локальную ноду.
    Значение, которое лежит по ключу `LOCAL`  имеет тип `dict` с ключевыми словами:
    `{TRANSITIONS:..., RESPONSE:..., PROCESSING:..., MISC:...}`
    Локальная нода определяется так же как и остальные ноды в определенном flow.
    Локальная нода позволяет переопределять значения по умолчанию для всех нод в определенном flow.

    TRANSITIONS : ключевое слово, которое определяет возможные переходы из node.
    Значение, которое лежит по ключу `TRANSITIONS`  имеет тип `dict`,
    каждая пара ключ-значение описывает ноду перехода и условие:
    `{label_to_transition_0: condition_for_transition_0, ...,  label_to_transition_N: condition_for_transition_N}`
    `label_to_transition_i` - определяет куда нахождение ноды, в которую будет выполнен переход, если условие
    `condition_for_transition_i` будет равно `True`.

    RESPONSE : ключевое слово, которое определяет результат возращаемый пользователю при попадании в ноду.
    Значение, лежащее по ключу `RESPONSE`  может иметь любой тип данных.

    PROCESSING : ключевое слово, которое определяет препросессинг, который вызывается перед генерацией респонса.
    Значение, лежащее по ключу `PROCESSING` должно иметь тип `dict`:
    `{"PROC_0": proc_func_0, ..., "PROC_N": proc_func_N}`
    `"PROC_i"` - это произвольное название этапа препроцессинга в пайплайне.
    Очередность определения препроцессинга в `dict` и определяет порядок вызова функции `proc_func_i`

    MISC : ключевое слово, которое определяет `dict` содержащий дополнительные данные,
    использование которых не было предусмотренно при проектировании `DFF`.
    Значение, лежащее по ключу `MISC` должно иметь тип `dict`:
    `{"VAR_KEY_0": VAR_VALUE_0, ..., "VAR_KEY_N": VAR_VALUE_N}`
    `"VAR_KEY_0"` - это произвольное название переменной, которая сохраняется в `MISC`.

    """

    GLOBAL = auto()
    LOCAL = auto()
    TRANSITIONS = auto()
    RESPONSE = auto()
    PROCESSING = auto()
    MISC = auto()


# Redefine shortcuts
GLOBAL = Keywords.GLOBAL
LOCAL = Keywords.LOCAL
TRANSITIONS = Keywords.TRANSITIONS
RESPONSE = Keywords.RESPONSE
PROCESSING = Keywords.PROCESSING
MISC = Keywords.MISC

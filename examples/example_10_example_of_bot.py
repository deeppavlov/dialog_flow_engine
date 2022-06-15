from df_engine.core.keywords import GLOBAL, TRANSITIONS, RESPONSE, MISC, LOCAL
from df_engine.core.keywords import PRE_RESPONSE_PROCESSING, PRE_TRANSITIONS_PROCESSING
from df_engine.core import Context, Actor
import df_engine.conditions as cnd
import df_engine.responses as rsp
import df_engine.labels as lbl
import example_1_basics
from df_engine.core.types import NodeLabel3Type
from typing import Union, Optional, Any
import logging
import re

logger = logging.getLogger(__name__)


def complex_user_answer_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    request = ctx.last_request
    # the user request can be any dict
    return not isinstance(request, str)


def flow_node_ok_transition(ctx: Context, actor: Actor, *args, **kwargs) -> NodeLabel3Type:
    return ("flow", "node_ok", 1.0)


def save_previous_node_response_to_ctx_processing(ctx: Context, actor: Actor, prefix=None, *args, **kwargs) -> Context:
    processed_node = ctx.current_node
    ctx.misc["previous_node_response"] = processed_node.response
    if prefix is not None:
        if not callable(ctx.misc["previous_node_response"]):
            processed_node.response = f"{prefix}: {ctx.misc['previous_node_response']}"
        elif callable(processed_node.response):
            processed_node.response = f"{prefix}: {ctx.misc['previous_node_response'](ctx, actor, *args, **kwargs)}"
    return ctx


def add_prefix(prefix):
    def add_prefix_processing(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
        processed_node = ctx.current_node
        if not callable(processed_node.response):
            processed_node.response = f"{prefix}: {processed_node.response}"
        elif callable(processed_node.response):
            processed_node.response = f"{prefix}: {processed_node.response(ctx, actor, *args, **kwargs)}"
        ctx.overwrite_current_node_in_processing(processed_node)
        return ctx

    return add_prefix_processing


def add_misc():
    def add_misc_processing(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
        processed_node = ctx.current_node
        if not callable(processed_node.response):
            processed_node.response = f"misc: {processed_node.misc} {processed_node.response}"
        elif callable(processed_node.response):
            processed_node.response = (
                f"misc: {processed_node.misc} " f"{processed_node.response(ctx, actor, *args, **kwargs)}"
            )
        ctx.overwrite_current_node_in_processing(processed_node)
        return ctx

    return add_misc_processing


def high_priority_node_transition(flow_label, label):
    def transition(ctx: Context, actor: Actor, *args, **kwargs) -> NodeLabel3Type:
        return (flow_label, label, 2.0)

    return transition


def upper_case_response(response: str):
    return response.upper()


def okay_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
    return str(rsp.choice(["OKAY", "OK"])(ctx, actor, *args, **kwargs))


def fallback_trace_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
    logger.warning(f"ctx={ctx}")
    return str(
        {
            "previous_node": list(ctx.labels.values())[-2],
            "last_request": ctx.last_request,
        }
    )


def talk_about_topic_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
    request = ctx.last_request
    topic_pattern = re.compile(r"(.*talk about )(.*)\.")
    topic = topic_pattern.findall(request)
    topic = topic and topic[0] and topic[0][-1]
    if topic:
        return f"Sorry, I can not talk about {topic} now. Dialog len {len(ctx.requests)}"
    else:
        return f"Sorry, I can not talk about that now. {len(ctx.requests)}"


def talk_about_topic_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    request = ctx.last_request
    return "talk about" in request.lower()


def no_lower_case_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    request = ctx.last_request
    return "no" in request.lower()


# create script of dialog

script = {
    GLOBAL: {
        TRANSITIONS: {
            ("global_flow", "start_node", 1.5): cnd.exact_match("global start"),
            ("flow", "node_hi", 1.5): cnd.exact_match("global hi"),
        },
        MISC: {"var1": "global_data", "var2": "global_data", "var3": "global_data"},
        PRE_RESPONSE_PROCESSING: {
            "proc_name_1": add_prefix("l1_global"),
            "proc_name_2": add_prefix("l2_global"),
        },
        PRE_TRANSITIONS_PROCESSING: {"proc_tr__name_1": save_previous_node_response_to_ctx_processing},
    },
    "global_flow": {
        "start_node": {
            RESPONSE: "INITIAL NODE",
            TRANSITIONS: {
                ("flow", "node_hi"): cnd.regexp(r"base"),
                "fallback_node": cnd.true(),
            },
        },
        "fallback_node": {
            RESPONSE: "oops",
            TRANSITIONS: {
                lbl.previous(): cnd.exact_match("initial"),
                # to global flow start node
                lbl.repeat(): cnd.true()
                # global flow, fallback node
            },
        },
    },
    "flow": {
        LOCAL: {
            MISC: {
                "var2": "rewrite_by_flow",
                "var3": "rewrite_by_flow",
            },
            PRE_RESPONSE_PROCESSING: {
                "proc_name_1": add_prefix("l1_flow"),
                "proc_name_2": add_prefix("l2_flow"),
            },
            PRE_TRANSITIONS_PROCESSING: {"proc_tr__name_2": save_previous_node_response_to_ctx_processing},
        },
        "node_hi": {
            MISC: {"var3": "rewrite_by_hi"},
            PRE_RESPONSE_PROCESSING: {
                "proc_name_1": add_prefix("l1_flow_hi"),
                "proc_name_2": add_prefix("l2_flow_hi"),
                "proc_name_3": add_misc(),
            },
            RESPONSE: "Hi!!!",
            TRANSITIONS: {
                ("flow", "node_complex"): complex_user_answer_condition,
                ("flow", "node_hi"): cnd.exact_match("Hi"),
                high_priority_node_transition("flow", "node_no"): no_lower_case_condition,
                ("flow", "node_topic"): talk_about_topic_condition,
                flow_node_ok_transition: cnd.all([cnd.true(), cnd.has_last_labels(flow_labels=["global_flow"])]),
            },
        },
        "node_no": {
            MISC: {"var3": "rewrite_by_NO"},
            PRE_RESPONSE_PROCESSING: {
                "proc_name_1": add_prefix("l1_flow_no"),
                "proc_name_2": add_prefix("l2_flow_no"),
                "proc_name_3": add_misc(),
            },
            RESPONSE: upper_case_response("NO"),
            TRANSITIONS: {
                ("flow", "node_complex"): complex_user_answer_condition,
                ("flow", "node_hi"): cnd.regexp(r"hi"),
                ("flow", "node_topic"): talk_about_topic_condition,
                lbl.to_fallback(0.1): cnd.true(),
            },
        },
        "node_complex": {
            MISC: {"var3": "rewrite_by_COMPLEX"},
            PRE_RESPONSE_PROCESSING: {
                "proc_name_1": add_prefix("l1_flow_complex"),
                "proc_name_2": add_prefix("l2_flow_complex"),
                "proc_name_3": add_misc(),
            },
            RESPONSE: "Not string detected",
            TRANSITIONS: {
                ("flow", "node_complex"): complex_user_answer_condition,
                ("flow", "node_hi"): cnd.regexp(r"hi"),
                lbl.to_fallback(0.1): cnd.true(),
            },
        },
        "node_topic": {
            MISC: {"var3": "rewrite_by_TOPIC"},
            # PRE_RESPONSE_PROCESSING: {"proc_name_1": add_prefix("l1_flow_topic"), "proc_name_2": add_prefix("l2_flow_topic"),"proc_name_3": add_misc()},
            RESPONSE: talk_about_topic_response,
            TRANSITIONS: {
                ("flow", "node_complex"): complex_user_answer_condition,
                lbl.forward(0.5): cnd.any([cnd.regexp(r"ok"), cnd.regexp(r"o k")]),
                lbl.backward(0.5): cnd.any([cnd.regexp(r"node complex"), complex_user_answer_condition]),
            },
        },
        "node_ok": {
            MISC: {"var3": "rewrite_by_OK"},
            PRE_RESPONSE_PROCESSING: {
                "proc_name_1": add_prefix("l1_flow_ok"),
                "proc_name_2": add_prefix("l2_flow_ok"),
                "proc_name_3": add_misc(),
            },
            RESPONSE: okay_response,
            TRANSITIONS: {
                ("flow", "node_complex"): complex_user_answer_condition,
                lbl.previous(): cnd.regexp(r"previous"),
            },
        },
        "fallback_node": {  # We get to this node if an error occurred while the agent was running
            RESPONSE: fallback_trace_response,
            TRANSITIONS: {
                ("flow", "node_complex"): complex_user_answer_condition,
                "node_hi": cnd.all([cnd.exact_match("Hi"), cnd.exact_match("Hello")]),
                "node_ok": cnd.exact_match("Okey"),
            },
        },
    },
}

# init actor
actor = Actor(
    script,
    start_label=("global_flow", "start_node"),
    fallback_label=("global_flow", "fallback_node"),
    label_priority=1.0,
)


# handler requests

# turn_handler - a function is made for the convenience of working with an actor


def turn_handler(
    in_request: str,
    ctx: Union[Context, str, dict],
    actor: Actor,
    true_out_response: Optional[str] = None,
):
    # Context.cast - gets an object type of [Context, str, dict] returns an object type of Context
    ctx = Context.cast(ctx)
    # Add in current context a next request of user
    ctx.add_request(in_request)
    # pass the context into actor and it returns updated context with actor response
    ctx = actor(ctx)
    #  breakpoint()
    # get last actor response from the context
    out_response = ctx.last_response
    # the next condition branching needs for testing
    if true_out_response is not None and true_out_response != out_response:
        msg = f"in_request={in_request} -> true_out_response != out_response: {true_out_response} != {out_response}"
        raise Exception(msg)
    else:
        print(f"in_request={in_request} -> NODE {list(ctx.labels.values())[-1]} RESPONSE {out_response}")
    return out_response, ctx


# edit this dialog


testing_dialog = [
    (
        "base",
        "misc: {'var1': 'global_data', 'var2': 'rewrite_by_flow', 'var3': 'rewrite_by_hi'} response: l2_flow_hi: l1_flow_hi: Hi!!!",
    ),
    # start_node -> node1
    (
        "no",
        "misc: {'var1': 'global_data', 'var2': 'rewrite_by_flow', 'var3': 'rewrite_by_NO'} response: l2_flow_no: l1_flow_no: NO",
    ),
    # node1 -> node2
    (
        "talk about books",
        "misc: {'var1': 'global_data', 'var2': 'rewrite_by_flow', 'var3': 'rewrite_by_TOPIC'} response: l2_flow_topic: l1_flow_topic:",
    ),
    # node3 -> node4
    (
        "ok",
        "misc: {'var1': 'global_data', 'var2': 'rewrite_by_flow', 'var3': 'rewrite_by_OK'} response: l2_flow_ok: l1_flow_ok: ",
    ),
    # node4 -> node1
    (
        "previous",
        "NODE ('flow', 'node_topic') RESPONSE misc: {'var1': 'global_data', 'var2': 'rewrite_by_flow', 'var3': 'rewrite_by_TOPIC'} response: l2_flow_topic: l1_flow_topic: ",
    ),
    # node1 -> fallback_node
    (
        "{1:2}",
        "misc: {'var1': 'global_data', 'var2': 'rewrite_by_flow', 'var3': 'rewrite_by_COMPLEX'} response: l2_flow_complex: l1_flow_complex:",
    ),
    # fallback_node -> fallback_node
    (
        "f",
        "misc: {'var1': 'global_data', 'var2': 'global_data', 'var3': 'global_data'} response: l2_global: l1_global: oops ",
    ),
]


def run_test(mode=None):
    ctx = {}
    for in_request, true_out_response in testing_dialog:
        _, ctx = turn_handler(in_request, ctx, actor, true_out_response=true_out_response)
        if mode == "json":
            ctx = ctx.json()
            if isinstance(ctx, str):
                logging.info("context serialized to json str")
            else:
                raise Exception(f"ctx={ctx} has to be serialized to json string")
        elif mode == "dict":
            ctx = ctx.dict()
            if isinstance(ctx, dict):
                logging.info("context serialized to dict")
            else:
                raise Exception(f"ctx={ctx} has to be serialized to dict")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s-%(name)15s:%(lineno)3s:%(funcName)20s():%(levelname)s - %(message)s",
        level=logging.INFO,
    )
    # run_test()
    example_1_basics.run_interactive_mode(actor)

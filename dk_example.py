from df_engine.core.keywords import GLOBAL, TRANSITIONS, RESPONSE
from df_engine.core import Context, Actor
import df_engine.conditions as cnd
from typing import Union, Optional

def complex_user_answer_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    request = ctx.last_request
    # the user request can be anything
    return {"some_key": "some_value"} == request



def complex_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
    request = ctx.last_request
    topic_pattern = re.compile(r"(.*talk about )(.*)\.")
    topic = topic_pattern.findall(request)
    topic = topic and topic[0] and topic[0][-1]
    if topic:
        return f"Sorry, I can not talk about {topic} now."
    else:
        return "Sorry, I can not talk about that now."


def predetermined_condition(condition: bool):
    # wrapper for internal condition function
    def internal_condition_function(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        # It always returns `condition`.
        return condition

    return internal_condition_function



def no_lower_case_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    request = ctx.last_request
    return "no" in request.lower()

# create script of dialog
script = {
    GLOBAL: {TRANSITIONS: {("flow", "node_hi"): cnd.exact_match("Hi"),
                           ("flow","node_no"): no_lower_case_condition,
                           ("flow","node_complex"):complex_user_answer_condition,
                           ("flow", "node_ok"): cnd.true()}},
    "flow": {
        "node_hi": {RESPONSE: "Hi!!!"},
        "node_no": {RESPONSE: "NO"},
        "node_complex":{RESPONSE:complex_response},
        "node_ok": {RESPONSE: "Okey"},
        "fallback_node": {  # We get to this node if an error occurred while the agent was running
            RESPONSE: "Ooops",
            TRANSITIONS: {"node_hi": cnd.exact_match("Hi"),
                          "node_ok": cnd.exact_match("Okey")},
        },
    },



}

# init actor
actor = Actor(script, start_label=("flow", "node_hi"))


# handler requests

# turn_handler - a function is made for the convenience of working with an actor
def turn_handler(
    in_request: str, ctx: Union[Context, str, dict], actor: Actor, true_out_response: Optional[str] = None
):
    # Context.cast - gets an object type of [Context, str, dict] returns an object type of Context
    ctx = Context.cast(ctx)
    # Add in current context a next request of user
    ctx.add_request(in_request)
    # pass the context into actor and it returns updated context with actor response
    ctx = actor(ctx)
    # get last actor response from the context
    out_response = ctx.last_response
    # the next condition branching needs for testing
    if true_out_response is not None and true_out_response != out_response:
        msg = f"in_request={in_request} -> true_out_response != out_response: {true_out_response} != {out_response}"
        raise Exception(msg)
    else:
        print(f"in_request={in_request} -> {out_response}")
    return out_response, ctx


# edit this dialog
testing_dialog = [
    ("Hi", "Hi, how are you?"),  # start_node -> node1
    ("i'm fine, how are you?", "Good. What do you want to talk about?"),  # node1 -> node2
    ("Let's talk about music.", "Sorry, I can not talk about music now."),  # node2 -> node3
    ("Ok, goodbye.", "bye"),  # node3 -> node4
    ("Hi", "Hi, how are you?"),  # node4 -> node1
    ("stop", "Ooops"),  # node1 -> fallback_node
    ("stop", "Ooops"),  # fallback_node -> fallback_node
    ("Hi", "Hi, how are you?"),  # fallback_node -> node1
    ("i'm fine, how are you?", "Good. What do you want to talk about?"),  # node1 -> node2
    ("Let's talk about music.", "Sorry, I can not talk about music now."),  # node2 -> node3
    ("Ok, goodbye.", "bye"),  # node3 -> node4
]


def run_test():
    ctx = {}
    for in_request, true_out_response in testing_dialog:
        _, ctx = turn_handler(in_request, ctx, actor, true_out_response=true_out_response)


# interactive mode
def run_interactive_mode(actor):
    ctx = {}
    while True:
        in_request = input("type your answer: ")
        _, ctx = turn_handler(in_request, ctx, actor)

run_test()
print('TESTED WELL')
run_interactive_mode(actor)

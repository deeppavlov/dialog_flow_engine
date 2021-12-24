# %%
from dfe.core import Context, Actor
import dfe.responses as rsp


def test_response():
    ctx = Context()
    actor = Actor(plot={"flow": {"node": {}}}, start_label=("flow", "node"))
    for _ in range(10):
        assert rsp.choice(["text1", "text2"])(ctx, actor) in ["text1", "text2"]

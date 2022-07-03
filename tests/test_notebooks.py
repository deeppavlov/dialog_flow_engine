from testbook import testbook


@testbook("./notebooks/Quickstart.ipynb", execute=True)
def test_quickstart(tb):
    tb.ref("run_test")()


@testbook("./notebooks/Using_db&Integrating_models.ipynb", execute=True)
def test_db(tb):
    tb.ref("run_test")()

from testbook import testbook


@testbook('./notebooks/Quickstart.ipynb', execute=True)
def test_quickstart(tb):
   tb.ref("run_test")()

from ward import test
from agents_api.activities.utils import get_evaluator


@test("evaluator: csv reader")
def _():
    e = get_evaluator({})
    result = e.eval('[r for r in csv.reader("a,b,c\\n1,2,3")]')
    assert result == [['a', 'b', 'c'], ['1', '2', '3']]


@test("evaluator: csv writer")
def _():
    e = get_evaluator({})
    result = e.eval('csv.writer("a,b,c\\n1,2,3").writerow(["4", "5", "6"])')
    # at least no exceptions
    assert result == 7

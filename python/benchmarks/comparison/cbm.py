import pathlib
from mapfmclient import Problem, Solution

from python.algorithm import MapfAlgorithm

this_dir = pathlib.Path(__file__).parent.absolute()
from python.benchmarks.comparison.src.main import solve

from python.benchmarks.comparison.util import get_src_modules, solve_with_modules

modules = get_src_modules()


class CBM(MapfAlgorithm):
    def solve(self, problem: Problem) -> Solution:
        return solve(problem, False, False)

    @property
    def name(self) -> str:
        return "CBM (Robbin)"

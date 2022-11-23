from typing import Union

from mapfmclient import Problem, Solution

from python.benchmarks.comparison.src.cbm.ssp.cbm_ssp_solver import CBMSSPSolver
from python.benchmarks.comparison.src.data.constraint_tree import ConstraintTree


def solve(problem: Problem, reset_teg: bool,
          disappearing_agents: bool) -> Union[Solution]:
    solver = CBMSSPSolver
    grid = solver.Grid(problem)

    low_level_solver = solver.LowLevelSolver(grid, reset_teg,
                                             disappearing_agents)
    high_level_solver = solver.HighLevelSolver(low_level_solver, problem)

    constraint_tree = ConstraintTree(0, None)
    root = solver.CTNode(set(), constraint_tree)

    solution = high_level_solver.solve(root)

    return solution.to_mapfm_solution(grid, problem)

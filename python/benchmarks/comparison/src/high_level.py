from pathlib import Path

import time
from queue import PriorityQueue
from copy import copy

from mapfmclient import Problem

from python.benchmarks.comparison.src.data.conflicts import VertexConflict, EdgeConflict
from python.benchmarks.comparison.src.data.constraints import VertexConstraint, EdgeConstraint
from python.benchmarks.comparison.src.low_level import LowLevelSolver
from python.benchmarks.comparison.src.ctnode import CTNode
from python.benchmarks.comparison.src.paths import FullSolution


class HighLevelSolver:
    def __init__(self, low_level_solver: LowLevelSolver,
                 problem: Problem) -> None:
        self.low_level_solver = low_level_solver
        self.OPEN: PriorityQueue[CTNode] = PriorityQueue()

        self.problem = problem

        # Telemetry
        self.amount_of_conflicts = 0

    def solve(self, root: CTNode) -> FullSolution:
        sol = self.low_level_solver.solve_all_agents(root)
        if sol is None:
            raise RuntimeError("No solution found in ROOT!")

        root.update_sol(sol)

        self.append_node(root)

        while self.OPEN.qsize() > 0:
            current_node = self.OPEN.get()

            first_conflict = current_node.full_solution.get_first_conflict()
            if first_conflict is None:
                current_node.full_solution.amount_of_conflicts = self.amount_of_conflicts
                return current_node.full_solution

            self.amount_of_conflicts += 1
            for agent in [first_conflict.a_i, first_conflict.a_j]:
                child = copy(current_node)
                child.full_solution = copy(current_node.full_solution)

                if isinstance(first_conflict, VertexConflict):
                    child.add_constraint(
                        VertexConstraint(first_conflict.v, agent,
                                         first_conflict.t))
                elif isinstance(first_conflict, EdgeConflict):
                    if agent == first_conflict.a_i:
                        child.add_constraint(
                            EdgeConstraint(
                                (first_conflict.e[0], first_conflict.e[1]),
                                agent, first_conflict.t))
                    else:
                        child.add_constraint(
                            EdgeConstraint(
                                (first_conflict.e[1], first_conflict.e[0]),
                                agent, first_conflict.t))

                path = self.low_level_solver.solve_for_agent(agent, child)
                if path is not None:
                    child.update_agent_path(agent, path)
                    self.append_node(child)

        raise RuntimeError("NO SOLUTION FOUND!")

    def append_node(self, node: CTNode) -> None:
        if node.cost is not None:
            self.OPEN.put(node)

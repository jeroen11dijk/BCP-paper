import re
import subprocess

from mapfmclient import Problem as cProblem, Solution

from python.algorithm import MapfAlgorithm

bcp_mapf_path = "/data/BCP-paper/python/benchmarks/comparison/bcp-inmatch/bcp-inmatch"


class BCPSolver(MapfAlgorithm):
    def solve(self, problem: cProblem) -> Solution:
        version_info = "version 1 graph"
        map_path = "temp/" + problem.name
        num_of_agents = len(problem.starts)

        types = {}
        starts = []
        goals = []
        for i, start in enumerate(problem.starts):
            x = start.x
            y = start.y
            c = start.color
            start_node = "({},{})".format(x, y)
            starts.append(start_node)
            if not c in types: types[c] = []
            types[c].append(i)
        for i, goal in enumerate(problem.goals):
            x = goal.x
            y = goal.y
            c = goal.color
            goal_node = "({},{})".format(x, y)
            goals.append((goal_node, c))

        scenario_path = map_path.replace(".map", ".scen")
        with open(scenario_path, "w") as f:
            f.write(version_info + "\n")
            f.write(problem.name + "\n")
            f.write("Num_of_Agents {}\n".format(num_of_agents))
            f.write("types\n")
            for key, val in types.items():
                f.write("{} {}\n".format(key, " ".join([str(v) for v in val])))
            f.write("agents starts\n")
            for i, start in enumerate(starts):
                f.write("{} {}\n".format(i, start))
            f.write("goals\n")
            for goal in goals:
                f.write("{} {}\n".format(goal[1], goal[0]))
            f.close()

        with open(map_path, "w") as f:
            f.write("type octile\nheight {}\nwidth {}\nmap\n".format(problem.height, problem.width))
            for line in problem.grid:
                for cell in line:
                    f.write("@" if cell else ".")
                f.write("\n")
            f.close()

        subprocess.run([bcp_mapf_path, "-f", scenario_path], timeout=problem.timeout,
                       stdout=subprocess.DEVNULL)  # .returncode

        paths = []
        with open("outputs/" + problem.name.replace(".map", ".sol"), "r") as f:
            try:
                sol_val = int(f.readline())
            except:
                return None;
            f.readline()
            re_p = re.compile("(\(\d+,\d+\))")
            while True:
                line = f.readline()
                if not line: break
                path = []
                for node in re_p.findall(line):
                    node = node.replace("(", "").replace(")", "")
                    x, y = node.split(",")
                    path.append((int(x), int(y)))
                paths.append(path)

        return Solution.from_paths(paths)

    @property
    def name(self) -> str:
        return "BCP-MAPFM-Inmatch"

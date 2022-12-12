import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

colors = [
    "#648fff",
    "#785ef0",
    "#dc267f",
    "#fe6100",
    "#ffb000",
    "0000000"
]

linestyles = {"CBSPrematch": '--', "BCPPrematch": '-', "CBS-TA": (5, (10, 3)), "CBSInmatch": ":", "BCPInmatch": '-.', "CBM": (0, (5, 1))}
labels = {"CBSPrematch": 'CBS-Outmatch', "BCPPrematch": 'BCP-Outmatch', "CBS-TA": 'CBS-TA', "CBSInmatch": 'CBS-Inmatch', "BCPInmatch": 'BCP-Inmatch', "CBM": "CBM"}
background = (34, 39, 46)


def lighten(r, g, b, amount):
    return int(min(255, r + 255*amount)), int(min(255, g + 255*amount)), int(min(255, b + 255*amount))


def rgb_to_colour(r, g, b, transparency_fraction=None):
    if transparency_fraction is None:
        return f"#{hex(r)[2:]}{hex(g)[2:]}{hex(b)[2:]}"
    else:
        return f"#{hex(r)[2:]}{hex(g)[2:]}{hex(b)[2:]}{hex(int(transparency_fraction * 255))[2:]}"


def average(l: list) -> float:
    return sum(l) / len(l) if len(l) != 0 else -1


def percentile(l: list[float], perc: float) -> float:
    if len(l) == 0:
        return -1

    l.sort()
    index = len(l) * (perc/100)

    i = int(index)
    f = index - i

    v1 = l[i]
    v2 = l[i + 1] if i + 1 < len(l) else l[i]
    return v1 * f + v2 * (1 - f)


def graph_results(*args, under,
                  save=True,
                  graph_times=False,
                  graph_percentage=True,
                  legend=True,
                  limit=float("inf")
                  ):
    plt.style.use('seaborn-white')
    plt.rcParams["axes.grid"] = True

    if graph_times and graph_percentage:
        plt.rcParams["figure.figsize"] = (7, 5)
        fig, (percentage, times) = plt.subplots(2, 1, sharex=True)

    elif graph_times or graph_percentage:
        plt.rcParams["figure.figsize"] = (6, 4)
        fig, (subplt) = plt.subplots(1, 1)
        if graph_percentage:
            percentage = subplt
        else:
            times = subplt
    else:
        assert False, "should graph something"

    plt.rcParams['font.size'] = '14'

    if graph_percentage and graph_times:
        plt.subplots_adjust(hspace=0.3)
        plt.tight_layout(pad=0)
        plt.margins(0, 0)

    if graph_percentage:
        percentage.xaxis.set_major_locator(MaxNLocator(integer=True))
        percentage.set_ylabel("% solved")
        if not graph_times:
            percentage.set_xlabel(under)

    if graph_times:
        times.xaxis.set_major_locator(MaxNLocator(integer=True))
        times.set_xlabel("number of agents")
        times.set_ylabel("seconds")

    if graph_percentage:
        percentage.set_ylim(0, 105)

    save_location = args[-1] + "/Graphs"
    ppydata = []

    plt.tight_layout()

    longest = 65

    for plt_index, (fn, label) in enumerate(args[:-1]):
        with open(fn, "r") as f:
            if graph_percentage:
                percentagexdata = []
                percentageydata = []

            if graph_times:
                timesxdata = []
                times10pydata = []
                times50pydata = []
                times90pydata = []

            lines = f.readlines()
            first_non_solved = False
            for l in [l.strip() for l in lines if l.strip() != ""]:
                before, after = l.split(":")
                after_list = eval(after)
                num_agents = int(before)
                if limit is not None:
                    after_list = [x if x is None or x <= limit else None for x in after_list]
                fraction_solved = (len(after_list) - after_list.count(None)) / len(after_list)
                solved_times = [i for i in after_list if i is not None]

                if fraction_solved == 0 and num_agents > 10 and not first_non_solved:
                    first_non_solved = True
                    if num_agents > longest:
                        longest = num_agents

                if fraction_solved != 0:
                    if num_agents == 100:
                        longest = 100
                    if graph_percentage:
                        percentagexdata.append(num_agents)
                        percentageydata.append(fraction_solved * 100)

                    if graph_times and len(solved_times) != 0:
                        timesxdata.append(num_agents)
                        times10pydata.append(percentile(solved_times, 10))
                        times50pydata.append(percentile(solved_times, 50))
                        times90pydata.append(percentile(solved_times, 90))
                elif len(percentageydata) > 0 and percentageydata[-1] != 0 and graph_percentage:
                    percentagexdata.append(num_agents)
                    percentageydata.append(0)

            if graph_percentage:
                percentage.plot(
                    percentagexdata,
                    percentageydata,
                    linestyle=linestyles[label],
                    color=colors[plt_index],
                    label=labels[label],
                    linewidth=2
                )
    if graph_percentage:
        percentage.set_xlim(0, longest)
    else:
        times.set_xlim(0, longest + 1)

    if legend:
        plt.legend(facecolor='white', framealpha=1, frameon=True, edgecolor="black", prop={'size': 10})
    plt.show()
    if save:
        fig.savefig(f"{save_location}.png", pad_inches=0, format='png')

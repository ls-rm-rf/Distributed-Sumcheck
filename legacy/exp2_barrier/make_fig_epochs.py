"""Recovery-epoch curves for kernel-only refresh.

From the bundle root: python legacy/exp2_barrier/make_fig_epochs.py
Writes figures/epochs_to_recovery.pdf and .png beside this script.
The curves use ceil((t+1)/c) only where c <= t.
"""
import math
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "mathtext.fontset": "cm",
    "font.size": 8.5,
    "axes.labelsize": 9,
    "axes.linewidth": 0.6,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
})

SURFACE = "#fcfcfb"
INK, INK2 = "#0b0b0b", "#52514e"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]      # validated slots 1-3
MARKERS = ["o", "s", "^"]
DASHES = [(None, None), (5, 1.8), (1.4, 1.4)]

ts = list(range(2, 21))
budgets = [1, 2, 4]

fig, ax = plt.subplots(figsize=(4.65, 2.75))
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)

for c, col, mk, dsh in zip(budgets, SERIES, MARKERS, DASHES):
    xs = [t for t in ts if t >= c]          # the theorem assumes c <= t
    ys = [math.ceil((t + 1) / c) for t in xs]
    assert all(y * c >= t + 1 and (y - 1) * c < t + 1 for t, y in zip(xs, ys))
    line, = ax.plot(xs, ys, color=col, lw=1.8, marker=mk, ms=4.0,
                    markevery=2, markeredgecolor=SURFACE, markeredgewidth=0.9,
                    solid_capstyle="round", zorder=3)
    if dsh[0] is not None:
        line.set_dashes(dsh)
    ax.annotate(rf"$c={c}$", xy=(xs[-1], ys[-1]), xytext=(4, 0),
                textcoords="offset points", va="center", ha="left",
                fontsize=8.8, color=INK2, zorder=4)

ax.set_xlabel(r"Sharing threshold $t$")
ax.set_ylabel("Epochs until $Pz$ is recovered")
ax.set_xlim(1.4, 22.6)
ax.set_ylim(0, 22.5)
ax.set_xticks([2, 5, 10, 15, 20])
ax.set_yticks([0, 5, 10, 15, 20])
ax.grid(True, color="#e6e5e1", lw=0.5, zorder=0)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color("#c8c7c2")
ax.tick_params(colors=INK2, length=3, width=0.6)
ax.xaxis.label.set_color(INK); ax.yaxis.label.set_color(INK)

ax.annotate("with the completed sampler:\nno recovery, for any number of epochs",
            xy=(0.035, 0.97), xycoords="axes fraction", ha="left", va="top",
            fontsize=8.0, color=INK2, style="italic", linespacing=1.35)

fig.tight_layout(pad=0.4)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(OUT, exist_ok=True)
fig.savefig(os.path.join(OUT, "epochs_to_recovery.pdf"), facecolor=SURFACE, bbox_inches="tight")
fig.savefig(os.path.join(OUT, "epochs_to_recovery.png"), dpi=320, facecolor=SURFACE, bbox_inches="tight")
print("written")

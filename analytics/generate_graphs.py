import os
import sqlite3
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
from dotenv import load_dotenv
import calendar
import datetime
from scipy.interpolate import make_interp_spline
import numpy as np
import json
import logging
from lxml import etree

today_weekday = datetime.datetime.today().weekday()
weekday_name = calendar.day_name[today_weekday]
print(f"Ticking every {weekday_name}")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_PATH = os.path.join(BASE_DIR, ".env")
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)

REPO_NAME = os.getenv("REPO")
DARK_MODE = os.getenv("DARK_MODE", "false").lower() == "true"

if not REPO_NAME:
    print("ERROR: Environment variable 'REPO' is not set. Aborting graph generation.")
    exit(1)

if DARK_MODE:
    plt.style.use("dark_background")
    print("Dark mode enabled for graphs.")
else:
    plt.style.use("seaborn-v0_8-darkgrid")
    print("Light mode enabled for graphs.")

DB_PATH = os.path.join(BASE_DIR, "data", "github_traffic.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "assets", "graphs")

os.makedirs(OUTPUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
query = """
SELECT
    timestamp, clones, views, total_downloads, total_stars 
FROM
    traffic
ORDER BY
    timestamp
"""
df = pd.read_sql(query, conn)
conn.close()

df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.date
df.fillna(0, inplace=True)

matplotlib_logger = logging.getLogger("matplotlib.font_manager")
matplotlib_logger.setLevel(logging.ERROR)

mpl.rcParams.update({
    "svg.fonttype": "none",
    "font.family": "Helvetica",
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "xtick.labelsize": 8,
    "ytick.labelsize": 12,
})


def save_graph(x, y, title, ylabel, filename, marker, color):
    df_plot = pd.DataFrame({"timestamp": x, "value": y})
    df_plot["timestamp"] = pd.to_datetime(df_plot["timestamp"])
    df_plot = df_plot[df_plot["timestamp"].dt.weekday == today_weekday]

    if df_plot.empty:
        print(f"Skipping {filename} - No matching weekday data.")
        return

    x_dates = mdates.date2num(df_plot["timestamp"])
    y_vals = df_plot["value"]

    plt.figure(figsize=(7, 5), dpi=100)

    if len(x_dates) > 3:
        x_smooth = np.linspace(x_dates.min(), x_dates.max(), 300)
        spline = make_interp_spline(x_dates, y_vals, k=3)
        y_smooth = spline(x_smooth)
        plt.plot(
            mdates.num2date(x_smooth), y_smooth, color=color, label=title, linewidth=2.5
        )

    plt.scatter(df_plot["timestamp"], y_vals, color=color, marker=marker, zorder=3)

    plt.xlabel("Date")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle="-", linewidth=0.5, alpha=0.2)
    plt.tight_layout()

    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%-m-%-d-%Y"))
    ax.xaxis.set_major_locator(
        mdates.WeekdayLocator(byweekday=today_weekday, interval=1)
    )
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    if len(x_dates) == 1:
        plt.xlim(mdates.num2date(x_dates[0]), mdates.num2date(x_dates[0] + 10))
    else:
        plt.xlim(mdates.num2date(x_dates.min()), mdates.num2date(x_dates.max()))

    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, format="svg", bbox_inches="tight", dpi=100)
    print(f"Graph saved as {filepath}")


def save_snapshot_graph(df, column_name, title, ylabel, filename, marker, color):
    df_filtered = df[df[column_name] > 0].copy()
    df_filtered["timestamp"] = pd.to_datetime(df_filtered["timestamp"])
    df_filtered = df_filtered[df_filtered["timestamp"].dt.weekday == today_weekday]

    if df_filtered.empty:
        print(f"Skipping {filename} - No matching weekday data.")
        return

    x_dates = mdates.date2num(df_filtered["timestamp"])
    y_vals = df_filtered[column_name]

    first_date = df_filtered["timestamp"].iloc[0]
    last_date = df_filtered["timestamp"].iloc[-1]
    x_axis_end = (
        last_date
        if (last_date - first_date).days >= 3
        else first_date + pd.Timedelta(days=3)
    )

    plt.figure(figsize=(7, 5), dpi=100)

    if len(x_dates) > 3:
        x_smooth = np.linspace(x_dates.min(), x_dates.max(), 300)
        spline = make_interp_spline(x_dates, y_vals, k=3)
        y_smooth = spline(x_smooth)
        plt.plot(
            mdates.num2date(x_smooth), y_smooth, color=color, label=title, linewidth=2.5
        )

    plt.scatter(df_filtered["timestamp"], y_vals, color=color, marker=marker, zorder=3)

    plt.xlabel("Date")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle="-", linewidth=0.5, alpha=0.2)
    plt.tight_layout()

    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%-m-%-d-%Y"))
    ax.xaxis.set_major_locator(
        mdates.WeekdayLocator(byweekday=today_weekday, interval=1)
    )
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.xlim(first_date, x_axis_end)

    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, format="svg", bbox_inches="tight", dpi=100)
    print(f"Graph saved as {filepath}")


# uncomment to generate daily clone graph
# save_graph(
#     df["timestamp"],
#     df["clones"],
#     f"{REPO_NAME} Daily Clones Over Time",
#     "Number of Clones",
#     "daily_clones.svg",
#     marker="o",
#     color="cyan" if DARK_MODE else "blue",
# )

# uncomment to generate daily view graph
# save_graph(
#     df["timestamp"],
#     df["views"],
#     f"{REPO_NAME} Daily Views Over Time",
#     "Number of Views",
#     "daily_views.svg",
#     marker="s",
#     color="lime" if DARK_MODE else "green",
# )

df["total_clones"] = df["clones"].cumsum()
save_graph(
    df["timestamp"],
    df["total_clones"],
    f"Total {REPO_NAME} Clones",
    "Clones",
    "total_clones.svg",
    marker="o",
    color="#2ea44f",
)

# uncomment to generate total view graph
# df["total_views"] = df["views"].cumsum()
# save_graph(
#     df["timestamp"],
#     df["total_views"],
#     f"Total {REPO_NAME} Views Over Time",
#     "Total Views",
#     "total_views.svg",
#     marker="s",
#     color="lime" if DARK_MODE else "green",
# )

save_snapshot_graph(
    df,
    "total_downloads",
    f"Total {REPO_NAME} Downloads",
    "Downloads",
    "total_downloads.svg",
    marker="o",
    color="#1793d1",
)

# uncomment to generate star graph
# save_snapshot_graph(
#     df,
#     "total_stars",
#     f"Total {REPO_NAME} Stars Over Time",
#     "Total Stars",
#     "total_stars.svg",
#     marker="*",
#     color="gold",
# )


def glue_svgs_horizontally(svg_paths, output_path):
    svgs = [etree.parse(os.path.join(OUTPUT_DIR, path)).getroot() for path in svg_paths]
    widths = [float(svg.get("width", "800").replace("pt", "")) for svg in svgs]
    heights = [float(svg.get("height", "400").replace("pt", "")) for svg in svgs]

    total_width = sum(widths)
    max_height = max(heights)

    out_svg = etree.Element(
        "svg",
        xmlns="http://www.w3.org/2000/svg",
        width=str(total_width),
        height=str(max_height),
    )

    x_offset = 0
    for svg, w in zip(svgs, widths):
        g = etree.SubElement(out_svg, "g", transform=f"translate({x_offset}, 0)")
        for element in svg:
            g.append(element)
        x_offset += w

    etree.ElementTree(out_svg).write(
        os.path.join(OUTPUT_DIR, output_path),
        pretty_print=True,
        xml_declaration=True,
        encoding="utf-8",
    )


glue_svgs_horizontally(
    [
        "total_downloads.svg",
        "total_clones.svg",
    ],
    "combined_graphs.svg",
)

BADGE_DATA_DIR = os.path.join(BASE_DIR, "assets")

os.makedirs(BADGE_DATA_DIR, exist_ok=True)
badge_data = {
    "total_clones": int(df["clones"].sum()),
    "total_downloads": int(df.sort_values("timestamp")["total_downloads"].iloc[-1]),
}

badge_data_path = os.path.join(BADGE_DATA_DIR, "badge_data.json")
with open(badge_data_path, "w") as f:
    json.dump(badge_data, f)

print(f"Badge data written to {badge_data_path}")

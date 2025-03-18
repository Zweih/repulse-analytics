import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
from dotenv import load_dotenv

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


def save_graph(x, y, title, ylabel, filename, marker, color):
    plt.figure(figsize=(10, 5), dpi=300)
    plt.plot(x, y, marker=marker, linestyle="-", label=title, color=color)
    plt.xlabel("Date")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, linestyle="--" if DARK_MODE else "-")
    plt.tight_layout()

    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # plt.ylim(0, max(y) * 1.1 if len(y) > 0 else 1)

    if len(x) == 1:
        plt.xlim(x.iloc[0], x.iloc[0] + pd.Timedelta(days=10))
    else:
        plt.xlim(x.min(), x.max())

    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    print(f"Graph saved as {filepath}")


def save_snapshot_graph(df, column_name, title, ylabel, filename, marker, color):
    non_zero_data = df[df[column_name] > 0]

    if not non_zero_data.empty:
        df_filtered = non_zero_data
        first_date = df_filtered["timestamp"].iloc[0]
        last_date = df_filtered["timestamp"].iloc[-1]

        if (last_date - first_date).days < 3:
            x_axis_end = first_date + pd.Timedelta(days=3)
        else:
            x_axis_end = last_date
    else:
        print(f"Skipping {filename} - No non-zero data.")
        return

    plt.figure(figsize=(10, 5), dpi=300)
    plt.plot(
        df_filtered["timestamp"],
        df_filtered[column_name],
        marker=marker,
        linestyle="-",
        label=title,
        color=color,
    )
    plt.xlabel("Date")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, linestyle="--" if DARK_MODE else "-")
    plt.tight_layout()

    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # max_val = df_filtered[column_name].max() if not df_filtered.empty else 1
    # plt.ylim(0, max_val * 1.1)
    plt.xlim(first_date, x_axis_end)

    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    print(f"Graph saved as {filepath}")


save_graph(
    df["timestamp"],
    df["clones"],
    f"{REPO_NAME} Daily Clones Over Time",
    "Number of Clones",
    "daily_clones.png",
    marker="o",
    color="cyan" if DARK_MODE else "blue",
)

save_graph(
    df["timestamp"],
    df["views"],
    f"{REPO_NAME} Daily Views Over Time",
    "Number of Views",
    "daily_views.png",
    marker="s",
    color="lime" if DARK_MODE else "green",
)

df["total_clones"] = df["clones"].cumsum()
save_graph(
    df["timestamp"],
    df["total_clones"],
    f"Total {REPO_NAME} Clones Over Time",
    "Total Clones",
    "total_clones.png",
    marker="o",
    color="cyan" if DARK_MODE else "blue",
)

df["total_views"] = df["views"].cumsum()
save_graph(
    df["timestamp"],
    df["total_views"],
    f"Total {REPO_NAME} Views Over Time",
    "Total Views",
    "total_views.png",
    marker="s",
    color="lime" if DARK_MODE else "green",
)

save_snapshot_graph(
    df,
    "total_downloads",
    f"Total {REPO_NAME} Downloads Over Time",
    "Total Downloads",
    "total_downloads.png",
    marker="^",
    color="red",
)

save_snapshot_graph(
    df,
    "total_stars",
    f"Total {REPO_NAME} Stars Over Time",
    "Total Stars",
    "total_stars.png",
    marker="*",
    color="gold",
)

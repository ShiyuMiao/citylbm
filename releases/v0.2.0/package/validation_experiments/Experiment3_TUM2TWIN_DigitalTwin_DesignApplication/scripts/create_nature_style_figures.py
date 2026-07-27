from __future__ import annotations

import csv
import json
import math
import re
import shutil
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patches
from matplotlib.colors import LinearSegmentedColormap


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = Path(r"F:\citylbm_fluidx3d_workspace\tum2twin_case")
OUT_DIR = CASE_DIR / "output"
HEAVY_FIG_DIR = Path(r"D:\citylbm_tum2twin_heavy_store\paper_figures\nature_style_20260727")
PROJECT_FIG_DIR = ROOT / "figures" / "nature_style"
SOURCE_DATA_DIR = HEAVY_FIG_DIR / "source_data"
PROJECT_FIG_DIR.mkdir(parents=True, exist_ok=True)
HEAVY_FIG_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DATA_DIR.mkdir(parents=True, exist_ok=True)

LABEL_TEMPLATE = "core_prism_avg_wd{wd:03d}_dx2m_spin6k_s3"
WIND_DIRS = [0, 45, 90, 135, 180, 225, 270, 315]
SAMPLES = [(0, "000008000"), (1, "000010000"), (2, "000012000")]
DX = 2.0
U_REF = 5.0
PANEL_Z = 1

BLUE = "#3B6EA8"
TEAL = "#3C9D8F"
RED = "#B34C4C"
GOLD = "#C9A227"
DARK = "#2B2B2B"
GREY = "#777777"
LIGHT_GREY = "#E8E8E8"
VERY_LIGHT = "#F7F7F7"


mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 7,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.7,
        "axes.labelsize": 7,
        "axes.titlesize": 7.5,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.frameon": False,
        "legend.fontsize": 6.5,
        "figure.dpi": 180,
        "savefig.dpi": 600,
    }
)


def mm_to_in(mm: float) -> float:
    return mm / 25.4


def panel_label(ax, label: str, x: float = -0.14, y: float = 1.10) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        fontsize=8,
        fontweight="bold",
        va="bottom",
        ha="left",
    )


def save_figure(fig: plt.Figure, stem: str) -> list[Path]:
    paths: list[Path] = []
    base = HEAVY_FIG_DIR / stem
    for ext, kwargs in [
        ("svg", {}),
        ("pdf", {}),
        ("png", {"dpi": 600}),
        ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}}),
    ]:
        path = base.with_suffix(f".{ext}")
        fig.savefig(path, bbox_inches="tight", **kwargs)
        paths.append(path)

    for path in paths:
        if path.suffix.lower() in {".svg", ".pdf", ".png"}:
            copy_if_space(path, PROJECT_FIG_DIR)
    return paths


def copy_if_space(src: Path, dst_dir: Path) -> Path:
    dst = dst_dir / src.name
    try:
        free = shutil.disk_usage(dst_dir).free
        if free < src.stat().st_size + 5_000_000:
            print(f"SKIP_COPY_NO_SPACE {src} -> {dst}", file=sys.stderr)
            return src
        shutil.copyfile(src, dst)
        return dst
    except OSError as exc:
        print(f"SKIP_COPY_ERROR {src} -> {dst}: {exc}", file=sys.stderr)
        return src


def read_vtk(path: Path):
    raw = path.read_bytes()
    marker = b"LOOKUP_TABLE default\n"
    start = raw.index(marker) + len(marker)
    header = raw[:start].decode("ascii", errors="replace")
    dims = tuple(int(v) for v in re.search(r"DIMENSIONS\s+(\d+)\s+(\d+)\s+(\d+)", header).groups())
    origin = tuple(float(v) for v in re.search(r"ORIGIN\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)", header).groups())
    spacing = tuple(float(v) for v in re.search(r"SPACING\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)", header).groups())
    point_data = int(re.search(r"POINT_DATA\s+(\d+)", header).group(1))
    scalar_match = re.search(r"SCALARS\s+\S+\s+(\S+)(?:\s+(\d+))?", header)
    dtype_name = scalar_match.group(1)
    components = int(scalar_match.group(2) or "1")
    dtype = ">f4" if dtype_name == "float" else np.uint8
    arr = np.frombuffer(raw, dtype=dtype, count=point_data * components, offset=start).copy()
    if dtype_name == "float":
        arr = arr.astype(np.float32)
    if components > 1:
        arr = arr.reshape((dims[2], dims[1], dims[0], components))
    else:
        arr = arr.reshape((dims[2], dims[1], dims[0]))
    return {"dims": dims, "origin": origin, "spacing": spacing}, arr


def extent_xy(meta):
    nx, ny, _ = meta["dims"]
    ox, oy, _ = meta["origin"]
    sx, sy, _ = meta["spacing"]
    return [ox, ox + sx * (nx - 1), oy, oy + sy * (ny - 1)]


def load_wind_weights():
    weights = {}
    path = ROOT / "manifests" / "open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv"
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            weights[int(row["simulated_velocity_direction_deg"])] = float(row["weight"])
    total = sum(weights.values())
    return {wd: weights.get(wd, 0.0) / total for wd in WIND_DIRS}


def load_core_arrays():
    weights = load_wind_weights()
    stack = []
    meta0 = None
    solid = None
    for wd in WIND_DIRS:
        label = LABEL_TEMPLATE.format(wd=wd)
        flags_path = OUT_DIR / f"matrix_{label}_flags_sample_2flags-000012000.vtk"
        meta, flags = read_vtk(flags_path)
        if meta0 is None:
            meta0 = meta
        solid = (flags[PANEL_Z] & 1) > 0

        speed_sum = None
        for sample_idx, step in SAMPLES:
            u_path = OUT_DIR / f"matrix_{label}_u_sample_{sample_idx}u-{step}.vtk"
            _, u = read_vtk(u_path)
            speed = np.linalg.norm(u, axis=3) / U_REF
            plane = speed[PANEL_Z].astype(np.float32)
            speed_sum = plane if speed_sum is None else speed_sum + plane
        time_mean = speed_sum / float(len(SAMPLES))
        stack.append(np.where(~solid, time_mean, np.nan).astype(np.float32))

    arr = np.stack(stack, axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean_map = np.nanmean(arr, axis=0)
        std_map = np.nanstd(arr, axis=0)
        stag_freq = np.nanmean(arr < 0.2, axis=0)
        weighted_stag = np.zeros_like(mean_map, dtype=np.float32)
        weighted_vr = np.zeros_like(mean_map, dtype=np.float32)
        for i, wd in enumerate(WIND_DIRS):
            weighted_stag += np.nan_to_num((arr[i] < 0.2).astype(np.float32), nan=0.0) * weights[wd]
            weighted_vr += np.nan_to_num(arr[i], nan=0.0) * weights[wd]
    return {
        "meta": meta0,
        "solid": solid,
        "mean_map": mean_map,
        "std_map": std_map,
        "stag_freq": stag_freq,
        "weighted_stag": weighted_stag,
        "weighted_vr": weighted_vr,
        "weights": weights,
    }


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_source_data(name: str, rows: list[dict[str, object]]) -> None:
    path = SOURCE_DATA_DIR / name
    if not rows:
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    copy_if_space(path, PROJECT_FIG_DIR)


def add_scale_bar(ax, length_m: float = 100.0) -> None:
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    margin_x = 0.08 * (x1 - x0)
    margin_y = 0.08 * (y1 - y0)
    sx0 = x0 + margin_x
    sy0 = y0 + margin_y
    ax.plot([sx0, sx0 + length_m], [sy0, sy0], color=DARK, lw=1.2, solid_capstyle="butt")
    ax.text(sx0 + length_m / 2, sy0 + 0.025 * (y1 - y0), f"{int(length_m)} m", ha="center", va="bottom", fontsize=6)


def make_figure1_workflow():
    core_qa = json.loads((ROOT / "manifests" / "geometry_qa_core_photogrammetry_extent_prism.json").read_text(encoding="utf-8"))
    scope_rows = read_csv_rows(ROOT / "manifests" / "tum2twin_rhino_layered_geometry_scope_audit.csv")
    visual = next(r for r in scope_rows if r["source"] == "existing_3dm_UAS_Mesh")

    fig = plt.figure(figsize=(mm_to_in(183), mm_to_in(112)))
    gs = fig.add_gridspec(2, 5, height_ratios=[1.0, 0.88], width_ratios=[1.0, 1.0, 1.05, 1.15, 1.15], hspace=0.55, wspace=0.55)
    ax_flow = fig.add_subplot(gs[0, :])
    ax_flow.axis("off")
    panel_label(ax_flow, "a", x=-0.02, y=1.0)

    stages = [
        ("Visual twin", "photogrammetry/Rhino\nappearance reference", "#D9E6F2"),
        ("Semantic city model", "LoD3 OBJ surfaces\nbuilding semantics", "#DDEBDD"),
        ("CFD-ready geometry", "closed prism STL\nz0, solid boundary", "#F1E7C7"),
        ("FluidX3D case", "8 directions, dx=2 m\n3 samples after spin-up", "#E7D8E9"),
        ("Wind metrics", "VR, stagnation,\nrobustness, profiles", "#E4E4E4"),
    ]
    xs = np.linspace(0.04, 0.78, len(stages))
    box_w = 0.15
    box_h = 0.42
    for i, ((title, subtitle, color), x) in enumerate(zip(stages, xs)):
        rect = patches.FancyBboxPatch((x, 0.34), box_w, box_h, boxstyle="round,pad=0.008,rounding_size=0.012", fc=color, ec=DARK, lw=0.6)
        ax_flow.add_patch(rect)
        ax_flow.text(x + box_w / 2, 0.62, title, ha="center", va="center", fontsize=6.8, fontweight="bold")
        ax_flow.text(x + box_w / 2, 0.48, subtitle, ha="center", va="center", fontsize=5.9, color=DARK, linespacing=1.2)
        if i < len(stages) - 1:
            ax_flow.annotate("", xy=(xs[i + 1] - 0.015, 0.55), xytext=(x + box_w + 0.012, 0.55), arrowprops=dict(arrowstyle="-|>", lw=0.7, color=DARK))
    ax_flow.text(0.06, 0.18, "central claim: visual digital-twin assets define the scene, but CFD needs a semantic closed collision boundary", fontsize=7.2, color=DARK)
    ax_flow.set_xlim(0, 1)
    ax_flow.set_ylim(0, 1)

    ax_b = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[1, 1])
    ax_d = fig.add_subplot(gs[1, 2])
    ax_e = fig.add_subplot(gs[1, 3:])
    for label, ax in zip(["b", "c", "d", "e"], [ax_b, ax_c, ax_d, ax_e]):
        panel_label(ax, label)

    ax_b.bar(["visual\n3dm"], [float(visual["size_x"])], color=BLUE, width=0.55)
    ax_b.bar(["core\nSTL"], [core_qa["bbox"]["max"][0] - core_qa["bbox"]["min"][0]], color=TEAL, width=0.55)
    ax_b.set_ylabel("x extent (m)")
    ax_b.set_title("matched study extent")
    ax_b.tick_params(axis="x", rotation=0)
    ax_b.spines["left"].set_bounds(0, 450)
    ax_b.set_ylim(0, 460)

    ax_c.bar(["visual\nmesh", "core\nSTL"], [999_999, core_qa["triangles"]], color=[BLUE, TEAL], width=0.55)
    ax_c.set_yscale("log")
    ax_c.set_ylabel("triangles")
    ax_c.set_title("representation shift")

    ax_d.bar(["visual\nSTL", "core\nSTL"], [2245, 0], color=[RED, TEAL], width=0.55)
    ax_d.set_ylabel("boundary edges")
    ax_d.set_title("collision readiness")
    ax_d.set_ylim(0, 2450)

    y = np.arange(4)
    labels = ["visual reference", "semantic source", "closed collision", "simulation-ready"]
    visual_scores = [1.0, 0.15, 0.0, 0.25]
    prism_scores = [0.45, 1.0, 1.0, 1.0]
    ax_e.barh(y + 0.16, visual_scores, height=0.28, color=BLUE, alpha=0.85, label="photogrammetry/Rhino")
    ax_e.barh(y - 0.16, prism_scores, height=0.28, color=TEAL, alpha=0.9, label="LoD3-derived prism")
    ax_e.set_yticks(y)
    ax_e.set_yticklabels(labels)
    ax_e.set_xlim(0, 1.05)
    ax_e.set_xlabel("readiness score (qualitative)", labelpad=6)
    ax_e.set_title("geometry-to-CFD readiness logic")
    ax_e.legend(loc="lower center", bbox_to_anchor=(0.5, -0.50), ncol=2)
    ax_e.grid(axis="x", color=LIGHT_GREY, lw=0.5)

    source_rows = [
        {"panel": "b", "metric": "visual_3dm_x_extent_m", "value": visual["size_x"], "source": "tum2twin_rhino_layered_geometry_scope_audit.csv"},
        {"panel": "b", "metric": "core_stl_x_extent_m", "value": core_qa["bbox"]["max"][0] - core_qa["bbox"]["min"][0], "source": "geometry_qa_core_photogrammetry_extent_prism.json"},
        {"panel": "c", "metric": "visual_mesh_triangles", "value": 999999, "source": "user_converted_rhino_layered_package_audit.md"},
        {"panel": "c", "metric": "core_stl_triangles", "value": core_qa["triangles"], "source": "geometry_qa_core_photogrammetry_extent_prism.json"},
        {"panel": "d", "metric": "visual_stl_boundary_edges", "value": 2245, "source": "user_converted_rhino_layered_package_audit.md"},
        {"panel": "d", "metric": "core_stl_boundary_edges", "value": 0, "source": "semantic closed-prism construction"},
    ]
    write_source_data("source_data_nature_fig1_geometry_workflow.csv", source_rows)

    paths = save_figure(fig, "nature_fig1_digital_twin_to_cfd_workflow")
    plt.close(fig)
    return paths


def make_figure2_results():
    arrays = load_core_arrays()
    extent = extent_xy(arrays["meta"])
    solid = arrays["solid"]
    weighted_stag = arrays["weighted_stag"]
    std_map = arrays["std_map"]

    directional_rows_all = read_csv_rows(ROOT / "figures" / "fluidx3d_core_prism_deepened_directional_summary.csv")
    directional_rows = [r for r in directional_rows_all if math.isclose(float(r["height_m"]), 2.0)]
    robustness_rows = read_csv_rows(ROOT / "figures" / "fluidx3d_core_prism_deepened_spatial_robustness_metrics.csv")
    equal_rows = [r for r in read_csv_rows(ROOT / "figures" / "fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv") if r["averaging"] == "time_mean_3_samples_then_direction_mean"]
    weighted_rows = read_csv_rows(ROOT / "figures" / "fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv")
    equal_rows.sort(key=lambda r: float(r["z_height_m_approx"]))
    weighted_rows.sort(key=lambda r: float(r["z_height_m_approx"]))

    prob_cmap = LinearSegmentedColormap.from_list("soft_prob", ["#F7FBFF", "#C7DCEF", "#6FA7C6", "#24577A"])
    std_cmap = LinearSegmentedColormap.from_list("soft_std", ["#FAFAFA", "#D9D4E8", "#8E79B8", "#4A2C6D"])

    fig = plt.figure(figsize=(mm_to_in(183), mm_to_in(185)))
    gs = fig.add_gridspec(3, 4, width_ratios=[1.18, 1.18, 1.0, 1.0], height_ratios=[1.08, 1.04, 0.82], hspace=0.72, wspace=0.65)
    ax_a = fig.add_subplot(gs[0:2, 0:2])
    ax_b = fig.add_subplot(gs[0, 2])
    ax_c = fig.add_subplot(gs[0, 3])
    gs_d = gs[1, 2:].subgridspec(1, 2, wspace=0.55)
    ax_d1 = fig.add_subplot(gs_d[0, 0])
    ax_d2 = fig.add_subplot(gs_d[0, 1])
    ax_e = fig.add_subplot(gs[2, :])
    for label, ax in zip(["a", "b", "c", "d", "e"], [ax_a, ax_b, ax_c, ax_d1, ax_e]):
        panel_label(ax, label)

    masked_prob = np.ma.masked_where(solid | np.isnan(weighted_stag), weighted_stag)
    im = ax_a.imshow(masked_prob, origin="lower", extent=extent, cmap=prob_cmap, vmin=0, vmax=1, interpolation="nearest")
    ax_a.contour(solid.astype(float), levels=[0.5], origin="lower", extent=extent, colors="#FFFFFF", linewidths=0.24)
    ax_a.set_title("Open-Meteo weighted stagnation probability, z~2 m")
    ax_a.set_xlabel("x (m)")
    ax_a.set_ylabel("y (m)")
    ax_a.set_aspect("equal")
    add_scale_bar(ax_a, 100)
    cbar = fig.colorbar(im, ax=ax_a, fraction=0.036, pad=0.018)
    cbar.set_label("P(VR < 0.2)")

    masked_std = np.ma.masked_where(solid | np.isnan(std_map), std_map)
    im2 = ax_b.imshow(masked_std, origin="lower", extent=extent, cmap=std_cmap, vmin=0, vmax=0.12, interpolation="nearest")
    ax_b.contour(solid.astype(float), levels=[0.5], origin="lower", extent=extent, colors="#FFFFFF", linewidths=0.18)
    ax_b.set_title("directional variability")
    ax_b.set_xticks([])
    ax_b.set_yticks([])
    ax_b.set_aspect("equal")
    cbar2 = fig.colorbar(im2, ax=ax_b, fraction=0.046, pad=0.02)
    cbar2.set_label("")

    wds = [int(float(r["wind_deg"])) for r in directional_rows]
    means = [float(r["vr_mean"]) for r in directional_rows]
    stags = [float(r["stagnation_ratio_vr_lt_0p2"]) for r in directional_rows]
    weights = [float(r["wind_climate_weight"]) for r in directional_rows]
    ax_c.bar(wds, means, width=28, color=BLUE, alpha=0.9, label="mean VR")
    ax_c.set_ylim(0, 0.09)
    ax_c.set_ylabel("")
    ax_c.set_xlabel("")
    ax_c.set_title("directional response")
    ax_c.set_xticks([0, 90, 180, 270])
    ax_c.grid(axis="y", color=LIGHT_GREY, lw=0.5)
    ax_c2 = ax_c.twinx()
    ax_c2.plot(wds, stags, color=RED, lw=1.1, marker="o", ms=2.5, label="VR<0.2")
    ax_c2.set_ylim(0.9, 0.95)
    ax_c2.set_ylabel("VR<0.2 ratio", color=RED)
    ax_c2.spines["top"].set_visible(False)
    ax_c2.tick_params(axis="y", colors=RED)

    heights = [float(r["z_height_m_approx"]) for r in equal_rows]
    eq_mean = [float(r["vr_mean"]) for r in equal_rows]
    wt_mean = [float(r["vr_mean"]) for r in weighted_rows]
    eq_stag = [float(r["stagnation_ratio_vr_lt_0p2"]) for r in equal_rows]
    wt_stag = [float(r["stagnation_ratio_vr_lt_0p2"]) for r in weighted_rows]
    ax_d1.plot(eq_mean, heights, marker="o", lw=1.2, color=BLUE, label="equal")
    ax_d1.plot(wt_mean, heights, marker="o", lw=1.2, color=TEAL, label="weighted")
    ax_d1.set_xlabel("VR mean")
    ax_d1.set_ylabel("height (m)")
    ax_d1.set_title("vertical recovery")
    ax_d1.grid(True, color=LIGHT_GREY, lw=0.5)
    ax_d1.set_ylim(0, 42)
    ax_d1.legend(loc="lower right")

    ax_d2.plot(eq_stag, heights, marker="s", lw=1.0, color=RED, label="equal")
    ax_d2.plot(wt_stag, heights, marker="s", lw=1.0, color=GOLD, label="weighted")
    ax_d2.set_xlabel("VR<0.2 ratio")
    ax_d2.set_title("stagnation decay")
    ax_d2.grid(True, color=LIGHT_GREY, lw=0.5)
    ax_d2.set_ylim(0, 42)
    ax_d2.set_xlim(1.0, 0.0)
    ax_d2.set_yticklabels([])

    metric_map = {r["metric"]: float(r["value"]) for r in robustness_rows}
    bars = [
        ("stagnant in >=6/8 directions", metric_map["robust_stagnation_ratio_freq_ge_0p75"], RED),
        ("stagnant in all directions", metric_map["all_direction_stagnation_ratio"], RED),
        ("weighted stagnation prob. >=0.75", metric_map["climate_weighted_stag_prob_ge_0p75_area_ratio"], GOLD),
        ("accelerated in >=2/8 directions", metric_map["directionally_accelerated_ratio_freq_ge_0p25"], BLUE),
    ]
    y = np.arange(len(bars))[::-1]
    vals = [b[1] for b in bars]
    ax_e.barh(y, vals, color=[b[2] for b in bars], height=0.46)
    ax_e.set_yticks(y)
    ax_e.set_yticklabels([b[0] for b in bars])
    ax_e.set_xlim(0, 1)
    ax_e.set_xlabel("area ratio of open z~2 m cells")
    ax_e.set_title("robustness metrics")
    ax_e.grid(axis="x", color=LIGHT_GREY, lw=0.5)
    for yi, val in zip(y, vals):
        ax_e.text(min(val + 0.015, 0.96), yi, f"{val:.3f}", va="center", ha="left", fontsize=6.5)

    write_source_data(
        "source_data_nature_fig2_core_wind_robustness.csv",
        [
            *[{"panel": "c", **r} for r in directional_rows],
            *[{"panel": "d_equal", **r} for r in equal_rows],
            *[{"panel": "d_weighted", **r} for r in weighted_rows],
            *[{"panel": "e", **r} for r in robustness_rows],
        ],
    )
    paths = save_figure(fig, "nature_fig2_core_wind_robustness")
    plt.close(fig)
    return paths


def main():
    paths = []
    paths.extend(make_figure1_workflow())
    paths.extend(make_figure2_results())
    print("NATURE_STYLE_OUTPUT_DIR", HEAVY_FIG_DIR)
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()

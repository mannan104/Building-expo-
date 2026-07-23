# BuildWise Pro 3D
# A civil engineering planning dashboard built with Streamlit.
#
# Given soil type, plot dimensions, floor count and material choices, the
# app auto-generates:
#   - A soil and foundation cross-section diagram
#   - A 3D building shape model (foundation, floors, roof) with adjustable
#     view angle
#   - Recommended concrete grade, nominal mix ratio and water-cement ratio
#   - Material quantity estimates (cement, sand, aggregate, water)
#   - A downloadable planning summary report
#
# ENGINEERING DISCLAIMER
# All figures are standard textbook / IS 456 nominal-mix approximations and
# simplified planning-stage rules of thumb, intended for early concept
# visualization and learning only. They are NOT a substitute for a proper
# geotechnical soil investigation and a structural design carried out and
# stamped by a licensed structural engineer.

import streamlit as st

try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
except ModuleNotFoundError as missing_pkg_error:
    st.error(
        f"Missing package: {missing_pkg_error}. \n\n"
        "This means requirements.txt was not installed for this deployment. "
        "Check that requirements.txt sits in the SAME folder as app.py at your "
        "repo root, then open 'Manage app' (bottom right) and click 'Reboot app'."
    )
    st.stop()

# -----------------------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------------------
st.set_page_config(
    page_title="BuildWise Pro 3D - Civil Engineering Studio",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------
# CUSTOM CSS - warm copper / teal / charcoal theme with animation
# -----------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background:
        radial-gradient(circle at 15% 10%, rgba(217,123,63,0.10), transparent 40%),
        radial-gradient(circle at 85% 90%, rgba(47,191,160,0.10), transparent 45%),
        linear-gradient(180deg, #171410 0%, #14120f 100%);
    background-color: #14120f;
}

.hero {
    padding: 2.2rem 2rem;
    border-radius: 18px;
    background: linear-gradient(120deg, #2a2018 0%, #3a2916 45%, #21312c 100%);
    border: 1px solid rgba(217,123,63,0.4);
    box-shadow: 0 0 40px rgba(217,123,63,0.14), inset 0 0 60px rgba(47,191,160,0.06);
    margin-bottom: 1.6rem;
    position: relative;
    overflow: hidden;
    animation: fadeSlideIn 0.8s ease-out;
}
.hero::after {
    content: "";
    position: absolute; top: -50%; left: -20%;
    width: 60%; height: 200%;
    background: linear-gradient(120deg, transparent, rgba(255,255,255,0.05), transparent);
    animation: shimmer 5s infinite;
}
@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(250%); }
}
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(-14px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 4px 14px rgba(217,123,63,0.35); }
    50% { box-shadow: 0 4px 22px rgba(242,166,90,0.6); }
}
.hero h1 {
    font-family: 'Orbitron', sans-serif;
    color: #f3ede4;
    font-size: 2.1rem;
    letter-spacing: 1px;
    margin-bottom: 0.2rem;
    text-shadow: 0 0 18px rgba(242,166,90,0.45);
}
.hero p { color: #c9bfae; font-size: 1rem; margin: 0; }

.eng-card {
    background: rgba(35, 30, 24, 0.75);
    border: 1px solid rgba(217,123,63,0.3);
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    margin-bottom: 1rem;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    animation: fadeSlideIn 0.6s ease-out;
}
.eng-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 28px rgba(217,123,63,0.2);
    border-color: rgba(242,166,90,0.6);
}
.eng-card h3 {
    color: #f2a65a;
    font-family: 'Orbitron', sans-serif;
    font-size: 1.05rem;
    margin-bottom: 0.6rem;
    border-bottom: 1px solid rgba(242,166,90,0.25);
    padding-bottom: 0.4rem;
}
.eng-card p, .eng-card li { color: #e6ded2; font-size: 0.94rem; line-height: 1.55; }

.badge {
    display: inline-block;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-right: 0.4rem;
    background: rgba(242,166,90,0.15);
    color: #f2a65a;
    border: 1px solid rgba(242,166,90,0.4);
}
.badge.teal { background: rgba(47,191,160,0.15); color: #5eead4; border-color: rgba(47,191,160,0.45); }
.badge.warn { background: rgba(239,113,80,0.15); color: #fca87c; border-color: rgba(239,113,80,0.45); }

.tile {
    background: linear-gradient(160deg, rgba(58,41,22,0.55), rgba(33,49,44,0.5));
    border: 1px solid rgba(217,123,63,0.3);
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}
.tile .val { font-family: 'Orbitron', sans-serif; font-size: 1.45rem; color: #5eead4; }
.tile .lbl { color: #c9bfae; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1c1712 0%, #201a14 100%);
    border-right: 1px solid rgba(217,123,63,0.3);
}

div.stButton > button {
    background: linear-gradient(120deg, #d97b3f, #b85c2a);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.4rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    animation: pulseGlow 2.4s infinite;
    transition: transform 0.2s ease;
}
div.stButton > button:hover { transform: translateY(-2px) scale(1.02); }

div.stDownloadButton > button {
    background: linear-gradient(120deg, #2fbfa0, #1f8f78);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
}

footer, #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------
# REFERENCE DATA
# -----------------------------------------------------------------------
SOIL_DATA = {
    "Rocky / Hard Rock":            {"sbc": (400, 450), "depth_m": (0.9, 1.2), "color": "#8a8a86",
        "note": "Excellent bearing capacity, very low settlement risk.",
        "foundation": "Isolated (spread) footing - most economical choice.",
        "shape_note": "Almost any plan shape is viable; shape can be driven by architecture."},
    "Dense Gravel / Dense Sand":     {"sbc": (250, 450), "depth_m": (1.0, 1.5), "color": "#c9a876",
        "note": "Good load-bearing soil with minor settlement.",
        "foundation": "Isolated footing for low-rise; combined footing for mid-rise.",
        "shape_note": "Compact rectangular footprints perform best; use joints for irregular wings."},
    "Loose Sand":                   {"sbc": (100, 150), "depth_m": (1.2, 1.8), "color": "#dcc498",
        "note": "Moderate capacity; prone to differential settlement if saturated.",
        "foundation": "Combined footing or raft beyond 2 floors; consider compaction.",
        "shape_note": "Prefer a compact symmetric shape to minimize differential settlement."},
    "Stiff Clay":                   {"sbc": (100, 200), "depth_m": (1.2, 1.8), "color": "#9c6b45",
        "note": "Reasonable capacity but sensitive to moisture changes.",
        "foundation": "Isolated/combined footing for low-rise; raft for taller structures.",
        "shape_note": "Symmetric shape recommended; avoid deep re-entrant corners."},
    "Soft Clay":                    {"sbc": (50, 100), "depth_m": (1.5, 2.0), "color": "#7a5233",
        "note": "Low capacity, high settlement and consolidation risk.",
        "foundation": "Raft foundation, or piles for multi-storey loads.",
        "shape_note": "Compact, near-square footprint reduces tilting risk."},
    "Black Cotton / Expansive Clay": {"sbc": (50, 100), "depth_m": (1.5, 2.5), "color": "#3f3b38",
        "note": "Highly expansive - significant swell/shrink movement with moisture.",
        "foundation": "Under-reamed piles or raft with a moisture barrier; avoid ordinary footings.",
        "shape_note": "Simple, box-like shapes with stiff plinth beams resist differential heave."},
    "Peaty / Made-up / Filled Soil": {"sbc": (20, 50), "depth_m": (2.0, 3.0), "color": "#4a5a3a",
        "note": "Very poor, organic or loosely filled soil - high compressibility.",
        "foundation": "Pile foundation to firm strata is essentially mandatory.",
        "shape_note": "Lightweight, compact plan strongly advised; avoid heavy cantilevers."},
    "Silty Soil":                   {"sbc": (80, 150), "depth_m": (1.2, 1.8), "color": "#b3a077",
        "note": "Fine-grained, moderate capacity, can be moisture sensitive.",
        "foundation": "Combined footing or raft depending on load; ensure good drainage.",
        "shape_note": "Compact symmetric footprint; keep the building centre of mass near centroid."},
}

MIX_DATA = {
    "M10": {"ratio": (1, 3, 6), "wc": 0.55, "use": "Plain concrete, leveling course, low-load footings"},
    "M15": {"ratio": (1, 2, 4), "wc": 0.50, "use": "Small residential footings, low-rise (1-2 floors)"},
    "M20": {"ratio": (1, 1.5, 3), "wc": 0.45, "use": "RCC columns/slabs for low to mid-rise (2-4 floors)"},
    "M25": {"ratio": (1, 1, 2), "wc": 0.42, "use": "Mid-rise structural members (4-6 floors)"},
    "M30": {"ratio": None, "wc": 0.40, "use": "High-rise / heavy load - design mix REQUIRED"},
}

WALL_MATERIALS = {
    "Brick Masonry": "#b5533c",
    "Concrete Block": "#8f9295",
    "AAC Block": "#d8d3c4",
}

DRY_VOLUME_FACTOR = 1.54
CEMENT_DENSITY_KG_M3 = 1440
LOAD_PER_FLOOR_KPA = 12.0          # rough combined dead+live load assumption
CONCRETE_FACTOR_M3_PER_M2 = 0.17   # rough structural concrete per m2 floor area

FLOOR_COLOR_SCALE = ["#d97b3f", "#e0973c", "#e8b25a", "#2fbfa0", "#3fd6b8", "#5eead4"]

PANEL_BG = "#171410"
TEXT_COLOR = "#e6ded2"


def recommend_grade(floors: int) -> str:
    if floors <= 2:
        return "M15"
    elif floors <= 4:
        return "M20"
    elif floors <= 6:
        return "M25"
    return "M30"


def compute_materials(volume_m3, ratio, wc):
    dry_volume = volume_m3 * DRY_VOLUME_FACTOR
    total_parts = sum(ratio)
    cement_vol = dry_volume * (ratio[0] / total_parts)
    sand_vol = dry_volume * (ratio[1] / total_parts)
    agg_vol = dry_volume * (ratio[2] / total_parts)
    cement_weight_kg = cement_vol * CEMENT_DENSITY_KG_M3
    cement_bags = cement_weight_kg / 50.0
    water_liters = cement_weight_kg * wc
    return {
        "cement_vol_m3": cement_vol, "sand_vol_m3": sand_vol, "agg_vol_m3": agg_vol,
        "cement_bags": cement_bags, "cement_weight_kg": cement_weight_kg, "water_liters": water_liters,
    }


def box_faces(x0, x1, y0, y1, z0, z1):
    v = {
        "000": (x0, y0, z0), "100": (x1, y0, z0), "110": (x1, y1, z0), "010": (x0, y1, z0),
        "001": (x0, y0, z1), "101": (x1, y0, z1), "111": (x1, y1, z1), "011": (x0, y1, z1),
    }
    return [
        [v["000"], v["100"], v["110"], v["010"]],  # bottom
        [v["001"], v["101"], v["111"], v["011"]],  # top
        [v["000"], v["100"], v["101"], v["001"]],  # front (y0)
        [v["010"], v["110"], v["111"], v["011"]],  # back (y1)
        [v["000"], v["010"], v["011"], v["001"]],  # left (x0)
        [v["100"], v["110"], v["111"], v["101"]],  # right (x1)
    ]


def add_box(ax, x0, x1, y0, y1, z0, z1, color, alpha=1.0):
    poly = Poly3DCollection(box_faces(x0, x1, y0, y1, z0, z1),
                             facecolor=color, edgecolor="#241f19", linewidths=0.4, alpha=alpha)
    ax.add_collection3d(poly)


def add_gable_roof(ax, L, W, z_base, apex_height, color):
    p0 = (0, 0, z_base); p1 = (L, 0, z_base); p2 = (L, W, z_base); p3 = (0, W, z_base)
    r0 = (0, W / 2, z_base + apex_height); r1 = (L, W / 2, z_base + apex_height)
    faces = [
        [p0, p1, r1, r0],  # front slope
        [p3, p2, r1, r0],  # back slope
        [p0, p3, r0],      # left gable end (triangle)
        [p1, p2, r1],      # right gable end (triangle)
    ]
    poly = Poly3DCollection(faces, facecolor=color, edgecolor="#241f19", linewidths=0.4, alpha=1.0)
    ax.add_collection3d(poly)


def style_fig(fig):
    fig.patch.set_facecolor(PANEL_BG)
    fig.patch.set_alpha(0.0)


def style_2d_axis(ax):
    ax.set_facecolor(PANEL_BG)
    ax.set_facecolor((0, 0, 0, 0))
    for spine in ax.spines.values():
        spine.set_color("#4a4038")
    ax.tick_params(colors=TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)


def style_3d_axis(ax):
    ax.set_facecolor((0, 0, 0, 0))
    for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
        pane.set_facecolor((1, 1, 1, 0.03))
        pane.set_edgecolor((1, 1, 1, 0.08))
    ax.tick_params(colors=TEXT_COLOR)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.zaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)


# -----------------------------------------------------------------------
# HERO
# -----------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>BuildWise Pro 3D</h1>
    <p>Enter your soil, dimensions and materials - get an instant soil/foundation diagram, 3D building model, concrete mix design and material quantities.</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------
# SIDEBAR INPUTS
# -----------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Site & Soil")
    soil_type = st.selectbox("Soil Type", list(SOIL_DATA.keys()), index=0)

    st.markdown("### Plot Dimensions")
    plot_length = st.number_input("Plot Length (m)", min_value=3.0, value=12.0, step=0.5)
    plot_width = st.number_input("Plot Width (m)", min_value=3.0, value=8.0, step=0.5)

    st.markdown("### Building Details")
    floors = st.number_input("Number of Floors (incl. ground)", min_value=1, max_value=15, value=2, step=1)
    floor_height = st.number_input("Floor-to-Floor Height (m)", min_value=2.4, max_value=5.0, value=3.0, step=0.1)
    roof_type = st.selectbox("Roof Type", ["Flat", "Gable"])
    usage = st.selectbox("Building Usage", ["Residential", "Commercial", "Industrial"])

    st.markdown("### Materials")
    wall_material = st.selectbox("Wall Material", list(WALL_MATERIALS.keys()))
    grade_mode = st.radio("Concrete Grade", ["Auto (recommended)", "Manual"], horizontal=True)
    if grade_mode == "Manual":
        grade = st.selectbox("Select Grade", list(MIX_DATA.keys()))
    else:
        grade = None  # resolved after floors known

    st.markdown("### 3D View Angle")
    view_azim = st.slider("Rotate (azimuth)", 0, 360, 235)
    view_elev = st.slider("Tilt (elevation)", 5, 80, 20)

    st.markdown("---")
    run = st.button("Generate Building Design", use_container_width=True)

if not run:
    st.info("Fill in the site, dimensions and material details in the sidebar, then click **Generate Building Design**.")
    st.stop()

# -----------------------------------------------------------------------
# CORE CALCULATIONS
# -----------------------------------------------------------------------
soil = SOIL_DATA[soil_type]
sbc_low, sbc_high = soil["sbc"]
sbc_avg = (sbc_low + sbc_high) / 2
depth_low, depth_high = soil["depth_m"]
depth_mid = (depth_low + depth_high) / 2

if grade is None:
    grade = recommend_grade(floors)
mix = MIX_DATA[grade]

plot_area = plot_length * plot_width
building_load_kn = plot_area * floors * LOAD_PER_FLOOR_KPA
required_footing_area = building_load_kn / sbc_avg
area_ratio = required_footing_area / plot_area

if area_ratio <= 0.45:
    foundation_type = "Isolated (spread) footings - soil comfortably supports column loads."
elif area_ratio <= 0.9:
    foundation_type = "Combined / strip footings recommended - load approaches plot capacity."
else:
    foundation_type = "Raft or pile foundation required - load exceeds safe isolated footing capacity."

auto_concrete_volume = round(plot_area * floors * CONCRETE_FACTOR_M3_PER_M2, 1)

st.success(f"Design generated for a {floors}-floor {usage.lower()} building ({plot_length}m x {plot_width}m) on {soil_type}.")

# -----------------------------------------------------------------------
# METRIC TILES
# -----------------------------------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)
tiles = [
    (f"{sbc_low}-{sbc_high} kPa", "Safe Bearing Capacity"),
    (f"{depth_low}-{depth_high} m", "Recommended Foundation Depth"),
    (f"{area_ratio*100:.0f}%", "Footing Area / Plot Area"),
    (grade, "Concrete Grade"),
    (f"{auto_concrete_volume} m3", "Est. Structural Concrete"),
]
for col, (val, lbl) in zip([c1, c2, c3, c4, c5], tiles):
    col.markdown(f'<div class="tile"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Soil & Foundation", "3D Building Model", "Concrete Mix Design", "Material Estimator", "Full Report"
])

# -----------------------------------------------------------------------
# TAB 1 - SOIL & FOUNDATION CROSS-SECTION
# -----------------------------------------------------------------------
with tab1:
    colA, colB = st.columns([1, 1.2])
    with colA:
        st.markdown(f"""
        <div class="eng-card">
            <h3>Soil Assessment - {soil_type}</h3>
            <p><span class="badge">SBC {sbc_low}-{sbc_high} kPa</span>
               <span class="badge teal">Depth {depth_low}-{depth_high} m</span></p>
            <p>{soil['note']}</p>
            <p><b>Recommended Foundation:</b> {foundation_type}</p>
            <p><b>Base guidance for this soil:</b> {soil['foundation']}</p>
        </div>
        <div class="eng-card">
            <h3>Load vs Capacity Check</h3>
            <p>Estimated building load: <b>{building_load_kn:,.0f} kN</b> (planning-stage assumption of {LOAD_PER_FLOOR_KPA} kPa per floor)</p>
            <p>Required footing area: <b>{required_footing_area:.1f} m2</b> vs plot area <b>{plot_area:.1f} m2</b></p>
        </div>
        """, unsafe_allow_html=True)

    with colB:
        fig1, ax1 = plt.subplots(figsize=(6.2, 4.6))
        style_fig(fig1)
        style_2d_axis(ax1)

        # soil block
        ax1.add_patch(Rectangle((-1, -depth_mid - 1), plot_length + 2, depth_mid + 1,
                                 facecolor=soil["color"], alpha=0.55, edgecolor="none"))
        # ground level line
        ax1.axhline(0, color="#2fbfa0", linewidth=3, zorder=5)

        # footing block
        footing_width = min(plot_length, max(2.0, (required_footing_area / plot_width)))
        fx0 = (plot_length - footing_width) / 2
        ax1.add_patch(Rectangle((fx0, -depth_mid), footing_width, 0.35,
                                 facecolor="#8f9295", edgecolor=TEXT_COLOR, linewidth=1, zorder=6))
        # plinth / column stub above footing to ground
        ax1.add_patch(Rectangle((fx0 + footing_width * 0.35, -depth_mid + 0.35),
                                 footing_width * 0.3, depth_mid - 0.35,
                                 facecolor="#d97b3f", edgecolor="none", zorder=6))
        # building base above ground
        ax1.add_patch(Rectangle((0, 0), plot_length, floor_height * 0.6,
                                 facecolor=WALL_MATERIALS[wall_material], alpha=0.5,
                                 edgecolor=TEXT_COLOR, linewidth=1, zorder=4))

        ax1.set_xlim(-1, plot_length + 1)
        ax1.set_ylim(-depth_mid - 1, floor_height * 0.6 + 0.5)
        ax1.set_xlabel("Length (m)")
        ax1.set_ylabel("Depth (m)")
        ax1.set_title("Soil & Foundation Cross-Section (side view)")
        ax1.grid(False)
        st.pyplot(fig1, use_container_width=True)
        plt.close(fig1)
        st.caption(f"Schematic footing width shown: {footing_width:.1f} m (derived from required footing area). Not an exact structural design.")

# -----------------------------------------------------------------------
# TAB 2 - 3D BUILDING MODEL
# -----------------------------------------------------------------------
with tab2:
    st.markdown("""
    <div class="eng-card">
        <h3>3D Building Shape</h3>
        <p>Use the rotate and tilt sliders in the sidebar to view the model from different angles. The model reflects your plot size, floor count, floor height, roof type and wall material color.</p>
    </div>
    """, unsafe_allow_html=True)

    L, W, n, fh = plot_length, plot_width, int(floors), floor_height
    margin = max(L, W) * 0.25
    found_top = -depth_mid
    roof_base = n * fh
    apex_h = max(1.0, W * 0.35) if roof_type == "Gable" else 0.0
    total_top = roof_base + (apex_h if roof_type == "Gable" else 0.3)

    fig2 = plt.figure(figsize=(8, 6.5))
    style_fig(fig2)
    ax2 = fig2.add_subplot(111, projection="3d")
    style_3d_axis(ax2)

    # ground plane (thin box)
    add_box(ax2, -margin, L + margin, -margin, W + margin, -0.05, 0, soil["color"], alpha=0.85)

    # foundation block below ground
    add_box(ax2, 0, L, 0, W, found_top, found_top + 0.4, "#8f9295", alpha=0.95)

    # floors
    wall_color = WALL_MATERIALS[wall_material]
    for i in range(n):
        z0, z1 = i * fh, (i + 1) * fh
        color = FLOOR_COLOR_SCALE[i % len(FLOOR_COLOR_SCALE)] if n > 1 else wall_color
        add_box(ax2, 0, L, 0, W, z0, z1, wall_color if n <= 1 else color, alpha=0.9)

    # roof
    if roof_type == "Flat":
        add_box(ax2, 0, L, 0, W, roof_base, roof_base + 0.3, "#3a2f26", alpha=1.0)
    else:
        add_gable_roof(ax2, L, W, roof_base, apex_h, "#7a3b28")

    ax2.set_xlim(-margin, L + margin)
    ax2.set_ylim(-margin, W + margin)
    ax2.set_zlim(found_top - 0.5, total_top + 0.5)
    ax2.set_box_aspect((L + 2 * margin, W + 2 * margin, (total_top - found_top) + 1))
    ax2.view_init(elev=view_elev, azim=view_azim)
    ax2.set_xlabel("Length (m)")
    ax2.set_ylabel("Width (m)")
    ax2.set_zlabel("Height (m)")
    ax2.set_title("3D Building Massing Model")

    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)
    st.caption("Model is a schematic massing study (footprint, floor count, roof form) - not an architectural or structural drawing.")

# -----------------------------------------------------------------------
# TAB 3 - CONCRETE MIX DESIGN
# -----------------------------------------------------------------------
with tab3:
    colA, colB = st.columns([1.2, 1])
    with colA:
        ratio_txt = "Design mix required - lab trial needed" if mix["ratio"] is None else f"{mix['ratio'][0]} : {mix['ratio'][1]} : {mix['ratio'][2]}"
        st.markdown(f"""
        <div class="eng-card">
            <h3>Recommended Grade - {grade}</h3>
            <p>{mix['use']}</p>
            <p><b>Nominal Mix Ratio (Cement : Sand : Aggregate):</b> {ratio_txt}</p>
            <p><b>Water-Cement Ratio:</b> {mix['wc']}</p>
        </div>
        """, unsafe_allow_html=True)
        grade_df = pd.DataFrame([
            {"Grade": g, "Mix Ratio": f"{d['ratio'][0]}:{d['ratio'][1]}:{d['ratio'][2]}" if d["ratio"] else "Design mix",
             "W/C Ratio": d["wc"], "Typical Use": d["use"]}
            for g, d in MIX_DATA.items()
        ])
        st.dataframe(grade_df, use_container_width=True, hide_index=True)
    with colB:
        if mix["ratio"]:
            fig3, ax3 = plt.subplots(figsize=(5, 4.6))
            style_fig(fig3)
            wedges, texts, autotexts = ax3.pie(
                mix["ratio"], labels=["Cement", "Sand", "Aggregate"],
                colors=["#d97b3f", "#f2a65a", "#2fbfa0"],
                autopct="%1.0f%%", pctdistance=0.8,
                wedgeprops=dict(width=0.55, edgecolor=PANEL_BG),
                textprops=dict(color=TEXT_COLOR),
            )
            ax3.set_title(f"{grade} Mix Composition", color=TEXT_COLOR)
            st.pyplot(fig3, use_container_width=True)
            plt.close(fig3)
        else:
            st.warning("M30 requires a lab-designed mix - no fixed nominal ratio to chart.")

# -----------------------------------------------------------------------
# TAB 4 - MATERIAL ESTIMATOR
# -----------------------------------------------------------------------
with tab4:
    st.markdown(f"""
    <div class="eng-card">
        <h3>Structural Concrete Volume</h3>
        <p>Auto-estimated at {CONCRETE_FACTOR_M3_PER_M2} m3 per m2 of floor area across {floors} floor(s):
        <b>{auto_concrete_volume} m3</b>. Adjust below if you have your own quantity take-off.</p>
    </div>
    """, unsafe_allow_html=True)

    concrete_volume = st.number_input("Concrete Volume for Estimate (m3)", min_value=0.1, value=float(auto_concrete_volume), step=0.5)
    calc_ratio = mix["ratio"] if mix["ratio"] else MIX_DATA["M25"]["ratio"]
    calc_wc = mix["wc"] if mix["ratio"] else MIX_DATA["M25"]["wc"]
    result = compute_materials(concrete_volume, calc_ratio, calc_wc)

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="tile"><div class="val">{result["cement_bags"]:.1f}</div><div class="lbl">Cement Bags (50kg)</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="tile"><div class="val">{result["sand_vol_m3"]:.2f} m3</div><div class="lbl">Sand Volume</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="tile"><div class="val">{result["agg_vol_m3"]:.2f} m3</div><div class="lbl">Aggregate Volume</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="tile"><div class="val">{result["water_liters"]:.1f} L</div><div class="lbl">Water Required</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    detail_df = pd.DataFrame({
        "Material": ["Cement", "Sand", "Aggregate", "Water"],
        "Quantity": [
            f"{result['cement_weight_kg']:.1f} kg ({result['cement_bags']:.1f} bags)",
            f"{result['sand_vol_m3']:.2f} m3",
            f"{result['agg_vol_m3']:.2f} m3",
            f"{result['water_liters']:.1f} liters",
        ]
    })
    st.dataframe(detail_df, use_container_width=True, hide_index=True)
    st.caption("Add a 5-8% wastage margin for tender/purchase quantities and confirm with your site engineer.")

# -----------------------------------------------------------------------
# TAB 5 - FULL REPORT
# -----------------------------------------------------------------------
with tab5:
    report = f"""BUILDWISE PRO 3D - PLANNING SUMMARY REPORT
==============================================

PROJECT
  Usage: {usage}
  Plot size: {plot_length} m x {plot_width} m ({plot_area:.1f} m2)
  Floors: {floors} (floor-to-floor height {floor_height} m)
  Roof type: {roof_type}
  Wall material: {wall_material}

SOIL & FOUNDATION
  Soil type: {soil_type}
  Safe Bearing Capacity: {sbc_low}-{sbc_high} kPa
  Recommended foundation depth: {depth_low}-{depth_high} m
  Estimated building load: {building_load_kn:,.0f} kN
  Required footing area: {required_footing_area:.1f} m2 ({area_ratio*100:.0f}% of plot area)
  Foundation recommendation: {foundation_type}
  Soil note: {soil['note']}

CONCRETE MIX DESIGN
  Recommended grade: {grade}
  Nominal mix ratio: {"Design mix required" if mix['ratio'] is None else f"{mix['ratio'][0]}:{mix['ratio'][1]}:{mix['ratio'][2]}"}
  Water-cement ratio: {mix['wc']}
  Typical use: {mix['use']}

MATERIAL ESTIMATE (for {concrete_volume} m3 of concrete)
  Cement: {result['cement_weight_kg']:.1f} kg ({result['cement_bags']:.1f} bags)
  Sand: {result['sand_vol_m3']:.2f} m3
  Aggregate: {result['agg_vol_m3']:.2f} m3
  Water: {result['water_liters']:.1f} liters

DISCLAIMER
  All figures are planning-stage approximations based on standard textbook
  and IS 456 nominal-mix guidance. They are not a substitute for a proper
  geotechnical soil investigation and a licensed structural engineer's design.
"""
    st.markdown('<div class="eng-card"><h3>Planning Summary</h3></div>', unsafe_allow_html=True)
    st.text(report)
    st.download_button("Download Report (.txt)", data=report, file_name="buildwise_pro_report.txt", mime="text/plain")

st.markdown("---")
st.caption("BuildWise Pro 3D - built with Streamlit. For educational and preliminary planning use only, not a substitute for licensed structural design.")

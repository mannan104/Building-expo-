# BuildWise Pro 3D
# A civil engineering planning dashboard built with Streamlit.
#
# Given soil type, plot dimensions, floor count and material choices, the
# app auto-generates:
#   - A soil and foundation cross-section diagram
#   - An interactive 3D building shape model (foundation, floors, roof)
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
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

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
CONCRETE_FACTOR_M3_PER_M2 = 0.17   # rough structural concrete per m² floor area

FLOOR_COLOR_SCALE = ["#d97b3f", "#e0973c", "#e8b25a", "#2fbfa0", "#3fd6b8", "#5eead4"]


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


def box_mesh(x0, x1, y0, y1, z0, z1, color, opacity=1.0, name=None):
    x = [x0, x1, x1, x0, x0, x1, x1, x0]
    y = [y0, y0, y1, y1, y0, y0, y1, y1]
    z = [z0, z0, z0, z0, z1, z1, z1, z1]
    i = [0, 0, 4, 4, 0, 0, 3, 3, 0, 1, 2, 1]
    j = [1, 2, 5, 6, 1, 5, 2, 6, 3, 2, 6, 5]
    k = [2, 3, 6, 7, 5, 4, 6, 7, 7, 6, 7, 6]
    return go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color=color, opacity=opacity,
                      flatshading=True, name=name, showscale=False, hoverinfo="name")


def rect_outline(x0, x1, y0, y1, z, color):
    xs = [x0, x1, x1, x0, x0]
    ys = [y0, y0, y1, y1, y0]
    zs = [z] * 5
    return go.Scatter3d(x=xs, y=ys, z=zs, mode="lines",
                         line=dict(color=color, width=4), showlegend=False, hoverinfo="skip")


def gable_roof_mesh(L, W, z_base, apex_height, color):
    x = [0, L, L, 0, 0, L]
    y = [0, 0, W, W, W / 2, W / 2]
    z = [z_base, z_base, z_base, z_base, z_base + apex_height, z_base + apex_height]
    i = [0, 0, 3, 3, 0, 1]
    j = [1, 5, 2, 5, 3, 2]
    k = [5, 4, 5, 4, 4, 5]
    return go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color=color, opacity=1.0,
                      flatshading=True, name="Roof", showscale=False, hoverinfo="name")


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
        depth_mid = (depth_low + depth_high) / 2
        fig1 = go.Figure()
        # soil block
        fig1.add_shape(type="rect", x0=-1, x1=plot_length + 1, y0=-depth_mid - 1, y1=0,
                        fillcolor=soil["color"], line=dict(width=0), opacity=0.55)
        # ground level line
        fig1.add_shape(type="line", x0=-1, x1=plot_length + 1, y0=0, y1=0,
                        line=dict(color="#2fbfa0", width=3))
        # footing block
        footing_width = min(plot_length, max(2.0, (required_footing_area / plot_width)))
        fx0 = (plot_length - footing_width) / 2
        fig1.add_shape(type="rect", x0=fx0, x1=fx0 + footing_width, y0=-depth_mid, y1=-depth_mid + 0.35,
                        fillcolor="#8f9295", line=dict(color="#e6ded2", width=1))
        # plinth / column stub above footing to ground
        fig1.add_shape(type="rect", x0=fx0 + footing_width * 0.35, x1=fx0 + footing_width * 0.65,
                        y0=-depth_mid + 0.35, y1=0, fillcolor="#d97b3f", line=dict(width=0))
        # building base above ground
        fig1.add_shape(type="rect", x0=0, x1=plot_length, y0=0, y1=floor_height * 0.6,
                        fillcolor=WALL_MATERIALS[wall_material], opacity=0.5, line=dict(color="#e6ded2", width=1))

        fig1.update_layout(
            title="Soil & Foundation Cross-Section (side view)",
            xaxis=dict(title="Length (m)", range=[-1, plot_length + 1], showgrid=False),
            yaxis=dict(title="Depth (m)", range=[-depth_mid - 1, floor_height * 0.6 + 0.5], showgrid=False),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e6ded2"), height=420, margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig1, use_container_width=True)
        st.caption(f"Schematic footing width shown: {footing_width:.1f} m (derived from required footing area). Not an exact structural design.")

# -----------------------------------------------------------------------
# TAB 2 - 3D BUILDING MODEL
# -----------------------------------------------------------------------
with tab2:
    st.markdown("""
    <div class="eng-card">
        <h3>Interactive 3D Building Shape</h3>
        <p>Drag to rotate, scroll to zoom. The model reflects your plot size, floor count, floor height, roof type and wall material color.</p>
    </div>
    """, unsafe_allow_html=True)

    L, W, n, fh = plot_length, plot_width, int(floors), floor_height
    fig3d = go.Figure()

    # ground plane
    margin = max(L, W) * 0.25
    fig3d.add_trace(box_mesh(-margin, L + margin, -margin, W + margin, -0.05, 0, soil["color"], opacity=0.9, name="Ground"))

    # foundation block below ground
    found_top = -((depth_low + depth_high) / 2)
    fig3d.add_trace(box_mesh(0, L, 0, W, found_top, found_top + 0.4, "#8f9295", opacity=0.95, name="Foundation"))

    # floors
    wall_color = WALL_MATERIALS[wall_material]
    for i in range(n):
        z0, z1 = i * fh, (i + 1) * fh
        color = FLOOR_COLOR_SCALE[i % len(FLOOR_COLOR_SCALE)] if n > 1 else wall_color
        fig3d.add_trace(box_mesh(0, L, 0, W, z0, z1, wall_color if n <= 1 else color, opacity=0.88, name=f"Floor {i+1}"))
        fig3d.add_trace(rect_outline(0, L, 0, W, z1, "#f3ede4"))
    fig3d.add_trace(rect_outline(0, L, 0, W, 0, "#f3ede4"))

    # roof
    roof_base = n * fh
    if roof_type == "Flat":
        fig3d.add_trace(box_mesh(0, L, 0, W, roof_base, roof_base + 0.3, "#3a2f26", opacity=1.0, name="Roof"))
    else:
        apex_h = max(1.0, W * 0.35)
        fig3d.add_trace(gable_roof_mesh(L, W, roof_base, apex_h, "#7a3b28"))

    fig3d.update_layout(
        scene=dict(
            xaxis=dict(title="Length (m)", backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(230,222,210,0.15)"),
            yaxis=dict(title="Width (m)", backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(230,222,210,0.15)"),
            zaxis=dict(title="Height (m)", backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(230,222,210,0.15)"),
            aspectmode="data",
            camera=dict(eye=dict(x=1.5, y=-1.6, z=1.0)),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e6ded2"),
        height=560,
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
    )
    st.plotly_chart(fig3d, use_container_width=True)
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
            fig_pie = px.pie(names=["Cement", "Sand", "Aggregate"], values=mix["ratio"], hole=0.45,
                              color_discrete_sequence=["#d97b3f", "#f2a65a", "#2fbfa0"])
            fig_pie.update_layout(title=f"{grade} Mix Composition", paper_bgcolor="rgba(0,0,0,0)",
                                   font=dict(color="#e6ded2"), height=380)
            st.plotly_chart(fig_pie, use_container_width=True)
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

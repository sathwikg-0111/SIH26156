import streamlit as st
import time
import json
import threading
import sys
import os

# Add parent directory to path so UI can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app.main as app_main
from app.main import LOG_BUFFER, run_bg_listener
from simulator.log_generator import start_simulation

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AXIS Log Engine",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------------------------
# Background Ingestion & Simulation Services
# ---------------------------------------------------------------------------
@st.cache_resource
def initialize_background_services():
    listener_thread = threading.Thread(target=run_bg_listener, daemon=True)
    simulator_thread = threading.Thread(target=start_simulation, daemon=True)
    listener_thread.start()
    simulator_thread.start()

initialize_background_services()

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
if "selected_event_hash" not in st.session_state:
    st.session_state.selected_event_hash = None
if "active_dialog" not in st.session_state:
    st.session_state.active_dialog = None
if "follow_live" not in st.session_state:
    st.session_state.follow_live = True
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark Mode"

# ---------------------------------------------------------------------------
# Dynamic Theming: Dark Mode, Light Mode, and High Contrast Mode
# ---------------------------------------------------------------------------
def get_theme_css(theme: str) -> str:
    if theme == "Light Mode":
        return """
        <style>
        .stApp {
            background-color: #f8fafc !important;
            color: #0f172a !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        #MainMenu, header, footer { visibility: hidden; height: 0; }
        .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 100%; }

        [data-testid="stMetricValue"] { color: #0f172a !important; font-weight: 800 !important; }
        [data-testid="stMetricLabel"] { color: #475569 !important; font-weight: 600 !important; }

        /* Container Cards in Light Mode */
        [data-testid="stVerticalBlock"] > div[data-testid="stContainer"] {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
            border-radius: 6px !important;
        }

        /* Code Blocks in Light Mode */
        [data-testid="stCodeBlock"] pre {
            background-color: #f1f5f9 !important;
            border: 1px solid #cbd5e1 !important;
            color: #0f172a !important;
            border-radius: 4px !important;
        }
        code, pre code {
            color: #0f172a !important;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace !important;
        }

        /* Global Buttons in Light Mode */
        button[kind="secondary"] {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            font-weight: 600 !important;
        }
        button[kind="secondary"]:hover {
            background-color: #f1f5f9 !important;
            border-color: #94a3b8 !important;
            color: #0284c7 !important;
        }
        button[kind="primary"] {
            background-color: #0284c7 !important;
            color: #ffffff !important;
        }

        /* DIALOG BOX LIGHT MODE FIX: Ensure 100% visibility of inner portion */
        div[data-testid="stModal"],
        div[data-baseweb="modal"],
        div[role="dialog"] {
            background-color: rgba(15, 23, 42, 0.55) !important;
        }

        div[data-testid="stModal"] > div,
        div[data-testid="stDialog"] > div,
        div[data-baseweb="modal"] > div,
        div[role="dialog"] {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25) !important;
        }

        div[data-testid="stModal"] * {
            color: #0f172a !important;
        }

        div[data-testid="stModal"] [data-testid="stMarkdownContainer"] p,
        div[data-testid="stModal"] [data-testid="stMarkdownContainer"] span,
        div[data-testid="stModal"] [data-testid="stCaptionContainer"] p,
        div[data-testid="stModal"] caption,
        div[data-testid="stModal"] h1,
        div[data-testid="stModal"] h2,
        div[data-testid="stModal"] h3 {
            color: #0f172a !important;
        }

        div[data-testid="stModal"] [data-testid="stCodeBlock"] pre {
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
        }

        div[data-testid="stModal"] [data-testid="stCodeBlock"] code {
            color: #0f172a !important;
            background-color: transparent !important;
        }

        div[data-testid="stModal"] button {
            background-color: #f8fafc !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
        }

        div[data-testid="stModal"] button:hover {
            background-color: #e2e8f0 !important;
            border-color: #94a3b8 !important;
        }

        /* Mistake Banner (Image 2 style in Light Mode) */
        .mistake-banner {
            background: #fef2f2 !important;
            border: 1px solid #fecaca !important;
            border-left: 5px solid #ef4444 !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
            margin-bottom: 8px !important;
            color: #991b1b !important;
        }

        .clean-banner {
            background: #f0fdf4 !important;
            border: 1px solid #bbf7d0 !important;
            border-left: 5px solid #10b981 !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
            margin-bottom: 8px !important;
            color: #166534 !important;
        }

        /* Bottom Alert Cards in Light Mode */
        .alert-card-critical {
            background: #fff1f2 !important;
            border-left: 4px solid #e11d48 !important;
            border-top: 1px solid #fecdd3 !important;
            border-right: 1px solid #fecdd3 !important;
            border-bottom: 1px solid #fecdd3 !important;
            border-radius: 4px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }
        .alert-card-high {
            background: #fffbeb !important;
            border-left: 4px solid #d97706 !important;
            border-top: 1px solid #fde68a !important;
            border-right: 1px solid #fde68a !important;
            border-bottom: 1px solid #fde68a !important;
            border-radius: 4px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }
        .alert-card-medium {
            background: #f0f9ff !important;
            border-left: 4px solid #0284c7 !important;
            border-top: 1px solid #bae6fd !important;
            border-right: 1px solid #bae6fd !important;
            border-bottom: 1px solid #bae6fd !important;
            border-radius: 4px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }

        .alert-title { font-size: 14px; font-weight: 700; color: #0f172a !important; margin-top: 2px; }
        .alert-desc { font-size: 12px; color: #334155 !important; margin-top: 2px; margin-bottom: 6px; }
        .alert-meta-bar {
            background: #f1f5f9 !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 3px;
            padding: 4px 8px;
            font-family: monospace;
            font-size: 11px;
            color: #0369a1 !important;
            display: flex;
            gap: 16px;
        }

        .badge-critical { background: #fee2e2 !important; color: #b91c1c !important; border: 1px solid #f87171 !important; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
        .badge-high { background: #fef3c7 !important; color: #b45309 !important; border: 1px solid #fbbf24 !important; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
        .badge-medium { background: #e0f2fe !important; color: #0369a1 !important; border: 1px solid #38bdf8 !important; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }

        .badge-vendor-cisco { background: #e0f2fe !important; color: #0284c7 !important; border: 1px solid #0284c7 !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }
        .badge-vendor-palo { background: #f3e8ff !important; color: #7c3aed !important; border: 1px solid #7c3aed !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }
        .badge-vendor-fortinet { background: #ffedd5 !important; color: #ea580c !important; border: 1px solid #ea580c !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }
        .badge-vendor-linux { background: #dcfce7 !important; color: #16a34a !important; border: 1px solid #16a34a !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }
        .badge-vendor-windows { background: #cffafe !important; color: #0891b2 !important; border: 1px solid #0891b2 !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }
        .badge-vendor-aws { background: #fef3c7 !important; color: #d97706 !important; border: 1px solid #d97706 !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }
        .badge-vendor-waf { background: #ffe4e6 !important; color: #e11d48 !important; border: 1px solid #e11d48 !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }
        .badge-vendor-ibm { background: #e0e7ff !important; color: #4f46e5 !important; border: 1px solid #4f46e5 !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }

        .badge-allow { background: #ecfdf5 !important; color: #059669 !important; border: 1px solid #34d399 !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; }
        .badge-deny { background: #fef2f2 !important; color: #dc2626 !important; border: 1px solid #f87171 !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; }

        .status-pill-active { background: #e0f2fe !important; border: 1px solid #7dd3fc !important; border-radius: 4px; padding: 4px 10px; font-size: 11px; color: #0369a1 !important; display: inline-flex; align-items: center; gap: 6px; }
        .status-pill-frozen { background: #fef3c7 !important; border: 1px solid #fcd34d !important; border-radius: 4px; padding: 4px 10px; font-size: 11px; color: #92400e !important; display: inline-flex; align-items: center; gap: 6px; }
        hr { border-color: #cbd5e1 !important; }
        </style>
        """
    elif theme == "High Contrast":
        return """
        <style>
        .stApp {
            background-color: #000000 !important;
            color: #ffffff !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        #MainMenu, header, footer { visibility: hidden; height: 0; }
        .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 100%; }

        [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 900 !important; }
        [data-testid="stMetricLabel"] { color: #38bdf8 !important; font-weight: 800 !important; }

        [data-testid="stVerticalBlock"] > div[data-testid="stContainer"] {
            background-color: #000000 !important;
            border: 2px solid #38bdf8 !important;
            border-radius: 6px !important;
        }

        [data-testid="stCodeBlock"] pre {
            background-color: #000000 !important;
            border: 2px solid #ffffff !important;
            color: #ffffff !important;
        }
        code, pre code {
            color: #ffffff !important;
            font-weight: 700;
        }

        /* Modal Dialogs in High Contrast Mode */
        div[data-testid="stModal"],
        div[data-baseweb="modal"],
        div[role="dialog"] {
            background-color: rgba(0, 0, 0, 0.85) !important;
        }

        div[data-testid="stModal"] > div,
        div[data-testid="stDialog"] > div,
        div[data-baseweb="modal"] > div,
        div[role="dialog"] {
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 2px solid #38bdf8 !important;
            border-radius: 8px !important;
        }

        div[data-testid="stModal"] * {
            color: #ffffff !important;
        }

        div[data-testid="stModal"] [data-testid="stCodeBlock"] pre {
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 2px solid #ffffff !important;
        }

        div[data-testid="stModal"] button {
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 2px solid #38bdf8 !important;
        }

        .mistake-banner {
            background: #000000 !important;
            border: 2px solid #ff0055 !important;
            border-left: 6px solid #ff0055 !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
            margin-bottom: 8px !important;
            color: #ffffff !important;
        }

        .clean-banner {
            background: #000000 !important;
            border: 2px solid #00ff66 !important;
            border-left: 6px solid #00ff66 !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
            margin-bottom: 8px !important;
            color: #00ff66 !important;
        }

        .alert-card-critical {
            background: #000000 !important;
            border-left: 6px solid #ff0055 !important;
            border-top: 2px solid #ff0055 !important;
            border-right: 2px solid #ff0055 !important;
            border-bottom: 2px solid #ff0055 !important;
            border-radius: 4px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }
        .alert-card-high {
            background: #000000 !important;
            border-left: 6px solid #ffd000 !important;
            border-top: 2px solid #ffd000 !important;
            border-right: 2px solid #ffd000 !important;
            border-bottom: 2px solid #ffd000 !important;
            border-radius: 4px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }
        .alert-card-medium {
            background: #000000 !important;
            border-left: 6px solid #00d9ff !important;
            border-top: 2px solid #00d9ff !important;
            border-right: 2px solid #00d9ff !important;
            border-bottom: 2px solid #00d9ff !important;
            border-radius: 4px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }

        .alert-title { font-size: 14px; font-weight: 800; color: #ffffff !important; margin-top: 2px; }
        .alert-desc { font-size: 12px; color: #f1f5f9 !important; margin-top: 2px; margin-bottom: 6px; }
        .alert-meta-bar {
            background: #000000 !important;
            border: 2px solid #00d9ff !important;
            border-radius: 3px;
            padding: 4px 8px;
            font-family: monospace;
            font-size: 11px;
            color: #00d9ff !important;
            display: flex;
            gap: 16px;
        }

        .badge-critical { background: #000000 !important; color: #ff0055 !important; border: 2px solid #ff0055 !important; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 800; }
        .badge-high { background: #000000 !important; color: #ffd000 !important; border: 2px solid #ffd000 !important; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 800; }
        .badge-medium { background: #000000 !important; color: #00d9ff !important; border: 2px solid #00d9ff !important; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 800; }

        .badge-vendor-cisco { background: #000000 !important; color: #00d9ff !important; border: 2px solid #00d9ff !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 800; font-family: monospace; }
        .badge-vendor-palo { background: #000000 !important; color: #d946ef !important; border: 2px solid #d946ef !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 800; font-family: monospace; }
        .badge-vendor-fortinet { background: #000000 !important; color: #fb923c !important; border: 2px solid #fb923c !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 800; font-family: monospace; }
        .badge-vendor-linux { background: #000000 !important; color: #00ff66 !important; border: 2px solid #00ff66 !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 800; font-family: monospace; }
        .badge-vendor-windows { background: #000000 !important; color: #22d3ee !important; border: 2px solid #22d3ee !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 800; font-family: monospace; }
        .badge-vendor-aws { background: #000000 !important; color: #ffd000 !important; border: 2px solid #ffd000 !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 800; font-family: monospace; }
        .badge-vendor-waf { background: #000000 !important; color: #ff0055 !important; border: 2px solid #ff0055 !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 800; font-family: monospace; }
        .badge-vendor-ibm { background: #000000 !important; color: #a855f7 !important; border: 2px solid #a855f7 !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 800; font-family: monospace; }

        .badge-allow { background: #000000 !important; color: #00ff66 !important; border: 2px solid #00ff66 !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 800; }
        .badge-deny { background: #000000 !important; color: #ff0055 !important; border: 2px solid #ff0055 !important; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 800; }

        .status-pill-active { background: #000000 !important; border: 2px solid #00ff66 !important; border-radius: 4px; padding: 4px 10px; font-size: 11px; color: #00ff66 !important; font-weight: 800; display: inline-flex; align-items: center; gap: 6px; }
        .status-pill-frozen { background: #000000 !important; border: 2px solid #ffd000 !important; border-radius: 4px; padding: 4px 10px; font-size: 11px; color: #ffd000 !important; font-weight: 800; display: inline-flex; align-items: center; gap: 6px; }
        hr { border-color: #38bdf8 !important; }
        </style>
        """
    else:  # Dark Mode (Default)
        return """
        <style>
        .stApp {
            background-color: #0b0f17 !important;
            color: #e2e8f0 !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        #MainMenu, header, footer { visibility: hidden; height: 0; }
        .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 100%; }

        [data-testid="stMetricValue"] { color: #f8fafc !important; font-weight: 700 !important; }
        [data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: 600 !important; }

        [data-testid="stVerticalBlock"] > div[data-testid="stContainer"] {
            background-color: #0f1523 !important;
            border: 1px solid #1e293b !important;
            border-radius: 6px !important;
        }

        [data-testid="stCodeBlock"] pre {
            background-color: #070a10 !important;
            border: 1px solid #1a2333 !important;
            color: #cbd5e1 !important;
            border-radius: 4px !important;
        }

        /* Modal Dialogs in Dark Mode */
        div[data-testid="stModal"],
        div[data-baseweb="modal"],
        div[role="dialog"] {
            background-color: rgba(0, 0, 0, 0.7) !important;
        }

        div[data-testid="stModal"] > div,
        div[data-testid="stDialog"] > div,
        div[data-baseweb="modal"] > div,
        div[role="dialog"] {
            background-color: #111827 !important;
            color: #f8fafc !important;
            border: 1px solid #1f2937 !important;
            border-radius: 8px !important;
        }

        div[data-testid="stModal"] [data-testid="stMarkdownContainer"] p,
        div[data-testid="stModal"] [data-testid="stMarkdownContainer"] span,
        div[data-testid="stModal"] [data-testid="stCaptionContainer"] p,
        div[data-testid="stModal"] caption,
        div[data-testid="stModal"] h1,
        div[data-testid="stModal"] h2,
        div[data-testid="stModal"] h3 {
            color: #f8fafc !important;
        }

        div[data-testid="stModal"] [data-testid="stCodeBlock"] pre {
            background-color: #090d14 !important;
            color: #93c5fd !important;
            border: 1px solid #1f2937 !important;
        }

        div[data-testid="stModal"] button {
            background-color: #1f2937 !important;
            color: #f8fafc !important;
            border: 1px solid #374151 !important;
        }

        /* Mistake Banner Dark Mode */
        .mistake-banner {
            background: #241419 !important;
            border: 1px solid #571c26 !important;
            border-left: 5px solid #ef4444 !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
            margin-bottom: 8px !important;
            color: #fca5a5 !important;
        }

        .clean-banner {
            background: #0f231d !important;
            border: 1px solid #164e3f !important;
            border-left: 5px solid #10b981 !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
            margin-bottom: 8px !important;
            color: #6ee7b7 !important;
        }

        .alert-card-critical {
            background: #151a24;
            border-left: 4px solid #ef4444;
            border-top: 1px solid #243042;
            border-right: 1px solid #243042;
            border-bottom: 1px solid #243042;
            border-radius: 4px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }
        .alert-card-high {
            background: #151a24;
            border-left: 4px solid #f59e0b;
            border-top: 1px solid #243042;
            border-right: 1px solid #243042;
            border-bottom: 1px solid #243042;
            border-radius: 4px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }
        .alert-card-medium {
            background: #151a24;
            border-left: 4px solid #38bdf8;
            border-top: 1px solid #243042;
            border-right: 1px solid #243042;
            border-bottom: 1px solid #243042;
            border-radius: 4px;
            padding: 12px 16px;
            margin-bottom: 8px;
        }

        .alert-title { font-size: 14px; font-weight: 700; color: #ffffff !important; margin-top: 2px; }
        .alert-desc { font-size: 12px; color: #cbd5e1 !important; margin-top: 2px; margin-bottom: 6px; }
        .alert-meta-bar {
            background: #090d14 !important;
            border: 1px solid #1a2433 !important;
            border-radius: 3px;
            padding: 4px 8px;
            font-family: monospace;
            font-size: 11px;
            color: #93c5fd !important;
            display: flex;
            gap: 16px;
        }

        .badge-critical { background: rgba(239, 68, 68, 0.18); color: #f87171; border: 1px solid #ef4444; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
        .badge-high { background: rgba(245, 158, 11, 0.18); color: #fbbf24; border: 1px solid #f59e0b; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
        .badge-medium { background: rgba(56, 189, 248, 0.18); color: #38bdf8; border: 1px solid #38bdf8; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }

        .badge-vendor-cisco { background: #1e293b; color: #38bdf8; border: 1px solid #0284c7; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }
        .badge-vendor-palo { background: #261d36; color: #c084fc; border: 1px solid #7c3aed; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }
        .badge-vendor-fortinet { background: #2e1c14; color: #fb923c; border: 1px solid #ea580c; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }
        .badge-vendor-linux { background: #15291f; color: #4ade80; border: 1px solid #16a34a; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }
        .badge-vendor-windows { background: #112838; color: #22d3ee; border: 1px solid #0891b2; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }
        .badge-vendor-aws { background: #2b2212; color: #fbbf24; border: 1px solid #d97706; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }
        .badge-vendor-waf { background: #311520; color: #fb7185; border: 1px solid #e11d48; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }
        .badge-vendor-ibm { background: #19203b; color: #818cf8; border: 1px solid #4f46e5; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: monospace; }

        .badge-allow { background: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; }
        .badge-deny { background: rgba(248, 113, 113, 0.15); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.3); padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; }

        .status-pill-active { background: #0d1926; border: 1px solid #1e3a5f; border-radius: 4px; padding: 4px 10px; font-size: 11px; color: #38bdf8; display: inline-flex; align-items: center; gap: 6px; }
        .status-pill-frozen { background: #2b1a11; border: 1px solid #78350f; border-radius: 4px; padding: 4px 10px; font-size: 11px; color: #fbbf24; display: inline-flex; align-items: center; gap: 6px; }
        hr { border-color: #1e293b !important; }
        </style>
        """

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def get_event_hash(event: dict) -> str:
    return event.get("metadata", {}).get("log_hash", "")

def get_vendor_badge_html(vendor: str) -> str:
    v = vendor.upper()
    if "CISCO" in v:
        return f"<span class='badge-vendor-cisco'>{vendor}</span>"
    elif "PALO" in v:
        return f"<span class='badge-vendor-palo'>{vendor}</span>"
    elif "FORTI" in v:
        return f"<span class='badge-vendor-fortinet'>{vendor}</span>"
    elif "WINDOWS" in v or "AD" in v:
        return f"<span class='badge-vendor-windows'>{vendor}</span>"
    elif "AWS" in v or "VPC" in v:
        return f"<span class='badge-vendor-aws'>{vendor}</span>"
    elif "WAF" in v or "CLOUDFLARE" in v or "NGINX" in v:
        return f"<span class='badge-vendor-waf'>{vendor}</span>"
    elif "IBM" in v:
        return f"<span class='badge-vendor-ibm'>{vendor}</span>"
    return f"<span class='badge-vendor-linux'>{vendor}</span>"

SEVERITY_WEIGHT = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "WATCH": 4}

# ---------------------------------------------------------------------------
# Modal Dialogs (Inspecting Original Log & Full OCSF JSON)
# ---------------------------------------------------------------------------
def dismiss_dialog():
    st.session_state.active_dialog = None

@st.dialog("ORIGINAL LOG INSPECTION", width="large")
def render_raw_log_dialog(event: dict):
    raw_payload = event.get("unmapped", {}).get("raw_payload", "")
    metadata = event.get("metadata", {})
    src = event.get("src_endpoint", {})
    dst = event.get("dst_endpoint", {})
    conn = event.get("connection_info", {})
    disposition = event.get("disposition", "UNKNOWN")
    time_str = event.get("time", "")

    c1, c2, c3 = st.columns(3)
    c1.caption(f"Vendor: **{metadata.get('original_vendor', 'LINUX')}**")
    c2.caption(f"Disposition: **{disposition}**")
    c3.caption(f"Protocol: **{conn.get('protocol_name', 'TCP')}**")

    c4, c5, c6 = st.columns(3)
    c4.caption(f"Source: **{src.get('ip', '-')}:{src.get('port', '-')}**")
    c5.caption(f"Destination: **{dst.get('ip', '-')}:{dst.get('port', '-')}**")
    c6.caption(f"Time (UTC): **{time_str[:19]}**")

    st.markdown("**Original Raw Ingested Payload**")
    st.code(raw_payload, language="text")
    st.caption(f"SHA-256 Digest: `{metadata.get('log_hash', 'N/A')}`")

    if st.button("Close Window", key="close_raw_dlg"):
        st.session_state.active_dialog = None
        st.rerun()

@st.dialog("NORMALIZED OCSF JSON", width="large")
def render_json_dialog(event: dict):
    metadata = event.get("metadata", {})
    st.caption(f"OCSF Schema: **v{metadata.get('version', '1.1.0')}** | Class: **Network Activity (4001)** | Vendor: **{metadata.get('original_vendor', 'LINUX')}**")
    
    st.markdown("**Normalized OCSF JSON (Full Line-by-Line Indented View)**")
    json_str = json.dumps(event, indent=2)
    st.code(json_str, language="json")

    c_dl, c_cls = st.columns([1, 1])
    with c_dl:
        st.download_button(
            "Download JSON Payload",
            data=json_str,
            file_name=f"ocsf_event_{metadata.get('log_hash', 'export')[:8]}.json",
            mime="application/json",
            key="dl_json_dlg"
        )
    with c_cls:
        if st.button("Close Window", key="close_json_dlg"):
            st.session_state.active_dialog = None
            st.rerun()

if st.session_state.active_dialog:
    dlg_event, dlg_type = st.session_state.active_dialog
    if dlg_type == "raw":
        render_raw_log_dialog(dlg_event)
    elif dlg_type == "json":
        render_json_dialog(dlg_event)

# ---------------------------------------------------------------------------
# Real-Time Dashboard Fragment (2s refresh rate decoupled from ingestion)
# ---------------------------------------------------------------------------
run_interval = "2s" if st.session_state.follow_live and not st.session_state.active_dialog else None

@st.fragment(run_every=run_interval)
def render_dashboard():
    # Dynamically inject theme CSS
    st.markdown(get_theme_css(st.session_state.get("theme_mode", "Dark Mode")), unsafe_allow_html=True)

    current_logs = list(LOG_BUFFER)
    total_events = getattr(app_main, "TOTAL_EVENTS_PROCESSED", len(LOG_BUFFER))
    buffer_len = len(current_logs)

    # -----------------------------------------------------------------------
    # 1. TOP ROW: LOGO (LEFT) + STATUS METRICS (RIGHT) AS SKETCHED
    # -----------------------------------------------------------------------
    top_col_logo, top_col_m1, top_col_m2, top_col_m3 = st.columns([1.5, 1.2, 1.2, 1.3])

    with top_col_logo:
        if os.path.exists("UI/logo.png"):
            st.image("UI/logo.png", width=190)
        else:
            st.markdown("### AXIS LOG ENGINE")

    with top_col_m1:
        st.metric("Pipeline Status", "ACTIVE (UDP 5140)", "Online")

    with top_col_m2:
        st.metric("Target Output Schema", "OCSF v1.1.0", "Compliant")

    with top_col_m3:
        # Buffer Saturation Indicator with dynamic color shifts (Slate -> Amber 75% -> Crimson 90%)
        sat_pct = (buffer_len / 100.0) * 100.0
        if sat_pct >= 90:
            delta_label = f"Buffer: {buffer_len}/100 (Queue Backlog: CRITICAL)"
            delta_style = "inverse"
            tag_color = "#ef4444"
        elif sat_pct >= 75:
            delta_label = f"Buffer: {buffer_len}/100 (Queue Load: HIGH)"
            delta_style = "off"
            tag_color = "#f59e0b"
        else:
            delta_label = f"Buffer: {buffer_len}/100 (Optimal Ingest)"
            delta_style = "normal"
            tag_color = "#34d399"

        st.metric("Total Events Ingested", f"{total_events} Events", delta=delta_label, delta_color=delta_style)

    # -----------------------------------------------------------------------
    # LIVE INGEST PAUSE & STREAM CONTROLS BAR + THEME SELECTOR
    # -----------------------------------------------------------------------
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2.3, 1.3, 1.1])
    with ctrl_col1:
        if st.session_state.follow_live:
            st.markdown("<div class='status-pill-active'>● Live Telemetry Stream: ACTIVE (Decoupled Ingest)</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='status-pill-frozen'>❚❚ Stream View FROZEN for Investigation</div>", unsafe_allow_html=True)
    with ctrl_col2:
        theme_names = ["Dark Mode", "Light Mode", "High Contrast"]
        current_theme = st.session_state.get("theme_mode", "Dark Mode")
        theme_idx = theme_names.index(current_theme) if current_theme in theme_names else 0
        chosen_theme = st.selectbox(
            "Theme Mode",
            theme_names,
            index=theme_idx,
            key="theme_mode_selector",
            label_visibility="collapsed"
        )
        if chosen_theme != st.session_state.get("theme_mode"):
            st.session_state.theme_mode = chosen_theme
            st.rerun()
    with ctrl_col3:
        if st.session_state.follow_live:
            if st.button("Pause Live Stream", key="btn_pause_stream"):
                st.session_state.follow_live = False
                st.rerun()
        else:
            if st.button("Resume Live Stream", key="btn_resume_stream_top"):
                st.session_state.follow_live = True
                st.session_state.selected_event_hash = None
                st.rerun()

    st.divider()

    # -----------------------------------------------------------------------
    # 2. TRANSFORMATION PIPELINE SECTION (1-to-1 Event-by-Event Stream)
    # Matches user format: Every incoming raw log has its own corresponding
    # normalized OCSF JSON and alerts directly beside it in a 1-to-1 row.
    # -----------------------------------------------------------------------
    st.subheader("Transformation Pipeline")
    st.caption("Real-Time 1-to-1 Normalization: Heterogeneous Multi-Vendor Raw Stream  →  Standardized OCSF JSON")

    hdr_c1, hdr_c2 = st.columns([1.1, 1.1], gap="medium")
    with hdr_c1:
        st.markdown("**Incoming Raw Log Stream** *(Cisco / Palo Alto / Fortinet / Linux / Windows / AWS / WAF / IBM)*")
    with hdr_c2:
        st.markdown("**Normalized OCSF JSON & Security Alerts** *(OCSF Schema v1.1.0)*")

    if not current_logs:
        st.info("Waiting for incoming telemetry stream on UDP 5140...")
    else:
        for idx, ev in enumerate(current_logs[:10]):
            raw_text = ev.get("unmapped", {}).get("raw_payload", "")
            metadata = ev.get("metadata", {})
            vendor = metadata.get("original_vendor", "LINUX")
            action = ev.get("disposition", "ALLOW")
            ev_hash = get_event_hash(ev)
            ev_hash_short = ev_hash[:8] if ev_hash else f"{idx:03d}"
            has_alert = ev.get("has_mistake_flag", False)
            highlights = ev.get("security_highlights", [])
            json_str = json.dumps(ev, indent=2)

            with st.container(border=True):
                c_raw, c_json = st.columns([1.1, 1.1], gap="medium")

                # LEFT COLUMN: THE SINGLE RAW INCOMING LOG
                with c_raw:
                    meta_col1, meta_col2 = st.columns([2.5, 1])
                    with meta_col1:
                        disp_badge = f"<span class='badge-allow'>{action}</span>" if action == "ALLOW" else f"<span class='badge-deny'>{action}</span>"
                        vendor_badge = get_vendor_badge_html(vendor)
                        alert_tag = "<span class='badge-critical' style='margin-left:4px;'>MISTAKE DETECTED</span>" if has_alert else ""
                        st.markdown(f"{disp_badge} {vendor_badge} {alert_tag}", unsafe_allow_html=True)
                    with meta_col2:
                        st.caption(f"{ev.get('time', '')[11:19]} UTC")

                    st.code(raw_text, language="text")

                    b1, b2 = st.columns([1.2, 1])
                    with b1:
                        if st.button("Inspect Raw Log", key=f"btn_raw_row_{idx}_{ev_hash_short}"):
                            st.session_state.active_dialog = (ev, "raw")
                            st.rerun()
                    with b2:
                        st.caption(f"SHA-256: `{ev_hash_short}`")

                # RIGHT COLUMN: THE EXACT CORRESPONDING NORMALIZED OCSF JSON & ALERTS
                with c_json:
                    if has_alert:
                        top_h = min(highlights, key=lambda h: SEVERITY_WEIGHT.get(h.get("severity", "LOW"), 99)) if highlights else {}
                        sev = top_h.get("severity", "HIGH")
                        msg = top_h.get("alert_message", "Policy Misconfiguration Detected")
                        rule_id = top_h.get("rule_id", "RULE-ALERT")
                        
                        st.markdown(f"""
                        <div class="mistake-banner">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-weight:800; font-size:12px; letter-spacing:0.04em;">NETWORKING MISTAKE DETECTED</span>
                                <span class="badge-{sev.lower()}">{sev}</span>
                            </div>
                            <div style="font-size:12px; font-weight:700; margin-top:3px;">[{sev}] {msg} ({rule_id})</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="clean-banner">
                            <span style="font-weight:700; font-size:12px;">NORMALIZED OCSF v1.1.0</span>
                            <span style="font-size:11px; opacity:0.8; margin-left:8px;">Policy Compliant</span>
                        </div>
                        """, unsafe_allow_html=True)

                    # Real line-by-line formatted JSON
                    st.code(json_str, language="json")

                    dl_c1, dl_c2 = st.columns([1, 1])
                    with dl_c1:
                        st.download_button(
                            "Download JSON",
                            data=json_str,
                            file_name=f"ocsf_{ev_hash_short}.json",
                            mime="application/json",
                            key=f"dl_row_{idx}_{ev_hash_short}"
                        )
                    with dl_c2:
                        if st.button("Full Screen JSON", key=f"btn_fs_row_{idx}_{ev_hash_short}"):
                            st.session_state.active_dialog = (ev, "json")
                            st.rerun()

            st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

    st.divider()

    # -----------------------------------------------------------------------
    # 3. PRIORITIZED NETWORKING ALERTS SECTION
    # As in sketch: severity (e.g. critical), issue details,
    # and the issue part of code that is written in json normalised
    # -----------------------------------------------------------------------
    st.subheader("Prioritized Networking Alerts")
    st.caption("Policy Misconfigurations Detected Across Ingested Traffic (Sorted by Severity)")

    alerts = [e for e in current_logs if e.get("has_mistake_flag")]
    sorted_alerts = sorted(
        alerts,
        key=lambda e: min(
            SEVERITY_WEIGHT.get(h.get("severity", "LOW"), 99) for h in e.get("security_highlights", [])
        ) if e.get("security_highlights") else 99
    )

    if not sorted_alerts:
        st.info("No active security alerts detected in current buffer. All traffic complies with firewall policy.")
    else:
        for a_idx, ev in enumerate(sorted_alerts[:8]):
            highlights = ev.get("security_highlights", [])
            top_h = min(highlights, key=lambda h: SEVERITY_WEIGHT.get(h.get("severity", "LOW"), 99)) if highlights else {}
            sev = top_h.get("severity", "HIGH")
            msg = top_h.get("alert_message", "Policy Misconfiguration Detected")
            rule_id = top_h.get("rule_id", "RULE-MISCONFIG")
            ev_hash = get_event_hash(ev)
            ev_hash_short = ev_hash[:8] if ev_hash else f"{a_idx:03d}"

            # Contextual Explanations for Scaled Rules
            if rule_id == "RULE-001":
                explanation = "Direct external management exposure: Inbound administrative access on critical ports (22, 23, 3389, 445) from untrusted external WAN was permitted into internal servers."
            elif rule_id == "RULE-002":
                explanation = "Database direct access: Cross-subnet connection attempt directly to database port (MySQL 3306) was permitted without intermediary bastion or API proxy."
            elif rule_id == "RULE-003":
                explanation = "Cleartext egress: Cleartext transmission protocol (FTP/Telnet port 21/23) was allowed outbound, exposing sensitive data to interception."
            elif rule_id == "RULE-004":
                explanation = "Lateral movement pattern: Ephemeral SMB/RPC connection (port 445) between internal workstations and server infrastructure was detected."
            elif rule_id == "RULE-005":
                explanation = "Brute force threshold exceeded: Multiple consecutive SSH authentication failures detected from an external IP address."
            elif rule_id == "RULE-006":
                explanation = "Host privilege escalation: Unauthorized sudo command execution attempt failed PAM authentication on host."
            elif rule_id == "RULE-007":
                explanation = "Active Directory audit warning: Windows Event ID logon failure or privilege assignment anomaly detected on domain controller."
            elif rule_id == "RULE-008":
                explanation = "Cloud security group misconfiguration: AWS VPC Flow Log reveals outbound egress to 0.0.0.0/0 on high-risk non-standard ports with ACCEPT."
            elif rule_id == "RULE-009":
                explanation = "Web Application Firewall trigger: Malicious payload probe containing SQL injection or directory traversal patterns blocked at reverse proxy."
            else:
                explanation = "Network traffic matching security policy violation rule was allowed through firewall policy without explicit authorization."

            src = ev.get("src_endpoint", {})
            dst = ev.get("dst_endpoint", {})
            conn = ev.get("connection_info", {})
            disposition = ev.get("disposition", "UNKNOWN")

            # Extract the offending part of the code in normalized JSON format as sketched
            offending_json_snippet = {
                "dst_endpoint": dst,
                "disposition": disposition,
                "security_highlights": highlights,
                "has_mistake_flag": True
            }
            if ev.get("http_request"):
                offending_json_snippet["http_request"] = ev["http_request"]
            if ev.get("actor"):
                offending_json_snippet["actor"] = ev["actor"]

            snippet_str = json.dumps(offending_json_snippet, indent=2)

            if sev == "CRITICAL":
                card_class = "alert-card-critical"
                badge_class = "badge-critical"
            elif sev == "HIGH":
                card_class = "alert-card-high"
                badge_class = "badge-high"
            else:
                card_class = "alert-card-medium"
                badge_class = "badge-medium"

            # Alert Card
            st.markdown(f"""
            <div class="{card_class}">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <div>
                        <span class="{badge_class}">{sev}</span>
                        <span style="font-family:monospace; font-size:11px; margin-left:8px; opacity:0.8;">{rule_id}</span>
                    </div>
                    <span style="font-family:monospace; font-size:11px; opacity:0.8;">{ev.get('time', '')[:19]} UTC</span>
                </div>
                <div class="alert-title">{msg}</div>
                <div class="alert-desc">{explanation}</div>
                <div class="alert-meta-bar">
                    <span>Source: <b>{src.get('ip', '-')}:{src.get('port', '-')}</b></span>
                    <span>→</span>
                    <span>Destination: <b>{dst.get('ip', '-')}:{dst.get('port', '-')}</b></span>
                    <span>Protocol: <b>{conn.get('protocol_name', 'TCP')}</b></span>
                    <span>Action: <b>{disposition}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Display the issue part of code that is written in JSON normalised as sketched
            st.caption("Offending OCSF JSON Normalized Snippet:")
            st.code(snippet_str, language="json")

            # Actions
            ac1, ac2, ac3 = st.columns([1, 1, 1.2])
            with ac1:
                if st.button("View Original Log", key=f"alt_raw_{a_idx}_{ev_hash_short}"):
                    st.session_state.active_dialog = (ev, "raw")
                    st.rerun()
            with ac2:
                if st.button("Inspect Full OCSF JSON", key=f"alt_json_{a_idx}_{ev_hash_short}"):
                    st.session_state.active_dialog = (ev, "json")
                    st.rerun()
            with ac3:
                if st.button("Inspect in Pipeline", key=f"alt_pipe_{a_idx}_{ev_hash_short}"):
                    st.session_state.selected_event_hash = ev_hash
                    st.session_state.follow_live = False
                    st.rerun()

            st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

# Render live dashboard
render_dashboard()
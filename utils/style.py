import base64
from pathlib import Path
import streamlit as st
from .constants import LOGO_PATH, FAVICON_PATH, BACKGROUND_PATH


def _b64(path: Path):
    try:
        if path.exists():
            return base64.b64encode(path.read_bytes()).decode()
    except Exception:
        return ''
    return ''


def setup_page(title='BLT Swimming Club Manager'):
    page_icon = str(FAVICON_PATH) if FAVICON_PATH.exists() else '🏊'
    st.set_page_config(page_title=title, page_icon=page_icon, layout='wide')
    inject_css()


def inject_css():
    bg64 = _b64(BACKGROUND_PATH)
    bg_css = "background: linear-gradient(135deg,#F4FBFF 0%,#EAF8FF 45%,#FFFFFF 100%);"
    if bg64:
        bg_css = f"background-image: linear-gradient(135deg, rgba(246,251,255,.94), rgba(234,248,255,.88)), url(data:image/jpg;base64,{bg64}); background-size: cover; background-attachment: fixed; background-position: center;"
    st.markdown(f'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
:root {{
  --primary:#023E8A; --secondary:#0077B6; --aqua:#00B4D8; --soft:#EAF8FF;
  --green:#2DC653; --red:#E63946; --text:#0B2545; --muted:#638297;
}}
html, body, [class*="css"] {{font-family: 'Inter', sans-serif;}}
.stApp {{{bg_css}}}
.block-container {{padding-top: 1rem; padding-bottom: 2rem; max-width: 1460px;}}
[data-testid="stSidebar"] {{background: linear-gradient(180deg, rgba(2,62,138,.98) 0%, rgba(0,119,182,.96) 70%, rgba(0,180,216,.92) 100%);}}
[data-testid="stSidebar"] * {{color: white !important;}}
[data-testid="stSidebar"] img {{border-radius: 22px; background: white; padding: 8px; box-shadow: 0 12px 28px rgba(0,0,0,.18);}}
[data-testid="stSidebarNav"] li div a {{border-radius: 16px; margin: 4px 8px;}}
[data-testid="stSidebarNav"] li div a:hover {{background: rgba(255,255,255,.14);}}
.hero {{position: relative; overflow: hidden; border-radius: 32px; padding: 34px; min-height: 170px; background: linear-gradient(110deg, rgba(2,62,138,.96), rgba(0,119,182,.84), rgba(0,180,216,.72)); box-shadow: 0 22px 60px rgba(2,62,138,.24); color: white; border: 1px solid rgba(255,255,255,.35);}}
.hero:after {{content:""; position:absolute; right:-80px; top:-110px; width:300px; height:300px; border-radius:50%; background:rgba(255,255,255,.16);}}
.hero h1 {{font-size: 44px; line-height: 1.02; margin:0; font-weight:900; letter-spacing: -.055em;}}
.hero p {{font-size: 18px; margin-top: 10px; opacity:.95; font-weight:600;}}
.hero-logo img {{filter: drop-shadow(0 16px 24px rgba(2,62,138,.24)); border-radius: 32px; background: rgba(255,255,255,.95); padding: 8px;}}
.banner-img img {{border-radius: 30px; max-height: 330px; object-fit: cover; box-shadow: 0 18px 45px rgba(2,62,138,.18); border: 1px solid rgba(255,255,255,.8);}}
.glass-card {{background: rgba(255,255,255,.78); border: 1px solid rgba(255,255,255,.72); backdrop-filter: blur(18px); border-radius: 28px; padding: 22px; box-shadow: 0 16px 42px rgba(12,74,110,.11);}}
.metric-card {{background: rgba(255,255,255,.92); border: 1px solid #DDF1F8; border-radius: 26px; padding: 22px; box-shadow: 0 14px 34px rgba(2,62,138,.10); transition: all .18s ease; min-height: 128px;}}
.metric-card:hover {{transform: translateY(-4px); box-shadow: 0 20px 46px rgba(2,62,138,.16);}}
.metric-icon {{font-size: 26px;}}
.metric-title {{color:#54748A; font-size:13px; font-weight:800; text-transform: uppercase; letter-spacing:.06em; margin-top:6px;}}
.metric-value {{color:#023E8A; font-size:36px; font-weight:900; margin-top: 2px; line-height:1;}}
.metric-note {{color:#6B8794; font-size:13px; margin-top:7px;}}
.student-card {{background:rgba(255,255,255,.94); border-radius:26px; padding:22px; border:1px solid #DDEFF7; box-shadow:0 14px 34px rgba(2,62,138,.09); margin-bottom:16px;}}
.student-name {{font-size:20px; font-weight:900; color:#023E8A;}}
.badge {{display:inline-block; border-radius:999px; padding:6px 12px; font-size:12px; font-weight:900; margin-right:6px;}}
.badge-green {{background:#D8F3DC; color:#1B4332;}}
.badge-yellow {{background:#FFF3BF; color:#7A4F01;}}
.badge-blue {{background:#DFF6FF; color:#005F8A;}}
.badge-red {{background:#FFE0E6; color:#A4133C;}}
.small-muted {{color:#6B8794; font-size:13px; font-weight:600;}}
.slot-card {{background:rgba(255,255,255,.93); border:1px solid #DDEFF7; border-radius:24px; padding:18px; box-shadow:0 12px 28px rgba(2,62,138,.08); margin-bottom:14px;}}
.slot-title {{font-weight:900; color:#023E8A; font-size:18px;}}
hr {{border:none; border-top:1px solid #D8ECF5; margin: 1.4rem 0;}}
.stButton > button {{border-radius: 16px; font-weight: 800; border: 0; box-shadow: 0 10px 22px rgba(2,62,138,.10);}}
.stDownloadButton > button {{border-radius: 16px; font-weight: 800;}}
.stDataFrame, [data-testid="stDataFrame"] {{border-radius: 22px; overflow: hidden;}}
div[data-testid="stTabs"] button {{font-size: 16px; font-weight: 800;}}
</style>
''', unsafe_allow_html=True)


def sidebar_brand():
    with st.sidebar:
        if Path(LOGO_PATH).exists():
            st.image(str(LOGO_PATH), width=118)
        st.markdown('## BLT Swimming')
        st.caption('Swim Management System')
        st.divider()
        st.markdown('**Hồ bơi Bình Lợi Trung**')
        st.caption('Quản lý học viên, lịch dạy, học phí và tiền giáo viên')


def hero(title='BLT SWIMMING CLUB', subtitle='Quản lý học viên & lịch dạy Hồ Bơi Bình Lợi Trung'):
    col1, col2 = st.columns([4.3, 1])
    with col1:
        st.markdown(f'''<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>''', unsafe_allow_html=True)
    with col2:
        if Path(LOGO_PATH).exists():
            st.markdown('<div class="hero-logo">', unsafe_allow_html=True)
            st.image(str(LOGO_PATH), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)


def metric_card(title, value, note='', icon=''):
    st.markdown(f'''
<div class="metric-card">
  <div class="metric-icon">{icon}</div>
  <div class="metric-title">{title}</div>
  <div class="metric-value">{value}</div>
  <div class="metric-note">{note}</div>
</div>
''', unsafe_allow_html=True)


def section_image(path, caption=None):
    path = Path(path)
    if path.exists():
        st.markdown('<div class="banner-img">', unsafe_allow_html=True)
        st.image(str(path), use_container_width=True, caption=caption)
        st.markdown('</div>', unsafe_allow_html=True)

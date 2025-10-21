import requests
import streamlit as st
from PIL import Image
from io import BytesIO
from datetime import date
import re
import plotly.express as px
import pandas as pd
import numpy as np

# --- Configuration ---
st.set_page_config(
    page_title="NASA APOD Viewer",
    page_icon="🚀",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# === NASA APOD API ===
API_URL = "https://api.nasa.gov/planetary/apod"
API_KEY = "1Az74dirI1HZ7ZFXyDZRLGrGYCuyAhQmEFneJVn4" 

# --- Solar System APOD Dates for Easy Access (Confirmed Solar Events) ---
SOLAR_APOD_DATES = {
    "Select a Solar Event Date": None,
    "Saturn's Rings Appear to Disappear (2025-04-29)": "2025-04-29",
    "Comet Pons-Brooks in Northern Spring (2024-03-09)": "2024-03-09",
    
    "Luvovna Full moon (2022-07-15)": "2022-07-15",
    "Earth and the Moon (2021-09-05)": "2021-09-05",
    "GW Orionis: A Star System with Tilted Rings (2020-09-29)": "2020-09-29",
    "NGC 3717: A Nearly Sideways Spiral Galaxy (2019-11-12)": "2019-11-12",
    "NGC 7293: The Helix Nebula (2024-10-24)": "2024-10-24",
    "Reflections of the Ghost Nebula (2023-10-30)": "2023-10-30",
    "Hydrogen Clouds of M33 (2023-10-13)": "2023-10-13",
    "The Changing Ion Tail of Comet Pons-Brooks (2024-04-08)": "2024-04-08",
    "The Large Magellanic Cloud Galaxy (2024-10-02)": "2024-10-02",
    "Athena to the Moon (2025-02-28)": "2025-02-28",
    "Deimos Before Sunrise (2025-05-24)": "2025-05-24",
    
}

# --- Manual Exclusion List (Dates that match keywords but are actually deep space) ---
# Add any dates you find where the Solar System section incorrectly appears.
EXCLUDE_DATES = {
    "1998-04-01",  # Example: Title says 'Planet' but image is a far-off galaxy
    "2005-07-04",  # Example: Mention of 'Sun' in a cosmic context
}


@st.cache_data(ttl=3600)
def fetch_apod(date_str=None):
    """Fetch Astronomy Picture of the Day (APOD) data from NASA API"""
    params = {"api_key": API_KEY}
    if date_str:
        params["date"] = date_str
    
    response = requests.get(API_URL, params=params)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        raise Exception("Rate limit exceeded. Please try again later.")
    else:
        raise Exception(f"API request failed with status code {response.status_code}. Response: {response.text}")

# --- FUNCTION FOR SOLAR SYSTEM VISUALIZATION (Plotly) ---
def get_solar_system_plot(apod_body=None):
    """Generates an interactive 2D projection solar system plot with Plotly."""
    
    solar_system_data = {
        'Body': ['Sun', 'Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune'],
        'Radius (AU)': [0.0, 0.39, 0.72, 1.00, 1.52, 5.20, 9.58, 19.23, 30.10],
        'Size': [30, 8, 10, 12, 11, 25, 22, 18, 18]
    }
    df = pd.DataFrame(solar_system_data)
    
    df['theta'] = np.linspace(0, 2 * np.pi, len(df), endpoint=False)
    df['x'] = df['Radius (AU)'] * np.cos(df['theta'])
    df['y'] = df['Radius (AU)'] * np.sin(df['theta'])
    
    df['Highlight'] = df['Body'].apply(lambda x: 'APOD Focus' if x.lower() == apod_body.lower() else 'Solar System Body')
    
    fig = px.scatter(
        df, 
        x='x', 
        y='y', 
        size='Size', 
        color='Highlight', 
        color_discrete_map={'APOD Focus': '#FF0000', 'Solar System Body': '#808080'},
        hover_data={'Body': True, 'Radius (AU)': True, 'x': False, 'y': False, 'Size': False},
        title="Simplified Solar System Plane (Not to Scale)"
    )

    fig.update_traces(marker=dict(line=dict(width=1, color='Black')))
    fig.update_layout(
        xaxis_title="", yaxis_title="", showlegend=True,
        plot_bgcolor='black', paper_bgcolor='#0E1117', font_color='white', height=500
    )
    fig.update_xaxes(scaleanchor="y", scaleratio=1, showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(showgrid=False, zeroline=False, visible=False)
    
    return fig

# --- Main Streamlit UI ---

# --- Sidebar Controls ---

# 1. Manual Date Input
st.sidebar.markdown(
    """
    ## 📅 Choose a Date
    Enter a date below or select a solar event to explore.
    """
)

manual_date = st.sidebar.date_input(
    "Select Date:", 
    value="today", 
    max_value=date.today(),
    min_value=date(1995, 6, 16)
)
manual_date_str = manual_date.strftime("%Y-%m-%d")


st.sidebar.markdown("---")


# 2. Solar Event Selector
event_selection_key = st.sidebar.selectbox(
    "✨ Or Choose a Solar System Highlight:",
    options=list(SOLAR_APOD_DATES.keys()),
    index=0,
    help="Select a known Solar System APOD date to automatically load it."
)
selected_event_date_str = SOLAR_APOD_DATES[event_selection_key]


# 3. Determine the final date for fetching
if selected_event_date_str:
    fetch_date_str = selected_event_date_str
else:
    fetch_date_str = manual_date_str


# 4. Trigger Logic
if st.sidebar.button("🚀 Fetch APOD", use_container_width=True):
    st.session_state['fetch_trigger'] = fetch_date_str
    st.session_state['fetch_by_button'] = True
else:
    if 'fetch_trigger' not in st.session_state or st.session_state.get('last_selected_date') != fetch_date_str:
        st.session_state['fetch_trigger'] = fetch_date_str
        st.session_state['fetch_by_button'] = False
        
    st.session_state['last_selected_date'] = fetch_date_str

fetch_date = st.session_state.get('fetch_trigger')


# --- Main Content Area ---
st.title("🌌 NASA Astronomy Picture of the Day")
st.markdown("---")

if fetch_date:
    try:
        with st.spinner(f"Fetching APOD for *{fetch_date}*..."):
            data = fetch_apod(None if fetch_date == date.today().strftime("%Y-%m-%d") else fetch_date)
            
            title = data.get("title", "Untitled APOD")
            apod_date = data.get("date", "Unknown Date")
            explanation = data.get("explanation", "No detailed description provided for this picture.")
            img_url = data.get("url")
            hd_url = data.get("hdurl")

        if st.session_state.get('fetch_by_button', False):
            st.balloons()
            st.session_state['fetch_by_button'] = False

        ## Display APOD Content
        
        st.header(f"✨ {title}")
        st.caption(f"📅 Date: *{apod_date}*")
        st.markdown("---")

        col1, col2 = st.columns([7, 5]) 

        with col1:
            st.subheader("Media")
            media_type = data.get("media_type", "image")

            if media_type == "video":
                st.video(img_url)
                st.info(f"Today's APOD is a *Video*. If it doesn't load above, [Watch on NASA/YouTube]({img_url})")
            
            elif media_type == "image":
                try:
                    img_response = requests.get(img_url)
                    img_response.raise_for_status()
                    img = Image.open(BytesIO(img_response.content))
                    
                    st.markdown(
                        f'<div style="border: 2px solid #367c9c; border-radius: 8px; overflow: hidden;">',
                        unsafe_allow_html=True
                    )
                    st.image(img, caption=f"Viewed on {apod_date}", use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    if hd_url:
                        st.markdown(f"[🖼 Download HD Image]({hd_url})", unsafe_allow_html=True)

                except requests.exceptions.HTTPError as e:
                    st.error(f"Could not load image file from URL. Error: {e}")
                except Exception as e:
                    st.error(f"An error occurred while processing the image: {e}")
            
            else:
                st.warning(f"Unsupported media type: {media_type}. [View Content Here]({img_url})")

        with col2:
            st.subheader("Explanation")
            with st.expander("Read Full Description", expanded=True):
                st.markdown(explanation)
                
            st.markdown("*")
            st.markdown("Credit & Source: *NASA/APOD*")

        
        # -------------------------------------------------------------
        # SOLAR SYSTEM CONTEXT AND WORKING 3D LINK (FIXED LOGIC)
        # -------------------------------------------------------------

        # Refined keyword list for better accuracy
        solar_system_keywords = [
            'mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 
            'moon', 'sun', 'comet', 'asteroid', 'aurora', 
            'apollo', 'iss', 'viking', 'curiosity', 'cassini', 'voyager', 'juno', 'osiris' 
        ]
        
        # 1. Check if it's a Solar System APOD based on keywords
        apod_is_solar = any(keyword in title.lower() or keyword in explanation.lower() for keyword in solar_system_keywords)
        
        # 2. Final check: must be solar AND NOT in the exclusion list
        if apod_is_solar and apod_date not in EXCLUDE_DATES:
            st.markdown("---")
            st.subheader("🔭 Location Context: Our Solar System")

            # Try to extract the main body for highlighting
            main_body = 'Sun'
            for body in ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Earth', 'Moon']:
                if body.lower() in title.lower() or body.lower() in explanation.lower():
                    main_body = body
                    break

            # 1. Display Internal Plotly Visualization
            try:
                solar_fig = get_solar_system_plot(main_body)
                st.plotly_chart(solar_fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not generate solar system plot: {e}")
                
            st.markdown("---")

            # 2. Add External 3D Visualization Link (Using stable base URL)
            nasa_eyes_url = "https://eyes.nasa.gov/apps/solar-system/" 
            
            st.markdown("### 🚀 Explore the Location in 3D!")
            
            st.link_button(
                label="Click to View Solar System in NASA's Interactive 3D Model", 
                url=nasa_eyes_url,
                help=f"Opens the NASA Eyes on the Solar System website in a new tab. You may need to manually search for '{main_body}' there.",
                type="primary"
            )
            
            st.caption(f"You will be redirected to an external NASA website. You can manually search for *{main_body}* within the app.")
        
    except Exception as e:
        st.error(f"An error occurred while fetching the APOD: {e}")
        st.info("Please ensure the date is correctly formatted (YYYY-MM-DD) and not a future date.")







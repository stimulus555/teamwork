import streamlit as st
import requests
import random
import os

# --- Configuration ---
# Using the NASA Image and Video Library API for searching for images
NASA_API_SEARCH_URL = "https://images-api.nasa.gov/search"

# Streamlit App Setup
st.set_page_config(
    page_title="Random NASA Image Search",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to fetch a random image from the NASA Image and Video Library
# Uses Streamlit's cache feature to prevent unnecessary re-runs if inputs don't change.
# The search query is passed directly to the function to break the cache when the input changes.
@st.cache_data(show_spinner=False)
def get_random_nasa_image(query: str):
    """
    Fetches a random image URL, title, and description based on a search query 
    from the NASA Image and Video Library API.
    
    Returns a 3-tuple: (image_url, title, description). Returns (None, None, None) on failure.
    """
    st.info(f"Preparing to search for: *'{query}'*...")
    
    params = {
        'q': query,         
        'media_type': 'image', 
        'page_size': 100    # Larger pool for randomness
    }

    try:
        response = requests.get(NASA_API_SEARCH_URL, params=params, timeout=10)
        response.raise_for_status() 
        
        data = response.json()

        items = data.get('collection', {}).get('items', [])
        
        if not items:
            # Explicitly return the failure tuple
            return None, None, None

        # Select a random item from the results
        random_item = random.choice(items)
        
        # Extract metadata
        metadata = random_item.get('data', [{}])[0]
        title = metadata.get('title', 'Untitled NASA Image')
        description = metadata.get('description', 'No description available for this asset.')
        
        # Extract the direct image link (the first link that is of type 'image')
        links = random_item.get('links', [])
        image_link_obj = next((link for link in links if link.get('render') == 'image'), None)
        image_url = image_link_obj.get('href') if image_link_obj else None

        if not image_url:
             # Even if an item was found, the link might be missing, treat as failure
             return None, None, None
            
        return image_url, title, description

    except requests.exceptions.HTTPError as e:
        # Catch specific HTTP errors (404, 500, etc.)
        st.error(f"HTTP Error: Could not reach the NASA API. Status Code: {e.response.status_code}")
        return None, None, None
    except requests.exceptions.RequestException as e:
        # Catch network errors (timeout, connection refused)
        st.error(f"Connection Error: Failed to connect to NASA API. Details: {e}")
        return None, None, None
    except Exception as e:
        # Catch any unexpected parsing or logic errors
        st.error(f"An unexpected error occurred during data processing: {e}")
        return None, None, None


# --- Streamlit UI Layout ---
def main():
    st.title("🌌 NASA Image Randomizer")
    st.markdown("Pulls random, high-quality space images using the *NASA Image and Video Library API*.")
    
    # Text input for the search query
    search_query = st.sidebar.text_input(
        "Enter a search term (e.g., 'nebula', 'galaxy', 'apollo'):", 
        value="mars rover"
    ).strip() # .strip() ensures no leading/trailing spaces cause unnecessary re-runs

    # Ensure search_query is not empty
    if not search_query:
        st.warning("Please enter a valid search term.")
        return

    # Check if a search needs to be performed
    search_needed = st.sidebar.button("Generate New Image", use_container_width=True)
    
    # Initial run and button click logic combined
    if search_needed or 'image_data' not in st.session_state:
        # Use a spinner that covers the whole screen while fetching data
        with st.spinner(f'Fetching a random image for *{search_query}*...'):
            st.session_state.image_data = get_random_nasa_image(search_query)

    
    # Retrieve data fro

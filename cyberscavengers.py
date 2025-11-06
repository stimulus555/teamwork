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
def get_random_nasa_image(query="mars rover"):
    """
    Fetches a random image URL, title, and description based on a search query 
    from the NASA Image and Video Library API.
    """
    # 1. Define the API request parameters
    params = {
        'q': query,         # The search term (e.g., 'mars rover', 'nebula', 'galaxy')
        'media_type': 'image', # We only want image results
        'page_size': 100    # Requesting a larger page size to increase the randomness pool
    }

    try:
        # 2. Make the API call
        st.info(f"Searching NASA Image Library for: *'{query}'*...")
        response = requests.get(NASA_API_SEARCH_URL, params=params, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()

        # 3. Process the results
        items = data.get('collection', {}).get('items', [])
        
        if not items:
            st.warning(f"No results found for '{query}'. Try a different term.")
            return None, None, None

        # 4. Select a random item from the results
        random_item = random.choice(items)
        
        # Extract the image metadata (data array)
        metadata = random_item.get('data', [{}])[0]
        title = metadata.get('title', 'No Title Available')
        description = metadata.get('description', 'No description available.')
        
        # Extract the image link (links array). The first link is typically the preview image.
        links = random_item.get('links', [])
        image_url = links[0].get('href') if links and links[0].get('render') == 'image' else None

        # Fallback to the main asset collection link if a direct image link isn't immediately found.
        # Note: The 'links' array usually contains the direct image link for 'image' media types.
        if not image_url:
            st.error("Could not find a direct image link in the result structure.")
            return None, None, None
            
        return image_url, title, description

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from NASA API: {e}")
        return None, None, None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None, None, None


# --- Streamlit UI Layout ---
def main():
    st.title("🌌 NASA Image Randomizer")
    st.markdown("Pulls random, high-quality space images using the *NASA Image and Video Library API*.")
    
    # Text input for the user to change the search query
    search_query = st.sidebar.text_input(
        "Enter a search term (e.g., 'nebula', 'galaxy', 'apollo'):", 
        value="mars rover"
    )

    # State management for caching the image data
    if 'image_data' not in st.session_state:
        st.session_state.image_data = get_random_nasa_image(search_query)

    # Button to generate a new random image
    if st.sidebar.button("Generate New Image", use_container_width=True):
        st.session_state.image_data = get_random_nasa_image(search_query)

    
    image_url, title, description = st.session_state.image_data

    # Display the content in the main area
    st.header(title)
    
    if image_url:
        st.image(image_url, caption=f"Image from the NASA Image and Video Library - {title}", use_column_width=True)
    else:
        # Placeholder image if the API failed or returned no results
        st.markdown(
            """
            <div style='text-align: center; padding: 20px; border: 2px dashed #4B4B4B; border-radius: 10px; background-color: #1E1E1E;'>
                <h3 style='color: #FFD700;'>Image Not Ava

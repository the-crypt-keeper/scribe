import streamlit as st
import pandas as pd
import json
import sys
import math
from typing import List, Dict

@st.cache_data
def create_merged_dataframe(cleaner_data, prepare_data):
    # Extract relevant information from cleaner data
    cleaner_info = [{
        'idea_id': i + 1,
        'model': item.get('model', '').replace('openai/', ''),
        'method': item.get('title', ''),
    } for i, item in enumerate(cleaner_data)]

    # Create DataFrame from prepare data
    prepare_df = pd.DataFrame(prepare_data)

    # Create DataFrame from cleaner info
    cleaner_df = pd.DataFrame(cleaner_info)

    # Merge the DataFrames
    merged_df = pd.merge(prepare_df, cleaner_df, on='idea_id', how='left')

    return merged_df

@st.cache_resource
def load_cleaner_data(file_path):
    with open(file_path, 'r') as f:
        return [json.loads(line) for line in f]

def get_original_idea(cleaner_data: List[Dict], idea_id: int) -> Dict:
    return cleaner_data[idea_id-1]

@st.cache_resource
def load_prepare_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    st.set_page_config(layout="wide", page_title='World Builder Data Viewer')
    st.markdown("""
            <style>
                .block-container {
                        padding-top: 2rem;
                        padding-bottom: 0rem;
                        padding-left: 1rem;
                        padding-right: 1rem;
                }
            </style>
            """, unsafe_allow_html=True)   

    cleaner_path = sys.argv[1]
    prepare_path = sys.argv[2]

    cleaner_data = load_cleaner_data(cleaner_path)
    prepare_data = load_prepare_data(prepare_path)

    # Create and cache the merged dataframe
    merged_df = create_merged_dataframe(cleaner_data, prepare_data)

    # Initialize session state for selected world and current page
    if 'selected_world' not in st.session_state:
        st.session_state.selected_world = 0
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0

    # Create two columns for the layout
    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("World List")
        
        # Pagination
        items_per_page = 10
        total_pages = math.ceil(len(merged_df) / items_per_page)
        current_page = st.session_state.current_page
        
        # Ensure the selected world is visible
        selected_page = st.session_state.selected_world // items_per_page
        if selected_page != current_page:
            current_page = selected_page
            st.session_state.current_page = current_page

        # Previous and Next page buttons
        col1_1, col1_2, col1_3 = st.columns([1, 3, 1])
        with col1_1:
            if st.button('< Prev Page') and current_page > 0:
                st.session_state.current_page -= 1
                st.experimental_rerun()
        with col1_2:
            st.write(f"Page {current_page + 1} of {total_pages}")
        with col1_3:
            if st.button('Next Page >') and current_page < total_pages - 1:
                st.session_state.current_page += 1
                st.experimental_rerun()

        # Display worlds for the current page
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(merged_df))
        for index in range(start_idx, end_idx):
            world = merged_df.iloc[index]
            col1_1, col1_2 = st.columns([3, 1])
            with col1_1:
                if index == st.session_state.selected_world:
                    st.markdown(f"**{index + 1}. {world['world_name']}**")
                else:
                    st.write(f"{index + 1}. {world['world_name']}")
            with col1_2:
                if st.button('Jump', key=f'jump_{index}'):
                    st.session_state.selected_world = index
                    st.experimental_rerun()

    with col2:
        st.subheader("World Details")
        selected_world = merged_df.iloc[st.session_state.selected_world]
        
        col2_1, col2_2, col2_3 = st.columns([1, 3, 1])
        with col2_1:
            if st.button('< Previous') and st.session_state.selected_world > 0:
                st.session_state.selected_world -= 1
                st.experimental_rerun()
        with col2_2:
            st.write(f"**{selected_world['world_name']}**")
        with col2_3:
            if st.button('Next >') and st.session_state.selected_world < len(merged_df) - 1:
                st.session_state.selected_world += 1
                st.experimental_rerun()

        for key, value in selected_world.items():
            if key != 'world_name':
                st.write(f"**{key.capitalize()}:** {value}")

        with st.expander('DEBUG: Original Idea'):
            original_idea = get_original_idea(cleaner_data, selected_world['idea_id'])
            st.json(original_idea)

if __name__ == "__main__":
    main()

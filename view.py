import streamlit as st
import pandas as pd
import json
import sys
import math
import os
import random
from typing import List, Dict

@st.cache_data
def create_merged_dataframe(cleaner_data, prepare_data):
    # Extract relevant information from cleaner data
    cleaner_info = [{
        'idea_id': i + 1,
        'model': item.get('model', '').replace('openai/', ''),
        'method': item.get('vars', {}).get('title'),
    } for i, item in enumerate(cleaner_data)]

    # Create DataFrame from prepare data
    prepare_df = pd.DataFrame(prepare_data)

    # Create DataFrame from cleaner info
    cleaner_df = pd.DataFrame(cleaner_info)

    # Merge the DataFrames
    merged_df = pd.merge(prepare_df, cleaner_df, on='idea_id', how='left')

    # Shuffle the DataFrame
    merged_df = merged_df.sample(frac=1, random_state=random.randint(1, 1000)).reset_index(drop=True)

    return merged_df

def get_original_idea(cleaner_data: List[Dict], idea_id: int) -> Dict:
    return cleaner_data[idea_id-1]

@st.cache_resource
def load_prepare_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

@st.cache_resource
def load_reactions():
    if os.path.exists('reactions.json'):
        with open('reactions.json', 'r') as f:
            return json.load(f)
    return {}

def save_reactions(reactions):
    with open('reactions.json', 'w') as f:
        json.dump(reactions, f)

REACTIONS = {
    'star': '⭐',
    'flame': '🔥',
    'poop': '💩',
    'thumbs_up': '👍',
    'thumbs_down': '👎'
}

def main():
    st.set_page_config(page_title='World Builder Data Viewer')
    st.markdown("""
            <style>
                .block-container {
                        padding-top: 2rem;
                        padding-bottom: 0rem;
                        padding-left: 1rem;
                        padding-right: 1rem;
                }
                html {
                    font-size: 1.5em;
                }
            </style>
            """, unsafe_allow_html=True)   

    raw_prepare_data = load_prepare_data(sys.argv[1])

    # Create and cache the merged dataframe
    merged_df = create_merged_dataframe(raw_prepare_data['ideas'], raw_prepare_data['worlds'])

    # Load reactions
    reactions = load_reactions()

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
        items_per_page = 6
        total_pages = math.ceil(len(merged_df) / items_per_page)
        current_page = st.session_state.current_page

        # Previous and Next page buttons
        col1_1, col1_2, col1_3 = st.columns([1, 1, 1])
        with col1_1:
            if st.button('⬅️') and current_page > 0:
                st.session_state.current_page -= 1
                current_page = st.session_state.current_page
        with col1_3:
            if st.button('➡️') and current_page < total_pages - 1:
                st.session_state.current_page += 1
                current_page = st.session_state.current_page        
        with col1_2:
            st.write(f"#{current_page + 1} of {total_pages}")

        # Display worlds for the current page
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(merged_df))
        for index in range(start_idx, end_idx):
            world = merged_df.iloc[index]
            col1_1, col1_2 = st.columns([4, 1])
            with col1_1:
                if index == st.session_state.selected_world:
                    if st.button(f"**{index + 1}. {world['world_name']}**", key=f'world_{index}', use_container_width=True, type="primary"):
                        st.session_state.selected_world = index
                        st.rerun()
                else:
                    if st.button(f"**{index + 1}. {world['world_name']}**", key=f'world_{index}', use_container_width=True):
                        st.session_state.selected_world = index
                        st.rerun()
            with col1_2:
                world_reactions = reactions.get(str(world['id']), {})
                st.write(''.join([REACTIONS[r] for r in world_reactions if world_reactions[r]]))

    with col2:
        st.subheader("World Details")
        selected_world = merged_df.iloc[st.session_state.selected_world]
        
        col2_1, col2_2, col2_3 = st.columns([1, 2, 1])
        with col2_1:
            if st.button('< Previous') and st.session_state.selected_world > 0:
                st.session_state.selected_world -= 1                                    
                # Ensure the selected world is visible when changed from detail panel
                selected_page = st.session_state.selected_world // items_per_page
                if selected_page != current_page:
                    st.session_state.current_page = selected_page
                st.rerun()
                
        with col2_2:
            st.write(f"**{selected_world['world_name']}**")
        with col2_3:
            if st.button('Next >') and st.session_state.selected_world < len(merged_df) - 1:
                st.session_state.selected_world += 1                    
                # Ensure the selected world is visible when changed from detail panel
                selected_page = st.session_state.selected_world // items_per_page
                if selected_page != current_page:
                    st.session_state.current_page = selected_page
                st.rerun()                

        for key, value in selected_world.items():
            if key not in ['id', 'world_name']:
                st.markdown(f"**{key.replace('_',' ').title()}:** {value}")

        world_reactions = reactions.get(str(selected_world['id']), {})
        cols = st.columns(5)
        reaction_changed = False
        for i, (reaction, emoji) in enumerate(REACTIONS.items()):
            with cols[i]:
                new_value = st.checkbox(f"{emoji}", value=world_reactions.get(reaction, False), key=f"reaction_{selected_world['id']}_{reaction}")
                if new_value != world_reactions.get(reaction, False):
                    reaction_changed = True
                    if str(selected_world['id']) not in reactions:
                        reactions[str(selected_world['id'])] = {}
                    reactions[str(selected_world['id'])][reaction] = new_value
        if reaction_changed:
            save_reactions(reactions)
            st.rerun()

        with st.expander('DEBUG: Original Idea'):
            original_idea = get_original_idea(raw_prepare_data['ideas'], selected_world['idea_id'])
            st.json(original_idea)

if __name__ == "__main__":
    main()

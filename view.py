import streamlit as st
import pandas as pd
import json
import sys
import os
import random
import glob
from typing import List, Dict

@st.cache_data
def create_merged_dataframe(cleaner_data, prepare_data):
    # Extract relevant information from cleaner data
    cleaner_info = [{
        'idea_id': item.get('idea_id'),
        'model': item.get('model', '').split('/')[-1] if '/' in item.get('model', '') else item.get('model', ''),
        'method': item.get('vars', {}).get('title'),
    } for i, item in enumerate(cleaner_data)]

    # Create DataFrame from prepare data
    prepare_df = pd.DataFrame(prepare_data)

    # Create DataFrame from cleaner info
    cleaner_df = pd.DataFrame(cleaner_info)

    # Merge the DataFrames
    merged_df = pd.merge(prepare_df, cleaner_df, on='idea_id', how='left')

    return merged_df

def get_original_idea(cleaner_data: List[Dict], idea_id: int) -> Dict:
    for idea in cleaner_data:
        if idea.get('idea_id') == idea_id:
            return idea
    return {}  # Return an empty dict if no matching idea is found

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

@st.cache_data
def get_available_images():
    return glob.glob('flux/world*.png')

def find_world_by_id(merged_df, world_id):
    matching_worlds = merged_df[merged_df['id'].str.startswith(world_id)]
    return matching_worlds.index[0] if not matching_worlds.empty else None

REACTIONS = {
    'star': '⭐',
    'flame': '🔥',
    'poop': '💩',
    'thumbs_up': '👍',
    'thumbs_down': '👎',
    'lol': '😂'
}

def main():
    st.set_page_config(page_title='World Builder Data Viewer', layout="wide")
    st.markdown("""
            <style>
                .block-container {
                        padding-top: 2rem;
                        padding-bottom: 0rem;
                        padding-left: 1rem;
                        padding-right: 1rem;
                        margin-top: 1rem;
                }
                html {
                    font-size: 1.2em;
                }
            </style>
            """, unsafe_allow_html=True)   

    raw_prepare_data = load_prepare_data(sys.argv[1])

    # Create and cache the merged dataframe
    merged_df = create_merged_dataframe(raw_prepare_data['ideas'], raw_prepare_data['worlds'])

    # Load reactions
    reactions = load_reactions()

    # Initialize session state for selected world
    if 'selected_world' not in st.session_state:
        st.session_state.selected_world = random.randint(0, len(merged_df) - 1)
        if 'id' in st.query_params:
            world_id = st.query_params['id']
            found_index = find_world_by_id(merged_df, world_id)
            if found_index is not None:
                st.session_state.selected_world = found_index

    # Display world name as heading
    title_world_name = st.empty()

    # Row of buttons
    col0, col1, col2, col3 = st.columns(4)
    with col0:
        share_link = st.empty()
    with col1:
        if st.button('⬅️ Previous', disabled=(st.session_state.selected_world == 0)):
            st.session_state.selected_world -= 1
    with col2:
        if st.button('🎲 Random'):
            st.session_state.selected_world = random.randint(0, len(merged_df) - 1)
    with col3:
        if st.button('Next ➡️', disabled=(st.session_state.selected_world == len(merged_df) - 1)):
            st.session_state.selected_world += 1

    # Display world name as heading
    selected_world = merged_df.iloc[st.session_state.selected_world]
    world_id = selected_world['id'][0:8]
    title_world_name.write(f"<h1>{selected_world['world_name']}<sub>{world_id}</sub></h1>", unsafe_allow_html=True)
    share_link.write(f"<a href='/?id={selected_world['id']}'>Share This World</a>", unsafe_allow_html=True)       
    
    # Select and display an image
    available_images = get_available_images()
    world_images = [img for img in available_images if f"{selected_world['id']}" in img]
    if world_images:
        image_path = random.choice(world_images)
        st.image(image_path)
    else:
        st.warning(f"No images found for World ID {selected_world['id']}")

    # Reactions
    with st.expander('Reactions', expanded=False):
        world_reactions = reactions.get(str(selected_world['id']), {})
        cols = st.columns(6, gap='small', vertical_alignment='center')
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
            
    # Display world details
    detail_order = ['concept', 'description', 'twist', 'sensory', 'story_seeds', 'challenges_opportunities']
    for key in detail_order:
        if key in selected_world:
            if key == 'story_seeds':
                text = f"**{key.replace('_',' ').title()}:**\n"
                for seed in selected_world[key]:
                    text += f"- {seed}\n"
                st.markdown(text)
            else:
                st.markdown(f"**{key.replace('_',' ').title()}:** {selected_world[key]}")

    # Display model and method in two columns
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Model:** {selected_world['model']}")
    with col2:
        st.markdown(f"**Method:** {selected_world['method']}")

    with st.expander('DEBUG: Original Idea'):
        original_idea = get_original_idea(raw_prepare_data['ideas'], selected_world['idea_id'])
        st.json(original_idea)

if __name__ == "__main__":
    main()

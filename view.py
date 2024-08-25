import streamlit as st
import pandas as pd
import json
import sys
import os
import random
from typing import List, Dict

@st.cache_data
def create_merged_dataframe(cleaner_data, prepare_data):
    # Extract relevant information from cleaner data
    cleaner_info = [{
        'idea_id': i + 1,
        'model': item.get('model', '').split('/')[-1] if '/' in item.get('model', '') else item.get('model', ''),
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
                    font-size: 1.5em;
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
        st.session_state.selected_world = 0

    selected_world = merged_df.iloc[st.session_state.selected_world]

    # Display world name as heading
    st.title(selected_world['world_name'])

    # Row of buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button('⬅️ Previous') and st.session_state.selected_world > 0:
            st.session_state.selected_world -= 1
            st.rerun()
    with col2:
        if st.button('🎲 Random'):
            st.session_state.selected_world = random.randint(0, len(merged_df) - 1)
            st.rerun()
    with col3:
        if st.button('Next ➡️') and st.session_state.selected_world < len(merged_df) - 1:
            st.session_state.selected_world += 1
            st.rerun()

    # Display world details
    for key, value in selected_world.items():
        if key not in ['id', 'idea_id', 'world_name']:
            st.markdown(f"**{key.replace('_',' ').title()}:** {value}")

    # Reactions
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

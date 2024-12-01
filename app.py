import streamlit as st
import pandas as pd
import json
import sys
import os
import random
import glob
from typing import List, Dict
from base import SQLiteScribe

@st.cache_resource
def load_scribe(project_name):
    return SQLiteScribe(project=project_name)

@st.cache_data
def create_merged_dataframe(scribe):
    worlds = scribe.find(key='world')
    df = pd.DataFrame([
        {
            'id': id,
            'world_name': payload['world_name'],
            'concept': payload['concept'],
            'description': payload['description'],
            'twist': payload['twist'],
            'sensory': payload['sensory'],
            'challenges_opportunities': payload['challenges_opportunities'],
            'story_seeds': payload['story_seeds'],
            'model': meta.get('model', ''),
            'method': meta.get('method', '')
        }
        for _, id, payload, meta in worlds
    ])
    return df

def find_world_by_id(merged_df, world_id):
    matching_worlds = merged_df[merged_df['id'].str.startswith(world_id)]
    return matching_worlds.index[0] if not matching_worlds.empty else None

@st.cache_data
def get_available_images(scribe):
    return [id for _, id, _, _ in scribe.find(key='image')]

def main():
    st.set_page_config(page_title='Altered Worlds', layout="wide")
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

    project_name = sys.argv[1] if len(sys.argv) > 1 else 'default_project'
    scribe = load_scribe(project_name)

    # Create and cache the merged dataframe
    merged_df = create_merged_dataframe(scribe)

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
    world_id = selected_world.name[0:8]
    title_world_name.write(f"<h1>{selected_world['world_name']}<sub>{world_id}</sub></h1>", unsafe_allow_html=True)
    share_link.write(f"<a href='/?id={selected_world.name}'>Share This World</a>", unsafe_allow_html=True)       
    
    # Select and display an image
    available_images = get_available_images(scribe)
    if selected_world.name in available_images:
        image_data, _ = scribe.load('image', selected_world.name)
        st.image(image_data)
    else:
        st.warning(f"No image found for World ID {selected_world.name}")
            
    # Display world details
    detail_order = ['concept', 'description', 'twist', 'sensory', 'challenges_opportunities', 'story_seeds']
    for key in detail_order:
        if key in selected_world:
            if key == 'story_seeds':
                text = f"**{key.replace('_',' ').title()}:**\n"
                for seed in selected_world[key]:
                    text += f"- {seed}\n"
                st.markdown(text)
            else:
                st.markdown(f"**{key.replace('_',' ').title()}:**\n{selected_world[key]}")

    # Display model and method in two columns
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Model:** {selected_world['model']}")
    with col2:
        st.markdown(f"**Method:** {selected_world['method']}")

if __name__ == "__main__":
    main()

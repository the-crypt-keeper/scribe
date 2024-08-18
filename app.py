import streamlit as st
import pandas as pd
import json
import sys
from typing import List, Dict
from st_aggrid import AgGrid, GridUpdateMode
from st_aggrid.grid_options_builder import GridOptionsBuilder

@st.cache_resource
def create_merged_dataframe(cleaner_data, prepare_data):
    # Extract relevant information from cleaner data
    cleaner_info = [{
        'idea_id': i + 1,
        'model': item.get('model', '').replace('openai/', ''),
        'method': item.get('method', ''),
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
    st.set_page_config(layout="wide")
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
    st.title("World Builder Data Viewer")

    cleaner_path = sys.argv[1]
    prepare_path = sys.argv[2]

    cleaner_data = load_cleaner_data(cleaner_path)
    prepare_data = load_prepare_data(prepare_path)

    # Create and cache the merged dataframe
    merged_df = create_merged_dataframe(cleaner_data, prepare_data)

    # Display the merged DataFrame using AgGrid
    gb = GridOptionsBuilder.from_dataframe(merged_df)
    gb.configure_selection(selection_mode='single', use_checkbox=False)
    gb.configure_column("concept", header_name="Concept", width="300")
    gb.configure_column("twist", header_name="Twist", width="300")
    gb.configure_column("description", header_name="Description")
    gb.configure_column("idea_id", header_name="Idea ID", hide=True)
    gb.configure_column("id", hide=True)    
    gridOptions = gb.build()

    grid_response = AgGrid(
        merged_df,
        gridOptions=gridOptions,
        height=400,
        width='100%',
        data_return_mode='AS_INPUT',
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
    )

    selected_row = grid_response['selected_rows'][0] if grid_response['selected_rows'] else None

    # Display selected record details
    if selected_row:
        st.subheader("Selected Record Details:")
        selected_row_dict = {k: v for k, v in selected_row.items() if k != '_selectedRowNodeInfo'}
        st.json(selected_row_dict)
        
        with st.expander('DEBUG: Original Ideal'):
            original_idea = get_original_idea(cleaner_data, selected_row['idea_id'])
            st.json(original_idea)

if __name__ == "__main__":
    main()

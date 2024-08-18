import streamlit as st
import pandas as pd
import json
import sys
from typing import List, Dict

@st.cache_resource
def load_cleaner_data(file_path):
    with open(file_path, 'r') as f:
        return [json.loads(line) for line in f]

def get_original_idea(cleaner_data: List[Dict], idea_id: int) -> Dict:
    return next((item for item in cleaner_data if item.get('idea_id') == idea_id), None)

@st.cache_resource
def load_prepare_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    st.set_page_config(layout="wide")
    st.title("World Builder Data Viewer")

    cleaner_path = sys.argv[1]
    prepare_path = sys.argv[2]

    cleaner_data = load_cleaner_data(cleaner_path)
    prepare_data = load_prepare_data(prepare_path)

    # Extract relevant information from cleaner data
    cleaner_info = [{
        'idea_id': i + 1,
        'model': item.get('model', ''),
        'method': item.get('method', ''),
    } for i, item in enumerate(cleaner_data)]

    # Create DataFrame from prepare data
    prepare_df = pd.DataFrame(prepare_data)

    # Create DataFrame from cleaner info
    cleaner_df = pd.DataFrame(cleaner_info)

    # Merge the DataFrames
    merged_df = pd.merge(prepare_df, cleaner_df, on='idea_id', how='left')

    # Add a checkbox column as the first column
    merged_df.insert(0, 'Select', False)

    # Display the merged DataFrame with checkboxes
    # Exclude 'idea_id' from the displayed columns
    display_columns = [col for col in merged_df.columns if col != 'idea_id']
    
    edited_df = st.data_editor(
        merged_df[display_columns],
        height=int(st.get_option('deprecation.showPyplotGlobalUse') * 0.5),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Select",
                help="Select this row",
                default=False,
            )
        },
        disabled=merged_df.columns.drop(['Select', 'idea_id']).tolist(),
    )

    # Get the selected row
    selected_row = edited_df[edited_df['Select']].iloc[0] if not edited_df[edited_df['Select']].empty else None

    # Display selected record details
    if selected_row is not None:
        st.subheader("Selected Record Details:")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Prepared Data")
            selected_row_dict = selected_row.drop('Select').to_dict()
            st.json(selected_row_dict)
        
        with col2:
            st.subheader("Original Idea")
            original_idea = get_original_idea(cleaner_data, selected_row['idea_id'])
            if original_idea:
                st.json(original_idea)
            else:
                st.write("Original idea not found.")

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import json
import sys

@st.cache_resource
def load_cleaner_data(file_path):
    with open(file_path, 'r') as f:
        return [json.loads(line) for line in f]

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

    # Display the merged DataFrame
    res = st.dataframe(merged_df, height=int(st.get_option('deprecation.showPyplotGlobalUse') * 0.5), use_container_width=True)

    # Add row selection functionality
    print(res)
    selected_indices = res.selected_rows()
    if selected_indices:
        selected_row = merged_df.iloc[selected_indices[0]]
        st.subheader("Selected Record Details:")
        st.json(selected_row.to_dict())

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import json

@st.cache_resource
def load_cleaner_data(file_path):
    with open(file_path, 'r') as f:
        return [json.loads(line) for line in f]

@st.cache_resource
def load_prepare_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    st.title("World Builder Data Viewer")

    cleaner_path = st.text_input("Enter path to cleaner output:")
    prepare_path = st.text_input("Enter path to prepare output:")

    if cleaner_path and prepare_path:
        cleaner_data = load_cleaner_data(cleaner_path)
        prepare_data = load_prepare_data(prepare_path)

        # Extract relevant information from cleaner data
        cleaner_info = [{
            'idea_id': i + 1,
            'model': item.get('clean_model', ''),
            'method': 'cleaner'
        } for i, item in enumerate(cleaner_data)]

        # Create DataFrame from prepare data
        prepare_df = pd.DataFrame(prepare_data)

        # Create DataFrame from cleaner info
        cleaner_df = pd.DataFrame(cleaner_info)

        # Merge the DataFrames
        merged_df = pd.merge(prepare_df, cleaner_df, on='idea_id', how='left')

        # Display the merged DataFrame
        st.dataframe(merged_df)

if __name__ == "__main__":
    main()

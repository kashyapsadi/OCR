import streamlit as st
import easyocr
import pandas as pd
from PIL import Image
import numpy as np

# Function to fix Hindi numbers to English
def fix_hindi_nums(text):
    hindi_to_eng = str.maketrans('०१२३४५६७८९', '0123456789')
    return text.translate(hindi_to_eng)

st.set_page_config(page_title="Final Land Parser", layout="wide")
st.title("🚜 Fixed Land Record Parser")

@st.cache_resource
def load_model():
    return easyocr.Reader(['hi', 'en'])

reader = load_model()
uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, width=400)
    
    if st.button("Final Fix & Extract"):
        img_array = np.array(img)
        width, height = img.size
        results = reader.readtext(img_array)
        
        rows = []
        for (bbox, text, prob) in results:
            text = fix_hindi_nums(text).strip()
            x_center = (bbox[0][0] + bbox[1][0]) / 2
            y_center = (bbox[0][1] + bbox[2][1]) / 2
            rows.append({'text': text, 'x': x_center, 'y': y_center})

        df_raw = pd.DataFrame(rows)
        # 1. Group by Rows (Y-axis) with a bigger margin to avoid split rows
        df_raw['row_group'] = (df_raw['y'] / 35).round() 
        
        final_data = []
        for _, group in df_raw.groupby('row_group'):
            row_dict = {"Khata": "", "Khesra": "", "Rakba": "", "Decimal": ""}
            for _, item in group.iterrows():
                val = item['text']
                x = item['x']
                
                # STRICT COLUMN LOGIC based on image width percentage
                x_pct = (x / width) * 100
                
                if x_pct < 25: # Left side
                    if val.isdigit() and len(val) < 4: row_dict["Khata"] = val
                elif 25 <= x_pct < 50: # Mid-left
                    if val.isdigit() and len(val) >= 3: row_dict["Khesra"] = val
                elif 50 <= x_pct < 75: # Mid-right
                    if "." in val or "कठ्ठा" in val: row_dict["Rakba"] = val
                elif x_pct >= 75: # Far right
                    if "." in val or val.replace(".","").isdigit(): row_dict["Decimal"] = val
            
            # Sirf tab add karein agar Khesra ya Khata mil gaya ho
            if row_dict["Khata"] or row_dict["Khesra"]:
                final_data.append(row_dict)

        st.table(pd.DataFrame(final_data))

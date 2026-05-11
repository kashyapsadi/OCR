import streamlit as st
import easyocr
import pandas as pd
from PIL import Image
import numpy as np
import re

def fix_numbers(text):
    hindi_to_eng = str.maketrans('०१२३४५६७८९', '0123456789')
    t = text.translate(hindi_to_eng).replace(" ", "")
    return t.strip('.')

st.set_page_config(page_title="Land Parser Pro", layout="wide")
st.title("📑 Smart Land Record Parser (Dash/Dot Fix)")

@st.cache_resource
def load_model():
    return easyocr.Reader(['hi', 'en'], gpu=False)

reader = load_model()
uploaded_file = st.file_uploader("Document upload karein...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    width, height = img.size
    st.image(img, width=400)
    
    if st.button("Extract Data (Global Symbol Fix)"):
        with st.spinner('Parsing...'):
            img_array = np.array(img)
            results = reader.readtext(img_array)
            
            data_points = []
            for (bbox, text, prob) in results:
                clean_text = fix_numbers(text)
                x_center = (bbox[0][0] + bbox[1][0]) / 2
                y_center = (bbox[0][1] + bbox[2][1]) / 2
                if clean_text:
                    data_points.append({'text': clean_text, 'x': x_center, 'y': y_center})

            df_raw = pd.DataFrame(data_points)
            df_raw['row'] = (df_raw['y'] / 38).round()
            
            final_table = []
            for _, group in df_raw.groupby('row'):
                row_dict = {"Khata": "", "Khesra": "", "Rakba": "", "Decimal": ""}
                sorted_group = group.sort_values('x')
                
                for _, item in sorted_group.iterrows():
                    val = item['text']
                    x_pct = (item['x'] / width) * 100
                    
                    # 1. RAKBA LOGIC (Dots ya Dashes dono ke liye)
                    # Agar string mein '-' hai ya 2 se zyada dots hain
                    if "-" in val or val.count('.') >= 2:
                        row_dict["Rakba"] = val
                    
                    # 2. DECIMAL LOGIC (Ekdot aur right side mein)
                    elif val.count('.') == 1:
                        if x_pct > 65: # Page ke right side mein hai toh Decimal
                            row_dict["Decimal"] = val
                        else: # Agar middle mein hai toh Rakba ho sakta hai
                            row_dict["Rakba"] = val
                            
                    # 3. BASIC NUMBERS
                    elif val.isdigit():
                        if x_pct < 30: 
                            row_dict["Khata"] = val
                        elif 30 <= x_pct < 60: 
                            row_dict["Khesra"] = val

                if row_dict["Khesra"] or row_dict["Khata"]:
                    final_table.append(row_dict)

            st.table(pd.DataFrame(final_table))

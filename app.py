import streamlit as st
import easyocr
import pandas as pd
from PIL import Image
import numpy as np

def fix_numbers(text):
    hindi_to_eng = str.maketrans('०१२३४५६७८९', '0123456789')
    # Space hatana aur characters clean karna
    t = text.translate(hindi_to_eng).replace(" ", "").replace(",", ".")
    # Agar text ke end mein dot ho toh hata dein
    return t.strip('.')

st.set_page_config(page_title="Land Parser Final", layout="wide")
st.title("📑 Smart Land Record Parser")

@st.cache_resource
def load_model():
    return easyocr.Reader(['hi', 'en'], gpu=False)

reader = load_model()
uploaded_file = st.file_uploader("Document upload karein...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, width=400)
    
    if st.button("Extract Data (Multi-Dot Fix)"):
        with st.spinner('Reading document...'):
            img_array = np.array(img)
            results = reader.readtext(img_array)
            
            data_points = []
            for (bbox, text, prob) in results:
                clean_text = fix_numbers(text)
                x_center = (bbox[0][0] + bbox[1][0]) / 2
                y_center = (bbox[0][1] + bbox[2][1]) / 2
                if clean_text: # Khali text ignore karein
                    data_points.append({'text': clean_text, 'x': x_center, 'y': y_center})

            df_raw = pd.DataFrame(data_points)
            # Row grouping
            df_raw['row'] = (df_raw['y'] / 38).round()
            
            final_table = []
            for _, group in df_raw.groupby('row'):
                row_dict = {"Khata": "", "Khesra": "", "Rakba": "", "Decimal": ""}
                sorted_group = group.sort_values('x')
                
                for _, item in sorted_group.iterrows():
                    val = item['text']
                    dot_count = val.count('.')
                    
                    # 1. RAKBA LOGIC (2 ya 3 dots)
                    if dot_count >= 2:
                        row_dict["Rakba"] = val
                    
                    # 2. DECIMAL LOGIC (Strictly 1 dot)
                    elif dot_count == 1:
                        # Agar x-position page ke right side mein hai toh Decimal pakka hai
                        row_dict["Decimal"] = val
                            
                    # 3. NUMBERS (No dots)
                    elif val.isdigit():
                        if len(val) <= 3: 
                            row_dict["Khata"] = val
                        else: 
                            row_dict["Khesra"] = val

                # Row tabhi add karein jab koi solid data mile
                if row_dict["Khata"] or row_dict["Khesra"]:
                    final_table.append(row_dict)

            st.table(pd.DataFrame(final_table))

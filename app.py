import streamlit as st
import easyocr
import pandas as pd
from PIL import Image
import numpy as np

# Hindi numbers ko English mein convert karne ke liye
def fix_numbers(text):
    hindi_to_eng = str.maketrans('०१२३४५६७८९', '0123456789')
    return text.translate(hindi_to_eng).replace(" ", "")

st.set_page_config(page_title="Land Parser Pro", layout="wide")
st.title("🚜 Land Record Parser (Decimal Fixed)")

@st.cache_resource
def load_model():
    return easyocr.Reader(['hi', 'en'], gpu=False)

reader = load_model()
uploaded_file = st.file_uploader("Document upload karein...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    width, height = img.size
    st.image(img, width=400)
    
    if st.button("Extract Clean Data"):
        with st.spinner('Processing...'):
            img_array = np.array(img)
            results = reader.readtext(img_array)
            
            data_points = []
            for (bbox, text, prob) in results:
                clean_text = fix_numbers(text)
                x_center = (bbox[0][0] + bbox[1][0]) / 2
                y_center = (bbox[0][1] + bbox[2][1]) / 2
                data_points.append({'text': clean_text, 'x': x_center, 'y': y_center})

            df_raw = pd.DataFrame(data_points)
            # Row grouping logic (30-40 pixels ka gap)
            df_raw['row'] = (df_raw['y'] / 35).round()
            
            final_table = []
            for _, group in df_raw.groupby('row'):
                row_dict = {"Khata": "", "Khesra": "", "Rakba": "", "Decimal": ""}
                
                for _, item in group.iterrows():
                    val = item['text']
                    # X-Coordinate percentage (Width ka kitna % hai)
                    x_pct = (item['x'] / width) * 100
                    
                    # 1. Khata (Ekdum Left)
                    if x_pct < 20:
                        if val.isdigit(): row_dict["Khata"] = val
                    
                    # 2. Khesra (Left-Middle)
                    elif 20 <= x_pct < 45:
                        if val.isdigit(): row_dict["Khesra"] = val
                    
                    # 3. Rakba (Middle-Right) - Isme hamesha 0.X.X jaisa format hota hai
                    elif 45 <= x_pct < 75:
                        if "." in val: row_dict["Rakba"] = val
                    
                    # 4. Decimal (Extreme Right) - Page ke aakhri 25% hisse mein
                    elif x_pct >= 75:
                        # Sirf wohi number jo page ke ekdum kone mein hain
                        row_dict["Decimal"] = val

                if row_dict["Khesra"] or row_dict["Khata"]:
                    final_table.append(row_dict)

            st.table(pd.DataFrame(final_table))

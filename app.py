import streamlit as st
import easyocr
import pandas as pd
from PIL import Image
import numpy as np

st.set_page_config(page_title="Land Record Extractor", layout="wide")
st.title("📊 Land Record to Excel Converter")

@st.cache_resource
def load_model():
    return easyocr.Reader(['hi', 'en'])

reader = load_model()

uploaded_file = st.file_uploader("Document upload karein...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", width=400)
    
    if st.button("Extract Table"):
        with st.spinner('Data extract ho raha hai...'):
            img_array = np.array(image)
            # detail=1 coordinates ke liye zaroori hai
            results = reader.readtext(img_array, detail=1)
            
            # Hum data ko structure karne ke liye lists banayenge
            all_data = []
            for (bbox, text, prob) in results:
                all_data.append({
                    'text': text,
                    'x': bbox[0][0],
                    'y': bbox[0][1]
                })
            
            # Logic: Jo text ek horizontal line mein hain unhe ek row mein group karna
            # Is document mein numbers headers ke niche hain
            khata_list = []
            khesra_list = []
            rakba_list = []
            decimal_list = []

            for i, item in enumerate(all_data):
                txt = item['text'].replace(" ", "")
                # Khata detection (e.g., 86, 109)
                if txt in ["86", "109"] or (txt.isdigit() and len(txt) <= 3 and item['x'] < 200):
                    khata_list.append(txt)
                # Khesra detection (usually 4 digits)
                elif txt.isdigit() and len(txt) >= 4:
                    khesra_list.append(txt)
                # Rakba detection (contains dots like 0.4.7)
                elif "." in txt and len(txt.split('.')) >= 2 and "0." in txt:
                    rakba_list.append(txt)
                # Decimal detection
                elif "." in txt and len(txt) > 4 and item['x'] > 500:
                    decimal_list.append(txt)

            # Sabse kam length wali list ke barabar table banana
            min_len = min(len(khata_list), len(khesra_list), len(rakba_list))
            
            structured_data = []
            for i in range(min_len):
                structured_data.append({
                    "Khata No": khata_list[i] if i < len(khata_list) else "",
                    "Khesra No": khesra_list[i] if i < len(khesra_list) else "",
                    "Rakba": rakba_list[i] if i < len(rakba_list) else "",
                    "Decimal": decimal_list[i] if i < len(decimal_list) else ""
                })

            df = pd.DataFrame(structured_data)
            
            if not df.empty:
                st.subheader("✅ Extracted Data (Excel Format)")
                st.table(df) # Bilkul aapki image jaisa format
                
                # Download button
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("Download as CSV", csv, "land_data.csv", "text/csv")
            else:
                st.error("Data theek se detect nahi hua. Please clear photo use karein.")

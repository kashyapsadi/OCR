import streamlit as st
import easyocr
import pandas as pd
from PIL import Image
import numpy as np

st.set_page_config(page_title="Accurate Land Parser", layout="wide")
st.title("🎯 Accurate Land Record Extractor")

@st.cache_resource
def load_model():
    return easyocr.Reader(['hi', 'en'])

reader = load_model()

uploaded_file = st.file_uploader("Document upload karein...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", width=500)
    
    if st.button("Fix & Extract Data"):
        with st.spinner('Rows align ho rahi hain...'):
            img_array = np.array(image)
            results = reader.readtext(img_array, detail=1)
            
            # Step 1: Raw data nikalna
            data_points = []
            for (bbox, text, prob) in results:
                # y_center nikalna taaki alignment sahi ho
                y_center = (bbox[0][1] + bbox[2][1]) / 2
                data_points.append({
                    'text': text,
                    'x': bbox[0][0],
                    'y': y_center
                })

            # Step 2: Y-axis grouping (Ek hi line wale text ko ek group mein dalna)
            df_raw = pd.DataFrame(data_points)
            # 15-20 pixels ka margin dete hain row alignment ke liye
            df_raw['row'] = (df_raw['y'] / 20).round() 
            
            structured_rows = []
            for row_id, group in df_raw.groupby('row'):
                row_text = " ".join(group.sort_values('x')['text'].values)
                
                # Logic: Agar line mein koi kaam ka number hai
                text_list = group.sort_values('x')['text'].tolist()
                
                # Hum yahan check kar rahe hain ki row mein data hai ya sirf header
                if any(char.isdigit() for char in "".join(text_list)):
                    structured_rows.append(text_list)

            # Step 3: Column Sorting
            # Is image mein 4-5 main columns hain. 
            # Hum x-position ke hisab se inhe dabba mein dalenge.
            final_table = []
            for r in structured_rows:
                row_dict = {"Khata": "", "Khesra": "", "Rakba": "", "D": ""}
                for item in r:
                    # Yahan hum x-coordinate aur text pattern se decide karenge
                    val = item.replace(" ", "")
                    if "खाता" in val: continue
                    
                    if len(val) <= 3 and val.isdigit(): row_dict["Khata"] = val
                    elif len(val) >= 4 and val.isdigit(): row_dict["Khesra"] = val
                    elif "." in val and "0." in val: row_dict["Rakba"] = val
                    elif "." in val and len(val) > 4: row_dict["D"] = val
                
                if row_dict["Khesra"]: # Khesra zaroori hai row valid hone ke liye
                    final_table.append(row_dict)

            df_final = pd.DataFrame(final_table)
            
            if not df_final.empty:
                st.subheader("✅ Aligned Table")
                st.table(df_final)
                
                csv = df_final.to_csv(index=False).encode('utf-8-sig')
                st.download_button("Download Correct Excel", csv, "fixed_land_data.csv")
            else:
                st.error("Data detect nahi hua. Pattern match nahi ho raha.")

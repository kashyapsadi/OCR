import streamlit as st
import easyocr
import pandas as pd
from PIL import Image
import numpy as np

st.set_page_config(page_title="Land Doc Parser", layout="wide")

st.title("🚜 Land Document Smart Parser")
st.write("Image se Khata, Khesra aur Rakba ka table banayein")

@st.cache_resource
def load_model():
    # Hindi aur English dono scripts enable hain
    return easyocr.Reader(['hi', 'en'])

reader = load_model()

uploaded_file = st.file_uploader("Document ki photo upload karein...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Document", width=500)
    
    if st.button("Extract Table Data"):
        with st.spinner('AI data process kar raha hai...'):
            img_array = np.array(image)
            results = reader.readtext(img_array)
            
            # extracted_data mein hum (text, x, y) store karenge
            raw_data = []
            for (bbox, text, prob) in results:
                raw_data.append({
                    'text': text,
                    'x': bbox[0][0],
                    'y': bbox[0][1]
                })

            # Logic: Hum specific keywords dhoond rahe hain
            final_rows = []
            temp_row = {"Khata": "", "Khesra": "", "Rakba": "", "D_Value": ""}
            
            # Simple Column logic (Experimental)
            # Hum text ki vertical position (y) se rows align karte hain
            for item in raw_data:
                txt = item['text']
                # Keywords checking
                if "खाता" in txt or "86" in txt or "109" in txt: # Example mapping
                    temp_row["Khata"] = txt
                elif "खेसरा" in txt or any(char.isdigit() for char in txt):
                    # Agar bada digit hai toh wo Khesra ho sakta hai
                    if len(txt) >= 4: temp_row["Khesra"] = txt
                elif "रकवा" in txt or "." in txt:
                    temp_row["Rakba"] = txt
                
                # Jab row bhar jaye (logic adjustment needed based on actual image)
                if len(temp_row["Khata"]) > 0 and len(temp_row["Khesra"]) > 0:
                    final_rows.append(temp_row.copy())
                    temp_row = {"Khata": "", "Khesra": "", "Rakba": "", "D_Value": ""}

            # DataFrame banana
            df = pd.DataFrame(raw_data) # Filhal raw data dikhate hain for accuracy
            
            st.subheader("Detected Text Blocks:")
            st.dataframe(df[['text']]) 
            
            # CSV Download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Excel/CSV", csv, "land_records.csv", "text/csv")

import streamlit as st
import easyocr
from PIL import Image
import numpy as np

# Page configuration
st.set_page_config(page_title="Hindi-English OCR Tool", layout="centered")

st.title("📸 Image to Text Converter")
st.subheader("Hindi, English aur Hinglish support ke saath")

# Model ko cache kar rahe hain taaki baar-baar load na ho
@st.cache_resource
def load_model():
    # 'hi' for Hindi, 'en' for English
    return easyocr.Reader(['hi', 'en'], gpu=False) 

reader = load_model()

# File uploader
uploaded_file = st.file_uploader("Apni image upload karein...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Image dikhana
    image = Image.open(uploaded_file)
    st.image(image, caption='Uploaded Image', use_column_width=True)
    
    st.write("---")
    
    with st.spinner('Text extract ho raha hai... Please wait...'):
        # Image ko array mein convert karna
        img_array = np.array(image)
        
        # OCR perform karna
        results = reader.readtext(img_array)
        
        # Text ko ek saath jodna
        full_text = ""
        for (bbox, text, prob) in results:
            full_text += text + " "
        
        if full_text:
            st.success("Extraction Complete!")
            st.text_area("Extracted Text:", full_text, height=250)
            
            # Download button
            st.download_button(
                label="Download as Text File",
                data=full_text,
                file_name="extracted_text.txt",
                mime="text/plain"
            )
        else:
            st.warning("Koi text nahi mila. Please clear image use karein.")

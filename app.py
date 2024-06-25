import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import sqlite3

def image_to_text(path):

  input_img = Image.open(path)

  #Converting Image to Array Format
  img_arr = np.array(input_img)

  reader = easyocr.Reader(['en'])
  text = reader.readtext(img_arr, detail = 0)

  return text, input_img


def extracted_text(texts):

  extrd_dict = {"NAME" : [],
                "DESIGNATION" : [],
                "COMPANY NAME" : [],
                "CONTACT" : [],
                "EMAIL" : [],
                "WEBSITE" : [],
                "ADDRESS" : [],
                "PINCODE" : []}

  extrd_dict["NAME"].append(texts[0])
  extrd_dict["DESIGNATION"].append(texts[1])

  for i in range(2, len(texts)):
    if texts[i].startswith("+") or (texts[i].replace("-", "").isdigit() and "-" in texts[i]):
      extrd_dict["CONTACT"].append(texts[i])

    elif "@" in texts[i] and ".com" in texts[i]:
      extrd_dict["EMAIL"].append(texts[i])

    elif "WWW" in texts[i] or "www" in texts[i] or "Www" in texts[i] or "wWw" in texts[i] or "wwW" in texts [i]:
      small = texts[i].lower()
      extrd_dict["WEBSITE"].append(small)

    elif "TamilNadu" in texts[i] or "Tamil Nadu" in texts[i] or texts[i].isdigit():
      extrd_dict["PINCODE"].append(texts[i])

    elif re.match(r'^[A-Za-z]', texts[i]):
     extrd_dict["COMPANY NAME"].append(texts[i])

    else:
      remove_colon = re.sub(r'[,;]','', texts[i])
      extrd_dict["ADDRESS"].append(remove_colon)

  for key, value in extrd_dict.items():
    if len(value) > 0 :
      concatenate = " ".join(value)
      print(concatenate)
      extrd_dict[key] = [concatenate]

    else:
      extrd_dict[key] = ["NA"]


  return extrd_dict


#Streamlit Part

st.set_page_config(layout = "wide")
st.title("EXTRACTING BUSINESS CARD DATA WITH 'OCR'")

with st.sidebar:

  select = option_menu("Main Menu", ["Home", "Upload & Modify", "Delete"])

if select == "Home":
  st.markdown("### :blue[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")



  st.write(
            "### :green[**About :**] Bizcard is a Python application designed to extract information from business cards.")
  st.write(
            '### The main purpose of Bizcard is to automate the process of extracting key details from business card images, such as the name, designation, company, contact information, and other relevant data. By leveraging the power of OCR (Optical Character Recognition) provided by EasyOCR, Bizcard is able to extract text from the images.')


elif select == "Upload & Modify":
  img = st.file_uploader("Upload the Image", type = ["png", "jpg", "jpeg"])

  if img is not None:
    st.image(img, width = 300)

    text_img, input_img = image_to_text(img)

    text_dict = extracted_text(text_img)

    if text_dict:
      st.success("Text is Extracted Successfully")

    df = pd.DataFrame(text_dict)

    #Converting Image to Bytes

    Image_bytes = io.BytesIO()
    input_img.save(Image_bytes, format = "PNG")

    image_data = Image_bytes.getvalue()

    #Creating Dictionary

    data = {"IMAGE": [image_data]}
    df_1 = pd.DataFrame(data)

    concat_df = pd.concat([df, df_1], axis = 1)
    st.dataframe(concat_df)

    button_1 = st.button("Save", use_container_width = True)
    if button_1:
      mydb = sqlite3.connect("bizcardx.db")
      cursor = mydb.cursor()

      #Table Creation

      create_table_query = """CREATE TABLE IF NOT EXISTS bizcardx (NAME VARCHAR(225),
                                                                    DESIGNATION VARCHAR(225),
                                                                    COMPANY_NAME VARCHAR(225),
                                                                    CONTACT VARCHAR(225),
                                                                    EMAIL VARCHAR(225),
                                                                    WEBSITE TEXT,
                                                                    ADDRESS TEXT,
                                                                    PINCODE VARCHAR(225),
                                                                    IMAGE TEXT)"""

      cursor.execute(create_table_query)
      mydb.commit()

      #Insert Query

      insert_query = """INSERT INTO bizcardx (NAME, DESIGNATION, COMPANY_NAME, CONTACT, EMAIL, WEBSITE, ADDRESS, PINCODE, IMAGE)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""

      data = concat_df.values.tolist()[0]

      cursor.execute(insert_query, data)
      mydb.commit()

      st.success("Saved Successfully")

  method = st.radio("Select the Method", ["None", "Preview", "Modify"])

  if method == "None":
    st.write("")

  if method == "Preview":
    mydb = sqlite3.connect("bizcardx.db")
    cursor = mydb.cursor()

    #Select Query
    select_query = "SELECT * FROM bizcardx"

    cursor.execute(select_query)
    result = cursor.fetchall()
    mydb.commit()

    result_df = pd.DataFrame(result, columns = ("NAME", "DESIGNATION", "COMPANY NAME", "CONTACT", "EMAIL", "WEBSITE",
                                                "ADDRESS", "PINCODE", "IMAGE"))

    result_df

  elif method == "Modify":
    mydb = sqlite3.connect("bizcardx.db")
    cursor = mydb.cursor()

    #Select Query
    select_query = "SELECT * FROM bizcardx"

    cursor.execute(select_query)
    result = cursor.fetchall()
    mydb.commit()

    result_df = pd.DataFrame(result, columns = ("NAME", "DESIGNATION", "COMPANY NAME", "CONTACT", "EMAIL", "WEBSITE",
                                                "ADDRESS", "PINCODE", "IMAGE"))

    result_df

    col1, col2 = st.columns(2)
    with col1:
      selected_name = st.selectbox("Select the Name", result_df["NAME"])

    df_3 = result_df[result_df["NAME"] == selected_name]

    df_4 = df_3.copy()

    col1, col2 = st.columns(2)
    with col1:
      m_name = st.text_input("NAME",df_3["NAME"].unique()[0])
      m_designation = st.text_input("DESIGNATION",df_3["DESIGNATION"].unique()[0])
      m_company_name = st.text_input("COMPANY NAME",df_3["COMPANY NAME"].unique()[0])
      m_contact = st.text_input("CONTACT",df_3["CONTACT"].unique()[0])
      m_email = st.text_input("EMAIL",df_3["EMAIL"].unique()[0])

      df_4["NAME"] = m_name
      df_4["DESIGNATION"] = m_designation
      df_4["COMPANY NAME"] = m_company_name
      df_4["CONTACT"] = m_contact
      df_4["EMAIL"] = m_email

    with col2:
      m_website = st.text_input("WEBSITE",df_3["WEBSITE"].unique()[0])
      m_address = st.text_input("ADDRESS",df_3["ADDRESS"].unique()[0])
      m_pincode = st.text_input("PINCODE",df_3["PINCODE"].unique()[0])
      m_image = st.text_input("IMAGE",df_3["IMAGE"].unique()[0])

      df_4["WEBSITE"] = m_website
      df_4["ADDRESS"] = m_address
      df_4["PINCODE"] = m_pincode
      df_4["IMAGE"] = m_image

    st.dataframe(df_4)

    col1, col2 = st.columns(2)
    with col1:
      button_3 = st.button("Modify", use_container_width= True)

    if button_3:
      mydb = sqlite3.connect("bizcardx.db")
      cursor = mydb.cursor()

      cursor.execute(f"Delete from bizcardx WHERE NAME = '{selected_name}'")
      mydb.commit()

      #Insert Query

      insert_query = """INSERT INTO bizcardx (NAME, DESIGNATION, COMPANY_NAME, CONTACT, EMAIL, WEBSITE, ADDRESS, PINCODE, IMAGE)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""

      data = df_4.values.tolist()[0]

      cursor.execute(insert_query, data)
      mydb.commit()

      st.success("Modified Successfully")


elif select == "Delete":
  mydb = sqlite3.connect("bizcardx.db")
  cursor = mydb.cursor()

  col1, col2 = st.columns(2)
  with col1:
    select_query = "SELECT NAME FROM bizcardx"

    cursor.execute(select_query)
    result1 = cursor.fetchall()
    mydb.commit()

    names = []

    for i in result1:
      names.append(i[0])

    name_select = st.selectbox("Select the Name", names)


  with col2:
    select_query = f"SELECT DESIGNATION FROM bizcardx WHERE NAME = '{name_select}'"

    cursor.execute(select_query)
    result2 = cursor.fetchall()
    mydb.commit()

    designations = []

    for j in result2:
      designations.append(j[0])

    designation_select = st.selectbox("Select the Name", designations)

  if name_select and designation_select:
    col1, col2, col3 = st.columns(3)

    with col1:
     st.write(f"Selected Name : {name_select}")
     st.write(f"Selected Designation : {designation_select}")

    with col2:
     st.write("")
     st.write("")
     st.write("")
     st.write("")
     st.write("")
     st.write("")

     remove = st.button("Delete", use_container_width= True)

     if remove:
      cursor.execute(f"DELETE FROM bizcardx  WHERE NAME = '{name_select}' AND DESIGNATION = '{designation_select}'")
      mydb.commit()

      st.warning("Deleted")




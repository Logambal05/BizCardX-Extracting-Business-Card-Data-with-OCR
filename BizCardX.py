# Importing The Necessary Libraries
from IPython.display import display
from streamlit_option_menu import option_menu
from PIL import Image
import io
import numpy as np
import pandas as pd
import streamlit as st
import pymysql
import re
import easyocr

# Page Config
layout="wide"
initial_sidebar_state="expanded"
primaryColor= "#96B3A4"
backgroundColor= "#B5D5C5"
secondaryBackgroundColor= "#7AA08D"
textColor= "#0A0A0A"
font="serif"

# SQL Connection
myconnection = pymysql.connect(host = '127.0.0.1',user='root',passwd='Logi@2908')
cur = myconnection.cursor()
cur.execute("CREATE DATABASE IF NOT EXISTS BizCardX_Extracting")
cur = myconnection.cursor()
cur.execute("USE BizCardX_Extracting")

# def function for image formating
def formating(results):
    result = []
    for i in results:
        a = i.split(',')
        for j in a:
            if j != '':
                b = j.split(';')
                for k in b:
                    result.append(k.strip())
    return result

# function for extracting data from text
def extracing_data(formated_data):
    datas={'Name': [],'Company Name':[],'Designation': [],'Email': [],'Contact Number': [],'Address':[],
           'City':[],'State':[],'PinCode':[],'Card Holder':[],'Website':[]}
    
   

    datas['Name']= [formated_data[0]]
    datas['Designation'] = [formated_data[1]]
    datas['Card Holder'] = [formated_data[0]]
    

    for i in formated_data[2:]:
        if i.startswith('+') or re.match(r"\d{3}-\d{3}-\d{4}", i):
            datas['Contact Number']=[' & '.join(datas['Contact Number'] + [i])]
        elif re.match(r"[^@]+@[^@]+\.[^@]+", i):
            datas['Email'].append(i)
        elif i.endswith('.com') or i.lower().startswith('www'):
            i=i.lower()
            datas['Website']=[''.join(datas['Website'] + [i])]
            if i.startswith('www') and not i.startswith('www.'):
                 datas['Website'] = [website.replace('www', 'www.') for website in datas['Website']]
            if i.endswith('com') and not i.endswith('.com'):
                 datas['Website'] = [website.replace('com', '.com') for website in datas['Website']]
        elif i.startswith('Ta') or i.isdigit():
            datas['PinCode'] = ''.join(char for char in i if char.isdigit())
            if i.startswith('Ta'):
                datas['State'] = ''.join(char for char in i if char.isalpha())
        elif i.startswith('1') or i.startswith('St') or  i.isdigit() and i.isalpha():
            datas['Address']=[' '.join(datas['Address'] + [i])]
            address_next = True
        elif address_next:
            datas['City'].append(i)
            address_next = False 
        else:
            datas['Company Name'] = [' '.join(datas['Company Name'] + [i])]
    return datas

# Option Menu
with st.sidebar:
        SELECT = option_menu(None,
                options = ["🏡Home","🌍Data Management","🔚Exit"],
                default_index=0,
                orientation="vertical",
                styles={"container": {"width": "90%"},
                        "icon": {"color": "white", "font-size": "18px"},
                        "nav-link": {"font-size": "18px"}})
        

if SELECT == "🏡Home":
    st.header("CardSnap: Business Card Intelligence Platform!")
    st.write("""Introducing BizCardX, a cutting-edge Streamlit application designed to seamlessly streamline the extraction of 
             business card data through advanced Optical Character Recognition (OCR) technology. Users can effortlessly upload 
             business card images, gaining instant access to vital details such as company names, cardholder information, and 
             contact details. Emphasizing robust data security and user authentication, BizCardX ensures safe data storage while 
             providing simplified management through its intuitive Streamlit User Interface. Immerse yourself in an efficient, 
             secure, and user-friendly solution for effortlessly managing and organizing business card information with BizCardX.""")
    
    st.subheader("**Features**")
    st.write("**Easy Extraction:**  BizCardX's interface with the easyOCR (Optical Character Recognition) library makes it simple to extract information from business cards by uploading an image.")
    st.write("**Hierarchical Presentation:**  To provide a concise and well-organized summary, the extracted data is tastefully displayed next to the submitted image.")
    st.write("**Comprehensive Information:** Extracted information comprises the name of the company, the name of the cardholder, the designation, the contact details, and the address.")
    st.write("**User-Friendly GUI**: For a seamless experience, navigate and interact with the user-friendly graphical interface.")

if SELECT == "🌍Data Management":
    Option = st.sidebar.selectbox("**Select Any One Option:**", (None,'Data Acquisition And DB Insertion','Update Database Records','Perform Database Record Deletion'))
    if Option == 'Data Acquisition And DB Insertion':
        image = st.file_uploader(label="upload image",type=['png', 'jpg', 'jpeg'], label_visibility="hidden")
        if image is not None:
            # Image Displaying
            input_image=Image.open(image)
            st.image(input_image,width=350,caption = "The Image You Have Provided")
            
            with st.spinner("Please Wait! Your Image Is Converting Into Text"):

           
                reader = easyocr.Reader(['en'])
                result=reader.readtext(np.array(input_image))
                image_to_text=[]
                for i in result:
                    text=i[1]
                    image_to_text.append(text)
                
                # image to text
                extracted_text = image_to_text
            
                # formating the text
                formated_img = formating(extracted_text)

                final_data = extracing_data(formated_img)
                st.write(final_data) 
            
            upload = st.button("Upload Data To DataBase!")
            if upload:
                # extracting data from text
                final_data = extracing_data(formated_img)
                df = pd.DataFrame(final_data)

                # converting the image into bytes
                image_bytes = io.BytesIO()
                input_image.save(image_bytes, format='PNG')
                image_data = image_bytes.getvalue()
                data = {"Image": [image_data]}
                df_1 = pd.DataFrame(data)
                concat_df = pd.concat([df, df_1], axis=1)
                st.dataframe(concat_df)

                # SQL
                cur.execute("CREATE TABLE  IF NOT EXISTS Bizcardx (Name VARCHAR(255),Company_Name VARCHAR(255),Designation VARCHAR(255),Email VARCHAR(255),Contact_Number VARCHAR(255) ,Address VARCHAR(255), City VARCHAR(255) , State VARCHAR(255), PinCode INT ,Card_Holder VARCHAR(255),Website VARCHAR(255),Image LONGBLOB)")
                sql = "insert into Bizcardx(Name,Company_Name,Designation,Email,Contact_Number,Address,City,State,PinCode,Card_Holder,Website,Image) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"   
                for i in range(0,len(concat_df)):
                    cur.execute(sql,tuple(concat_df.iloc[i]))
                    myconnection.commit()

                st.success("✅Data Uploaded Successfully!!!") 

    if Option == 'Update Database Records':
            st.subheader("Check Individual Data And Modify As Needed")
            col1,col2=st.columns(2)
            with col1:
                # list of names
                cur.execute("SELECT Name FROM bizcardx")
                result = cur.fetchall()
                names_list = [row[0] for row in result]
                selected_name = st.selectbox("Select Names", names_list,key="names")
                cur.execute(f"SELECT Name,Company_Name,Designation,Email,Contact_Number,Address,City,State,PinCode,Card_Holder,Website FROM bizcardx WHERE Name ='{selected_name}'")
                result1 = cur.fetchall()
                if result1:
                    # Editing 
                    Tab = pd.DataFrame(result1, columns=['Name', 'Company_Name', 'Designation', 'Email', 'Contact_Number', 'Address', 'City', 'State', 'PinCode', 'Card_Holder', 'Website'])
                    transposed_df = Tab.T
                    st.dataframe(transposed_df)

                    st.subheader("Modify Data And Update It In Database")
                    company_Name = st.text_input("Company_Name", Tab["Company_Name"][0])
                    designation = st.text_input("Designation", Tab["Designation"][0])
                    card_Holder = st.text_input("Card_Holder", Tab["Card_Holder"][0])
                    email = st.text_input("Email", Tab["Email"][0])
                    contact_number = st.text_input("Contact_Number", Tab["Contact_Number"][0])
                    address = st.text_input("Address", Tab["Address"][0])
                    city = st.text_input("City", Tab["City"][0])
                    state = st.text_input("State", Tab["State"][0])
                    pinCode = st.text_input("PinCode", Tab["PinCode"][0])
                    website = st.text_input("Website", Tab["Website"][0])

                   
                    if st.button("Commit Changes In DB"):
                        cur.execute(f"UPDATE Bizcardx SET Company_Name = '{company_Name}', Designation = '{designation}',Card_Holder='{card_Holder}',Contact_Number ='{contact_number}', Email = '{email}',Address = '{address}',City = '{city}',State = '{state}' ,PinCode = '{pinCode}',Website='{website}' WHERE Name = '{selected_name}'")
                        myconnection.commit()
                        st.success("✅Changes Commited Successfully!!")

                    if st.button("View The Updated Data"):
                        cur.execute(f"SELECT name,company_name,card_holder,designation,contact_number,email,website,address,city,state,pincode FROM bizcardx WHERE Name ='{selected_name}'")
                        updated_df = pd.DataFrame(cur.fetchall(),columns=["Name","Company_Name","Card_Holder","Designation","Contact_Number","Email","Website","Address","City","State","PinCode"])
                        df = updated_df.T
                        st.dataframe(df)
                    
    if Option == 'Perform Database Record Deletion':
        st.subheader("Checks the Indivudal Data Before Deleting The Datas")
        col1,col2=st.columns(2)
        with col1:
            st.subheader("Deletion On Field")
            # list of names
            cur.execute("SELECT Name FROM bizcardx")
            result = cur.fetchall()
            names_list = [row[0] for row in result]
            selected_name = st.selectbox("Select Names", names_list,key="names1")
            cur.execute(f"SELECT Name,Company_Name,Designation,Email,Contact_Number,Address,City,State,PinCode,Card_Holder,Website FROM bizcardx WHERE Name ='{selected_name}'")
            result1 = cur.fetchall()
            # deletion
            if st.button("Delete The Field"):
                cur.execute(f"DELETE FROM Bizcardx WHERE Name = '{selected_name}' LIMIT 1;")
                myconnection.commit()
                st.success("✅Field Successfully Deleted!")

            if st.button("View Data Post-Deletion Of The Specific Column"):
                cur.execute(f"SELECT name,company_name,card_holder,designation,contact_number,email,website,address,city,state,pincode FROM bizcardx")
                updated_df = pd.DataFrame(cur.fetchall(),columns=["Name","Company_Name","Card_Holder","Designation","Contact_Number","Email","Website","Address","City","State","PinCode"])
                df = updated_df.T
                st.dataframe(df)

if SELECT == "🔚Exit": 
    st.header("OverView Of The UI")
    st.write("""The project aims to create a Streamlit app for **managing** and **extracting** business card information using a **database system**, **easyOCR**, and **Python**. 
             Key components include an easy-to-use **Streamlit UI**, effective **image processing**, and meticulous **architectural planning**. The application simplifies 
             **uploading**, **extracting**, and **managing data** with direct capabilities for **reading**, **updating**, and **deleting entries**. Maintaining 
             **code organization** and **clarity** is essential for a clear and easy-to-use tool for **managing** and **extracting** information from business cards.""")
    but=st.button("EXIT!")
    if but:
        st.success("Thank You For Utilising This Platform. I Hope The Business Card You Uploaded Here Provided You With Some Insightful Data!❤️")
   
                    
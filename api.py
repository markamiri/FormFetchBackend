# backend/app.py
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from fillpdf import fillpdfs
import os
import pytz
from sendgrid import SendGridAPIClient
import base64
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from dotenv import load_dotenv
import os
import uuid
from database import init_db, insert_link, get_link
from datetime import datetime, timedelta
import fitz  # PyMuPDF
import json
app = Flask(__name__)
init_db()

start_time = datetime.utcnow()

CORS(app)  # Allow cross-origin requests from frontend

load_dotenv()  # Load environment variables from .env file

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
from_email = os.getenv("EMAIL_FROM")
to_email = os.getenv("EMAIL_TO")

# Prints the form values 
@app.route('/api/submit-form', methods=['POST'])
def submit_form():

    now = datetime.now()
    formatted_date = now.strftime("%Y/%m/%d")  # e.g. "2025/06/18"

    day_of_month = now.day                         # e.g. 18
    month_number = now.month                       # e.g. 6
    year = now.year                                # e.g. 2025
    hour = now.strftime("%I")                      # 12-hour format, zero-padded
    minute = now.strftime("%M")
    am_pm = now.strftime("%p")                     # 'AM' or 'PM'
    time_of_day = f"{hour}:{minute}"               # e.g. "03:42"
    data = request.json
    print("✅ Final Form Data (Received on Backend):", data)
    address = data["formData"]["address"]
    ownership_selection = data["ownershipSelection"]

    proxy_data = data["proxyData"]
    selected_rep = proxy_data.get("selectedRepresentative")
    proxy_a = proxy_data.get("proxyA", "")
    proxy_b = proxy_data.get("proxyB", "")
    voting_sections = data.get("votingSections", [])

    initials = data.get("initials", "")
    signature = data.get("signature", "")
    print("Is this working")
    print(initials)
    print(signature)


    # Decide how to fill the names
    if selected_rep:
        name_21 = selected_rep
        name_23 = ""
    else:
        name_21 = proxy_a
        name_23 = proxy_b

    
    # TODO: You can now use this data to fill a PDF here.
    accept = "Yes"
    decline = "No"
    data_dict = {
        #"form1[0].page1[0].full[0].left[0].header[0].navigationBtns[0].printBlankForm[0]" :"1",
        #"form1[0].page1[0].full[0].left[0].header[0].navigationBtns[0].printForm[0]" :"2",
        #"form1[0].page1[0].full[0].left[0].header[0].navigationBtns[0].backToForm[0]":"3",
        #"form1[0].page1[0].full[0].left[0].proxy[0].proxyID[0].PIN[0]" :"4",
        "form1[0].page1[0].full[0].left[0].proxy[0].addressTo[0].to[0]" : str(address),
        "form1[0].page1[0].full[0].left[0].proxy[0].people[0].registeredOwner[0]": "Yes" if ownership_selection == 1 else "Off",
        "form1[0].page1[0].full[0].left[0].proxy[0].people[0].agentRegisteredOwner[0]": "Yes" if ownership_selection == 2 else "Off",
        "form1[0].page1[0].full[0].left[0].proxy[0].people[0].morgagee[0]": "Yes" if ownership_selection == 3 else "Off",
        "form1[0].page1[0].full[0].left[0].proxy[0].people[0].agentOfMorgagee[0]": "Yes" if ownership_selection == 4 else "Off",
        "form1[0].page1[0].full[0].left[0].sweared[0].dayOfMonth[0]" : str(day_of_month),
        "form1[0].page1[0].full[0].left[0].sweared[0].month[0]" : str(month_number),
        "form1[0].page1[0].full[0].left[0].sweared[0].year[0]" : str(year),
        "form1[0].page1[0].full[0].left[0].sweared[0].timeOfDay[0]" : time_of_day,
        "form1[0].page1[0].full[0].left[0].sweared[0].am[0]": "Yes" if am_pm == "AM" else "Off",
        "form1[0].page1[0].full[0].left[0].sweared[0].pm[0]": "Yes" if am_pm == "PM" else "Off",
        #"form1[0].page1[0].full[0].right[0].tearawayPortion[0].PINoptional[0]" :"16",
        #"form1[0].page1[0].full[0].right[0].tearawayPortion[0].nameOfProxyGiver[0]" :"17",
        #"form1[0].page1[0].full[0].right[0].tearawayPortion[0].condoAddress[0]" :"18",
        "form1[0].page1[0].full[0].right[0].tearawayPortion[0].signature[0]" :signature,
        "form1[0].page2[0].authorizers[0].date[0]" : formatted_date,
        "form1[0].page2[0].authorizers[0].b[0].Table1[0].Row1[0].name[0]": name_21,

        "form1[0].page2[0].authorizers[0].b[0].Table1[0].Row1[0].addr[0]" :"22",
        "form1[0].page2[0].authorizers[0].b[0].Table1[0].Row2[0].name[0]": name_23,

        #"form1[0].page2[0].authorizers[0].b[0].Table1[0].Row2[0].addr[0]" :"24",
        #"form1[0].page2[0].body[0].candidates[0].option1[0].signature[0]" :"",
        #"form1[0].page2[0].body[0].candidates[0].option2[0].signature[0]" :"",
        #"form1[0].page2[0].body[0].candidates[0].option1[0].notAuthorize[0]": "Off",
        #"form1[0].page2[0].body[0].candidates[0].option2[0].votes[0]": "Off",
        #"form1[0].page2[0].body[0].candidates[0].option3[0].instruct[0]": "Off",
        #"form1[0].page2[0].body[0].candidates[0].option3[0].signature[0]" :"",
        #"form1[0].page2[0].body[0].one[0].instructBoard[0]" :"Off",
        #"form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[0].name[0]" :"32",
        #"form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[0].addr[0]" :"33",
        #"form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[0].emailaddr[0]" :"34",
        #"form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[0].dd[0]" :"35",
        #"form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[1].name[0]":"36",
        #"form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[1].addr[0]":"37",
        #"form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[1].emailaddr[0]" :"38",
        #"form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[1].dd[0]" :"39",
        #"form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[2].name[0]" :"40",
        #"form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[2].addr[0]" :"41",
        #"form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[2].emailaddr[0]"  :"42",
        #"form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[2].dd[0]" :"43",
        #"form1[0].page2[0].body[0].one[0].b[0].navigBtns[0].add[0]" :"44",
        #"form1[0].Page2[1].PIN[0]" :"45",
        #"form1[0].Page2[1].PINoptional[0]" :"46",
        #"form1[0].page2[0].body[0].two[0].instruct1[0]" :"Off",
        #"form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[0].name[0]" :"48",
        #"form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[0].addr[0]" :"49",
        #"form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[0].emailaddr[0]" :"50",
        #"form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[0].dd[0]" :"51",
        #"form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[1].name[0]" :"52",
        #"form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[1].addr[0]":"53",
        #"form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[1].emailaddr[0]" :"54",
        #"form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[1].dd[0]" :"55",
        #"form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[2].name[0]" :"56",
        #"form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[2].addr[0]" :"57",
        #"form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[2].emailaddr[0]" :"58",
        #"form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[2].dd[0]" :"59",
        #"form1[0].page2[0].body[0].two[0].b[0].navigBtns[0].add[0]" :"60",
        #"form1[0].page2[0].body[0].three[0].voting[0]" :"Off",
        #"form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[0].yes[0]#0" :"63",
        #"form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[0].no[0]#0" :"64",
        #"form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[0].emailaddr[0]" :"65",
        #"form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[0].dd[0]" :"66",
        
        #"form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[1].yes[0]":"68",
        #"form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[1].no[0]":"69",
        #"form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[1].emailaddr[0]" :"70",
        #"form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[1].dd[0]" :"71",
        #"form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[0].yes[0]#1" :"73",
        #"form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[0].no[0]#1" :"74",
        #"form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[2].emailaddr[0]" :"75",
        #"form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[2].dd[0]" :"76",
        #"form1[0].page2[0].body[0].three[0].b[0].navigBtns[0].add[0]" :"77",
        #"form1[0].page2[0].body[0].four[0].instructProxy[0]" :"Off",
        #"form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[0].inFavour[0]#0" :"80",
        #"form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[0].against[0]#0" :"81",
        #"form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[0].emailaddr[0]" :"82",
        #"form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[0].dd[0]" :"83",
                
        #"form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[1].inFavour[0]" :"85",
        #"form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[1].against[0]" :"86",
        #"form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[1].emailaddr[0]" :"87",
        #"form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[1].dd[0]" :"88",


        #"form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[0].inFavour[0]#1" :"90",
        #"form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[0].against[0]#1" :"91",
        #"form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[2].emailaddr[0]" :"92",
        #"form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[2].dd[0]" :"93",
        #"form1[0].page2[0].body[0].four[0].b[0].navigBtns[0].add[0]" :"94",
        #"form1[0].page2[0].body[0].vote[0].renominate[0]" :"95",
        #"form1[0].page2[0].body[0].vote[0].b[0].Table1[0].Row1[0].addr[0]" :"96",
        #"form1[0].page2[0].body[0].vote[0].b[0].Table1[0].Row1[0].name[0]" :"97",
        #"form1[0].page2[0].body[0].vote[0].b[0].Table1[0].Row1[0].emailaddr[0]" :"98",
        #"form1[0].page2[0].body[0].vote[0].b[0].Table1[0].Row1[0].dd[0]" :"99",
        #"form1[0].page2[0].body[0].vote[0].b[0].Table1[0].Row1[1].addr[0]" :"100",
        #"form1[0].page2[0].body[0].vote[0].b[0].Table1[0].Row1[1].name[0]" :"101",
        #"form1[0].page2[0].body[0].vote[0].b[0].Table1[0].Row1[1].emailaddr[0]" :"102",
        #"form1[0].page2[0].body[0].vote[0].b[0].Table1[0].Row1[1].dd[0]" :"103",
        #"form1[0].page2[0].body[0].vote[0].b[0].Table1[0].Row1[2].addr[0]" :"104",
        #"form1[0].page2[0].body[0].vote[0].b[0].Table1[0].Row1[2].name[0]" :"105",
        #"form1[0].page2[0].body[0].vote[0].b[0].Table1[0].Row1[2].emailaddr[0]" :"106",
        #"form1[0].page2[0].body[0].vote[0].b[0].Table1[0].Row1[2].dd[0]" :"107",
        #"form1[0].page2[0].body[0].vote[0].b[0].navigBtns[0].add[0]" :"108",
        #"form1[0].page2[0].body[0].vote1[0].renominateOwnerOwn[0]" :"109",
        #"form1[0].page2[0].body[0].vote1[0].c[0].Table2[0].Row1[0].addr[0]" :"110",
        #"form1[0].page2[0].body[0].vote1[0].c[0].Table2[0].Row1[0].name[0]" :"111",
        #"form1[0].page2[0].body[0].vote1[0].c[0].Table2[0].Row1[0].emailaddr[0]" :"112",
        #"form1[0].page2[0].body[0].vote1[0].c[0].Table2[0].Row1[0].dd[0]":"113",
        #"form1[0].page2[0].body[0].vote1[0].c[0].Table2[0].Row1[1].addr[0]" :"114",
        #"form1[0].page2[0].body[0].vote1[0].c[0].Table2[0].Row1[1].name[0]" :"115",
        #"form1[0].page2[0].body[0].vote1[0].c[0].Table2[0].Row1[1].emailaddr[0]" :"116",
        #"form1[0].page2[0].body[0].vote1[0].c[0].Table2[0].Row1[1].dd[0]" :"117",
        #"form1[0].page2[0].body[0].vote1[0].c[0].Table2[0].Row1[2].addr[0]" :"118",
        #"form1[0].page2[0].body[0].vote1[0].c[0].Table2[0].Row1[2].name[0]" :"119",
        #"form1[0].page2[0].body[0].vote1[0].c[0].Table2[0].Row1[2].emailaddr[0]" :"120",
        #"form1[0].page2[0].body[0].vote1[0].c[0].Table2[0].Row1[2].dd[0]" :"121",
        #"form1[0].page2[0].body[0].vote1[0].c[0].navigBtns[0].add[0]" :"121",
        #"form1[0].page2[0].body[0].navigationBtns1[0].saveForm[0]" :"122",
        #"form1[0].page2[0].body[0].navigationBtns1[0].Reset[0]" :"123",

        
    }
    # ✅ Add this block here, before writing PDF
    voting_instruction = data.get("votingInstruction", "")

    data_dict["form1[0].page2[0].body[0].candidates[0].option1[0].notAuthorize[0]"] = "Off"
    data_dict["form1[0].page2[0].body[0].candidates[0].option2[0].votes[0]"] = "Off"
    data_dict["form1[0].page2[0].body[0].candidates[0].option3[0].instruct[0]"] = "Off"

    if name_21:
        data_dict["form1[0].page2[0].authorizers[0].b[0].Table1[0].Row1[0].name[0]"] = name_21
        data_dict["form1[0].page2[0].authorizers[0].b[0].Table1[0].Row1[0].addr[0]"] = initials  # <- use initials

    if name_23:
        data_dict["form1[0].page2[0].authorizers[0].b[0].Table1[0].Row2[0].name[0]"] = name_23
        data_dict["form1[0].page2[0].authorizers[0].b[0].Table1[0].Row2[0].addr[0]"] = initials  # <- use initials


    if voting_instruction == "option1":
        data_dict["form1[0].page2[0].body[0].candidates[0].option1[0].notAuthorize[0]"] = "Yes"
        data_dict["form1[0].page2[0].body[0].candidates[0].option1[0].signature[0]"] = initials

    elif voting_instruction == "option2":
        data_dict["form1[0].page2[0].body[0].candidates[0].option2[0].votes[0]"] = "Yes"
        data_dict["form1[0].page2[0].body[0].candidates[0].option2[0].signature[0]"] = initials


    elif voting_instruction == "option3":
        data_dict["form1[0].page2[0].body[0].candidates[0].option3[0].instruct[0]"] = "Yes"
        data_dict["form1[0].page2[0].body[0].candidates[0].option3[0].signature[0]"] = initials





        # Conditionally check off based on selected sections
    if "section1" in voting_sections:
        data_dict["form1[0].page2[0].body[0].one[0].instructBoard[0]"] = "Yes"
    if "section2" in voting_sections:
        data_dict["form1[0].page2[0].body[0].two[0].instruct1[0]"] = "Yes"
    if "section3" in voting_sections:
        data_dict["form1[0].page2[0].body[0].three[0].voting[0]"] = "Yes"
    if "section4" in voting_sections:
        data_dict["form1[0].page2[0].body[0].four[0].instructProxy[0]"] = "Yes"
     # Path to the PDF template and where to save the new PDF
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_pdf_path = os.path.join(base_dir, "Proxy_Form_option3.pdf")
    output_pdf_path = os.path.join(base_dir, "new.pdf")

    section1Votes = data.get("section1Votes", [])
    #actual names 
    section1_addr_fields = [
        "form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[0].addr[0]",  # 33
        "form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[1].addr[0]",  # 37
        "form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[2].addr[0]",  # 41
    ]

    # ranking 
    section1_name_fields = [
        "form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[0].name[0]",  # 32
        "form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[1].name[0]",  # 36
        "form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[2].name[0]",  # 40
    ]

    for i, vote in enumerate(section1Votes):
        if i < 3 and vote.strip():  # Only process if vote is not empty or just spaces
            data_dict[section1_addr_fields[i]] = vote
            data_dict[section1_name_fields[i]] = str(i + 1)
            data_dict[f"form1[0].page2[0].body[0].one[0].b[0].Table1[0].Row1[{i}].emailaddr[0]"] = initials


        
    #actual names 
    section2Votes = data.get("section2Votes", [])

    section2_addr_fields = [
        "form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[0].addr[0]" ,
        "form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[1].addr[0]",
        "form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[2].addr[0]",
    ]



    # ranking 
    section2_name_fields = [
        "form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[0].name[0]",
        "form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[1].name[0]",
        "form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[2].name[0]",
    ]

    for i, vote in enumerate(section2Votes):
        if i < 3 and vote.strip():
            data_dict[section2_addr_fields[i]] = vote
            data_dict[section2_name_fields[i]] = str(i + 1)  # Fill 1, 2, 3 as name fields
            data_dict[f"form1[0].page2[0].body[0].two[0].b[0].Table1[0].Row1[{i}].emailaddr[0]"] = initials


    specificMatters = data.get("specificMatters", [])


    section3_name_fields = [
        "form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[0].name[0]" ,
        "form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[1].name[0]" ,
        "form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[2].name[0]" ,
    ]
    
    # Fill data_dict with the text values from specificMatters
    for i, matter in enumerate(specificMatters):
        text = matter["text"].strip()
        if i < len(section3_name_fields) and text:
            data_dict[section3_name_fields[i]] = text
            data_dict[f"form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[{i}].emailaddr[0]"] = initials



    # Define field IDs for "yes" and "no" checkboxes in each row
    section3_yes_fields = [
        "form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[0].yes[0]#0",
        "form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[1].yes[0]",
        "form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[0].yes[0]#1",
    ]

    section3_no_fields = [
        "form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[0].no[0]#0",
        "form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[1].no[0]",
        "form1[0].page2[0].body[0].three[0].b[0].Table1[0].Row1[0].no[0]#1",
    ]

    # Loop through the items and check the appropriate box
    for i, matter in enumerate(specificMatters):
        if i < len(section3_yes_fields):
            if matter.get("yes", False):
                data_dict[section3_yes_fields[i]] = "Yes"
            elif matter.get("no", False):
                data_dict[section3_no_fields[i]] = "Yes"

    
    
    removalVotes = data.get("removalVotes", [])


    section4_name_fields = [
        "form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[0].name[0]" ,

        "form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[1].name[0]" ,
        "form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[2].name[0]" ,
    ]
    
    # Fill data_dict with the text values from specificMatters
    for i, matter in enumerate(removalVotes):
        name = matter["name"].strip()
        if i < len(section4_name_fields) and name:
            data_dict[section4_name_fields[i]] = name
            data_dict[f"form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[{i}].emailaddr[0]"] = initials


    
    section4_favour_fields = [
        "form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[0].inFavour[0]#0",
        "form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[1].inFavour[0]",
        "form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[0].inFavour[0]#1",
    ]

    section4_against_fields = [
        "form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[0].against[0]#0",
        "form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[1].against[0]",
        "form1[0].page2[0].body[0].four[0].b[0].Table1[0].Row1[0].against[0]#1",
    ]

    # Loop through and assign checkmarks to the correct field
    for i, vote in enumerate(removalVotes):
        if i < len(section4_favour_fields):
            if vote.get("favour", False):
                data_dict[section4_favour_fields[i]] = "Yes"
            elif vote.get("against", False):
                data_dict[section4_against_fields[i]] = "Yes"
    # Fill the PDF
    fillpdfs.write_fillable_pdf(input_pdf_path, output_pdf_path, data_dict)



    return jsonify({"message": "Data received successfully!"}), 200


@app.route('/api/final-pdf', methods=['GET'])
def get_filled_pdf():
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "new.pdf")
    return send_file(pdf_path, mimetype='application/pdf')


@app.route('/api/submit-disclosure-form', methods=['POST'])
def submit_disclosure_form():
    data = request.json  # This is your `completeFormData` object

    name = data["name"]
    address = data["address"]
    is_owner = data["isOwner"]
    is_in_arrears = data["isInArrears"]
    is_occupant = data["isOccupant"]
    legal_proceedings = data["legalProceedings"]
    condo_conviction = data["condoConviction"]
    conflict_of_interest = data["conflictOfInterest"]
    conflict_with_declarant = data["conflictWithDeclarant"]
    to = data["to"]
    data_dict = {}

    print("\n📬 Disclosure Form Submitted")
    print("📝 Data:", json.dumps(data, indent=2))  # Pretty print the full payload


    if is_owner:
        data_dict["B1Y"] = "Yes"
    else:
        data_dict["B1N"] = "Yes"

    # Conditional logic for Arrears based on Ownership
    if is_owner:
        if is_in_arrears:
            data_dict["B2Y"] = "Yes"
        else:
            data_dict["B2N"] = "Yes"
    else:
        # Not owner, leave arrears checkboxes empty
        data_dict["B2Y"] = ""
        data_dict["B2N"] = ""

    if is_occupant:
        data_dict["B3Y"] = "Yes"
    else:
        data_dict["B3N"] = "Yes"

    if legal_proceedings:
        data_dict["C1Y"] = "Yes"
    else:
        data_dict["C1N"] = "Yes"

    if condo_conviction:
        data_dict["D1Y"] = "Yes"
    else:
        data_dict["D1N"] = "Yes"

    if conflict_of_interest:
        data_dict["E1Y"] = "Yes"
    else:
        data_dict["E1N"] = "Yes"

    if conflict_with_declarant:
        data_dict["F1Y"] = "Yes"
    else:
        data_dict["F1N"] = "Yes"

    # ✅ Generate date string like: 18th day of April, 2025 at 04:41 am EDT
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)

    day_str = get_day_with_suffix(now.day)
    formatted_date = f"{day_str} day of {now.strftime('%B')}, {now.year} at {now.strftime('%I:%M %p').lower()} {now.strftime('%Z')}"

    # ✅ Save it into data_dict
    data_dict["SubmittedAt"] = formatted_date
    
    data_dict["A1Name"] = name
    data_dict["A1Address"] = address
    data_dict["to"] = to

    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_pdf_path = os.path.join(base_dir, "DisclosureFormRebuild.pdf")
    output_pdf_path = os.path.join(base_dir, "newDisclosureForm.pdf")
    fillpdfs.write_fillable_pdf(input_pdf_path, output_pdf_path, data_dict)

     # ✅ Flatten the filled PDF
    doc = fitz.open(output_pdf_path)
    for page in doc:
        page.flatten_forms()
    doc.save(output_pdf_path)  # Overwrite with flattened version

    return jsonify({"message": "Data received successfully!"}), 200


@app.route('/api/final-disclosure-pdf', methods=['GET'])
def get_filled_disclosure_pdf():
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "newDisclosureForm.pdf")
    return send_file(pdf_path, mimetype='application/pdf')

# ✅ Helper function (no @app.route needed)
def get_day_with_suffix(day):
    if 11 <= day <= 13:
        return f"{day}th"
    last_digit = day % 10
    if last_digit == 1:
        return f"{day}st"
    elif last_digit == 2:
        return f"{day}nd"
    elif last_digit == 3:
        return f"{day}rd"
    else:
        return f"{day}th"



#submit email 

@app.route('/api/send-email', methods=['POST'])
def send_email():
    try:
        name = request.form.get("name", "Unknown")

        # Path to disclosure PDF
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_pdf_path = os.path.join(base_dir, "newDisclosureForm.pdf")

        # Encode the filled disclosure PDF
        with open(output_pdf_path, "rb") as f:
            disclosure_encoded = base64.b64encode(f.read()).decode()

        attachments = []
        disclosure_filename = f"{name.replace(' ', '')}-DisclosureForm.pdf"

        # ✅ Add filled disclosure form
        attachments.append(
            Attachment(
                FileContent(disclosure_encoded),
                FileName(f"{name.replace(' ', '')}-DisclosureForm.pdf"),
                FileType("application/pdf"),
                Disposition("attachment"),
            )
        )

        print(f"✔️ Attached: {disclosure_filename}")


        # ✅ Handle uploaded supporting files
        if "files" in request.files:
            for file in request.files.getlist("files"):
                file_data = file.read()
                encoded = base64.b64encode(file_data).decode()
                attachments.append(
                    Attachment(
                        FileContent(encoded),
                        FileName(file.filename),
                        FileType(file.mimetype),
                        Disposition("attachment")
                    )
                )
                print(f"✔️ Attached: {file.filename}")  # 📎 Log each uploaded file


        # Create email
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=f'Disclosure Form Submission from {name}',
            plain_text_content=f'Please find attached the completed disclosure form and supporting documents from {name}',
            
        )

        # ✅ Attach all files
        message.attachment = attachments

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        print("✅ Email sent:", response.status_code)
        return jsonify({"message": "Email sent successfully!"}), 200

    except Exception as e:
        print("❌ Error sending email:", str(e))
        return jsonify({"error": str(e)}), 500
    


#Url generation
@app.route("/api/generateLink", methods=["POST"])
def generate_link():
    data = request.json
    to = data.get("to")
    deadline = data.get("deadline")
    if not to or not deadline:
        return jsonify({"error": "Missing required fields"}), 400

    link_id = str(uuid.uuid4())[:8]  # Shorten to 8 chars
    insert_link(link_id, to, deadline)

    print("/api/generateLink Called ✔️ ")
    print(f"To: {to}")
    print(f"Deadline: {deadline}")
    print(f"Link ID: {link_id}")

    return jsonify({"id": link_id})

@app.route("/api/disclosureData", methods=["GET"])
def get_disclosure_data():
    id = request.args.get("id")
    data = get_link(id)
    if not data:
        return jsonify({"error": "Not found"}), 404
    
  
    return jsonify(data)

#ping
@app.route("/health")
def health():
    return "OK", 200

@app.route("/uptime")
def get_uptime():
    now = datetime.utcnow()
    uptime = now - start_time
    return jsonify({
        "uptime_seconds": int(uptime.total_seconds()),
        "uptime": str(timedelta(seconds=int(uptime.total_seconds())))
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Render sets the PORT environment variable
    app.run(host='0.0.0.0', port=port)

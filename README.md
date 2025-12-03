**Team:** RABBITT RANGERS  
**Members:**  
- Umang (2022006170)  
- Anamika Sangwan (2022542651)

---

## 🧠 Project Overview
Manual CRM data entry is time-consuming, repetitive, and error-prone.  
This project automates CRM data extraction from unstructured **sales meeting summaries**, improving accuracy and saving time.

Our AI agent:

- Reads raw meeting transcripts or notes  
- Extracts structured CRM-ready fields  
- Generates clean JSON output  
- Provides confidence scoring  
- Displays results in a polished UI  

---

## 🎯 Key Features
### **AI-Powered Extraction**
- Contact details (name, title, email, phone)  
- Company name  
- Deal value, currency & close date  
- Pain points  
- Competitors  
- Next actions with deadlines  
- Sales stage detection  
- Confidence scoring  

### **Frontend UI**
- Modern, clean, dual-panel interface  
- Agent-style feedback messages  
- Quick preview cards  
- Table view of extracted fields  
- JSON viewer  
- Copy JSON & Download JSON options  

### **Backend**
- FastAPI REST API  
- NLP using spaCy + regex + heuristics  
- Clean CRM-ready JSON mapping  
- Mock CRM push with auto-generated IDs  

---

## 🏗️ Architecture Flow
User Input
↓
FastAPI Backend
↓
NLP Pipeline (spaCy + regex + rule-based extraction)
↓
Structured CRM JSON
↓
Frontend UI Preview + JSON Download

---

## 🛠️ Tech Stack

### **Frontend**
- HTML  
- CSS  
- JavaScript  

### **Backend**
- FastAPI  
- Python  
- Uvicorn  
- Pydantic  

### **NLP Components**
- spaCy Named Entity Recognition  
- Regex for emails, phone numbers, designation patterns  
- Date parsing  
- Rule-based deal stage classification  

---

## 📡 API Endpoint

### `POST /extract`
**Request**
```json
{
  "meeting_text": "Had a call with Sarah Johnson..."
}
Response
{
  "agent_message": "Perfect! I extracted your CRM data.",
  "extracted": { ... },
  "crm_payload": { ... }
}
🖥️ Running the Project Locally
1️⃣ Create a virtual environment
python3 -m venv venv
source venv/bin/activate
2️⃣ Install dependencies
pip install -r crm-prototype/crm-prototype/requirements.txt
3️⃣ Run the FastAPI backend
cd crm-prototype/crm-prototype
source ../venv/bin/activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000
4️⃣ Open the frontend
http://localhost:8000/static/index.html
🧪 Sample Input to Test
Had a discovery call with Priya Sharma, Senior Product Manager at CloudNova. 
They discussed onboarding automation, $45K budget, demo next Thursday...
📦 Project Structure
crm-prototype/
 ├── crm-prototype/
 │    ├── app.py
 │    ├── static/
 │    │    └── index.html
 │    └── run.sh
 ├── venv/
 └── README.md
🏁 Conclusion

This system demonstrates a fully functional AI-driven CRM data extraction pipeline, fulfilling all required deliverables and providing a practical, real-world automation workflow for sales teams.
🙌 Team RABBITT RANGERS

Built by Umang & Anamika with ❤️
EOF

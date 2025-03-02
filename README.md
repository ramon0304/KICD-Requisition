# **KICD Requisition System 📋**  
A Flask-based web application to automate the requisition process for the **KICD Resource Centre Store**. This system allows users to fill out requisition forms in multiple steps, preview them as PDFs, and submit them for approval. It includes email notifications for approvals, stores PDFs in the database, and provides a beautiful and user-friendly interface.

---

## **Features 🌟**
- **Multi-step Form:** User-friendly and clean multi-step form for data entry.  
- **PDF Preview:** Generate and preview PDF before submission.  
- **Store PDFs:** Save PDFs directly in the SQLite database.  
- **Email Notifications:** Send emails with attached PDFs to approvers.  
- **Approval Workflow:** Track approval status (pending, approved, or rejected).  
- **Responsive UI:** Stylish and responsive forms using Bootstrap.  

---

## **Technologies Used 🛠️**
- **Backend:** Flask, SQLAlchemy, SQLite, Flask-Mail  
- **Frontend:** HTML, CSS, JavaScript, Bootstrap  
- **PDF Generation:** WeasyPrint  
- **Email Service:** Flask-Mail  
- **Language:** Python  

---

## **Installation 🚀**
1. **Clone the repository:**  
   ```bash
   git clone https://github.com/ramon/kicd-requisition-system.git
   cd kicd-requisition-system
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate 
    # On Windows: venv\Scripts\activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create the SQLite database:**
   ```bash
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   ```

5. **Configure your email settings in `config.py`:**
   ```python
   MAIL_SERVER = 'smtp.example.com'
   MAIL_PORT = 587
   MAIL_USERNAME = 'your-email@example.com'
   MAIL_PASSWORD = 'your-email-password'
   MAIL_USE_TLS = True
   MAIL_USE_SSL = False
   ```

6. **Run the app:**
   ```bash
   flask run
   ```

---

## **Database Models 🗄️**

### **Requisition Table**
| Column           | Type               | Description                           |
|------------------|--------------------|---------------------------------------|
| id               | Integer (Primary)  | Unique identifier.                    |
| office_name      | String             | Name of requesting office.            |
| requested_by     | String             | Name of the requester.                |
| user_email       | String             | Email of the requester.               |
| pdf_file         | LargeBinary        | Stores the PDF file.                  |
| status           | String             | Approval status (Pending/Approved).   |

---

## **Key Routes 🌐**

| Route                        | Method   | Description                                    |
|------------------------------|----------|------------------------------------------------|
| `/`                          | GET      | Home page with requisition form.               |
| `/submit`                    | POST     | Submit form data and generate PDF.             |
| `/preview-pdf/<req_id>`      | GET      | Preview PDF before submission.                 |
| `/generate-pdf/<req_id>`     | GET      | Download the PDF.                              |
| `/approve/<req_id>`          | POST     | Approve or reject requisition.                 |

---

## **PDF Preview & Storage 🖨️**
- **PDF Generation:** Uses **WeasyPrint** to convert HTML to PDF.  
- **Storage:** Saves the PDF as **binary data** in the SQLite database.  
- **Preview:** Inline preview before final submission.  

---

## **Email Notification 📧**
- Sends email with attached PDF to approvers.  
- Configurable SMTP settings in `config.py`.  
- Uses **Flask-Mail** for email handling.  

---

## **Approval Workflow ✅**
- **Pending:** Default status after submission.  
- **Approved:** Upon approver’s confirmation.  
- **Rejected:** If disapproved by an approver.  

---

## **Screenshots 📸**
*(Add screenshots of the multi-step form, PDF preview, and approval page here.)*  

---

## **Future Enhancements 🌱**
- **Role-Based Access:** Admin and Approver roles.  
- **Digital Signatures:** Capture approvers’ signatures.  
- **Analytics:** Track requisition trends and statistics.  

---

## **Contributing 🤝**
1. Fork the repository.  
2. Create a new branch: `git checkout -b feature/your-feature`.  
3. Commit your changes: `git commit -m 'Add new feature'`.  
4. Push to the branch: `git push origin feature/your-feature`.  
5. Open a Pull Request.  

---

## **License 📄**
This project is licensed under the **MIT License**.  

---

**Test credentials**
## User
- Email: test@test.com
- Password: test1234
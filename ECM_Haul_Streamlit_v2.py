
import streamlit as st
import json
import uuid
import os
from datetime import datetime

# --- Configuration ---
CUSTOMER_DATA_FILE = 'customers.json'
JOB_DATA_FILE = 'jobs.json'
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

# --- Helper Functions ---
def load_data(file_path):
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        st.error(f"Error loading {file_path}. File may be corrupted.")
        return {}

def save_data(data, file_path):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        st.error(f"Error saving data: {e}")

# --- Data Classes ---
class Customer:
    def __init__(self, name, phone, email, address, boat_make, boat_model, customer_id=None):
        self.customer_id = customer_id or str(uuid.uuid4())[:8]
        self.name = name
        self.phone = phone
        self.email = email
        self.address = address
        self.boat_make = boat_make
        self.boat_model = boat_model

    def to_dict(self):
        return self.__dict__

class Job:
    VALID_STATUSES = ["Scheduled", "In Progress", "Completed", "Cancelled"]

    def __init__(self, customer_id, service_type, scheduled_dt, origin, destination,
                 quoted_price, notes="", job_id=None, status="Scheduled"):
        self.job_id = job_id or str(uuid.uuid4())[:8]
        self.customer_id = customer_id
        self.service_type = service_type
        self.scheduled_datetime = scheduled_dt.strftime(DATETIME_FORMAT)
        self.origin_location = origin
        self.destination_location = destination or origin
        self.quoted_price = quoted_price
        self.notes = notes
        self.status = status
        self.created_at = datetime.now().strftime(DATETIME_FORMAT)
        self.updated_at = self.created_at

    def to_dict(self):
        return self.__dict__

    def update_status(self, new_status):
        if new_status in self.VALID_STATUSES:
            self.status = new_status
            self.updated_at = datetime.now().strftime(DATETIME_FORMAT)
            return True
        return False

# --- Session State Initialization ---
if "customers" not in st.session_state:
    st.session_state.customers = load_data(CUSTOMER_DATA_FILE)

if "jobs" not in st.session_state:
    st.session_state.jobs = load_data(JOB_DATA_FILE)

# --- Sidebar Navigation ---
menu = st.sidebar.selectbox(
    "Main Menu",
    ["Add New Customer", "View Customers", "Add New Job", "View Jobs", "Update Job Status", "Save All Data"]
)

# --- Add New Customer ---
if menu == "Add New Customer":
    st.header("Add New Customer")
    with st.form("customer_form"):
        name = st.text_input("Customer Name")
        phone = st.text_input("Phone Number")
        email = st.text_input("Email Address")
        address = st.text_area("Billing Address")
        boat_make = st.text_input("Boat Make")
        boat_model = st.text_input("Boat Model")
        submitted = st.form_submit_button("Add Customer")

        if submitted:
            if not name:
                st.error("Customer name is required.")
            else:
                customer = Customer(name, phone, email, address, boat_make, boat_model)
                st.session_state.customers[customer.customer_id] = customer.to_dict()
                st.success(f"Customer '{name}' added successfully! ID: {customer.customer_id}")

# --- View Customers ---
elif menu == "View Customers":
    st.header("All Customers")
    if st.session_state.customers:
        st.dataframe(list(st.session_state.customers.values()))
    else:
        st.info("No customers found.")

# --- Add New Job ---
elif menu == "Add New Job":
    st.header("Add New Job")
    if not st.session_state.customers:
        st.warning("Please add at least one customer first.")
    else:
        cust_ids = list(st.session_state.customers.keys())
        cust_names = [f"{st.session_state.customers[cid]['name']} ({cid})" for cid in cust_ids]
        with st.form("job_form"):
            customer_choice = st.selectbox("Select Customer", cust_ids, format_func=lambda cid: st.session_state.customers[cid]['name'])
            service_type = st.selectbox("Service Type", ["Launch", "Haul", "Transport"])
            date = st.date_input("Scheduled Date")
            time = st.time_input("Scheduled Time")
            origin = st.text_input("Origin Location")
            destination = st.text_input("Destination Location (optional)")
            quoted_price = st.number_input("Quoted Price ($)", min_value=0.0, step=10.0)
            notes = st.text_area("Additional Notes (optional)")
            submitted_job = st.form_submit_button("Add Job")

            if submitted_job:
                dt = datetime.combine(date, time)
                job = Job(customer_choice, service_type, dt, origin, destination, quoted_price, notes)
                st.session_state.jobs[job.job_id] = job.to_dict()
                st.success(f"Job '{job.job_id}' created and scheduled!")

# --- View Jobs ---
elif menu == "View Jobs":
    st.header("All Jobs")
    status_filter = st.selectbox("Filter by Status", ["All"] + Job.VALID_STATUSES)
    jobs = list(st.session_state.jobs.values())
    if status_filter != "All":
        jobs = [j for j in jobs if j['status'] == status_filter]
    if jobs:
        st.dataframe(jobs)
    else:
        st.info("No jobs to display.")

# --- Update Job Status ---
elif menu == "Update Job Status":
    st.header("Update Job Status")
    if not st.session_state.jobs:
        st.warning("No jobs available. Please add a job first.")
    else:
        job_ids = list(st.session_state.jobs.keys())
        job_choice = st.selectbox("Select Job", job_ids, format_func=lambda jid: f"{jid} - {st.session_state.jobs[jid]['service_type']}")
        new_status = st.selectbox("New Status", Job.VALID_STATUSES)
        if st.button("Update Status"):
            job_data = st.session_state.jobs[job_choice]
            job_obj = Job(**job_data)  # recreate to use method
            if job_obj.update_status(new_status):
                st.session_state.jobs[job_choice]['status'] = new_status
                st.session_state.jobs[job_choice]['updated_at'] = job_obj.updated_at
                st.success(f"Job {job_choice} status updated to '{new_status}'.")
            else:
                st.error("Invalid status selected.")

# --- Save All Data ---
elif menu == "Save All Data":
    save_data(st.session_state.customers, CUSTOMER_DATA_FILE)
    save_data(st.session_state.jobs, JOB_DATA_FILE)
    st.success("All data saved successfully.")

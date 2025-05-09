import json
import uuid
from datetime import datetime
import os

# --- Configuration ---
CUSTOMER_DATA_FILE = 'customers.json'
JOB_DATA_FILE = 'jobs.json'
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

# --- Helper Functions for Data Handling ---
def load_data(file_path):
    """Loads data from a JSON file."""
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, IOError):
        return {}

def save_data(data, file_path):
    """Saves data to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError:
        print(f"Error: Could not save data to {file_path}")

# --- Customer Class ---
class Customer:
    def __init__(self, name, phone, email, address, boat_make, boat_model, boat_length, boat_name="", customer_id=None):
        self.customer_id = customer_id if customer_id else str(uuid.uuid4())
        self.name = name
        self.phone = phone
        self.email = email
        self.address = address # Billing/Contact address
        self.boat_make = boat_make
        self.boat_model = boat_model
        self.boat_length = boat_length # In feet
        self.boat_name = boat_name

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(data):
        return Customer(**data)

    def __str__(self):
        return (f"ID: {self.customer_id}\n"
                f"  Name: {self.name}\n"
                f"  Phone: {self.phone}\n"
                f"  Email: {self.email}\n"
                f"  Address: {self.address}\n"
                f"  Boat: {self.boat_length}ft {self.boat_make} {self.boat_model} (Name: {self.boat_name if self.boat_name else 'N/A'})")

# --- Job Class ---
class Job:
    VALID_STATUSES = ["Scheduled", "In Progress", "Completed", "Cancelled", "Invoiced", "Paid"]

    def __init__(self, customer_id, service_type, scheduled_datetime_str, origin_location, destination_location, quoted_price, notes="", job_id=None, status="Scheduled"):
        self.job_id = job_id if job_id else str(uuid.uuid4())
        self.customer_id = customer_id
        self.service_type = service_type # e.g., "Haul Out", "Launch", "Transport", "Mast Stepping"
        try:
            self.scheduled_datetime = datetime.strptime(scheduled_datetime_str, DATETIME_FORMAT).strftime(DATETIME_FORMAT)
        except ValueError:
            raise ValueError(f"Invalid datetime format. Please use YYYY-MM-DD HH:MM (e.g., 2025-09-15 14:30)")
        self.origin_location = origin_location
        self.destination_location = destination_location
        self.quoted_price = float(quoted_price)
        self.status = status if status in self.VALID_STATUSES else "Scheduled"
        self.notes = notes
        self.created_at = datetime.now().strftime(DATETIME_FORMAT)
        self.updated_at = self.created_at

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(data):
        return Job(**data)

    def update_status(self, new_status):
        if new_status in self.VALID_STATUSES:
            self.status = new_status
            self.updated_at = datetime.now().strftime(DATETIME_FORMAT)
            return True
        return False

    def __str__(self):
        return (f"Job ID: {self.job_id}\n"
                f"  Customer ID: {self.customer_id}\n"
                f"  Service: {self.service_type}\n"
                f"  Scheduled: {self.scheduled_datetime}\n"
                f"  Origin: {self.origin_location}\n"
                f"  Destination: {self.destination_location}\n"
                f"  Price: ${self.quoted_price:.2f}\n"
                f"  Status: {self.status}\n"
                f"  Notes: {self.notes if self.notes else 'N/A'}\n"
                f"  Last Updated: {self.updated_at}")

# --- Business Logic ---
class BoatHaulingManager:
    def __init__(self):
        self.customers = {cid: Customer.from_dict(cdata) for cid, cdata in load_data(CUSTOMER_DATA_FILE).items()}
        self.jobs = {jid: Job.from_dict(jdata) for jid, jdata in load_data(JOB_DATA_FILE).items()}

    def save_all(self):
        save_data({cid: c.to_dict() for cid, c in self.customers.items()}, CUSTOMER_DATA_FILE)
        save_data({jid: j.to_dict() for jid, j in self.jobs.items()}, JOB_DATA_FILE)
        print("Data saved successfully.")

    def add_customer(self):
        print("\n--- Add New Customer ---")
        name = input("Customer Name: ")
        phone = input("Phone Number: ")
        email = input("Email Address: ")
        address = input("Billing Address: ")
        boat_make = input("Boat Make: ")
        boat_model = input("Boat Model: ")
        customer = Customer(name, phone, email, address, boat_make, boat_model, boat_length, boat_name)
        self.customers[customer.customer_id] = customer
        print(f"\nCustomer '{name}' added successfully with ID: {customer.customer_id}")
        return customer.customer_id

    def list_customers(self):
        print("\n--- List of Customers ---")
        if not self.customers:
            print("No customers found.")
            return
        for customer_id, customer in self.customers.items():
            print(f"\n{customer}")
            # Optionally list jobs for this customer
            customer_jobs = [job for job in self.jobs.values() if job.customer_id == customer_id]
            if customer_jobs:
                print("  Associated Jobs:")
                for job in customer_jobs:
                    print(f"    - Job ID: {job.job_id}, Service: {job.service_type}, Status: {job.status}")

    def find_customer_by_id(self, customer_id):
        return self.customers.get(customer_id)

    def find_customer_interactive(self):
        print("\n--- Find Customer ---")
        search_term = input("Enter Customer Name, Phone, or Email to search: ").lower()
        if not search_term:
            print("Search term cannot be empty.")
            return None

        results = []
        for cust_id, customer in self.customers.items():
            if (search_term in customer.name.lower() or
                search_term in customer.phone.lower() or
                search_term in customer.email.lower()):
                results.append(customer)

        if not results:
            print("No customers found matching your search.")
            return None
        elif len(results) == 1:
            print(f"Found 1 customer:\n{results[0]}")
            return results[0]
        else:
            print("Found multiple customers:")
            for i, customer in enumerate(results):
                print(f"{i+1}. {customer.name} ({customer.email}) - ID: {customer.customer_id}")

    def add_job(self):
        print("\n--- Add New Job ---")
        if not self.customers:
            print("No customers available. Please add a customer first.")
            if input("Add a new customer now? (y/n): ").lower() == 'y':
                customer_id = self.add_customer()
                if not customer_id: return # Failed to add customer
            else:
                return
        else:
            customer_id_input = input("Enter Customer ID (or type 'search' to find a customer): ")
            if customer_id_input.lower() == 'search':
                customer = self.find_customer_interactive()
                if not customer:
                    print("No customer selected. Aborting job creation.")
                    return
                customer_id = customer.customer_id
                print(f"Selected customer: {customer.name} (ID: {customer.customer_id})")
            else:
                customer_id = customer_id_input
                if customer_id not in self.customers:
                    print("Customer ID not found.")
                    if input(f"Customer ID '{customer_id}' not found. Add as new customer? (y/n): ").lower() == 'y':
                         customer_id = self.add_customer() # This will prompt for all customer details
                         if not customer_id: return
                    else:
                         return


        service_type = input(f"Service Type (e.g., Haul Out, Launch, Transport): ")
        origin_location = input("Origin Location (e.g., Marina name, address): ")
        destination_location = input("Destination Location (if different, else leave blank): ")
        try:
            job = Job(customer_id, service_type, scheduled_datetime_str, origin_location, destination_location, quoted_price, notes)
            self.jobs[job.job_id] = job
            print(f"\nJob for customer '{self.customers[customer_id].name}' added successfully with ID: {job.job_id}")
        except ValueError as e:
            print(f"Error creating job: {e}")
        except KeyError:
            print(f"Error: Customer ID {customer_id} does not exist.")


    def list_jobs(self):
        print("\n--- List of Jobs ---")
        if not self.jobs:
            print("No jobs found.")
            return

        filter_status = input(f"Filter by status? {Job.VALID_STATUSES} (Leave blank for all, or type status): ").strip()
        if filter_status and filter_status not in Job.VALID_STATUSES:
            print(f"Invalid status. Showing all jobs.")
            filter_status = None

        jobs_to_display = []
        for job_id, job in self.jobs.items():
            if filter_status and job.status != filter_status:
                continue
            jobs_to_display.append(job)

        if not jobs_to_display:
            print(f"No jobs found with status '{filter_status if filter_status else 'any'}'.")
            return

        # Sort jobs by scheduled date (optional, but nice)
        jobs_to_display.sort(key=lambda j: datetime.strptime(j.scheduled_datetime, DATETIME_FORMAT))

        for job in jobs_to_display:
            customer_name = self.customers.get(job.customer_id).name if job.customer_id in self.customers else "N/A"
            print(f"\n{job}")
            print(f"  Customer Name: {customer_name}")

    def update_job_status(self):
        print("\n--- Update Job Status ---")
        job_id = input("Enter Job ID to update: ")
        job = self.jobs.get(job_id)

        if not job:
            print("Job ID not found.")
            return

        print(f"Current status for Job {job_id}: {job.status}")
        print(f"Available statuses: {', '.join(Job.VALID_STATUSES)}")
        new_status = input("Enter new status: ").strip()

        if job.update_status(new_status):
            print(f"Job {job_id} status updated to '{new_status}'.")
        else:
            print(f"Invalid status '{new_status}'. Status not updated.")

# --- Main Menu and CLI ---
def main_menu(manager):
        choice = input("Enter your choice: ")

        if choice == '1':
            manager.add_customer()
        elif choice == '2':
            manager.list_customers()
        elif choice == '3':
            customer = manager.find_customer_interactive()
            if customer:
                print(f"\nSelected Customer Details:\n{customer}")
        elif choice == '4':
            manager.add_job()
        elif choice == '5':
            manager.list_jobs()
        elif choice == '6':
            manager.update_job_status()
        elif choice == '7':
            manager.save_all()
        elif choice == '8':
            manager.save_all() # Save before exiting
            print("Exiting application. Goodbye!")
        else:
            print("Invalid choice. Please try again.")
        input("\nPress Enter to continue...") # Pause for readability

# --- Main Execution ---
if __name__ == "__main__":
    # Ensure data files exist or create them empty if they don't
    if not os.path.exists(CUSTOMER_DATA_FILE):
        save_data({}, CUSTOMER_DATA_FILE)
    if not os.path.exists(JOB_DATA_FILE):
        save_data({}, JOB_DATA_FILE)

    business_manager = BoatHaulingManager()
    main_menu(business_manager)
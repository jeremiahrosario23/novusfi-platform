# -------------------- Force the compute cluster to install faker every time the databricks runtime spins up
import subprocess
import sys

try:
    import faker
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "faker"])

# -------------------- Start of generation
# Import modules
import json
import random
import uuid
from faker import Faker
from datetime import datetime, timedelta

# initiate Faker object
fake = Faker()

# -------------------- Add Currency and Location Logic
def get_currency_and_location():
    """
    Assigns a currency and customer location based on the Neobank's regional distribution strategy.
    Currencies are compatible with https://open.er-api.com/v6/latest/USD
    """
    rand_val = random.random()
    
    if rand_val < 0.40:
        # 40% Local (Philippines)
        return "PHP", "Philippines"
    elif rand_val < 0.70:
        # 30% Southeast Asia
        return random.choice([
            ("SGD", "Singapore"), ("MYR", "Malaysia"), 
            ("IDR", "Indonesia"), ("THB", "Thailand"), 
            ("VND", "Vietnam")
        ])
    elif rand_val < 0.90:
        # 20% Rest of Asia
        return random.choice([
            ("JPY", "Japan"), ("KRW", "South Korea"), 
            ("HKD", "Hong Kong"), ("TWD", "Taiwan"), 
            ("INR", "India")
        ])
    else:
        # 10% Outliers (Global)
        return random.choice([
            ("USD", "USA"), ("EUR", "Eurozone"), 
            ("GBP", "United Kingdom"), ("AUD", "Australia")
        ])

# Define function for generating loans
def generate_loans(num_records=None):
    # Set random number of records to generate
    if num_records is None:
        num_records = random.randint(500, 1000)

    # Define output and input lists outside the loop 
    loans = []
    statuses = ["Active", "Paid Off", "Written Off", "Closed"]     
    product_types = [
        "Personal_Cash_Loan",      # Standard medium-term installment cash loan
        "Salary_Advance_Loan",     # Short-term earned wage / cash advance
        "Emergency_Cash_Loan",     # Fast-disbursal micro-cash loan
        "Digital_Credit_Drawdown"  # Cash drawn directly from an approved credit line
    ]    
    os_types = ["Android 14","Android 13","Android 12","iOS 17.4","iOS 16.7","Web_Chrome_Win11","Web_Safari_macOS","Unknown_Device"]    

    # Generate a timestamp for TODAY between 12:01:01 AM and 11:59:59 PM outside of the loop
    start_of_day = (datetime.now() -timedelta(days=1)).replace(hour=00, minute=0, second=1, microsecond=0)
    end_of_day = (datetime.now() -timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=0)
    time_diff = end_of_day - start_of_day

    # For loop through the records for today
    for _ in range(num_records):
    
        # Calculate a random time within that window
        random_seconds = random.randint(0, int(time_diff.total_seconds()))
        orig_date = start_of_day + timedelta(seconds=random_seconds)

        # Dirty Data Simulation 1: Inconsistent date formats
        date_format = "%Y-%m-%d" if random.random() > 0.2 else "%m/%d/%Y"
        
        # Determine Currency and Location
        contract_currency, contract_location = get_currency_and_location()

        # Base financial calculations
        principal = round(random.uniform(500.00, 25000.00), 2)
        apr = round(random.uniform(5.99, 35.99), 2)
        term = random.choice([3, 6, 12, 24, 36])
        
        loan = {
            "loan_id": str(uuid.uuid4()),
            "origination_date": orig_date.strftime(date_format),
            "currency": contract_currency,
            "customer_location": contract_location,
            "status": "Active",
            "borrower_details": {
                "personal_info": {
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                    # Dirty Data Simulation 2: Occasional missing PSNs (PhilSys Number because still did not receive their National ID) (NULL handling practice)
                    "psn": fake.ssn() if random.random() > 0.05 else None, 
                    "dob": fake.date_of_birth(minimum_age=18, maximum_age=75).strftime("%Y-%m-%d")
                },
                "contact": {
                    # Dirty Data Simulation 3: Messy email inputs (e.g., plus-addressing or trailing spaces)
                    "email": fake.email().replace("@", f"+{random.randint(1,99)}@") if random.random() > 0.9 else fake.email(),
                    "phone": fake.phone_number()
                }
            },
            "loan_terms": {
                "product_type": random.choice(product_types),
                "principal_amount": principal,
                "apr_pct": apr,
                "term_months": term,
                # Rough dummy calculation for Monthly EMI
                "monthly_emi": round((principal * (1 + (apr/100))) / term, 2) 
            },
            "risk_profile": {
                "internal_credit_score": random.randint(450, 850),
                "risk_tier": random.choice(["A+", "A", "B", "C", "Subprime"]),
                "decision_latency_ms": random.randint(120, 950), # Speed of automated approval
                "liveness_check_status": "PASSED" if random.random() > 0.02 else "MANUAL_REVIEW"
            },
            "device_metadata": {
                "device_os": random.choice(os_types),
                "app_version": f"v{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,5)}",
                "ip_address": fake.ipv4(),
                # Dirty Data Simulation 4: Nested dict that is sometimes completely missing (Users denying GPS permissions)
                "gps_coordinates": {
                    "lat": float(fake.latitude()),
                    "lon": float(fake.longitude())
                } if random.random() > 0.15 else None 
            },
            "funding_status": {
                "disbursement_method": random.choice(["Instant_Wallet", "External_ACH", "Virtual_Card"]),
                "destination_bank": fake.company() if random.random() > 0.4 else "NovusFi_Internal"
            }
        }
        loans.append(loan)
        
    # Save to raw volume as JSON since this is how OLTP loan systems save data
    current_datetime = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_path = f"/Volumes/dev_finance/raw/loan_records/raw_loans_extract_{current_datetime}.json"
    with open(output_path, "w") as f:
        # Saving as line-delimited JSON (very common in big data)
        for record in loans:
            f.write(json.dumps(record) + "\n")
            
    print(f"Successfully generated {num_records} messy loan records at {output_path}")

# "if I am the main file being run, then lets go" 
if __name__ == "__main__":
    generate_loans()
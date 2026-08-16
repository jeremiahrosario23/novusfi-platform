# Import modules
import os
import glob
import json
import random
import uuid
import csv
from datetime import datetime, timedelta

# Define the payment generator function that will locate existing contracts in the Volume and generate payments for them depending on their due dates
def generate_payments():
    # Locate the latest Loan JSON extract from the Volume
    loan_files = sorted(glob.glob("/Volumes/dev_finance/raw/loan_records/*.json"))
    print(loan_files)

    if not loan_files:
        print("No loan extract files found in Volume. Run the loan generator first!")
        return

    latest_loan_file = loan_files[-1]
    
    # Setup target date (Yesterday) for the batch run
    yesterday = datetime.now() - timedelta(days=1)
    target_day = yesterday.day

    # Extract active loan IDs, their expected monthly payments, and determine due dates
    due_loans = []
    random_loans = []
    
    with open(latest_loan_file, "r") as f:
        for line in f:
            record = json.loads(line)
            
            # Extract origination date to find the due day of the month
            # (Fallback to yesterday if the field is missing/corrupted)
            orig_date_str = record.get("origination_date", yesterday.strftime("%Y-%m-%d"))
            try:
                orig_date = datetime.strptime(orig_date_str, "%Y-%m-%d")
            except ValueError:
                orig_date = yesterday

            loan_data = {
                "loan_id": record["loan_id"],
                "monthly_emi": record["loan_terms"]["monthly_emi"],
                "due_day": orig_date.day,
                # Extract currency and location, using fallback defaults if missing
                "currency": record.get("currency", "PHP"),
                "customer_location": record.get("customer_location", "Philippines")
            }

            # Calculate how many days ago the loan was originated
            loan_age_days = (yesterday - orig_date).days

            # Check if the loan is "due" based on the calendar day
            diff = abs(target_day - loan_data["due_day"])
            is_due_day = (diff <= 3 or diff >= 27)

            # ONLY put them in the due_loans pool if it's their due day AND the loan is at least 25 days old
            if is_due_day and loan_age_days > 25:
                due_loans.append(loan_data)
            else:
                # If they just got the loan yesterday, they go into the random pool 
                # (where they only have a tiny 1-3% chance of making a weird Day 1 payment)
                random_loans.append(loan_data)

    # Simulate payments realistically based on due dates
    # 80% - 90% of borrowers whose due date is near will make a payment (the rest simulate missed payments/defaults)
    num_due_payments = int(len(due_loans) * random.uniform(0.80, 0.90))
    sampled_due = random.sample(due_loans, min(num_due_payments, len(due_loans)))
    
    # 1% - 3% of other borrowers will make random off-cycle payments (early/late/extra)
    num_random_payments = int(len(random_loans) * random.uniform(0.01, 0.03))
    sampled_random = random.sample(random_loans, min(num_random_payments, len(random_loans)))

    # Combine the pools for generation
    sampled_loans = sampled_due + sampled_random
    
    payments = []

    # List payment methods (local and international)
    payment_methods = ["GCash", "Maya", "BDO_Online", "BPI_Express", "7_Eleven_OTC", "Stripe", "Adyen", "PayPal", "SWIFT_Wire"]
    statuses = ["SETTLED", "SETTLED", "SETTLED", "FAILED", "PENDING"] # Weighted towards settled
    
    for item in sampled_loans:
        # Simulation: Some borrowers underpay, some pay exact EMI, some overpay
        emi = item["monthly_emi"]
        multiplier = random.choice([0.5, 1.0, 1.0, 1.0, 1.2, 2.0])
        paid_amount = round(emi * multiplier, 2)
        
        # Payment timestamp during the day
        payment_time = yesterday.replace(
            hour=random.randint(6, 22),
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )

        payments.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:10].upper()}",
            "loan_reference_id": item["loan_id"],
            "amount": paid_amount,
            "currency": item["currency"],              # <-- Dynamically mapped from loan
            "customer_location": item["customer_location"],  # <-- Dynamically mapped from loan
            "payment_channel": random.choice(payment_methods),
            "status": random.choice(statuses),
            "transaction_timestamp": payment_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    # Save to CSV in raw payment landing zone
    current_datetime = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_path = f"/Volumes/dev_finance/raw/payment_records/raw_payments_{current_datetime}.csv"

    # Ensure target directory volume exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Added customer_location to the fieldnames
    fieldnames = ["transaction_id", "loan_reference_id", "amount", "currency", "customer_location", "payment_channel", "status", "transaction_timestamp"]
    with open(output_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(payments)

    print(f"Successfully generated {len(payments)} payment transactions at {output_path}")

if __name__ == "__main__":
    generate_payments()
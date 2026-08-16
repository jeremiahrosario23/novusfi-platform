# Import modules
import os
import glob
import json
import random
import uuid
import csv
from datetime import datetime, timedelta

# Define the payment generator function
def generate_payments():
    # Locate the latest Loan JSON extract from the Volume
    loan_files = sorted(glob.glob("/Volumes/dev_finance/raw/loan_records/*.json"))
    print(loan_files)

    if not loan_files:
        print("No loan extract files found in Volume. Run the loan generator first!")
        return

    latest_loan_file = loan_files[-1]
    
    # 2. Extract active loan IDs and their expected monthly payments
    loan_pool = []
    with open(latest_loan_file, "r") as f:
        for line in f:
            record = json.loads(line)
            loan_pool.append({
                "loan_id": record["loan_id"],
                "monthly_emi": record["loan_terms"]["monthly_emi"]
            })

    # 3. Simulate payments for a subset of borrowers (e.g., 60-80% make a payment)
    num_payments = int(len(loan_pool) * random.uniform(0.6, 0.8))
    sampled_loans = random.sample(loan_pool, num_payments)
    
    payments = []
    payment_methods = ["GCash", "Maya", "BDO_Online", "BPI_Express", "7_Eleven_OTC"]
    statuses = ["SETTLED", "SETTLED", "SETTLED", "FAILED", "PENDING"] # Weighted towards settled

    yesterday = datetime.now() - timedelta(days=1)
    
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
            "currency": "PHP",
            "payment_channel": random.choice(payment_methods),
            "status": random.choice(statuses),
            "transaction_timestamp": payment_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    # 4. Save to CSV in raw payment landing zone
    current_datetime = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_path = f"/Volumes/dev_finance/raw/payment_records/raw_payments_{current_datetime}.csv"

    # Ensure target directory volume exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = ["transaction_id", "loan_reference_id", "amount", "currency", "payment_channel", "status", "transaction_timestamp"]
    with open(output_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(payments)

    print(f"Successfully generated {len(payments)} payment transactions at {output_path}")

if __name__ == "__main__":
    generate_payments()
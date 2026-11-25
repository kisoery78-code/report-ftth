import csv
import requests
import json

# Define the input and output file paths
input_csv_file = 'input.csv'
output_csv_file = 'output.csv'
api_url = 'http://172.28.26.146:9910/query_balance'

# Function to call the API
def call_api(msisdn, package_price):
    payload = {
        "msisdn": msisdn,
        "product_type": "FTTH",
        "package_price": package_price
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic YWRtaW46I0x0YzFxYXoyd3N4QGNicw=='
    }
    response = requests.post(api_url, data=json.dumps(payload), headers=headers)
    return response.json()

# Read the input CSV file
with open(input_csv_file, mode='r') as infile:
    reader = csv.DictReader(infile)
    rows = [row for row in reader]

# Create the output CSV file and write the header
with open(output_csv_file, mode='w', newline='') as outfile:
    fieldnames = ['msisdn', 'package_price', 'ResultCode', 'ResultDesc', 'Total', 'RemainingDate', 'ExpireDate', 'TotalRemainAmount', 'TotalUsageAmount']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    # Iterate over each row in the input CSV
    for row in rows:
        msisdn = row['msisdn']
        package_price = row['package_price']

        # Call the API and get the response
        response = call_api(msisdn, package_price)

        # Extract the required values from the response
        result_code = response.get('ResultCode')
        result_desc = response.get('ResultDesc')
        total = response.get('Summary', {}).get('Total')
        remaining_date = response.get('RemainingDate')
        expire_date = response.get('ExpireDate')
        total_remain_amount = response.get('TotalRemainAmount')
        total_usage_amount = response.get('TotalUsageAmount')

        # Write the data to the output CSV file
        writer.writerow({
            'msisdn': msisdn,
            'package_price': package_price,
            'ResultCode': result_code,
            'ResultDesc': result_desc,
            'Total': total,
            'RemainingDate': remaining_date,
            'ExpireDate': expire_date,
            'TotalRemainAmount': total_remain_amount,
            'TotalUsageAmount': total_usage_amount
        })

print(f"Data has been successfully written to {output_csv_file}")




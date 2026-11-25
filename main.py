import csv
import requests
import json
import cx_Oracle


# Define the input and output file paths
input_csv_file = 'input23082024.csv'
output_csv_file = 'output23082024.csv'
api_url = 'http://172.28.26.146:9910/query_balance'



# Create the connection
connection = cx_Oracle.connect('cbs/Cb$$12345@172.28.26.239:1521/billdb')

# Create a cursor object
cursor = connection.cursor()

# Your SQL query
sql_query = f"""SELECT 
bss.*
, ROUND((bss.MONTHLY_FEE0+0)/30) as daily_fee
FROM (
SELECT sb.SUB_ID, sb.CUST_ID, sb.ISDN, sb.PACKAGE_ID, SB.PRODUCT_ID
, sb.BUS_TYPE as SUB_TYPE, cs.BUS_TYPE as CUST_TYPE  
, sb.CONTACT_TITLE||' '|| sb.NAME as NAME_SUB, cs.CONTACT_TITLE||' '||CS.NAME as NAME_CUS, sb.tel_fax
, sb.STA_DATETIME, sb.FIRST_CONNECT   
, pkg.PACKAGE_CODE, pkg.PACKAGE_NAME, pkg.PACKAGE_STATUS, pkg.MONTHLY_FEE1
, CASE WHEN pkg.MONTHLY_FEE1 > 0 THEN pkg.MONTHLY_FEE1+5000
   ELSE pkg.MONTHLY_FEE1 
END AS MONTHLY_FEE0
FROM 
(
select * from  CUS_OWNER.SUBSCRIBER@DBSS s  where S.STATUS=1 and s.PRODUCT_ID='509'
) sb LEFT JOIN  
(
select * from  CUS_OWNER.CUSTOMER@DBSS c  
)  cs on sb.CUST_ID=cs.CUST_ID
LEFT JOIN (
select pk.PACKAGE_ID, pk.CODE as PACKAGE_CODE, pk.NAME as PACKAGE_NAME , PK.STATUS as PACKAGE_STATUS
, pt.STA_DATE, pt.END_DATE, pt.MONTHLY_FEE1, pt.PACKAGE_ID as PK_ID, pt.PRODUCT_ID, pk.PRODUCT_CODE
from CUS_OWNER.PACKAGES@DBSS pk LEFT JOIN CUS_OWNER.MON_FEE_TARIFF@DBSS pt on PK.PACKAGE_ID=PT.PACKAGE_ID
where 1=1 
and pt.PRODUCT_ID=509
--and pk.PRODUCT_CODE='F'
)  pkg on pkg.PACKAGE_ID=SB.PACKAGE_ID
) bss 
where 1=1
;"""

# Execute the query
cursor.execute(sql_query)

# Fetch the data
data = cursor.fetchall()

# Optionally, fetch column names
columns = [col[0] for col in cursor.description]



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




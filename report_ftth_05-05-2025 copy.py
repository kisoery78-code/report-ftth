
import csv
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import oracledb as cx_Oracle
import requests

print("start run...")
cx_Oracle.init_oracle_client(lib_dir=r"C:\oracel\instantclient_19_24")

# Example usage
username = "cbs"
password = "Cb$$12345"
host = "172.28.26.239"
port = "1521"
service_name = "billdb"

name_date=datetime.now().strftime("%Y%m%d%H%M")
# output_csv_file = f"""D:\BssWork\report_ftth\cmd\FTTH_REPORT_{name_date}.csv"""

#local
#directory = "D:/BssWork/report_ftth/LOG_OUTPUT"

#server public
directory = "F:/DATA/FTP_Shared/FTP_DT01"

filename = f"FTTH_REPORT_ONG_{name_date}.txt"
output_csv_file = os.path.join(directory, filename)

# Web service URL
api_url = 'http://172.28.26.146:9910/query_balance'
web_service_url = 'http://172.28.236.57:8080/services/BcServices'

# SQL 
query ="""
SELECT  bss.* , ROUND((bss.MONTHLY_FEE0+0)/30) as daily_fee FROM 
( SELECT sb.SUB_ID, sb.CUST_ID, sb.ISDN, sb.PACKAGE_ID, SB.PRODUCT_ID , 
sb.BUS_TYPE as SUB_TYPE, cs.BUS_TYPE as CUST_TYPE   , sb.CONTACT_TITLE||' '|| sb.NAME as NAME_SUB, cs.CONTACT_TITLE||' '||CS.NAME as NAME_CUS, 
sb.ADDRESS,sb.PAY_FULL_ADDRESS,
sb.tel_fax , sb.STA_DATETIME, sb.FIRST_CONNECT,sb.STATUS_DATE,sb.SUB_ACT_STATUS as BSS_STS 
, pkg.PACKAGE_CODE, pkg.PACKAGE_NAME, pkg.PACKAGE_STATUS,pkg.MONTHLY_FEE1 , 
CASE WHEN pkg.MONTHLY_FEE1 > 0 THEN pkg.MONTHLY_FEE1+5000    ELSE pkg.MONTHLY_FEE1  END AS MONTHLY_FEE0 
FROM  ( select s.*,d.name as SUB_ACT_STATUS from  CUS_OWNER.SUBSCRIBER@DBSS s 
LEFT join (select *  from ltc.status@dbss WHERE TYPE='SUB_ACT_STATUS') d
ON s.act_status = d.code  where S.STATUS=1 and s.PRODUCT_ID='509' ) sb LEFT JOIN   
( select * from  CUS_OWNER.CUSTOMER@DBSS c   )  cs on sb.CUST_ID=cs.CUST_ID LEFT JOIN 
( select pk.PACKAGE_ID, pk.CODE as PACKAGE_CODE, pk.NAME as PACKAGE_NAME , 
PK.STATUS as PACKAGE_STATUS , pt.STA_DATE, pt.END_DATE, pt.MONTHLY_FEE1, 
pt.PACKAGE_ID as PK_ID, pt.PRODUCT_ID, pk.PRODUCT_CODE 
from CUS_OWNER.PACKAGES@DBSS pk LEFT JOIN CUS_OWNER.MON_FEE_TARIFF@DBSS pt on PK.PACKAGE_ID=PT.PACKAGE_ID 
where 1=1  and pt.PRODUCT_ID=509 )  pkg on pkg.PACKAGE_ID=SB.PACKAGE_ID ) bss  where 1=1
"""

cleaned_query = query.replace('\n', ' ')


def connect_to_oracle(username, password, host, port, service_name):
    try:
        dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
        connection = cx_Oracle.connect(user=username, password=password, dsn=dsn)
        return connection
    except cx_Oracle.DatabaseError as e:
        print(f"Database connection error: {e}")
        return None

def query_data(username, password, host, port, service_name, cleaned_query):
    connection = connect_to_oracle(username, password, host, port, service_name)
    
    if connection is None:
        return None
    
    try:    
        cursor = connection.cursor()
        cursor.execute(cleaned_query)
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        return results
    except cx_Oracle.DatabaseError as e:
        print(f"Query execution error: {e}")
        return None


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

def post_to_web_service(web_service_url,xml_data):
    try:
        
        headers = {
        "Content-Type": "text/xml"
        }
        
        response = requests.request("POST", web_service_url, headers=headers, data=xml_data)
        respData = response.content.decode('utf-8')
        new_resp = str(respData[38:])
        soap_response = ET.fromstring(new_resp)
        
        result_status_elem = soap_response.find('.//{http://www.huawei.com/bme/cbsinterface/bcservices}StatusDetail')
        result_status=result_status_elem.text[0:4] if result_status_elem is not None else 'Unknow Error'

        StatusCBS=""
        if result_status=='2001':
            StatusCBS="Bar2way request + 1way debt/Switch"
        elif result_status=='2002':
            StatusCBS="Bar2way Debt&Request/Switch"
        elif result_status=='0001':
            StatusCBS="Bar1way Debt/Switch"
        elif result_status=='1000':
            StatusCBS="Bar1way Request"
        elif result_status=='1001':
            StatusCBS="Bar1way Request&Debt/Switch"
        elif result_status=='1002':
            StatusCBS="Bar1way request + 2way debt/Switch"
        elif result_status=='2000':
            StatusCBS="Bar2way Request"
        elif result_status=='0002':
            StatusCBS="Bar2way Debt/Switch"
        elif result_status=='0000':
            StatusCBS="Activated"  
        else:
            StatusCBS="Unknow"                    

        return StatusCBS

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
def getinfovaluecode (web_service_url,xml_data):
    try:
        
        headers = {
        "Content-Type": "text/xml"
        }
        response = requests.request("POST", web_service_url, headers=headers, data=xml_data)
        respData = response.content.decode('utf-8')
        new_resp = str(respData[38:])
        soap_response = ET.fromstring(new_resp)
        
        # Define namespaces
        namespace = {
            'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            'bcs': 'http://www.huawei.com/bme/cbsinterface/bcservices',
            'bcc': 'http://www.huawei.com/bme/cbsinterface/bccommon',
            'cbs': 'http://www.huawei.com/bme/cbsinterface/cbscommon'
        }
        # Find and extract AcctProperty elements
        acct_properties = soap_response.findall(".//bcc:AcctProperty", namespace)
        result = {}
        # Loop through AcctProperty elements and extract relevant values
        for prop in acct_properties:
            code = prop.find("bcc:Code", namespace).text
            if code in ['CN_ACCT_CC_FLAG', 'CN_ACCT_GROUP_TYPE']:
                value = prop.find("bcc:Value", namespace).text
                result[code] = value

        # Output the extracted values
        for code, value in result.items():
            print(f"{code}: {value}")
                  

        return result

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

results = query_data(username, password, host, port, service_name, cleaned_query)
# if results is not None:
#     for row in results:
#         print(row)
# else:
#     print("No results or an error occurred.")


with open(output_csv_file, mode='w', newline='', encoding='utf-8') as outfile:
    fieldnames = ['SUB_ID','CUST_ID','ISDN','PACKAGE_ID','PRODUCT_ID','SUB_TYPE','CUST_TYPE','NAME_SUB','NAME_CUS','ADDRESS_','PAYFULLADDRESS_','TEL_FAX','STA_DATETIME','FIRST_CONNECT','STATUS_DATE','BSS_STS','PACKAGE_CODE','PACKAGE_NAME','PACKAGE_STATUS','MONTHLY_FEE1','MONTHLY_FEE0','DAILY_FEE','ResultCode', 'ResultDesc', 'Total', 'RemainingDate', 'ExpireDate', 'TotalRemainAmount', 'TotalUsageAmount','Status','Value_']
    # writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer = csv.DictWriter(outfile, fieldnames=fieldnames,delimiter='|')
    writer.writeheader()
    for row in results:
        
        sub_id=row[0]
        cust_id=row[1]
        msisdn=row[2]
        package_id=row[3]
        product_id=row[4]
        sub_type=row[5]
        cust_type=row[6]
        name_sub=row[7]
        name_cust=row[8]
        address=row[9]
        pay_full_address=row[10]
        tel_fax=row[11]
        sta_datetime=row[12]
        first_connect=row[13]
        status_date=row[14]
        bss_status=row[15]
        package_code=row[16]
        package_name=row[17]
        package_sts=row[18]
        package_price= row[19]
        monthly_fee0=row[20]
        dalyfee=row[21]
        xml_data = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:bcs="http://www.huawei.com/bme/cbsinterface/bcservices" xmlns:cbs="http://www.huawei.com/bme/cbsinterface/cbscommon" xmlns:bcc="http://www.huawei.com/bme/cbsinterface/bccommon">
   <soapenv:Header/>
   <soapenv:Body>
      <bcs:QueryCustomerInfoRequestMsg>
         <RequestHeader>
            <cbs:Version>1</cbs:Version>
            <!--Optional:-->
            <cbs:BusinessCode>CBSCENTER</cbs:BusinessCode>
            <cbs:MessageSeq>QUERYCBSINFO</cbs:MessageSeq>
            <cbs:AccessSecurity>
               <cbs:LoginSystemCode>APICBS</cbs:LoginSystemCode>
               <cbs:Password>i85pm92PnsK9VpnFxzPiJYcvE10me2xPuHIycCRbxWbHrEFcT9OECUMF9nni0sGb</cbs:Password>
               <cbs:RemoteIP></cbs:RemoteIP>
            </cbs:AccessSecurity>
         </RequestHeader>
         <QueryCustomerInfoRequest>
            <bcs:QueryObj>
               <bcs:SubAccessCode>
                  <bcc:PrimaryIdentity>{msisdn}</bcc:PrimaryIdentity>
               </bcs:SubAccessCode>
            </bcs:QueryObj>
         </QueryCustomerInfoRequest>
      </bcs:QueryCustomerInfoRequestMsg>
   </soapenv:Body>
</soapenv:Envelope>"""

        # Call the API and get the response
        response = call_api(msisdn, package_price)
        
        result_code = response.get('ResultCode')
        result_desc = response.get('ResultDesc')
        total = response.get('Summary', {}).get('Total')
        remaining_date = response.get('RemainingDate')
        # expire_date = response.get('ExpireDate')
        expire_date = response.get('ExpireDate')
        if expire_date:
            dt=datetime.strptime(expire_date, "%Y-%m-%dT%H:%M:%S.%fZ")
            formatted_expiredate = dt.strftime("%Y-%m-%d %H:%M:%S")


        total_remain_amount = response.get('TotalRemainAmount')
        total_usage_amount = response.get('TotalUsageAmount')


        #CaAPI CBS Customerinfo and get the response
        getresponse_sts=post_to_web_service(web_service_url,xml_data)
        getresponse_value=getinfovaluecode(web_service_url,xml_data)


        
        # Write the data to the output CSV file
        writer.writerow({
            'SUB_ID': sub_id,
            'CUST_ID': cust_id,
            'ISDN': msisdn,
            'PACKAGE_ID': package_id,
            'PRODUCT_ID': product_id,
            'SUB_TYPE': sub_type,
            'CUST_TYPE': cust_type,
            'NAME_SUB': name_sub,
            'NAME_CUS': name_cust,
            'ADDRESS_':address,
            'PAYFULLADDRESS_':pay_full_address,
            'TEL_FAX': tel_fax.rstrip('|')if tel_fax is not None else tel_fax,
            'STA_DATETIME': sta_datetime,
            'FIRST_CONNECT': first_connect,
            'STATUS_DATE':status_date,
            'BSS_STS':bss_status,
            'PACKAGE_CODE': package_code,
            'PACKAGE_NAME': package_name,
            'PACKAGE_STATUS': package_sts,
            'MONTHLY_FEE1': package_price,
            'MONTHLY_FEE0': monthly_fee0,
            'DAILY_FEE': dalyfee,
            'ResultCode': result_code,
            'ResultDesc': result_desc,
            'Total': total,
            'RemainingDate': remaining_date,
            'ExpireDate': formatted_expiredate,
            'TotalRemainAmount': total_remain_amount,
            'TotalUsageAmount': total_usage_amount,
            'Status': getresponse_sts,
            'Value_':getresponse_value
        })

print(f"Data has been successfully written to {output_csv_file}")
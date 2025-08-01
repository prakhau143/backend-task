import requests

# Set the company ID to test
company_id = 1
# URL for the test
url = f"http://127.0.0.1:5001/api/companies/{company_id}/alerts/low-stock"

try:
    # Send a GET request to the endpoint
    response = requests.get(url)
    # Print the status code and response JSON
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
except requests.exceptions.RequestException as e:
    print("Error during the request:", e)

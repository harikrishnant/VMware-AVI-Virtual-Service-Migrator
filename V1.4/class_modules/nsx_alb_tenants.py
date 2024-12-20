#Import modules
import requests
import sys
from tabulate import tabulate

#Class for the Tenant object
class NsxAlbTenant():
    def __init__(self, url, headers, run_id):
        self._url = url + "/api/tenant"
        self._headers = headers
        self._run_id = run_id

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    def get_tenant(self): #Class Method to get the list of all Tenants and to handle API Pagination
        self._list_tenants = []
        self.dict_tenant_url_name = {}
        new_results = True
        page = 1
        while new_results:
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for tenant in new_results:
                if tenant != []:
                    self._list_tenants.append(tenant)
                    self.dict_tenant_url_name[tenant["url"]] = tenant["name"]
            page += 1
        if len(self._list_tenants) != 0:
            self.print_func("\n" + '\033[92m' + f"Authentication Success: You are successfully authenticated against Tenant \"{self._headers['X-Avi-Tenant']}\"" + '\033[0m' + "\n")
        else:
            self.print_func("\n" + '\033[91m' + f"ERROR: Login Failed ({response.status_code})" + '\033[0m' + "\n")
            #Print the error details in table using tabulate function
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
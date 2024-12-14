#Import modules
import requests
import sys
from tabulate import tabulate
import pandas

#Class for the DataScript pbject
class NsxAlbVsDataScriptSet:
    def __init__(self, url, headers, run_id):
        self._url = url + "/api/vsdatascriptset"
        self._headers = headers
        self._run_id = run_id

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    #Class Method to get the list of all datascripts and to handle API Pagination
    def get_vsdatascriptset(self):
        ''' Class Method to fetch the list of all VS DataScript Sets in the Tenant'''
        self._list_vsdatascriptset = []
        self.dict_vsdatascriptset_url_name = {}
        new_results = True
        page = 1
        while new_results: 
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for vsdatascriptset in new_results:
                if vsdatascriptset != []:
                    self._list_vsdatascriptset.append(vsdatascriptset)
                    self.dict_vsdatascriptset_url_name[vsdatascriptset["url"]] = vsdatascriptset["name"]
            page += 1
        if (len(self.dict_vsdatascriptset_url_name) == 0) and (response == False): #Handle a scenario where there are no pools in NSX ALB tenant
            self.print_func("\n" + '\033[91m' + f"ERROR: Scan for VS Datascript Sets Unsuccessful ({response.status_code})" + '\033[0m' + "\n")
            #Print the error details in table using tabulate function
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
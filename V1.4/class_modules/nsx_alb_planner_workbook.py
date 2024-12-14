import os, sys, pandas, requests
from tabulate import tabulate

class NsxAlbPlannerWorkbook:
    def __init__(self, url, headers, dict_tenant_url_name, dict_cloud_url_name, dict_vrfcontext_all_url_name, dict_segroup_all_url_name, list_all_vsvips, run_id):
        self._url = url + "/api/virtualservice"
        self._headers = headers
        self._dict_cloud_url_name = dict_cloud_url_name
        self._dict_tenant_url_name = dict_tenant_url_name
        self._dict_segroup_all_url_name = dict_segroup_all_url_name
        self._dict_vrfcontext_all_url_name = dict_vrfcontext_all_url_name
        self._list_all_vsvips = list_all_vsvips
        self._run_id = run_id

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)
    
    #Class Method to generate migration planner workbook
    def export_planner_workbook(self):
        dict_xls_headers = {
            "Batch" : [],
            "Tenant" : [],
            "Virtual Service" : [],
            "IP Address" : [],
            "VS Hosting Type" : [],
            "Cloud" : [],
            "Target Cloud" : [],
            "VRF Context" : [],
            "Target VRF Context" : [],
            "SE Group" : [],
            "Target SE Group" : [],
            "VIP Migration Strategy (STATIC / IPAM)" : [],
            "Prefix [Run-ID]" : [],
            "Migration Status" : []
        }
        df_xls_headers = pandas.DataFrame(dict_xls_headers)
        df_xls_headers.to_csv("Planner_Workbook.csv", index=False)
        counter = 0

        for each_tenant_url, each_tenant_name in self._dict_tenant_url_name.items():
            self._headers["X-Avi-Tenant"] = each_tenant_name
            new_results = True
            page = 1
            while new_results: #Handles API pagination
                response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
                response_body = response.json()
                new_results = response_body.get("results", []) #Returns False if "results" not found
                for vs in new_results:
                    if vs != []:
                        counter += 1
                        for cloud in self._dict_cloud_url_name:
                            if vs["cloud_ref"] == cloud:
                                xls_cloud_name = self._dict_cloud_url_name[cloud]
                        for vrfcontext in self._dict_vrfcontext_all_url_name:
                            if vs["vrf_context_ref"] == vrfcontext:
                                xls_vrfcontext = self._dict_vrfcontext_all_url_name[vrfcontext]
                        for segroup in self._dict_segroup_all_url_name:
                            if vs["se_group_ref"] == segroup:
                                xls_segroup = self._dict_segroup_all_url_name[segroup]                        
                        if "vsvip_ref" in vs.keys():
                            for each_vsvip in self._list_all_vsvips:
                                if vs["vsvip_ref"] == each_vsvip["url"]:
                                    ip_addr = each_vsvip.get("vip", [])[0].get("ip_address", {}).get("addr", "NONE")
                        else:
                            ip_addr = "NONE"
                        if vs.get("type", "") == "VS_TYPE_VH_PARENT":
                            vs_type = "PARENT"
                        elif vs.get("type", "") == "VS_TYPE_VH_CHILD":
                            vs_type = "CHILD"
                        else:
                            vs_type = "NORMAL"
                        dict_xls_item = {
                            "Batch" : ["<To be Filled>"],
                            "Tenant" : [each_tenant_name],
                            "Virtual Service" : [vs["name"]],
                            "IP Address" : [ip_addr],
                            "VS Hosting Type" : [vs_type],
                            "Cloud" : [xls_cloud_name],
                            "Target Cloud" : ["<To be Filled>"],
                            "VRF Context" : [xls_vrfcontext],
                            "Target VRF Context" : ["<To be Filled>"],
                            "SE Group" : [xls_segroup],
                            "Target SE Group" : ["<To be Filled>"],
                            "VIP Migration Strategy (STATIC / IPAM)" : ["<To be Filled>"],
                            "Prefix [Run-ID]" : ["<To be Filled>"],
                            "Migration Status" : ["PENDING"]
                        }
                        df_xls_item = pandas.DataFrame(dict_xls_item)
                        df_xls_item.to_csv("Planner_Workbook.csv", index=False, header=False, mode="a")
                page += 1
        if (counter == 0) and (response == False): #Handle a scenario where error is encountered to display Virtual Services
            self.print_func("\n" + '\033[91m' + f"ERROR: List NSX ALB Virtual Services Unsuccessful ({response.status_code})" + '\033[0m' + "\n")
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
        if counter == 0: #Handle a scenario where there are no virtual services in NSX ALB
            self.print_func("\n" + '\033[91m' + f"ERROR:No Virtual Services found in the AVI Controller ({response.status_code})" + '\033[0m' + "\n")
            #Print the error details in table using tabulate function
            self.print_func(tabulate([["No VS found", "Possibly no virtual services have been onboarded yet"]], headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()

        df_tabulate_view = pandas.read_csv("Planner_Workbook.csv")
        list_tabulate_view = []
        for index,row in df_tabulate_view.iterrows():
            list_tabulate_view.append([row["Tenant"], row["Virtual Service"], row["IP Address"], row["VS Hosting Type"], row["Cloud"], row["VRF Context"], row["SE Group"]])
        self.print_func(f"\n\nDiscovered {counter} Virtual Services in the AVI Controller cluster, Details are as below:\n")
        self.print_func(tabulate(list_tabulate_view, headers=["Tenant", "Virtual Service", "IP Address", "VS Hosting Type", "Cloud", "VRF Context", "SE Group"], showindex=True, tablefmt="fancy_grid"))
        #Generate xlsx file
        with pandas.ExcelWriter("./Planner_Workbook.xlsx", engine='openpyxl') as writer:
            df_tabulate_view.to_excel(writer, sheet_name="Migration Planner", index=False, )             
        self.print_func("\n" + "\033[92m" + "SUCCESS : Migration Planner Workbook is generated and saved to the current working directory [Planner_Workbook.xlsx]" + "\033[0m" + "\n")
        os.remove("Planner_Workbook.csv")
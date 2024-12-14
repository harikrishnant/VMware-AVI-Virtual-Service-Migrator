#Import modules
import requests
import sys
import pandas
from tabulate import tabulate
from collections import Counter

class NsxAlbVsVip:
    def __init__(self, url, headers, run_id, dict_tenant_url_name={}):
        self._url = url + "/api/vsvip"
        self._headers = headers
        self._run_id = run_id
        self._dict_tenant_url_name = dict_tenant_url_name

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    #Class Method to get the list of all VS Vips and to handle API Pagination
    def get_vsvip_all(self):
        ''' Class Method to fetch the list of all VS VIPs in the Controller'''
        self.list_all_vsvips = []
        self.list_all_vsvips_url_name = {}
        for each_tenant_url, each_tenant_name in self._dict_tenant_url_name.items():
            self._headers["X-Avi-Tenant"] = each_tenant_name        
            new_results = True
            page = 1
            while new_results: 
                response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
                response_body = response.json()
                new_results = response_body.get("results", []) #Returns False if "results" not found
                for vsvip in new_results:
                    if vsvip != []:
                        if vsvip["url"] not in self.list_all_vsvips_url_name:
                            self.list_all_vsvips_url_name[vsvip["url"]] = vsvip["name"]
                            self.list_all_vsvips.append(vsvip)
                page += 1
            if (len(self.list_all_vsvips) == 0) and (response == False): #Handle a scenario where there are no VS VIPs in VMware AVI tenant
                self.print_func("\n" + '\033[91m' + f"ERROR: List VMware AVI VS VIPs Unsuccessful ({response.status_code})" + '\033[0m' + "\n")
                self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
                sys.exit()
    #Class Method to get the list of all VS Vips and to handle API Pagination
    def get_vsvip(self):
        ''' Class Method to fetch the list of all VS VIPs in the Tenant'''
        self.list_vsvips = []
        self.dict_vsvip_url_name = {}
        new_results = True
        page = 1
        while new_results: 
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for vsvip in new_results:
                if vsvip != []:
                    self.list_vsvips.append(vsvip)
                    self.dict_vsvip_url_name[vsvip["url"]] = vsvip["name"]
            page += 1
        if (len(self.dict_vsvip_url_name) == 0) and (response == False): #Handle a scenario where there are no VS VIPs in VMware AVI tenant
            self.print_func("\n" + '\033[91m' + f"ERROR: List VMware AVI VS VIPs Unsuccessful ({response.status_code})" + '\033[0m' + "\n")
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
        
        #Block to scan for VSVIPs with name duplication
        self.df_duplicate_vsvips = pandas.DataFrame(
            {
                "obj_type" : [],
                "obj_name" : [],
                "obj_ref" : [],
                "tenant" : []
            }
        )
        dict_dup_counter = Counter(self.dict_vsvip_url_name.values())
        list_dup_names = [each for each in dict_dup_counter if dict_dup_counter[each] > 1]
        if list_dup_names:
            for each_vsvip_name in list_dup_names:
                for vsvip in self.list_vsvips:
                    if each_vsvip_name == vsvip["name"]:
                        df_dup_each_item = pandas.DataFrame(
                            {
                                "obj_type" : ["vsvip"],
                                "obj_name" : [vsvip["name"]],
                                "obj_ref" : [vsvip["url"]],
                                "tenant" : [self._headers["X-Avi-Tenant"]] 
                            }
                        )
                        self.df_duplicate_vsvips = pandas.concat([self.df_duplicate_vsvips, df_dup_each_item], ignore_index=True)

    def set_vsvip(self, dict_selectedvs_originalvsvipname):
        '''Class method to get the original VS VIP ref and name in required dict format for migration'''
        self.get_vsvip() #get_vsvip method is a pre-requisite for calling set_vsvip method
        self.dict_selectedvsvip_url_name = {}
        self._dict_selectedvs_originalvsvipname = dict_selectedvs_originalvsvipname
        if len(dict_selectedvs_originalvsvipname) != 0:
            for selectedvs, selectedvs_vsvipname in list(dict_selectedvs_originalvsvipname.items()):
                for vsvip_url, vsvip_name in list(self.dict_vsvip_url_name.items()):
                    if selectedvs_vsvipname == vsvip_name:
                        self.dict_selectedvsvip_url_name[vsvip_url] = vsvip_name
        else:
            self.dict_selectedvsvip_url_name = {}

    def create_vsvip(self, body):
        ''' Class Method to create VMware AVI VS VIPs in the Tenant on the selected Cloud Account'''
        response = requests.post(self._url, json=body, headers=self._headers, verify=False )
        if response:
            self.print_func("\n" + '\033[92m' + f"VS-VIP '{response.json()['name']}' successfully created ({response.status_code})" + '\033[0m')
        else:
            self.print_func("\n" + '\033[91m' + f"ERROR: VS-VIP '{body['name']}' creation Failed ({response.status_code})" + '\033[0m' +"\n")
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            self.print_func("\n" + '\033[91m' + "Exiting, Please cleanup any objects that are created, fix the error and re-run the migrator" + '\033[0m' +"\n")
            sys.exit()
        return response.json()
    
    def create_vip_dns(self, dns_domain, vsvip_name):
        dns_updates = []
        dns_host = ""
        for selectedvs,originalvip in self._dict_selectedvs_originalvsvipname.items():
            if originalvip == vsvip_name:
                dns_host = selectedvs
        for each_domain in dns_domain:
            dns_updates.append({
                "algorithm": "DNS_RECORD_RESPONSE_CONSISTENT_HASH",
                "fqdn": dns_host + "." + each_domain,
                "ttl": 30,
                "type": "DNS_RECORD_A" 
            })
        return {
            "dns_info": dns_updates
        }

    def update_vip_dns(self, dns_domain, vsvip_name, vip_dns_info):
        dns_updates = []
        dns_host = [each_dns_info.get("fqdn", "") for each_dns_info in vip_dns_info for each_domain in dns_domain if each_domain in each_dns_info.get("fqdn")]
        
        for selectedvs,originalvip in self._dict_selectedvs_originalvsvipname.items():
            if originalvip == vsvip_name:
                for each_domain in dns_domain:
                    if selectedvs + "." + each_domain not in dns_host:
                        dns_host.append(selectedvs + "." + each_domain)

        for each_fqdn in dns_host:
            dns_updates.append({
                "algorithm": "DNS_RECORD_RESPONSE_CONSISTENT_HASH",
                "fqdn": each_fqdn,
                "ttl": 30,
                "type": "DNS_RECORD_A" 
            })
        return dns_updates

    def migrate_vsvip(self, target_cloud_url, target_vrfcontext_url, target_vrfcontext_tier1path, prefix_tag, tracker_csv, dns_domain, target_ipam_network, target_ipam_subnet, target_ipam_block):
        ''' Class Method to migrate VS VIPs to target cloud account '''
        self._dict_vsvipmigrated_name_url = {}
        self.dict_originalvsvipurl_migratedvsvipurl = {}
        for selectedvsvip_url, selectedvsvip_name in list(self.dict_selectedvsvip_url_name.items()):
            for vsvip in self.list_vsvips:
                if selectedvsvip_name == vsvip["name"]:
                    del vsvip["uuid"]
                    del vsvip["_last_modified"]
                    if "tier1_lr" in vsvip:
                        del vsvip["tier1_lr"]
                    #DNS domain updates
                    if "dns_info" in vsvip and not dns_domain: #Condition 1
                        vsvip.pop("dns_info")
                    elif "dns_info" not in vsvip and dns_domain: #Condition 2
                        vsvip.update(self.create_vip_dns(dns_domain, vsvip.get("name")))
                    elif "dns_info" in vsvip and dns_domain: #Condition 3
                        vsvip["dns_info"] = self.update_vip_dns(dns_domain, vsvip.get("name"), vsvip.get("dns_info"))
                    #IPAM Updates
                    if not target_ipam_network and not target_ipam_subnet:
                        vsvip.get("vip", [])[0]["auto_allocate_ip"] = "false"
                        if "ipam_network_subnet" in vsvip.get("vip",[])[0]:
                            vsvip.get("vip",[])[0].pop("ipam_network_subnet")
                    elif target_ipam_network and target_ipam_subnet:
                        vsvip.get("vip", [])[0]["auto_allocate_ip"] = "true"
                        if "ipam_network_subnet" in vsvip.get("vip",[])[0]:
                            vsvip.get("vip",[])[0].pop("ipam_network_subnet")
                        if "ip_address" in vsvip.get("vip",[])[0]:
                            vsvip.get("vip",[])[0].pop("ip_address")
                        vsvip.get("vip",[])[0].update({
                            "ipam_network_subnet" : target_ipam_block
                        })
                    del vsvip["url"]
                    vsvip["cloud_ref"] = target_cloud_url
                    vsvip["vrf_context_ref"] = target_vrfcontext_url
                    if target_vrfcontext_tier1path != "":
                        vsvip["tier1_lr"] = target_vrfcontext_tier1path                    
                    for item in vsvip["vip"]:
                        if "discovered_networks" in item.keys():
                            del item["discovered_networks"]
                        if "placement_networks" in item.keys():
                            del item["placement_networks"]
                    vsvip["name"] = prefix_tag + "-" + vsvip["name"]
                    migrated_vsvip = self.create_vsvip(vsvip)
                    migrated_vsvip_url = self._url + "/" + migrated_vsvip["uuid"]
                    #Append to tracker
                    dict_migrated_vsvip = {
                                "obj_type" : ["vsvip"],
                                "obj_name" : [migrated_vsvip["name"]],
                                "uuid" : [migrated_vsvip["uuid"]],
                                "url" : [migrated_vsvip_url],
                                "custom_attr" : [""],
                                "status" : ["SUCCESS"]
                            }
                    df_migrated_vsvip = pandas.DataFrame(dict_migrated_vsvip)
                    df_migrated_vsvip.to_csv(tracker_csv, mode='a', index=False, header=False)
                    self._dict_vsvipmigrated_name_url[migrated_vsvip["name"]] = migrated_vsvip_url
                    self.dict_originalvsvipurl_migratedvsvipurl[selectedvsvip_url] = migrated_vsvip_url
        if len(self._dict_vsvipmigrated_name_url) != 0:
            self.print_func("\nThe below VS-VIPs are migrated successfully\n")
            self.print_func(tabulate(list(map(list, self._dict_vsvipmigrated_name_url.items())), headers=["VS-VIP_Name", "VS-VIP_Ref"], showindex=True, tablefmt="fancy_grid"))

    def slice_vsvip_name(self, vsvip_name):
        start_index = vsvip_name.find(self._run_id) + len(self._run_id) + 1
        return vsvip_name[start_index:]
        
    def remove_vsvip_prefix(self, obj_tracker, headers):
        ''' Class Method to remove the prefixes of VMware AVI vsvips '''
        self.get_vsvip() #get_pool methos is a pre-requisite for calling migrate_pool method
        df_obj_track_csv = pandas.read_csv(obj_tracker + "/obj_track-" + self._run_id + ".csv")
        for index, row in df_obj_track_csv.iterrows():
            if row["obj_type"] == "vsvip":
                if row["url"] in self.dict_vsvip_url_name.keys():
                    for vsvip in self.list_vsvips:
                        if row["url"] == vsvip["url"]:
                            if vsvip["name"][:len(self._run_id)] == self._run_id:
                                vsvip["name"] = self.slice_vsvip_name(vsvip["name"])
                                response = requests.put(vsvip["url"], json=vsvip, headers=headers, verify=False )
                                if response:
                                    print("\n" + '\033[92m' + f"vsvip Prefix for {row['obj_name']} removed successfully ({response.status_code}). New Object name is '{response.json()['name']}'" + '\033[0m')
                                    dict_df_obj_remove_prefix_status = {
                                        "obj_type" : ["vsvip"],
                                        "obj_name_old" : [row["obj_name"]],
                                        "obj_name_new" : [response.json()['name']],
                                        "PREFIX_REMOVAL_STATUS" : ["SUCCESS"],
                                        "Error" : [""]
                                    }  
                                    df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                    df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                                else:
                                    print("\n" + '\033[93m' + f"WARNING: vsvip Prefix removal failed for {row['obj_name']} - ({response.status_code})" + '\033[0m')
                                    dict_df_obj_remove_prefix_status = {
                                        "obj_type" : ["vsvip"],
                                        "obj_name_old" : [row["obj_name"]],
                                        "obj_name_new" : [row["obj_name"]],
                                        "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                                        "Error" : [response.json()]
                                    }  
                                    df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                    df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                            else:
                                print("\n" + '\033[93m' + f"WARNING: Prefix tag missing in {vsvip['name']}, hence not renamed" + '\033[0m')
                                dict_df_obj_remove_prefix_status = {
                                        "obj_type" : ["vsvip"],
                                        "obj_name_old" : [row["obj_name"]],
                                        "obj_name_new" : [vsvip["name"]],
                                        "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                                        "Error" : [f"Prefix tag missing in {vsvip['name']}"]
                                    }  
                                df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False) 
                else:
                    print("\n" + '\033[93m' + f"WARNING: vsvip object '{row['obj_name']}' not found, hence skipped" + '\033[0m')
                    dict_df_obj_remove_prefix_status = {
                            "obj_type" : ["vsvip"],
                            "obj_name_old" : [row["obj_name"]],
                            "obj_name_new" : ["NONE"],
                            "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                            "Error" : [f"vsvip object '{row['obj_name']}' not found"]
                        }  
                    df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                    df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)       
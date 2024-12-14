#Import modules
from urllib import response
import requests
import sys
import pandas
from tabulate import tabulate
from collections import Counter

#Class for the Virtual Service Object
class NsxAlbVirtualService:
    def __init__(self, url, headers, **kwargs):
        self._url = url + "/api/virtualservice"
        self._headers = headers
        self._dict_cloud_url_name = kwargs.get("dict_cloud_url_name", {})
        self._dict_pool_url_name = kwargs.get("dict_pool_url_name", {})
        self._dict_poolgroup_url_name = kwargs.get("dict_poolgroup_url_name", {})
        self._dict_vsvip_url_name = kwargs.get("dict_vsvip_url_name", {})
        self._run_id = kwargs.get("run_id", "")
        self._list_vsvips = kwargs.get("list_vsvips", [])
        self._originalvsurl_migratedvsurl = {}
        self._migration_mode = kwargs.get("migration_mode", "")

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    # Class Method to get the list of all Virtual Services and to handle API Pagination
    def get_virtualservice(self):
        self._list_virtualservices = [] #Returns a list of dictionaries of all virtual services in the tenant 
        self.dict_virtualservice_url_name = {}
        self._list_virtualservices_parentonly = []
        self._list_virtualservices_childonly = []
        self._dict_vs_originalpoolname = {} #Retuns a dictionary of virtual service (key) and original pool name, original poolgroup name and "POOL_NONE" if no pools/poolgroups found (value)
        self._dict_vs_originalpoolgroupname = {}
        self._dict_vs_originalvsvipname = {}
        self._list_parent_vs = []
        self._list_child_vs = []
        self._dict_parentvs_childvs = {}
        df_display = pandas.DataFrame({
            "Tenant" : [],
            "Virtual Service" : [],
            "IP Address" : [],
            "Pool / PoolGroup" : [],
            "Cloud" : [],
            "VS Hosting Type" : []
        })

        new_results = True
        page = 1
        #Defining null value for dynamic variables:
        pool_name = ""
        cloud_name = ""
        vs_type = ""
        ip_addr = ""

        while new_results: #Handles API pagination
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for vs in new_results:
                if vs != []:
                    self._list_virtualservices.append(vs)
                    self.dict_virtualservice_url_name[vs["url"]] = vs["name"]
                    if vs.get("type", "") == "VS_TYPE_VH_PARENT":
                        self._list_parent_vs.append(vs.get("name"))
                        self._list_virtualservices_parentonly.append(vs)
                        vs_type = "PARENT"
                    elif vs.get("type", "") == "VS_TYPE_VH_CHILD":
                        self._list_child_vs.append(vs.get("name"))
                        self._list_virtualservices_childonly.append(vs)
                        vs_type = "CHILD"
                    else:
                        vs_type = "NORMAL"
                    for cloud in self._dict_cloud_url_name:
                        if vs["cloud_ref"] == cloud:
                            cloud_name = self._dict_cloud_url_name[cloud]
                    if "vsvip_ref" in vs.keys():
                        for vsvip in self._list_vsvips:
                            if vs["vsvip_ref"] == vsvip["url"]:
                                ip_addr = vsvip.get("vip", [])[0].get("ip_address", {}).get("addr", "NONE")
                                self._dict_vs_originalvsvipname[vs["name"]] = vsvip["name"]
                    else:
                        ip_addr = "NONE"
                        self._dict_vs_originalvsvipname[vs["name"]] = "VSVIP_NONE"
                    if "pool_ref" in vs.keys():
                        for pool in self._dict_pool_url_name:                        
                            if vs["pool_ref"] == pool:
                                self._dict_vs_originalpoolname[vs["name"]] = self._dict_pool_url_name[pool]
                                pool_name = self._dict_pool_url_name[pool]
                    elif "pool_group_ref" in vs.keys():
                        for poolgroup in self._dict_poolgroup_url_name:                        
                            if vs["pool_group_ref"] == poolgroup:
                                self._dict_vs_originalpoolname[vs["name"]] = self._dict_poolgroup_url_name[poolgroup] + " (Pool_Group)"
                                self._dict_vs_originalpoolgroupname[vs["name"]] = self._dict_poolgroup_url_name[poolgroup]
                                pool_name = self._dict_poolgroup_url_name[poolgroup] + " (Pool_Group)"
                    else:
                        self._dict_vs_originalpoolname[vs["name"]] = "POOL_NONE"
                        pool_name = "NONE (PENDING POLICY SCAN)"
                    df_each_item = pandas.DataFrame({
                        "Tenant" : [self._headers.get("X-Avi-Tenant", "UNKNOWN")],
                        "Virtual Service" : [vs["name"]],
                        "IP Address" : [ip_addr],
                        "Pool / PoolGroup" : [pool_name],
                        "Cloud" : [cloud_name],
                        "VS Hosting Type" : [vs_type]
                    })
                    df_display = pandas.concat([df_display, df_each_item], ignore_index=True)
            page += 1
        
        #Create dict for Parent to Child relationships
        for each_parent_vs in self._list_virtualservices_parentonly:
            list_child_names = []
            for each_child_vs in self._list_virtualservices_childonly:
                if each_parent_vs.get("url", "") == each_child_vs.get("vh_parent_vs_ref", ""):
                    list_child_names.append(each_child_vs.get("name"))
            
            self._dict_parentvs_childvs.update(
                 {
                     each_parent_vs.get("name") : list_child_names
                 }
             )

        if df_display.empty and (response == False): #Handle a scenario where error is encountered to display Virtual Services
            self.print_func("\n" + '\033[91m' + f"ERROR: List VMware AVI Virtual Services Unsuccessful ({response.status_code})" + '\033[0m' + "\n")
            #Print the error details in table using tabulate function
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
        
        if df_display.empty: #Handle a scenario where there are no virtual services in VMware AVI tenant
            self.print_func("\n" + '\033[91m' + f"ERROR: No Virtual Services found in the tenant ({response.status_code})" + '\033[0m' + "\n")
            #Print the error details in table using tabulate function
            self.print_func(tabulate([["No VS found", "Please check if you are in the correct tenant context."]], headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
        
        #Block to scan for Virtual Services with name duplication
        if self._migration_mode == "migrate":
            self.df_duplicate_virtualservices = pandas.DataFrame(
                {
                    "obj_type" : [],
                    "obj_name" : [],
                    "obj_ref" : [],
                    "tenant" : []
                }
            )
            dict_dup_counter = Counter(self.dict_virtualservice_url_name.values())
            list_dup_names = [each for each in dict_dup_counter if dict_dup_counter[each] > 1]
            if list_dup_names:
                for each_virtualservice_name in list_dup_names:
                    for virtualservice in self._list_virtualservices:
                        if each_virtualservice_name == virtualservice["name"]:
                            df_dup_each_item = pandas.DataFrame(
                                {
                                    "obj_type" : ["virtualservice"],
                                    "obj_name" : [virtualservice["name"]],
                                    "obj_ref" : [virtualservice["url"]],
                                    "tenant" : [self._headers["X-Avi-Tenant"]] 
                                }
                            )
                            self.df_duplicate_virtualservices = pandas.concat([self.df_duplicate_virtualservices, df_dup_each_item], ignore_index=True)

        #Print Virtual Services using Tabulate
        if self._migration_mode == "migrate":
            if not df_display.empty:
                list_display = []
                for index,row in df_display.iterrows():
                    list_display.append([row["Tenant"], row["Virtual Service"], row["IP Address"], row["Pool / PoolGroup"], row["Cloud"], row["VS Hosting Type"]])
                self.print_func(tabulate(list_display, headers=["Tenant", "Virtual Service", "IP Address", "Pool / PoolGroup", "Cloud", "VS Hosting Type"], showindex=True, tablefmt="fancy_grid"))


    def set_virtualservice(self):
        ''' Method to select the list of virtual services to be migrated and create a dictionary of virtual service and original pool mapping '''
        self._dict_vs_typo_errors = {} #Dictionary to catch any VS type errors
        self.dict_selectedvs_originalpoolname = {}
        self.dict_selectedvs_originalpoolgroupname = {}
        self.dict_selectedvs_originalvsvipname = {}
        list_selected_parent_vs = []
        list_selected_child_vs = []
        list_selected_normal_vs = []
        curated_selected_vs = []

        self._list_vs_selected = input(f"\nEnter Virtual Services to migrate separated by comma (,) and without quotes. Type 'all' for all VS \n(Eg: VS1,VS2,VS3 or all)\n\n").split(",")
        if self._list_vs_selected == ["all", ] or self._list_vs_selected == ["ALL", ]:
            self._list_vs_selected = list(self._dict_vs_originalpoolname.keys())
        for vs_selected in self._list_vs_selected:
            if vs_selected in list(self._dict_vs_originalpoolname.keys()):
                if vs_selected in self._dict_parentvs_childvs.keys():
                    list_selected_parent_vs.append(vs_selected)
                    list_selected_child_vs.append(self._dict_parentvs_childvs[vs_selected]) #List of lists
                elif vs_selected in [item for each_list in self._dict_parentvs_childvs.values() for item in each_list]: #Flatten list of lists
                    continue
                else:
                    list_selected_normal_vs.append(vs_selected)
            else:
                self._dict_vs_typo_errors[vs_selected] = "VS not found. It's a possible typo, make sure the name is entered correctly"

        flatten_list_selected_child_vs = [item for each_list in list_selected_child_vs for item in each_list]

        for each_list in [list_selected_normal_vs, list_selected_parent_vs, flatten_list_selected_child_vs]:
            curated_selected_vs.extend(each_list) #VS'es need to be migrated in this order - Normal first, Parent second and Child third.

        for each_curated_selected_vs in curated_selected_vs:      
            for vs in self._dict_vs_originalpoolname:
                if each_curated_selected_vs == vs:
                    self.dict_selectedvs_originalpoolname[vs] = self._dict_vs_originalpoolname[vs]
            for vs in self._dict_vs_originalpoolgroupname:
                if each_curated_selected_vs == vs:
                    self.dict_selectedvs_originalpoolgroupname[vs] = self._dict_vs_originalpoolgroupname[vs]
            for vs in self._dict_vs_originalvsvipname:
                if each_curated_selected_vs == vs:
                    self.dict_selectedvs_originalvsvipname[vs] = self._dict_vs_originalvsvipname[vs]

        if len(self._dict_vs_typo_errors) != 0:
            self.print_func("\n" + '\033[93m' + f"WARNING: The below Virtual Services you entered were not found and will be skipped" + '\033[0m' + "\n")
            self.print_func(tabulate(list(map(list, self._dict_vs_typo_errors.items())), headers=["Virtual Service", "Error_Details"], showindex=True, tablefmt="fancy_grid"))
            prompt = input("\n" + '\033[93m' + "Continue? The above Virtual Services will be skipped (Y/N) " + '\033[0m').lower()
            if prompt == "n" or prompt == "no":
                self.print_func("\n" + '\033[91m' + "ERROR: Invalid Virtual Services Detected, Aborting..." + '\033[0m' + "\n")
                sys.exit()
            elif prompt == "y" or prompt == "yes":
                pass
            else:
                self.print_func("\n" + '\033[91m' + "ERROR: Invalid Option, Aborting..." + '\033[0m' + "\n")
                sys.exit()

        if len(self.dict_selectedvs_originalpoolname) != 0:
            self.print_func("\n" + '\033[95m' + f"INFO: The below Virtual Services are selected for migration in the current migration batch" + '\033[0m' + "\n")
            self.print_func(tabulate(list(map(list, self.dict_selectedvs_originalpoolname.items())), headers=["Virtual Service", "Pool / Pool_Group"], showindex=True, tablefmt="fancy_grid"))
            prompt = input("\n" + "Proceed with migration? (Y/N) ").lower()
            if prompt == "n" or prompt == "no":
                self.print_func("\n" + '\033[91m' + "ERROR: Migration Cancelled by User..." + '\033[0m' + "\n")
                sys.exit()
            elif prompt == "y" or prompt == "yes":
                pass
            else:
                self.print_func("\n" + '\033[91m' + "ERROR: Invalid Option, Aborting..." + '\033[0m' + "\n")
                sys.exit()
        else:
            self.print_func("\n" + '\033[91m' + "ERROR: No Virtual Services selected, Exiting.." + '\033[0m' + "\n")
            sys.exit()

    def get_virtualservice_policy(self, dict_httppolicyset_url_name):
        ''' Method to scan the selected VirtualServices for any HTTP Policy Sets '''
        self.dict_vs_httppolicysetname = {}
        self._dict_vs_httppolicyset_none = {}
        for selected_vs in self.dict_selectedvs_originalpoolname:
            for vs in self._list_virtualservices:
                if selected_vs == vs["name"]:
                    if "http_policies" in list(vs.keys()):
                        for policy_url in dict_httppolicyset_url_name:
                            if vs["http_policies"][0]["http_policy_set_ref"] == policy_url:
                                self.dict_vs_httppolicysetname[vs["name"]] = dict_httppolicyset_url_name[policy_url]
                    else:
                        self._dict_vs_httppolicyset_none[vs["name"]] = "POLICY_NONE"
        if len(self.dict_vs_httppolicysetname) != 0:
            self.print_func(f"\nThe selected Virtual Services for migration has the below HTTP Policy Sets defined. They will now be scanned for any Content switching Pools / PoolGroups\n")
            self.print_func(tabulate(list(map(list, self.dict_vs_httppolicysetname.items())), headers=["Virtual Service", "HTTPPolicySet_Name"], showindex=True, tablefmt="fancy_grid"))
        else:
            self.print_func(f"\nThe selected Virtual Services for migration has no HTTP Policy Sets defined\n")
            self.print_func(tabulate(list(map(list, self._dict_vs_httppolicyset_none.items())), headers=["Virtual Service", "HTTPPolicySet_Name"], showindex=True, tablefmt="fancy_grid"))

    def create_virtualservice(self, body):
        ''' Class Method to create VMware AVI VS in the Tenant on the selected Cloud Account'''
        response = requests.post(self._url, json=body, headers=self._headers, verify=False)
        if response:
            self.print_func("\n" + '\033[92m' + f"Virtual Service '{response.json()['name']}' successfully created ({response.status_code})" + '\033[0m')
        else:
            self.print_func("\n" + '\033[91m' + f"ERROR: Virtual Service '{body['name']}' creation Failed ({response.status_code})" + '\033[0m')
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            self.print_func("\n" + '\033[91m' + "Exiting, Please cleanup any objects that are created, fix the error and re-run the migrator" + '\033[0m')
            sys.exit()
        return response.json()

    def migrate_virtualservice(self, dict_originalpoolurl_migratedpoolurl, dict_originalpoolgroupurl_migratedpoolgroupurl, dict_vs_migratedhttppolicyseturl, dict_originalvsvipurl_migratedvsvipurl, target_cloud_url, target_vrfcontext_url, target_segroup_url, dict_vsdatascriptset_url_name, dict_wafpolicy_learninggroup_url_name, dict_l4policyset_url_name, prefix_tag, tracker_csv, skipped_settings_csv):
        '''Class method to migrate Virtual Services to the selected target cloud account'''
        self._dict_migratedvs_name_url = {}
        for selected_vs, originalpool_name in list(self.dict_selectedvs_originalpoolname.items()):
            for vs in self._list_virtualservices:
                if selected_vs == vs["name"]:
                    vs_url = vs["url"]
                    del vs["_last_modified"]
                    del vs["url"]
                    del vs["uuid"]
                    del vs["cloud_type"]
                    cust_attr = "normal" #Required to sort for prefix-removal and cleanup
                    if "discovered_networks" in list(vs.keys()):
                        del vs["discovered_networks"]
                    if "first_se_assigned_time" in list(vs.keys()):
                        del vs["first_se_assigned_time"]
                    if "requested_resource" in list(vs.keys()):
                        del vs["requested_resource"]
                    if "se_list" in list(vs.keys()):
                        del vs["se_list"]
                    if "vip_runtime" in list(vs.keys()):
                        del vs["vip_runtime"]
                    if "version" in list(vs.keys()):
                        del vs["version"]
                    if "http_policies" in list(vs.keys()):
                        for original_vs, httppolicyset in list(dict_vs_migratedhttppolicyseturl.items()):
                            if original_vs == vs["name"]:
                                vs["http_policies"][0]["http_policy_set_ref"] = dict_vs_migratedhttppolicyseturl[original_vs]
                    if "vs_datascripts" in list(vs.keys()):
                        for each_ds in vs["vs_datascripts"]:
                            for ds_url, ds_name in dict_vsdatascriptset_url_name.items():
                                if each_ds.get("vs_datascript_set_ref", "") == ds_url:
                                    skipped_settings_df = pandas.DataFrame(
                                        {
                                            "obj_type": ["virtualservice"],
                                            "obj_name_old": [vs["name"]],
                                            "obj_name_new": [prefix_tag + "-" + vs["name"]],
                                            "skipped_object_type": ["vsdatascriptset"],
                                            "skipped_object_name": [ds_name],
                                            "reason" : ["Unable to verify if the Datascript has reference to pools / poolgroups in the old cloud connector"],
                                            "recommendation" : ["Manually verify the datascript and update references to pools or poolgroups that are migrated to target cloud connector"]
                                        }
                                    )
                                    skipped_settings_df.to_csv(skipped_settings_csv, mode="a", header=False, index=False)
                        del vs["vs_datascripts"]
                    if "waf_policy_ref" in list(vs.keys()):
                        for each_wafpolicy_learning_url, each_wafpolicy_learning_name in dict_wafpolicy_learninggroup_url_name.items():
                            if vs["waf_policy_ref"] == each_wafpolicy_learning_url:
                                skipped_settings_df = pandas.DataFrame(
                                        {
                                            "obj_type": ["virtualservice"],
                                            "obj_name_old": [vs["name"]],
                                            "obj_name_new": [prefix_tag + "-" + vs["name"]],
                                            "skipped_object_type": ["wafpolicy"],
                                            "skipped_object_name": [each_wafpolicy_learning_name],
                                            "reason" : ["WAF policy has Learning Group enabled, which cannot be shared across multiple virtual services"],
                                            "recommendation" : ["Manually clone the WAF policy from the VMware AVI load balancer UI, and attach to the migrated virtual service"]
                                        }
                                    ) 
                                skipped_settings_df.to_csv(skipped_settings_csv, mode="a", header=False, index=False)
                                del vs["waf_policy_ref"] #Remove WAF Policy with learning groups defined
                    if "l4_policies" in list(vs.keys()):
                        for each_l4policy in vs["l4_policies"]:
                            for l4policy_url, l4policy_name in dict_l4policyset_url_name.items():
                                if each_l4policy.get("l4_policy_set_ref", "") == l4policy_url:
                                    skipped_settings_df = pandas.DataFrame(
                                        {
                                            "obj_type": ["virtualservice"],
                                            "obj_name_old": [vs["name"]],
                                            "obj_name_new": [prefix_tag + "-" + vs["name"]],
                                            "skipped_object_type": ["l4policyset"],
                                            "skipped_object_name": [l4policy_name],
                                            "reason" : ["Migration of virtual services with L4 Policy Sets is not supported in the current release"],
                                            "recommendation" : ["Manually migrate the Pools / Poolgroups in the L4 Policy set using the VMware AVI load balancer UI and apply the new L4 policy set to the migrated virtual service"]
                                        }
                                    )
                                    skipped_settings_df.to_csv(skipped_settings_csv, mode="a", header=False, index=False)
                        del vs["l4_policies"]
                    if "pool_ref" in list(vs.keys()):
                        for original_pool, migrated_pool in list(dict_originalpoolurl_migratedpoolurl.items()):
                            if vs["pool_ref"] == original_pool:
                                vs["pool_ref"] = migrated_pool
                    if "pool_group_ref" in list(vs.keys()):
                        for original_poolgroup, migrated_poolgroup in list(dict_originalpoolgroupurl_migratedpoolgroupurl.items()):
                            if vs["pool_group_ref"] == original_poolgroup:
                                vs["pool_group_ref"] = migrated_poolgroup
                    if "vsvip_ref" in list(vs.keys()):
                        for originalvsvip, migratedvsvip in list(dict_originalvsvipurl_migratedvsvipurl.items()):
                            if vs["vsvip_ref"] == originalvsvip:
                                vs["vsvip_ref"] = migratedvsvip
                    if vs["type"] == "VS_TYPE_VH_PARENT":
                            cust_attr = "parent"
                            if "vh_child_vs_uuid" in list(vs.keys()):
                                del vs["vh_child_vs_uuid"]
                    if vs["type"] == "VS_TYPE_VH_CHILD":
                            cust_attr = "child"
                            if "vh_parent_vs_ref" in list(vs.keys()):
                                for each_uuid in self._originalvsurl_migratedvsurl:
                                    if vs["vh_parent_vs_ref"] == each_uuid:
                                        vs["vh_parent_vs_ref"] = self._originalvsurl_migratedvsurl[each_uuid]
                    vs["enabled"] = "false"
                    vs["traffic_enabled"] = "false"
                    vs["name"] = prefix_tag + "-" + vs["name"]
                    vs["cloud_ref"] = target_cloud_url
                    vs["se_group_ref"] = target_segroup_url
                    vs["vrf_context_ref"] = target_vrfcontext_url
                    migrated_vs = self.create_virtualservice(vs)
                    migrated_vs_url = self._url + "/" + migrated_vs["uuid"]
                    #Track UUIDs in a class variable
                    self._originalvsurl_migratedvsurl.update({
                        vs_url : migrated_vs_url
                    })
                    #Adding to tracker
                    dict_migrated_vs = {
                                "obj_type" : ["virtualservice"],
                                "obj_name" : [migrated_vs["name"]],
                                "uuid" : [migrated_vs["uuid"]],
                                "url" : [migrated_vs_url],
                                "custom_attr" : [cust_attr],
                                "status" : ["SUCCESS"]
                            }
                    df_migrated_vs = pandas.DataFrame(dict_migrated_vs)
                    df_migrated_vs.to_csv(tracker_csv, mode='a', index=False, header=False)
                    self._dict_migratedvs_name_url[migrated_vs["name"]] = migrated_vs_url
        self.print_func(f"\nThe below Virtual Services are migrated successfully\n")
        self.print_func(tabulate(list(map(list,self._dict_migratedvs_name_url.items())), headers=["Migrated_VS_name", "Migrated_VS_Ref"], showindex=True, tablefmt="fancy_grid"))


    def slice_virtualservice_name(self, virtualservice_name):
        start_index = virtualservice_name.find(self._run_id) + len(self._run_id) + 1
        return virtualservice_name[start_index:]
        
    def remove_virtualservice_prefix(self, obj_tracker, headers):
        ''' Class Method to remove the prefixes of VMware AVI virtualservices '''
        self.get_virtualservice() #get_virtualservice methos is a pre-requisite for calling migrate_virtualservice method
        df_obj_track_csv = pandas.read_csv(obj_tracker + "/obj_track-" + self._run_id + ".csv")
        for index, row in df_obj_track_csv.iterrows():
            if row["obj_type"] == "virtualservice":
                if row["url"] in self.dict_virtualservice_url_name.keys():
                    for virtualservice in self._list_virtualservices:
                        if row["url"] == virtualservice["url"]:
                            if virtualservice["name"][:len(self._run_id)] == self._run_id:
                                virtualservice["name"] = self.slice_virtualservice_name(virtualservice["name"])
                                response = requests.put(virtualservice["url"], json=virtualservice, headers=headers, verify=False )
                                if response:
                                    print("\n" + '\033[92m' + f"virtualservice Prefix for {row['obj_name']} removed successfully ({response.status_code}). New Object name is '{response.json()['name']}'" + '\033[0m')
                                    dict_df_obj_remove_prefix_status = {
                                        "obj_type" : ["virtualservice"],
                                        "obj_name_old" : [row["obj_name"]],
                                        "obj_name_new" : [response.json()['name']],
                                        "PREFIX_REMOVAL_STATUS" : ["SUCCESS"],
                                        "Error" : [""]
                                    }  
                                    df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                    df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                                else:
                                    print("\n" + '\033[93m' + f"WARNING: virtualservice Prefix removal failed for {row['obj_name']} - ({response.status_code})" + '\033[0m')
                                    dict_df_obj_remove_prefix_status = {
                                        "obj_type" : ["virtualservice"],
                                        "obj_name_old" : [row["obj_name"]],
                                        "obj_name_new" : [row["obj_name"]],
                                        "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                                        "Error" : [response.json()]
                                    }  
                                    df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                    df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                            else:
                                print("\n" + '\033[93m' + f"WARNING: Prefix tag missing in {virtualservice['name']}, hence not renamed" + '\033[0m')
                                dict_df_obj_remove_prefix_status = {
                                        "obj_type" : ["virtualservice"],
                                        "obj_name_old" : [row["obj_name"]],
                                        "obj_name_new" : [virtualservice["name"]],
                                        "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                                        "Error" : [f"Prefix tag missing in {virtualservice['name']}"]
                                    }  
                                df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                else:
                    print("\n" + '\033[93m' + f"WARNING: virtual service object '{row['obj_name']}' not found, hence skipped" + '\033[0m')
                    dict_df_obj_remove_prefix_status = {
                            "obj_type" : ["virtualservice"],
                            "obj_name_old" : [row["obj_name"]],
                            "obj_name_new" : ["NONE"],
                            "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                            "Error" : [f"virtual service object '{row['obj_name']}' not found"]
                        }  
                    df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                    df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)               

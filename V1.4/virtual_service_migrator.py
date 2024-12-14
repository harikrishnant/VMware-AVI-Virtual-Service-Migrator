#Import Modules
import urllib3, sys, argparse, pandas, json, os, shutil
from datetime import datetime
from getpass import getpass
from tabulate import tabulate
from class_modules import *

def main():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print(titles_logo)

    #Block for Argparse and subcommands for migrate, prefix_removal and cleanup
    parser = argparse.ArgumentParser(description="VMware AVI Virtual Service Migrator v1.4 Flags", epilog="Credits : Harikrishnan T (@hari5611). Visit vxplanet.com for more information", add_help=True)
    parser.add_argument("-v", "--version", action="version", version="VMware AVI Virtual Service Migrator version 1.4")
    subparsers = parser.add_subparsers(title='Valid Subcommands', help="Available Subcommands")
    parser_migrate = subparsers.add_parser("migrate", help='Migrate Virtual Services across Cloud accounts (migrate -h for help)')
    parser_cleanup = subparsers.add_parser("cleanup", help='Cleanup objects from a failed run using the run ID (cleanup -h for help)')
    parser_remove_prefix = subparsers.add_parser("remove_prefix", help='Remove the prefix from objects after a successful migration (remove_prefix -h for help)')  
    parser_generate_workbook = subparsers.add_parser("generate_planner_workbook", help='Generate Migration Planner Workbook (generate_planner_workbook -h for help)')  
    parser_migrate.add_argument("-u", "--username", action="store", type=str, metavar="USERNAME", dest="username", required=True, help="User with system admin privileges to VMware AVI")
    parser_migrate.add_argument("-p", "--password", action="store", type=str, metavar="PASSWORD", dest="password", required=False, help="User Password")
    parser_migrate.add_argument("-i", "--controller_ip", action="store", type=str, metavar="CONTROLLER_IP/FQDN", dest="controller_ip", required=True, help="VMware AVI Controller IP or FQDN")
    parser_migrate.add_argument("-t", "--tenant", action="store", type=str, metavar="NSX_ALB_Tenant", dest="nsx_alb_tenant", required=True, help="VMware AVI Tenant. Currently only intra-Tenant migration is supported by this tool")
    parser_migrate.add_argument("-a", "--api-version", action="store", type=str, metavar="API_VERSION", dest="api_version", required=True, help="VMware AVI API version to use for migration. Should be either same or below the controller API version")
    parser_migrate.add_argument("-c", "--target_cloud", action="store", type=str, metavar="TARGET_CLOUD", dest="target_cloud_name", required=True, help="VMware AVI target Cloud account for migration")
    parser_migrate.add_argument("-r", "--target_vrf", action="store", type=str, metavar="TARGET_VRF", dest="target_vrf_name", required=True, help="VMware AVI target VRF Context for migration")
    parser_migrate.add_argument("-s", "--target_seg", action="store", type=str, metavar="TARGET_SERVICE_ENGINE_GROUP", dest="target_seg_name", required=True, help="VMware AVI target Service Engine Group for migration")
    parser_migrate.add_argument("-d", "--target_dns_domain", action="store", type=str, metavar="TARGET_APPLICATION_DNS_DOMAINS", dest="target_dns_domain", required=False, help="VMware AVI target DNS Application Domains")    
    parser_migrate.add_argument("-n", "--target_ipam_network", action="store", type=str, metavar="TARGET_IPAM_NETWORK_NAME", dest="target_ipam_network", required=False, help="VMware AVI target IPAM Network name")
    parser_migrate.add_argument("-S", "--target_ipam_subnet", action="store", type=str, metavar="TARGET IPAM SUBNET", dest="target_ipam_subnet", required=False, help="VMware AVI target IPAM subnet (x.x.x.x/x)")    
    parser_migrate.add_argument("-P", "--prefix", action="store", type=str, metavar="OBJECT_PREFIX", dest="prefix", required=True, help="Prefix for objets migrated by VMware AVI")
    parser_migrate.set_defaults(which="migrate")
    parser_cleanup.add_argument("-i", "--controller_ip", action="store", type=str, metavar="CONTROLLER_IP/FQDN", dest="controller_ip", required=True, help="VMware AVI Controller IP or FQDN")
    parser_cleanup.add_argument("-u", "--username", action="store", type=str, metavar="USERNAME", dest="username", required=True, help="User with system admin privileges to VMware AVI")
    parser_cleanup.add_argument("-p", "--password", action="store", type=str, metavar="PASSWORD", dest="password", required=False, help="User Password")
    parser_cleanup.add_argument("-r", "--run_id", action="store", type=str, metavar="RUN_ID", dest="prefix", required=True, help="Run ID (Prefix name) of the previous run")
    parser_cleanup.set_defaults(which="cleanup")
    parser_remove_prefix.add_argument("-i", "--controller_ip", action="store", type=str, metavar="CONTROLLER_IP/FQDN", dest="controller_ip", required=True, help="VMware AVI Controller IP or FQDN")
    parser_remove_prefix.add_argument("-u", "--username", action="store", type=str, metavar="USERNAME", dest="username", required=True, help="User with system admin privileges to VMware AVI")
    parser_remove_prefix.add_argument("-p", "--password", action="store", type=str, metavar="PASSWORD", dest="password", required=False, help="User Password")
    parser_remove_prefix.add_argument("-r", "--run_id", action="store", type=str, metavar="RUN_ID", dest="prefix", required=True, help="Run ID (Prefix name) of the run")
    parser_remove_prefix.set_defaults(which="remove_prefix")
    parser_generate_workbook.add_argument("-i", "--controller_ip", action="store", type=str, metavar="CONTROLLER_IP/FQDN", dest="controller_ip", required=True, help="VMware AVI Controller IP or FQDN")
    parser_generate_workbook.add_argument("-u", "--username", action="store", type=str, metavar="USERNAME", dest="username", required=True, help="User with system admin privileges to VMware AVI")
    parser_generate_workbook.add_argument("-p", "--password", action="store", type=str, metavar="PASSWORD", dest="password", required=False, help="User Password")
    parser_generate_workbook.add_argument("-a", "--api-version", action="store", type=str, metavar="API_VERSION", dest="api_version", required=True, help="VMware AVI API version. Should be either same or below the controller API version")
    parser_generate_workbook.set_defaults(which="generate_planner_workbook")
    args = parser.parse_args() #Creates a Namespace Object. The parameters are attributes of this object

    # Checking if subcommands are called with the main script
    if not hasattr(args, "which"):
        print(tabulate([["No Operation requested", "Select from one of the subcommands below:"]], headers=["Error", "Description"], showindex=True, tablefmt="fancy_grid"))
        parser.parse_args(["-h"])

    #Custom Print function   
    def print_func(item):
        print(item)                
        with open(f"./logs/run-{args.prefix}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    URL = "https://" + args.controller_ip
    
    # Block for setting API Request headers for migrate, cleanup and remove_prefix subcommands
    if args.which == "cleanup":        
        print("\n" + '\033[95m' + f"\nTASK NAME : Start CLEANUP for Run-ID \"{args.prefix}\"" + "\033[0m" + "\n")
        if os.path.exists("./Tracker-DONOTDELETE"):
            if ("infra_track" + "-" + args.prefix + ".json" in os.listdir("./Tracker-DONOTDELETE")) and ("obj_track" + "-" + args.prefix + ".csv" in os.listdir("./Tracker-DONOTDELETE")):
                with open("./Tracker-DONOTDELETE/infra_track" + "-" + args.prefix + ".json") as infra_track:
                    dict_infra_track = json.load(infra_track)
                    headers = {
                                "Content-Type": "application/json",
                                "Referer": URL,
                                "Accept-Encoding": "application/json",
                                "X-Avi-Tenant": dict_infra_track["nsx_alb_tenant"],
                                "X-Avi-Version": dict_infra_track["api_version"]
                            }
            else:
                print(tabulate([["Tracking information for Run ID not found", "Please enter a valid Run ID"]], headers=["Error", "Description"], showindex=True, tablefmt="fancy_grid"))
                sys.exit() 
        else:
                print(tabulate([["Tracking directory \"./Tracker-DONOTDELETE\" not found", "Please ensure tracking dir with the Run ID information is available"]], headers=["Error", "Description"], showindex=True, tablefmt="fancy_grid"))  
                sys.exit() 
    
    if args.which == "remove_prefix":
        print("\n" + '\033[95m' + f"\nTASK NAME : Start Remove_Prefix for Run-ID \"{args.prefix}\"" + "\033[0m" + "\n")        
        if os.path.exists("./Tracker-DONOTDELETE"):
            if ("infra_track" + "-" + args.prefix + ".json" in os.listdir("./Tracker-DONOTDELETE")) and ("obj_track" + "-" + args.prefix + ".csv" in os.listdir("./Tracker-DONOTDELETE")):
                with open("./Tracker-DONOTDELETE/infra_track" + "-" + args.prefix + ".json") as infra_track:
                    dict_infra_track = json.load(infra_track)
                    headers = {
                                "Content-Type": "application/json",
                                "Referer": URL,
                                "Accept-Encoding": "application/json",
                                "X-Avi-Tenant": dict_infra_track["nsx_alb_tenant"],
                                "X-Avi-Version": dict_infra_track["api_version"]
                            }
            else:
                print(tabulate([["Tracking information for Run ID not found", "Please enter a valid Run ID"]], headers=["Error", "Description"], showindex=True, tablefmt="fancy_grid"))
                sys.exit() 
        else:
                print(tabulate([["Tracking directory \"./Tracker-DONOTDELETE\" not found", "Please ensure tracking dir with the Run ID information is available"]], headers=["Error", "Description"], showindex=True, tablefmt="fancy_grid"))  
                sys.exit()

    if args.which == "migrate":
        #Checking dependency parameters for IPAM
        if (getattr(args, "target_ipam_network") is not None and getattr(args,"target_ipam_subnet") is None) or (getattr(args,"target_ipam_network") is None and getattr(args,"target_ipam_subnet") is not None):
            print(tabulate([["IPAM Parameter dependency error", "Both -n and -S flags are required for IPAM"]], headers=["Error", "Description"], showindex=True, tablefmt="fancy_grid"))
            parser.parse_args(["migrate", "-h", "migrate -h"])
        headers = {
                    "Content-Type": "application/json",
                    "Referer": URL,
                    "Accept-Encoding": "application/json",
                    "X-Avi-Tenant": args.nsx_alb_tenant,
                    "X-Avi-Version": args.api_version
                }
        #Create run log directory if action=migrate
        if not os.path.exists("./logs"):
            os.makedirs("./logs")
        if ("run-" + args.prefix + ".log" in os.listdir("./logs")):
            overwrite_prompt = input("\n" + '\033[93m' + f"WARNING: Logs with the same Run ID \"{args.prefix}\" exists. Overwrite? Y/N " + '\033[0m').lower()
            if overwrite_prompt == "n" or overwrite_prompt == "no":
                print("\n" + '\033[91m' + f"Aborting..... Cleanup the previous Run \"{args.prefix}\" and Re-run the migrator with a different prefix (Run ID)" + '\033[0m' + "\n")
                sys.exit()
            elif overwrite_prompt == "y" or overwrite_prompt == "yes":
                pass
            else:
                print("\n" + '\033[91m' + "ERROR: Invalid entry.....Aborting" + '\033[0m' + "\n")
                sys.exit()
        with open(f"./logs/run-{args.prefix}.log", "w", encoding="utf-8") as outfile:
                print(titles_logo, file=outfile)
                print(f"\nRun ID = {args.prefix}", file=outfile)
                print(f"\nVMware AVI Controller = {args.controller_ip}", file=outfile)
                print(f"\nJob run by = {args.username}", file=outfile)              
                print(f"\nTenant = {args.nsx_alb_tenant}", file=outfile)
                print(f"\nTimestamp = {datetime.now()}", file=outfile)

    if args.which == "generate_planner_workbook":
        headers = {
                    "Content-Type": "application/json",
                    "Referer": URL,
                    "Accept-Encoding": "application/json",
                    "X-Avi-Tenant": "admin",
                    "X-Avi-Version": args.api_version
                }
        args.prefix = "workbook"
        #Create Log directory
        if not os.path.exists("./logs"):
            os.makedirs("./logs")
        with open(f"./logs/run-{args.prefix}.log", "w", encoding="utf-8") as outfile:
                print(titles_logo, file=outfile)
                print(f"\nRun ID = {args.prefix}", file=outfile)
                print(f"\nVMware AVI Controller = {args.controller_ip}", file=outfile)
                print(f"\nJob run by = {args.username}", file=outfile)              
                print(f"\nTenant = admin", file=outfile)
                print(f"\nTimestamp = {datetime.now()}", file=outfile)

    LOGIN = {
                 "username": args.username, 
                 "password": args.password if args.password else getpass(prompt="Enter Password: "), 
             }

    #Login, fetch CSRFToken and set Header Cookie
    print_func(titles_login)
    login = NsxAlbLogin(URL, LOGIN, headers, args.prefix)
    login.get_cookie()
    headers["X-CSRFToken"] = login.csrf_token
    headers["Cookie"] = login.cookie

    #Verify Tenant exists and login to tenant is successful
    tenant = NsxAlbTenant(URL, headers, args.prefix)
    tenant.get_tenant()

    #If cleanup mode is selected, call the cleanup class after successful authentication.
    if args.which == "cleanup":
        print_func(titles_initiate_cleanup)
        prompt1 = input("\n" + '\033[93m' + f"WARNING : This action will cleanup all objects created for Run ID [{args.prefix}]. Continue? Y/N " + '\033[0m').lower()
        if prompt1 == "y" or prompt1 == "yes":
            if "obj_prefix_removal_status_" + args.prefix + ".csv" in os.listdir("./Tracker-DONOTDELETE"):
                prompt2 = input("\n" '\033[93m' + f"WARNING : Looks like you have already run prefix_removal for Run ID [{args.prefix}].\nIt's possible that objects might have been cut over to target cloud already. Continue? Y/N " + '\033[0m').lower()
                if prompt2 == "n" or prompt2 == "no":
                    print("\n" + '\033[91m' + f"Aborting Cleanup for Run [{args.prefix}] ....." + '\033[0m' + "\n")
                    sys.exit()
                elif prompt2 == "y" or prompt2 == "yes":
                    pass
                else:
                    print("\n" + '\033[91m' + "ERROR: Invalid entry, Aborting ......" + '\033[0m' + "\n")
                    sys.exit()
            cleanup = NsxAlbCleanup(headers, "./Tracker-DONOTDELETE", args.prefix)
            cleanup.initiate_cleanup()
            #Create Dataframe for tabulate View and export to xlsx
            df_cleanup = pandas.read_csv("./Tracker-DONOTDELETE" + "/obj_cleanup_status_" + args.prefix + ".csv",na_filter=False)
            list_display = []
            any_errors = 0
            for index,row in df_cleanup.iterrows():
                list_display.append([row["obj_type"], row["obj_name"], row["url"], row["CLEANUP_STATUS"], row["Error"]])
                if row["CLEANUP_STATUS"] == "FAILURE":
                    any_errors += 1
            print("\n" + '\033[95m' + "Status of task : Cleanup migrated objects is as below:" + '\033[0m')
            print(tabulate(list_display, headers=["Item", "Name", "URL", "Status", "Error"], showindex=True, tablefmt="fancy_grid"))

            if os.path.exists("./Cleanup_Status"):
                shutil.rmtree("./Cleanup_Status")
            os.makedirs("./Cleanup_Status")
            xls_loc = f"./Cleanup_Status/Cleanup_Status-" + args.prefix + ".xlsx"
            with pandas.ExcelWriter(xls_loc) as writer:
                df_cleanup.to_excel(writer, sheet_name="Cleanup Output", index=False, )
            if not any_errors:             
                print("\n" + "\033[92m" + f"SUCCESS : Cleanup task for Run ID '{args.prefix}' has been completed.\n" + '\033[0m')
                print("\033[93m" + f"Note: Review the status spreadsheet '{xls_loc}' for any errors" + "\033[0m" + "\n") 
            else:
                print("\n" + "\033[93m" + f"WARNING : Cleanup task failed for {any_errors} objects. Review the status spreadsheet '{xls_loc}' for more details" + "\033[0m" + "\n")  
            print(titles_thanks)
            sys.exit()
        elif prompt1 == "n" or prompt1 == "no":
            print(f"\n" + '\033[91m' + f"Aborting Cleanup for Run [{args.prefix}] ....." + '\033[0m' + "\n")
            sys.exit()
        else:
            print("\n" + '\033[91m' + "ERROR: Invalid entry, Aborting ......" + '\033[0m' + "\n")
            sys.exit()
    
    #If remove_prefix mode is selected, call the relevant classes after successful authentication.
    if args.which == "remove_prefix":
        dict_df_obj_remove_prefix_status = {
                "obj_type" : [],
                "obj_name_old" : [],
                "obj_name_new" : [],
                "PREFIX_REMOVAL_STATUS" : [],
                "Error" : []
            }  
        df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
        df_obj_remove_prefix_status.to_csv("./Tracker-DONOTDELETE" + "/obj_prefix_removal_status_" + args.prefix + ".csv", index=False)
        print(title_remove_prefix)
        rm_prefix_pool = NsxAlbPool(URL, headers, args.prefix)
        rm_prefix_pool.remove_pool_prefix("./Tracker-DONOTDELETE", headers)
        rm_prefix_poolgroup = NsxAlbPoolGroup(URL, headers, args.prefix)
        rm_prefix_poolgroup.remove_poolgroup_prefix("./Tracker-DONOTDELETE", headers)
        rm_prefix_httppolicyset = NsxAlbHttpPolicySet(URL, headers, args.prefix)
        rm_prefix_httppolicyset.remove_httppolicyset_prefix("./Tracker-DONOTDELETE", headers)
        rm_prefix_vip = NsxAlbVsVip(URL, headers, args.prefix)
        rm_prefix_vip.remove_vsvip_prefix("./Tracker-DONOTDELETE", headers)
        rm_prefix_virtualservice = NsxAlbVirtualService(URL, headers, run_id=args.prefix)
        rm_prefix_virtualservice.remove_virtualservice_prefix("./Tracker-DONOTDELETE", headers)
        #Create Dataframe for tabulate View and export to xlsx
        df_rm_prefix = pandas.read_csv("./Tracker-DONOTDELETE" + "/obj_prefix_removal_status_" + args.prefix + ".csv", na_filter=False)
        list_display = []
        any_errors = 0
        for index,row in df_rm_prefix.iterrows():
            list_display.append([row["obj_type"], row["obj_name_old"], row["obj_name_new"], row["PREFIX_REMOVAL_STATUS"], row["Error"]])
            if row["Error"]:
                any_errors += 1
        print("\n" + '\033[95m' + "Status of task : Remove object prefixes is as below:" + '\033[0m')
        print(tabulate(list_display, headers=["Item", "Name [Old]", "Name [New]", "Status", "Error"], showindex=True, tablefmt="fancy_grid"))

        if os.path.exists("./Prefix_Removal_Status"):
            shutil.rmtree("./Prefix_Removal_Status")
        os.makedirs("./Prefix_Removal_Status")
        xls_loc = f"./Prefix_Removal_Status/Prefix_Removal_Status-" + args.prefix + ".xlsx"
        with pandas.ExcelWriter(xls_loc) as writer:
            df_rm_prefix.to_excel(writer, sheet_name="Prefix Removal Output", index=False, )
        if not any_errors:             
            print("\n" + "\033[92m" + f"SUCCESS : Remove Prefix for Run ID '{args.prefix}' has been completed.\nNote: Review the status spreadsheet '{xls_loc}' for any errors" + "\033[0m" + "\n") 
        else:
            print("\n" + "\033[93m" + f"WARNING : Remove Prefix task failed for {any_errors} objects. Review the status spreadsheet '{xls_loc}' for more details" + "\033[0m" + "\n")  
        print(titles_thanks)
        sys.exit() 
        
    if args.which == "generate_planner_workbook":
        cloud = NsxAlbCloud(URL, headers, args.which, args.prefix) #Fetch cloud connector details from the AVI controller cluster.
        cloud.get_cloud()
        vrfcontext = NsxAlbVrfContext(URL, headers, args.which, args.prefix)
        vrfcontext.get_vrfcontext()
        segroup = NsxAlbSeGroup(URL, headers, args.which, args.prefix)
        segroup.get_segroup()
        vsvip = NsxAlbVsVip(URL, headers, args.prefix, dict_tenant_url_name=tenant.dict_tenant_url_name)
        vsvip.get_vsvip_all()
        print_func(titles_vs_display)
        planner_workbook = NsxAlbPlannerWorkbook(URL, headers, tenant.dict_tenant_url_name, cloud.dict_cloud_url_name, vrfcontext.dict_vrfcontext_all_url_name, segroup.dict_segroup_all_url_name, vsvip.list_all_vsvips, args.prefix)
        planner_workbook.export_planner_workbook()
        print(titles_thanks)
        sys.exit()


    #Scan for DNS Provider Profiles
    dnsproviderprofile = NsxAlbDnsProfile(URL, headers, args.prefix)
    dnsproviderprofile.get_dnsprofile()

    #Scan for IPAM Provider Profiles
    ipamproviderprofile = NsxAlbIpamProfile(URL, headers, args.prefix)
    ipamproviderprofile.get_network()
    ipamproviderprofile.get_ipamprofile()

    #List all VMware AVI cloud accounts and select the target cloud for migration
    print_func(titles_cloud)
    cloud = NsxAlbCloud(URL, headers, args.which, args.prefix)
    cloud.set_cloud(args.target_cloud_name, dnsproviderprofile.dict_dnsprofile_url_name, ipamproviderprofile.dict_ipamprofile_url_name)

    #List all VRFs under the selected VMware AVI cloud account and select the target VRF for migration
    print_func(titles_vrfcontext)
    vrfcontext = NsxAlbVrfContext(URL, headers, args.which, args.prefix, cloud.target_cloud_url, cloud.target_cloud_name)
    vrfcontext.set_vrfcontext(args.target_vrf_name)

    #Scan and validate supplied DNS domain list:
    if getattr(args, "target_dns_domain") is not None:
        print_func(titles_dnsprofile)
        dnsproviderprofile.scan_dnsprofile(cloud.target_cloud_dnsprofile_url, getattr(args, "target_dns_domain", "").split(","))

    #Scan and validate supplied IPAM networks:
    if getattr(args, "target_ipam_network") is not None and getattr(args, "target_ipam_subnet") is not None:
        print_func(titles_ipamprofile)
        ipamproviderprofile.scan_ipamprofile(cloud.target_cloud_ipamprofile_url, getattr(args, "target_ipam_network"), getattr(args, "target_ipam_subnet"), vrfcontext.list_vrfcontexts, args.target_vrf_name)
    
    #List all Service Engine Groups (SEG) under the selected VMware AVI cloud account and select the target SEG for migration
    print_func(titles_serviceenginegroup)
    segroup = NsxAlbSeGroup(URL, headers, args.which, args.prefix, cloud.target_cloud_url, cloud.target_cloud_name)
    segroup.set_segroup(args.target_seg_name)

    #Initialize migraton tracker object
    migration_tracker = NsxAlbMigrationTracker(URL, args.username, args.nsx_alb_tenant, args.api_version, args.prefix, "./Tracker-DONOTDELETE")
    migration_tracker.set_tracking()

    #Fetch pool information from the VMware AVI Tenant
    pool = NsxAlbPool(URL, headers, args.prefix)
    pool.get_pool()

    #Fetch Pool Group information for virtual services from the VMware AVI Tenant
    poolgroup = NsxAlbPoolGroup(URL, headers, args.prefix)
    poolgroup.get_poolgroup()

    #Fetch VS VIP information for virtual services from the VMware AVI Tenant
    vsvip = NsxAlbVsVip(URL, headers, args.prefix, dict_tenant_url_name=tenant.dict_tenant_url_name)
    vsvip.get_vsvip()

    #Fetch the list of all VS Datascript Sets in the Tenant
    vsdatascriptset = NsxAlbVsDataScriptSet(URL, headers, args.prefix)
    vsdatascriptset.get_vsdatascriptset()

    #Fetch the list of all WAF Policies in the Tenant
    wafpolicy = NsxAlbWafPolicy(URL, headers, args.prefix)
    wafpolicy.get_wafpolicy()

    #Fetch the list of all L4 policy sets in the Tenant
    l4policyset = NsxAlbL4PolicySet(URL, headers, args.prefix)
    l4policyset.get_l4policyset()

    #List the Virtual Services under the Tenant     
    print_func(titles_vs_selector)
    virtualservice = NsxAlbVirtualService(URL, headers, dict_cloud_url_name=cloud.dict_cloud_url_name, dict_pool_url_name=pool.dict_pool_url_name, dict_poolgroup_url_name=poolgroup.dict_poolgroup_url_name, dict_vsvip_url_name=vsvip.dict_vsvip_url_name, run_id=args.prefix, list_vsvips=vsvip.list_vsvips, migration_mode=args.which)
    virtualservice.get_virtualservice()

    # Handle ay name duplications for virtual services, pools, pool groups or vsvips
    df_duplicates_merged = pandas.concat([virtualservice.df_duplicate_virtualservices, poolgroup.df_duplicate_poolgroups, pool.df_duplicate_pools, vsvip.df_duplicate_vsvips], ignore_index=True)
    if not df_duplicates_merged.empty:
        list_tabulate_view = []
        for index,row in df_duplicates_merged.iterrows():
            list_tabulate_view.append([row["obj_type"], row["obj_name"], row["obj_ref"], row["tenant"]])
        print_func("\n" + '\033[95m' + "The below VMware AVI objects have duplicate names which need to be actioned:" + '\033[0m')
        print_func(tabulate(list_tabulate_view, headers=["Obj_Type", "Obj_Name", "Obj_Ref", "Tenant"], showindex=True, tablefmt="fancy_grid"))
        print_func("\n" + '\033[91m' + "ERROR: Found VMware AVI objects with dupliate names in the tenant. Please rename the duplicates to continue" + '\033[0m')
        # Create xlsx file
        with pandas.ExcelWriter("./Duplicate_Names.xlsx", engine='openpyxl') as writer:
            df_duplicates_merged.to_excel(writer, sheet_name="Duplicate Names", index=False, )
        print_func("\n" + "\033[93m" + f"Refer the spreadsheet './Duplicate_Names.xlsx' for more details" + '\033[0m')
        print_func("\n" + '\033[91m' + "Migrator will now exit..." + "\n" + '\033[0m')
        sys.exit()

    #Select the virtual services for migration
    virtualservice.set_virtualservice()

    #Scan for HTTPPolicySets in the Tenant
    httppolicyset = NsxAlbHttpPolicySet(URL, headers, args.prefix)
    httppolicyset.get_httppolicyset()

    #Scan selected Virtual Services for any HTTP Policy Sets and Content Switching Pools
    print_func(titles_httppolicyset_selector)
    virtualservice.get_virtualservice_policy(httppolicyset.dict_httppolicyset_url_name)
    print_func(titles_httppolicyset_scanner)
    httppolicyset.get_httppolicyset_pool(virtualservice.dict_vs_httppolicysetname, pool.dict_pool_url_name, poolgroup.dict_poolgroup_url_name)

    #Migrate Pools in Content Switching Policies to target VMware AVI Cloud Account
    pool_cs = NsxAlbPool(URL, headers, args.prefix) #Initialize a pool object to migrate pools in content switching policies
    if len(httppolicyset.dict_cs_originalpool_url_name) != 0: 
        print_func(titles_httppolicyset_migrate_pools)
        pool_cs.migrate_pool(httppolicyset.dict_cs_originalpool_url_name, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, args.prefix, migration_tracker.tracker_csv)
    else:
        pool_cs.dict_originalpoolurl_migratedpoolurl = {}

    #Migrate Pool groups in Content Switching Policies to target VMware AVI Cloud Account    
    poolgroup_cs = NsxAlbPoolGroup(URL, headers, args.prefix)
    poolgroup_cs.get_poolgroup()
    if len(httppolicyset.dict_cs_originalpoolgroup_url_name) != 0:
        print_func(titles_httppolicyset_migratepoolgroups)       
        poolgroup_cs.get_poolgroup_member(httppolicyset.dict_cs_originalpoolgroup_url_name, pool.dict_pool_url_name)
        pool_pg_cs = NsxAlbPool(URL, headers, args.prefix) #Initialize a pool object to migrate pools in Pool Groups assocaited with Content Switching Policies
        if len(poolgroup_cs.dict_poolgroupmembers_url_name) != 0:            
            pool_pg_cs.migrate_pool(poolgroup_cs.dict_poolgroupmembers_url_name, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, args.prefix, migration_tracker.tracker_csv)
        else:
            pool_pg_cs.dict_originalpoolurl_migratedpoolurl = {}
        poolgroup_cs.migrate_poolgroup(httppolicyset.dict_cs_originalpoolgroup_url_name, pool_pg_cs.dict_originalpoolurl_migratedpoolurl, cloud.target_cloud_url, args.prefix, migration_tracker.tracker_csv)   
    else:
        poolgroup_cs.dict_originalpoolgroupurl_migratedpoolgroupurl = {}
    
    #Migrate HTTP Policy Sets to target VMware AVI Cloud Account
    if len(httppolicyset.dict_cs_originalpool_url_name) != 0 or len(httppolicyset.dict_cs_originalpoolgroup_url_name) != 0: 
        print_func(titles_httppolicyset_migrate)
        httppolicyset.migrate_httppolicyset(pool_cs.dict_originalpoolurl_migratedpoolurl, poolgroup_cs.dict_originalpoolgroupurl_migratedpoolgroupurl, args.prefix, migration_tracker.tracker_csv)
    else:
        httppolicyset.dict_vs_httppolicysetmigratedurl = {}

    #Migrate Pool Groups directly associated with Virtual Services to target VMware AVI Cloud
    poolgroup_vs = NsxAlbPoolGroup(URL, headers, args.prefix)
    poolgroup_vs.get_poolgroup()
    poolgroup_vs.set_poolgroup(virtualservice.dict_selectedvs_originalpoolgroupname)
    if len(poolgroup_vs.dict_selectedpoolgroup_url_name) != 0:
        print_func(titles_vs_migratepoolgroups)
        poolgroup_vs.get_poolgroup_member(poolgroup_vs.dict_selectedpoolgroup_url_name, pool.dict_pool_url_name)
        pool_pg_vs = NsxAlbPool(URL, headers, args.prefix) #Initialize a pool object to migrate pools in Pool Groups assocaited with Virtual services
        if len(poolgroup_vs.dict_poolgroupmembers_url_name) != 0:
            pool_pg_vs.migrate_pool(poolgroup_vs.dict_poolgroupmembers_url_name, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, args.prefix, migration_tracker.tracker_csv)
        else:
            pool_pg_vs.dict_originalpoolurl_migratedpoolurl = {}
        poolgroup_vs.migrate_poolgroup(poolgroup_vs.dict_selectedpoolgroup_url_name, pool_pg_vs.dict_originalpoolurl_migratedpoolurl, cloud.target_cloud_url, args.prefix, migration_tracker.tracker_csv)
    else:
        poolgroup_vs.dict_originalpoolgroupurl_migratedpoolgroupurl = {}     
   
    #Migrate Pools directly associated with Virtual Services to target VMware AVI Cloud
    pool_vs = NsxAlbPool(URL, headers, args.prefix) 
    pool_vs.set_pool(virtualservice.dict_selectedvs_originalpoolname)
    if len(pool_vs.dict_selectedpool_url_name) != 0:
        print_func(titles_vs_migratepools)
        pool_vs.migrate_pool(pool_vs.dict_selectedpool_url_name, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, args.prefix, migration_tracker.tracker_csv)
    else:
        pool_vs.dict_originalpoolurl_migratedpoolurl = {}

    #Migrate VS VIPs of selected Virtual Services to target VMware AVI Cloud
    vsvip.set_vsvip(virtualservice.dict_selectedvs_originalvsvipname)
    if len(vsvip.dict_selectedvsvip_url_name) != 0:
        print_func(titles_vsvip_migrate)
        target_dns_domain = getattr(args, "target_dns_domain").split(",") if getattr(args, "target_dns_domain") is not None else []
        target_ipam_network = getattr(args, "target_ipam_network") if getattr(args, "target_ipam_network") is not None else ""
        target_ipam_subnet =  getattr(args, "target_ipam_subnet") if getattr(args, "target_ipam_subnet") is not None else ""
        vsvip.migrate_vsvip(cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, vrfcontext.target_vrfcontext_tier1path, args.prefix, migration_tracker.tracker_csv, target_dns_domain, target_ipam_network, target_ipam_subnet, ipamproviderprofile.create_ipam_block(target_ipam_network, target_ipam_subnet))
    else:
        vsvip.dict_originalvsvipurl_migratedvsvipurl = {}
    
    #Migrate Virtual Services to the target cloud account
    print_func(titles_vs_migrate)
    virtualservice.migrate_virtualservice(pool_vs.dict_originalpoolurl_migratedpoolurl, poolgroup_vs.dict_originalpoolgroupurl_migratedpoolgroupurl, httppolicyset.dict_vs_httppolicysetmigratedurl, vsvip.dict_originalvsvipurl_migratedvsvipurl, cloud.target_cloud_url, vrfcontext.target_vrfcontext_url, segroup.target_segroup_url, vsdatascriptset.dict_vsdatascriptset_url_name, wafpolicy.dict_wafpolicy_learninggroup_url_name, l4policyset.dict_l4policyset_url_name, args.prefix, migration_tracker.tracker_csv, migration_tracker.skipped_settings_csv)
    
    #Logout from VMware AVI Controller
    print_func(titles_logout)
    print_func("\n" + '\033[92m' + f"SUCCESS: Virtual Services are successfully migrated to destination Cloud Connector '{args.target_cloud_name}'" + '\033[0m')
    logout = NsxAlbLogout(URL, headers, args.prefix)
    logout.end_session()
    migration_tracker.set_migration_output_xls()
    print_func(titles_thanks)

main()
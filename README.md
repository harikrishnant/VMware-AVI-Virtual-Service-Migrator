# VMware AVI Virtual Service Migrator v1.4
VMware AVI Virtual Service Migrator is a community project to migrate Virtual Services (and it's dependencies - pools, poolgroups, HTTPPolicySets, VSVIPs and child virtual services, if in a Parent-Child relationship) across VMware AVI Cloud Accounts, VRF Contexts, Service Engine Groups and NSX-T T1 gateways. Currently the below VMware AVI cloud accounts are supported:
- vCenter Cloud
- NSX-T VLAN cloud
- NSX-T Overlay cloud
  - Including VMware AVI on Azure VMware Solution (AVS)
- No-Orchestrator cloud
  - Including VMware AVI on VMware Cloud on AWS (VMConAWS)

The latest release of VMware AVI Virtual Service Migrator (as of Dec 15, 2024)  is version 1.4 and the capabilities & limitations are available in the release notes.
# Overview
This VMware AVI Virtual Service Migrator supports the below migration scenarios for Virtual Services and dependencies within the same VMware AVI Tenant:

**Migration across Cloud Accounts**
1. Migration from vCenter Cloud Account to No-Orchestrator Cloud
2. Migration from No-Orchestrator Cloud to vCenter Cloud Account
3. Migration from one vCenter Cloud Account to another vCenter Cloud Account
4. Migration from vCenter Cloud Account to NSX-T VLAN Cloud Account
5. Migration from NSX-T VLAN Cloud Account to vCenter Cloud Account
6. Migration from No-orchestrator Cloud to NSX-T VLAN Cloud Account
7. Migration from NSX-T VLAN Cloud Account to No-orchestrator Cloud
8. Migration from vCenter Cloud Account to NSX-T Overlay Cloud
9. Migration from No-Orchestrator Cloud to NSX-T Overlay Cloud
10. Migration from NSX-T VLAN Cloud Account to NSX-T Overlay Cloud
11. Migration from one NSX-T cloud to another NSX-T cloud (onprem to AVS for example)

**Migration across VRF Contexts (Routing Domains)**
1. Migration from one VRF Context to another in vCenter Cloud accounts
2. Migration from one VRF Context to another in No-Orchestrator Cloud accounts
3. Migration from one VRF Context to another in NSX-T VLAN Cloud accounts
4. Migration from one VRF Context (T1 Gateway) to another in NSX-T Overlay Cloud accounts
5. Migration to VRF Contexts within the same or across cloud accounts - vCenter, No-Orchestrator, NSX-T VLAN and Overlay cloud accounts

**Migration across Service Engine Groups**
1. Migration from one Service Engine Group to another in vCenter Cloud accounts
2. Migration from one Service Engine Group to another in No-Orchestrator Cloud accounts
3. Migration from one Service Engine Group to another in NSX-T VLAN Cloud accounts
4. Migration from one Service Engine Group to another in NSX-T Overlay Cloud accounts

**Note:** This VMware AVI Virtual Service Migrator supports only migration within the same VMware AVI Tenant. Cross Tenant migration is in the roadmap.

# Instructions
1. Make sure that the target cloud account to which the Virtual Services need to be migrated is configured. This includes the cloud connector configuration, VRF Contexts, networks & routing configuration and service engine confguration under the Service Engine Group.
2. The necessary routes (default routes / static routes to the pool members) need to be avaialble on the target VRF context before migrating the VS / Pools.
3. Make sure that the target cloud account / VRF context doesn't have a conflicting VSVIP object (VIP) compared to the objects being migrated from the source cloud account. If it has any, perform migration with IPAM profiles attached.   
4. A linux / Windows VM (with an IDE like VSCode) with Python3 and connectivity to VMware AVI controllers is required to perform the migration.
5.  Install Python3
6.  Install git
7.  Install the below python modules:
     - requests -> *python3 -m pip install requests*
     - urllib3 -> *python3 -m pip install urllib3* 
     - tabulate -> *python3 -m pip install tabulate*
     - pandas -> *python3 -m pip install pandas*
     - openpyxl -> *python3 -m pip install openpyxl*
8. Clone the repository and navigate to VMware-AVI-Virtual-Service-Migrator/V1.4/ -> *git clone https://github.com/harikrishnant/VMware-AVI-Virtual-Service-Migrator.git && cd VMware-AVI-Virtual-Service-Migrator/V1.4/*
9. The migration tool has four modes:
    - **Generate Planner Workbook mode** -> This mode will generate a migration planner workbook with the details of all virtual services in the VMware AVI Controller Cluster. This workbook can be used for organizing the virtual services into migration batches with the target cloud, VRF, SE Group and VIP addressing options.
    - **Migration mode** -> This mode will perform migration of virtual services to same or different VMware AVI Cloud account.
    - **Remove Prefix mode** -> This mode will perform automated removal of prefixes appended to the migrated objects. This needs to be done post cutover of virtual services (ie, after the migrated virtual services are enabled and the old virtual services are deleted).
    - **Cleanup mode** -> This mode will perform cleanup of migrated objects incase the tool encounters an error or if post migration validation fails. Use this mode with caution as it deletes all the migrated objects under the specific migration batch (run-ID)
10. The migration workflow will create a tracking directory (VMware-AVI-Virtual-Service-Migrator/V1.4/Tracker-DONOTDELETE/) which has the tracking information for each job. DO NOT DELETE or access this directory, as this is required for cleanup and remove_prefix jobs.
11. The migration tool creates the below output directories / spreadsheets based on the mode it is run. These spreadsheets need to be reviewed for any errors. 
    - **Generate Planner Workbook mode** -> A spreadsheet named "Planner_Workbook.xlsx" will be generated in the working directory (VMware-AVI-Virtual-Service-Migrator/V1.4/)
    - **Migration mode** -> Output directory named "Migration_Status" (VMware-AVI-Virtual-Service-Migrator/V1.4/Migration_Status) that has two spreadsheets - Migration status spreadsheet (Migration-Status-<RunID>.xlsx) and Skipped settings spreadsheet (Skipped-Settings-<RunID>.xlsx). Both spreadsheets need to be reviewed once a migration batch is run.
    - **Remove Prefix mode** -> Output directory named "Prefix_Removal_Status" (VMware-AVI-Virtual-Service-Migrator/V1.4/Prefix_Removal_Status) that has one spreadsheet - Prefix Removal status spreadsheet (Prefix_Removal_Status-<RunID>.xlsx). This spreadsheet need to be reviewed once a prefix removal job is run.
    - **Cleanup mode** -> Output directory named "Cleanup_Status" (VMware-AVI-Virtual-Service-Migrator/V1.4/Cleanup_Status) that has one spreadsheet - Cleanup status spreadsheet (Cleanup_Status-<RunID>.xlsx). This spreadsheet need to be reviewed once a cleanup job is run.
12. Logs for each job is saved in VMware-AVI-Virtual-Service-Migrator/V1.4/logs

**Generate Planner Workbook Mode**

13. This is the first step in the migration process where we organize all the virtual services into migration batches. Virtual services that have similar migration requirements (like same target cloud account, VRF Context, SE Group and IPAM profile) will be a part of the same migration batch. Run the migrator tool in "generate_planner_workbook" mode to generate a spreadsheet having the details of all virtual services along with the corresponding cloud account, VRF Context, SE group, VIP, AVI tenant etc. This can be worked upon to organize the virtual services into migration batches along with a unique prefix ID (runID) for each migration batch.

Run ./virtual_service_migrator.py with the "generate_planner_workbook" subcommand -> *python3 virtual_service_migrator.py generate_planner_workbook --help*

This will launch VMware AVI Virtual Service Migrator help menu for the generate_planner_workbook mode. Follow instructions on the screen.

*python3 virtual_service_migrator.py generate_planner_workbook -i <CONTROLLER_IP/FQDN> -u <.USERNAME> -p <.PASSWORD> -a <API_VERSION>

where
- CONTROLLER_IP/FQDN -> This is the VMware AVI Controller cluster IP/FQDN [MANDATORY]
- USERNAME -> This is the local "system-admin" user account to login to the VMware AVI Controller cluster. SAML authentication is currently not supported.[MANDATORY]
- PASSWORD -> This is the password of the above user account to login to the VMware AVI Controller cluster.[MANDATORY]
- API_VERSION -> This is the API version of the controller cluster. This is also the controller version (Eg:30.2.2) [MANDATORY]

**Migration mode**

14. Run ./virtual_service_migrator.py with the "migrate" subcommand. -> *python3 virtual_service_migrator.py migrate --help* 

This will launch VMware AVI Virtual Service Migrator help menu for the migrate mode. Follow instructions on the screen.

*python3 virtual_service_migrator.py migrate -i <CONTROLLER_IP/FQDN> -u <.USERNAME> -p <.PASSWORD> -a <API_VERSION> -t <NSX_ALB_TENANT> -c <TARGET_CLOUD> -r <TARGET_VRF_CONTEXT> -s <TARGET_SERVICE_ENGINE_GROUP> -d <TARGET_APPLICATION_DNS_DOMAINS> -n <TARGET_IPAM_NETWORK_NAME> -S <TARGET_IPAM_SUBNET> -P <OBJECT_PREFIX/RUN-ID>*

where
- CONTROLLER_IP/FQDN -> This is the VMware AVI Controller cluster IP/FQDN [MANDATORY]
- USERNAME -> This is the local "system-admin" user account to login to the VMware AVI Controller cluster. SAML authentication is currently not supported.[MANDATORY]
- PASSWORD -> This is the password of the above user account to login to the VMware AVI Controller cluster.[MANDATORY]
- API_VERSION -> This is the API version of the controller cluster. This is also the controller version (Eg:22.1.4) [MANDATORY]
- NSX_ALB_TENANT -> This is the VMware AVI Tenant where the migration needs to be performed. [MANDATORY]
- TARGET_CLOUD -> This is the target VMware AVI Cloud connector name [MANDATORY]
- TARGET_VRF_CONTEXT -> This is the target VRF Context (under the target cloud connector) [MANDATORY]
- TARGET_SERVICE_ENGINE_GROUP -> This is the target Service Engine Group (under the target cloud connector) [MANDATORY]
- TARGET_APPLICATION_DNS_DOMAINS -> This is a comma separated list of DNS subdomains to create the application DNS records. These subdomains should be a avaialble in the DNS profile attached to the target cloud connector. [OPTIONAL]
- TARGET_IPAM_NETWORK_NAME -> This is the name of the network used for VIP auto-allocation. This network should be available in the IPAM profile attached to the target cloud connector. [OPTIONAL]
- TARGET_IPAM_SUBNET -> This is the subnet available on the network for VIP auto-allocation. This subnet should have IP pools defined for VIP allocation.[OPTIONAL]
- OBJECT_PREFIX/RUN-ID -> This is the prefix that will be attached to the migrated objects. This prefix should be unique for each migration job as this will be used for job tracking and cleanup mode.[MANDATORY]
 
**Remove prefix mode**

15. Run ./virtual_service_migrator.py with the "remove_prefix" subcommand. -> *python3 virtual_service_migrator.py remove_prefix --help* 
 
This will launch VMware AVI Virtual Service Migrator help menu for the remove_prefix mode. Follow instructions on the screen.

Eg: *python3 virtual_service_migrator.py remove_prefix -i <CONTROLLER_IP/FQDN> -u <.USERNAME> -p <.PASSWORD> -r <OBJECT_PREFIX/RUN-ID>*

where
- CONTROLLER_IP/FQDN -> This is the VMware AVI Controller cluster IP/FQDN [MANDATORY]
- USERNAME -> This is the local "system-admin" user account to login to the VMware AVI Controller cluster. SAML authentication is currently not supported.[MANDATORY]
- PASSWORD -> This is the password of the above user account to login to the VMware AVI Controller cluster.[MANDATORY]
- OBJECT_PREFIX/RUN-ID -> This is the run-ID that was used for the previous migration job. [MANDATORY]

This will automate the removal of prefixes attached to the migrated objects. This needs to be done post cutover of virtual services (ie, after the migrated virtual services are enabled and the old virtual services are deleted).

**Cleanup mode**

16. Run ./virtual_service_migrator.py with the "cleanup" subcommand. -> *python3 virtual_service_migrator.py cleanup --help* 
 
This will launch VMware AVI Virtual Service Migrator help menu for the cleanup mode. Follow instructions on the screen.

Eg: *python3 virtual_service_migrator.py cleanup -i <CONTROLLER_IP/FQDN> -u <.USERNAME> -p <.PASSWORD> -r <OBJECT_PREFIX/RUN-ID>*

This will cleanup all the objects that were migrated as part of the specific migration batch (runID)

**Note:** Use this mode with caution as it deletes all the objects that were migrated as part of the specific migration batch. If cleanup job is done post cutover of virtual services, you will end up in a state where both the original and migrated objects are lost. 

# Related blog posts from VxPlanet.com

[To be updated shortly]

# Migration Workflow

![VxPlanet.com](https://serveritpro.files.wordpress.com/2022/03/flowchart.jpg)

# Contact
Please contact me at https://vxplanet.com for improvising the code, feature enhancements and bugs. Alternatively you can also use Issue Tracker to report any bugs or questions regarding the VMware AVI Virtual Service Migrator tool. 

[![VxPlanet](https://serveritpro.files.wordpress.com/2021/09/vxplanet_correct.png)](https://vxplanet.com)

# Donate
If you found this project useful, saved you time and money, and/or you'd like donating to strangers, then here is my BuyMeACoffee button.

[![BuyMeACoffee](https://i0.wp.com/vxplanet.com/wp-content/uploads/2023/05/giphy-3.gif?resize=168%2C168&ssl=1)](https://buymeacoffee.com/op1hmo9)
[![BuyMeACoffee](https://i0.wp.com/vxplanet.com/wp-content/uploads/2019/11/65.png?resize=371%2C102&ssl=1)](https://buymeacoffee.com/op1hmo9)

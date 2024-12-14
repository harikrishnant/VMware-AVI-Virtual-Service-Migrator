# VMware AVI Virtual Service Migrator 1.4 Release Notes
This release notes cover the following topics:
- Document Revision History
- Supported VMware AVI Versions
- What's New
- Known Limitations

**Document Revision History**

First Edition - March 03, 2022

Second Edition - July 24, 2022

Third Edition - July 6, 2023

Fourth Edition - July 19, 2023

Fifth Edition - December 14, 2024

**Supported VMware AVI Versions**

NSX ALB API Versions 18.1.2 till 30.2.2

**Whats's New**
- Naming changes - NSX ALB Virtual Service Migrator is now renamed as VMware AVI Virtual Service Migrator
- Added option to generate migration planner workbook to assist with organizing AVI virtual services into migration batches. This will accelerate the migration planning phase.
- Consolidated the workflows for migrating virtual services of type "Normal" and "SNI_EVH", which was handled as separate workflows in the previous versions. The migration flag "-q" or "--virtual_hosted_vs" is now deprecated. This enhancement will reduce the number of migration batches involved.
- Improved job status reporting options. Status spreadsheets are generated in *.xlsx format for each of the migration modes.
- Included tracking of skipped settings as part of migration in a separate spreadsheet which can be reviewed post-migration of a batch.
- Added support for migrating virtual services that have WAF policies without a PSM group (learning group)
- Added support to scan AVI objects to identify possible naming duplications that can prevent a successful virtual service migration. Any naming duplicates, if found will be tracked as a separate spreadsheet which can be reviewed for action.

**Issues fixed**
- TULSI-005 : An issue preventing a successful cleanup of virtual services of type TLS-SNI / EVH is now fixed.
- TULSI-006 : Virtual service migration failues caused as part of WAF learning groups, custom datascripts and L4 policy sets are handled gracefully using skipped settings workflow. Entries in the skipped settings output will be a manual administrator task.
- TULSI-007 : Error, Warning and Info message customizations with color codes is completed.
- TULSI-008 : An issue preventing user prompt while an incorrect virtual service name is supplied is now fixed.
- TULSI-009 : An issue when remove_prefix and cleanup modes are returning success messages in a specific scenario is now fixed.
- TULSI-010 : An issue causing migration failures when duplicate object names are detected in the AVI tenant is now handled through a separate workflow.
- TULSI-011 : An issue causing migration failures for Parent-Child virtual services as part of API changes in 30.x versions is now fixed.

**Known Issues**
- TULSI-012 : Status output directories of migrate, remove_prefix and cleanup modes will be overwritten during each migration batch. 
   - Workaround : Manually backup the directories before a new migration batch is run.

**Known Limitations**

The below VMware AVI features are not yet tested with VMware AVI Virtual Service Migrator and hence migration of below features may or may not work as expected.
- VMware AVI Controllers with SAML / LDAP configured. Currently only local accounts are supported
- Any datascripts with mention of pools / pool groups need to be manually updated post migration
- GSLB Applications are not updated with migrated virtual services information
- For NSX-T VLAN backed clouds, the placement networks for each virtual service need to be manually added. This is a VMware AVI Cloud connector limitation
- Doesn't support cross-tenant migration

![VxPlanet.com](https://serveritpro.files.wordpress.com/2021/09/vxplanet_correct.png)


# NSX ALB Virtual Service Migrator 1.3 Release Notes
This release notes cover the following topics:
- Document Revision History
- Supported NSX ALB Versions
- What's New
- Known Limitations

**Document Revision History**

First Edition - March 03, 2022

Second Edition - July 24, 2022

Third Edition - July 6, 2023

Fourth Edition - July 19, 2023

**Supported NSX ALB Versions**

NSX ALB API Versions 18.1.2 till 22.1.3

**Whats's New**
- Added support for migration of virtual services which are part of Virtual Service Hosting (Parent-Child relationships)
     -  An new migration flag "-q" / "--virtual_hosted_vs" added to the migration mode to handle Parent and Child virtual services migration
     -  Parent-Child virtual services part of TLS-SNI hosting can be now migrated to any supported cloud account.
     -  Parent-Child virtual services part of EVH (Enhanced Virtual Hosting) can be now migrated to any supported cloud account.
- The "remove_prefix" mode in the migration tool is updated to support prefix removal of migrated VS'es which are part of Virtual Service Hosting (Parent-Child relationships)
- Supports migration of virtual services with VIP sharing

**Issues fixed**
- TULSI-004 : Virtual services migration errors in version 1.2 happening while encountering TLS-SNI or EVH hosted VS'es are now fixed.

**Known Issues**
- TULSI-005 : Cleanup job of TLS-SNI / EVH hosted virtual services will log failure errors for Parent Virtual services.
   - Workaround : Run the cleanup job twice


**Known Limitations**

The below NSX ALB features are not yet tested with NSX ALB Virtual Service Migrator and hence migration of below features may or may not work as expected.
- NSX ALB Controllers with SAML / LDAP configured. Currently only local accounts are supported
- Any datascripts with mention of pools / pool groups need to be manually updated post migration
- GSLB Applications are not updated with migrated virtual services information
- For NSX-T VLAN backed clouds, the placement networks for each virtual service need to be manually added. This is a NSX ALB Cloud limitation
- Migration from NSX-T Overlay Cloud to vCenter Cloud succeeds but requires additional manual intervention for VIP connectivity.
- Doesn't support cross-tenant migration

![VxPlanet.com](https://serveritpro.files.wordpress.com/2021/09/vxplanet_correct.png)


# NSX ALB Virtual Service Migrator 1.2 Release Notes
This release notes cover the following topics:
- Document Revision History
- Supported NSX ALB Versions
- What's New
- Known Limitations

**Document Revision History**

First Edition - March 03, 2022

Second Edition - July 24, 2022

Third Edition - July 6, 2023

**Supported NSX ALB Versions**

NSX ALB API Versions 18.1.2 till 22.1.3

**Whats's New**
- NSX ALB Cloud Migrator is now NSX ALB Virtual Service Migrator
- Added support till NSX ALB version 22.1.3
- Added support for virtual service migration with IPAM profiles
     -  Supports VIP auto-allocation for the migrated virtual services based on the target cloud's IPAM profile
     -  Supports migration of virtual services having IPAM profiles at the source cloud connector
     -  Validation checks for target IPAM networks and subnets before migration
     -  Supports VIP allocation based on VRF context
- Added support for virtual service migration with DNS profiles
     -  Supports adding DNS names for the migrated virtual services based on the target cloud's DNS profile
     -  Supports migration of virtual services having DNS profiles at the source cloud connector
     -  Validation checks for target DNS subdomains before migration
 - Supports virtual service cloning within the same cloud account (using IPAM profiles)

**Issues fixed**
- TULSI-002 : Duplicate VIP issues while cloning virtual services within the same cloud account is now fixed
- TULSI-003 : An issue with HTTP Policy set migration having content switching policies with empty pool groups (without pool group members) is now fixed.

**Known Limitations**

The below NSX ALB features are not yet tested with NSX ALB Virtual Service Migrator and hence migration of below features may or may not work as expected.
- NSX ALB Controllers with SAML / LDAP configured. Currently only local accounts are supported
- Virtual Services with VIP sharing
- TLS SNI based Virtual Service Hosting (Parent - Child VS)
- Enhanced Virtual Hosting (EVH)
- Any datascripts with mention of pools / pool groups need to be manually updated post migration
- GSLB Applications are not updated with migrated virtual services information
- For NSX-T VLAN backed clouds, the placement networks for each virtual service need to be manually added. This is a NSX ALB Cloud limitation
- Migration from NSX-T Overlay Cloud to vCenter Cloud succeeds but requires additional manual intervention for VIP connectivity.
- Doesn't support cross-tenant migration

![VxPlanet.com](https://serveritpro.files.wordpress.com/2021/09/vxplanet_correct.png)


# NSX ALB Cloud Migrator 1.1 Release Notes
This release notes cover the following topics:
- Document Revision History
- Supported NSX ALB Versions
- What's New
- Known Limitations

**Document Revision History**

First Edition - March 03, 2022

Second Edition - July 24, 2022

**Supported NSX ALB Versions**

NSX ALB API Versions 18.1.2 till 21.1.4

**Whats's New**
- Added support till NSX ALB version 21.1.4
- Completely written using Python Classes and Objects (Object oriented)
- Completely switched the script execution mode from interactive to parameter based. Tool supports three execution modes: a) Migration b) Cleanup and c) remove_prefix
- Added object tracking class which tracks each object created as part of the migration workflow
- Added automated cleanup of objects created by the migrator. Useful to revert in case of a failed migration
- Added automated removal of object prefixes created as part of the migration workflow
- Added logging options to the migration workflows.
- Switched from adding object suffixes to object prefixes 

**Issues fixed**
- TULSI-001 : An issue with migration of GSLB DNS Virtual Services is now fixed- 

**Known Limitations**

The below NSX ALB features are not yet tested with NSX ALB Cloud Migrator and hence migration of below features may or may not work as expected.
- NSX ALB Controllers with SAML / LDAP configured. Currently only local accounts are supported
- Virtual Services with VIP sharing
- TLS SNI based Virtual Service Hosting (Parent - Child VS)
- Any datascripts with mention of pools / pool groups need to be manually updated post migration
- GSLB Applications are not updated with migrated virtual services information
- IPAM / DNS profiles
- For NSX-T VLAN backed clouds, the placement networks for each virtual service need to be manually added. This is a NSX ALB Cloud limitation
- Migration from NSX-T Overlay Cloud to vCenter Cloud succeeds but requires additional manual intervention for VIP connectivity.
- This NSX ALB Cloud Migrator supports the below migration scenarios for Virtual Services and dependencies within the same NSX ALB Tenant

![VxPlanet.com](https://serveritpro.files.wordpress.com/2021/09/vxplanet_correct.png)


# NSX ALB Cloud Migrator 1.0 Release Notes
This release notes cover the following topics:
- Document Revision History
- Supported NSX ALB Versions
- What's New
- Known Limitations

**Document Revision History**

First Edition - March 03, 2022

**Supported NSX ALB Versions**

NSX ALB API Versions 18.1.2 till 21.1.2

**Whats's New**
- Ability to migrate Virtual services and dependencies (Pools, PoolGroups, HTTPPolicySets, VSVIPs) across NSX ALB Cloud Accounts:
     - Migration from vCenter Cloud Account to No-Orchestrator Cloud
     - Migration from No-Orchestrator Cloud to vCenter Cloud Account
     - Migration from one vCenter Cloud Account to another vCenter Cloud Account
     - Migration from vCenter Cloud Account to NSX-T VLAN Cloud Account
     - Migration from NSX-T VLAN Cloud Account to vCenter Cloud Account
     - Migration from No-orchestrator Cloud to NSX-T VLAN Cloud Account
     - Migration from NSX-T VLAN Cloud Account to No-orchestrator Cloud
     - Migration from vCenter Cloud Account to NSX-T Overlay Cloud
     - Migration from No-Orchestrator Cloud to NSX-T Overlay Cloud
     - Migration from NSX-T VLAN Cloud Account to NSX-T Overlay Cloud
 - Ability to migrate Virtual services and dependencies (Pools, PoolGroups, HTTPPolicySets, VSVIPs) across VRF Contexts (Routing domains):
      - Migration from one VRF Context to another in vCenter Cloud accounts
      - Migration from one VRF Context to another in No-Orchestrator Cloud accounts
      - Migration from one VRF Context to another in NSX-T VLAN Cloud accounts
      - Migration from one VRF Context (T1 Gateway) to another in NSX-T Overlay Cloud accounts
      - Migration to VRF Contexts within the same or across cloud accounts - vCenter, No-Orchestrator, NSX-T VLAN and Overlay cloud accounts
 - Ability to migrate Virtual services across Service Engine Groups:
      - Migration from one Service Engine Group to another in vCenter Cloud accounts
      - Migration from one Service Engine Group to another in No-Orchestrator Cloud accounts
      - Migration from one Service Engine Group to another in NSX-T VLAN Cloud accounts
      - Migration from one Service Engine Group to another in NSX-T Overlay Cloud accounts

**Known Limitations**

The below NSX ALB features are not yet tested with NSX ALB Cloud Migrator and hence migration of below features may or may not work as expected.
- NSX ALB Controllers with SAML / LDAP configured. Currently only local accounts are supported
- Virtual Services with VIP sharing
- TLS SNI based Virtual Service Hosting (Parent - Child VS)
- GSLB DNS Virtual Services
- Any datascripts with mention of pools / pool groups need to be manually updated post migration
- GSLB Applications are not updated with migrated virtual services information
- IPAM / DNS profiles
- For NSX-T VLAN backed clouds, the placement networks for each virtual service need to be manually added. This is a NSX ALB Cloud limitation
- Migration from NSX-T Overlay Cloud to vCenter Cloud succeeds but requires additional manual intervention for VIP connectivity.
- This NSX ALB Cloud Migrator supports the below migration scenarios for Virtual Services and dependencies within the same NSX ALB Tenant

![VxPlanet.com](https://serveritpro.files.wordpress.com/2021/09/vxplanet_correct.png)

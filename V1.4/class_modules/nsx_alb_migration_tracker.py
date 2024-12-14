import pandas
import os
import json
import sys
import shutil

class NsxAlbMigrationTracker:
    def __init__(self, controller_url, username, nsx_alb_tenant, api_version, run_id, track_dir):
        self._run_id = run_id
        self._controller_url = controller_url
        self._username = username
        self._nsx_alb_tenant = nsx_alb_tenant
        self._api_version = api_version
        self.track_dir = track_dir

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    def set_tracking(self):
        ''' Create the directory to save object tracking info '''
        if not os.path.exists(self.track_dir):
            os.makedirs(self.track_dir)
        if ("obj_track" + "-" + self._run_id + ".csv" in os.listdir(self.track_dir)) or ("infra_track" + "-" + self._run_id + ".json" in os.listdir(self.track_dir)):
            overwrite_prompt = input("\n" + '\033[93m' + f"WARNING : Track objects with the same Run ID {[self._run_id]} exists. Overwrite? Y/N " + '\033[0m').lower()
            if overwrite_prompt == "n" or overwrite_prompt == "no":
                self.print_func("\n" + '\033[91m' + f"ERROR: Aborting..... Cleanup the previous Run [{self._run_id}] and Re-run the migrator with a different prefix (Run ID)" + '\033[0m' +"\n")
                sys.exit()
            elif overwrite_prompt == "y" or overwrite_prompt == "yes":
                pass
            else:
                self.print_func("\n" + '\033[91m' + f"ERROR:Invalid entry.....Aborting" + '\033[0m' +"\n")
                sys.exit()
        csv_tracker_headers = {
            "obj_type": [],
            "obj_name": [],
            "uuid": [],
            "url": [],
            "custom_attr" : [],
            "status" : []
        }
        csv_skipped_settings_headers = {
            "obj_type": [],
            "obj_name_old": [],
            "obj_name_new": [],
            "skipped_object_type": [],
            "skipped_object_name": [],
            "reason" : [],
            "recommendation" : []
        }
        dict_infra_tracker = {
            "controller": self._controller_url,
            "username": self._username,
            "nsx_alb_tenant": self._nsx_alb_tenant,
            "api_version": self._api_version,
            "run_id": self._run_id
        }
        self.tracker_csv = self.track_dir + "/obj_track-" + self._run_id + ".csv"
        self.skipped_settings_csv = self.track_dir + "/skipped_settings-" + self._run_id + ".csv"
        self._infra_json = self.track_dir + "/infra_track-" + self._run_id + ".json"
        tracking_dataframe = pandas.DataFrame(csv_tracker_headers) #Create DF for trackinng csv
        tracking_dataframe.to_csv(self.tracker_csv, index=False)
        skipped_settings_dataframe = pandas.DataFrame(csv_skipped_settings_headers) #Create DF for skipped settings csv
        skipped_settings_dataframe.to_csv(self.skipped_settings_csv, index=False)

        with open(self._infra_json, "w") as outfile:
            json.dump(dict_infra_tracker, outfile, indent=4)
        self.print_func(f"\nTracking information for cleanup is saved to {self.track_dir}")
        
    def set_migration_output_xls(self):
        if os.path.exists("./Migration_Status"):
            shutil.rmtree("./Migration_Status")
        os.makedirs("./Migration_Status")
        df_output_xls = pandas.read_csv(self.tracker_csv)
        df_skipped_settings_xls = pandas.read_csv(self.skipped_settings_csv)
        xls_loc = f"./Migration_Status/Migration-Status-" + self._run_id + ".xlsx"
        xls_skipped_loc = f"./Migration_Status/Skipped-Settings-" + self._run_id + ".xlsx"
        with pandas.ExcelWriter(xls_loc) as writer:
            df_output_xls.to_excel(writer, sheet_name="Migration Output", index=False, ) 
        with pandas.ExcelWriter(xls_skipped_loc) as writer:
            df_skipped_settings_xls.to_excel(writer, sheet_name="Skipped Settings", index=False, )            
        if not df_skipped_settings_xls.empty:
            self.print_func("\n" + "\033[93m" + f"WARNING : There are few Skipped settings, Review the spreadsheet '{xls_skipped_loc}' and manually apply skipped settings to the migrated virtual services" + "\033[0m")
        self.print_func("\n" + "\033[92m" + f"SUCCESS : Review the migration Output spreadsheet '{xls_loc}' to verify the migration status" + "\033[0m")

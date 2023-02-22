'''
Written by Thomas Munzer (tmunzer@juniper.net)
Github repository: https://github.com/tmunzer/Mist_library/
'''
import sys
import mlib as mist_lib
from mlib import cli
import logging

import org_conf_backup
import org_conf_deploy
import org_inventory_backup
import org_inventory_precheck
import org_inventory_deploy

log_file = "./org_migration.log"
logging.basicConfig(filename=log_file, filemode='w')
# logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def _backup_org(source_mist_session, source_org_id, source_org_name):
    try:
        _print_new_step("Backuping SOURCE Org Configuration")
        org_conf_backup.start_org_backup(source_mist_session, source_org_id, source_org_name, log_file)    
    except: 
        sys.exit(255)

def _deploy_org(dest_mist_session, dest_org_id, dest_org_name, source_org_name, check_org_name=False, in_backup_folder=False):
    _print_new_step("Deploying Configuration to the DESTINATION Org")
    org_conf_deploy.start_deploy_org(dest_mist_session, dest_org_id, dest_org_name, source_org_name, check_org_name, in_backup_folder, dest_org_name, log_file)    

#######
#######

def _backup_inventory(source_mist_session, source_org_id, source_org_name, in_backup_folder=False):
    _print_new_step("Backuping SOURCE Org Inventory")
    org_inventory_backup.start_inventory_backup(source_mist_session, source_org_id, source_org_name, in_backup_folder, log_file)    

def _precheck_inventory(dest_mist_session, dest_org_id, dest_org_name, source_org_name, in_backup_folder=False):
    _print_new_step("Pre-check for INVENTORY restoration")
    org_inventory_precheck.start_precheck(dest_mist_session, dest_org_id, dest_org_name,source_org_name, None, in_backup_folder)    

def _restore_inventory(dest_mist_session, dest_org_id, dest_org_name, source_mist_session, source_org_name, source_org_id, check_org_name=False, in_backup_folder=False):
    _print_new_step("Deploying Inventory to the DESTINATION Org")
    org_inventory_deploy.start_deploy_inventory(dest_mist_session, dest_org_id, dest_org_name, source_mist_session, source_org_name, source_org_id, None, check_org_name, in_backup_folder, None, log_file)    

#######
#######

def _print_new_step(message):
    print()
    print("".center(80,'*'))
    print(f" {message} ".center(80,'*'))
    print("".center(80,'*'))
    print()
    logger.info(f"{message}")

#######
#######
def _create_org(mist_session):
    while True:
        custom_dest_org_name = input("What is the new Organization name? ")
        if custom_dest_org_name:
            org = {
                "name": custom_dest_org_name
            }
            try:
                print()
                print(f"Creating the organisation \"{custom_dest_org_name}\" in {mist_session.host} ".ljust(79, "."), end="", flush=True)
                print("\033[92m\u2714\033[0m")
                print()
            except:
                print('\033[31m\u2716\033[0m')
                sys.exit(10)
            org_id = mistapi.api.v1.orgs.orgs.create(mist_session, org)["result"]["id"]
            return (mist_session, org_id, custom_dest_org_name)


def select_or_create_org(mist_session=None):
    mist_session = mistapi.APISession()    
    while True:
        res = input("Do you want to create a (n)ew organisation or (r)estore to an existing one? ")
        if res.lower()=="r":
            return _select_org(mist_session)
        elif res.lower()=="n":
            return _create_org(mist_session)


def _check_org_name(org_name):
    while True:
        print()
        resp = input(
            "To avoid any error, please confirm the current destination orgnization name: ")
        if resp == org_name:
            return True
        else:
            print()            
            print("The orgnization names do not match... Please try again...")

#######
#######
def _select_org(mist_session=None, host=None):
    if not mist_session:
        mist_session = mistapi.APISession(host=host)    
    org_id = cli.select_org(mist_session)[0]
    org_name = mist_lib.orgs.info.get(mist_session, org_id)["result"]["name"]
    _check_org_name(org_name)
    return (mist_session, org_id, org_name)

if __name__ == "__main__":
    _print_new_step("Select the SOURCE Org")
    source_mist_session, source_org_id, source_org_name = _select_org()
    _print_new_step("Select the DESTINATION Org")
    dest_mist_session, dest_org_id, dest_org_name = select_or_create_org()

    _backup_org(source_mist_session, source_org_id, source_org_name)
    _backup_inventory(source_mist_session, source_org_id, source_org_name, in_backup_folder=True)
    _deploy_org(dest_mist_session, dest_org_id, dest_org_name, source_org_name, in_backup_folder=True)
    _precheck_inventory(dest_mist_session, dest_org_id, dest_org_name, source_org_name, in_backup_folder=True)
  
'''
Python script to restore organization backup file.
You can use the script "org_conf_backup.py" to generate the backup file from an
existing organization.

This script will not overide existing objects. If you already configured objects in the 
destination organisation, new objects will be created. If you want to "reset" the 
destination organization, you can use the script "org_conf_zeroise.py".
This script is trying to maintain objects integrity as much as possible. To do so, when 
an object is referencing another object by its ID, the script will replace be ID from 
the original organization by the corresponding ID from the destination org.

You can run the script with the command "python3 org_admins_import.py <path_to_the_json_file>"

The script has 2 different steps:
1) admin login
2) choose the destination org
3) restore all the objects from the json file. 
'''

#### PARAMETERS #####

#### IMPORTS ####

import mlib as mist_lib
from mlib.__debug import Console
from mlib import cli
from tabulate import tabulate
import json
import os.path
console = Console(6)
backup_file = "./org_conf_file.json"
image_prefix = ".".join(backup_file.split(".")[:-1])
session_file = None

org_id = ""

with open(backup_file) as f:
    backup = json.load(f)

#### CONSTANTS ####


#### GLOBAL VARS ####


rftemplate_id_dict = {}
site_id_dict = {}
sitegroup_id_dict = {}
map_id_dict = {}
deviceprofile_id_dict = {}
template_id_dict = {}
mxtunnel_id_dict = {}
wxtunnel_id_dict = {}
secpolicy_id_dict = {}
wxtags_id_dict = {}
mxcluster_id_dict = {}
wlan_id_dict = {}
alarmtemplate_id_dict = {}


#### FUNCTIONS ####

def get_new_id(old_id, new_ids_dict):
    if old_id in new_ids_dict:
        new_id = new_ids_dict[old_id]
        console.notice("id %s replaced with id %s" %(old_id, new_id))
        return new_id
    else:
        console.notice("Unable to replace id %s" %old_id)
        return None


def replace_id(old_ids_list, new_ids_dict):
    if old_ids_list == None:
        console.notice("Unable to replace id %s" %old_ids_list)
        return None
    if old_ids_list == {}:
        return {}
    elif type(old_ids_list) == str:
        return get_new_id(old_ids_list, new_ids_dict)
    elif type(old_ids_list) == list:
        new_ids_list = []
        for old_id in old_ids_list:
            new_ids_list.append(get_new_id(old_id, new_ids_dict))
        return new_ids_list
    else:
        console.error("Unable to replace ids: %s" % old_ids_list)


def clean_ids(data):
    if "id" in data:
        del data["id"]
    if "org_id" in data:
        del data["org_id"]
    if "modified_time" in data:
        del data["modified_time"]
    if "created_time" in data:
        del data["created_time"]
    return data


def common_restore(level, level_id, object_name, data):
    # console.debug(json.dumps(data))
    old_id = data["id"]
    data = clean_ids(data)
    module = mist_lib.requests.route(level, object_name)
    new_id = module.create(mist_session, level_id, data)["result"]["id"]
    return {old_id: new_id}


def wlan_restore(level, level_id, data):
    if "template_id" in data:
        data["template_id"] = replace_id(
            data["template_id"], template_id_dict)
    if "wxtunnel_id" in data:
        data["wxtunnel_id"] = replace_id(data["wxtunnel_id"], wxtags_id_dict)
    if "mxtunnel_id" in data:
        data["mxtunnel_id"] = replace_id(data["mxtunnel_id"], mxtunnel_id_dict)
    if "app_limit" in data and "wxtag_ids" in data["app_limit"]:
        data["app_limit"]["wxtag_ids"] = replace_id(
            data["app_limit"]["wxtag_ids"], wxtags_id_dict)
    ids = common_restore(level, level_id, 'wlans', data)
    wlan_id_dict.update(ids)


def restore_org(org):
    ####  ORG MAIN  ####
    data = org["data"]
    old_org_id = data["id"]
    # console.debug(json.dumps(data))
    del data["id"]
    if "orggroup_ids" in data:
        del data["orggroup_ids"]
    if "msp_id" in data:
        del data["msp_id"]
    if "msp_name" in data:
        del data["msp_name"]
    mist_lib.requests.orgs.info.update(mist_session, org_id, data)
    
    ####  ORG SETTINGS  ####
    data = clean_ids(org["settings"])
    # console.debug(json.dumps(data))
    mist_lib.requests.orgs.settings.update(mist_session, org_id, data)
    
    ####  ORG OBJECTS  ####
    for data in org["webhooks"]:
        common_restore('orgs', org_id, 'webhooks', data)

    for data in org["assetfilters"]:
        common_restore('orgs',  org_id, 'assetfilters', data)

    for data in org["deviceprofiles"]:
        ids = common_restore('orgs',  org_id, 'deviceprofiles', data)
        deviceprofile_id_dict.update(ids)

    for data in org["alarmtemplates"]:
        ids = common_restore('orgs',  org_id, 'alarmtemplates', data)
        deviceprofile_id_dict.update(ids)

    for data in org["mxclusters"]:
        ids = common_restore('orgs',  org_id, 'mxclusters', data)
        mxcluster_id_dict.update(ids)

    for data in org["mxtunnels"]:
        data["mxcluster_ids"] = replace_id(
            data["mxcluster_ids"], mxcluster_id_dict)
        ids = common_restore('orgs',  org_id, 'mxtunnels', data)
        mxtunnel_id_dict.update(ids)

    for data in org["psks"]:
        common_restore('orgs', org_id, 'psks', data)

    for data in org["secpolicies"]:
        ids = common_restore('orgs', org_id, 'secpolicies', data)
        secpolicy_id_dict.update(ids)

    for data in org["rftemplates"]:
        ids = common_restore('orgs', org_id, 'rftemplates', data)
        rftemplate_id_dict.update(ids)

    for data in org["sitegroups"]:
        del data["site_ids"]
        ids = common_restore('orgs', org_id, 'sitegroups', data)
        sitegroup_id_dict.update(ids)

    for data in org["wxtags"]:
        if data["match"] == "wlan_id":
            replace_id(data["values"], wlan_id_dict)
        ids = common_restore('orgs', org_id, 'wxtags', data)
        wxtags_id_dict.update(ids)

    for data in org["wxrules"]:
        data["src_wxtags"] = replace_id(data["src_wxtags"], wxtags_id_dict)
        data["dst_allow_wxtags"] = replace_id(data["dst_allow_wxtags"], wxtags_id_dict)
        data["dst_deny_wxtags"] = replace_id(data["dst_deny_wxtags"], wxtags_id_dict)
        common_restore('orgs',  org_id, 'wxrules', data)

    for data in org["wxtunnels"]:
        ids = common_restore('orgs', org_id, 'wxtunnels', data)
        wxtunnel_id_dict.update(ids)


    ####  SITES LOOP  ####
    for data in org["sites"]:
        ####  SITES MAIN  ####
        site = data["data"]
        old_site_id = site["id"]
        if "rftemplate_id" in site:
            site["rftemplate_id"] = replace_id(site["rftemplate_id"], rftemplate_id_dict)
        if "secpolicy_id" in site:
            site["secpolicy_id"] = replace_id(site["secpolicy_id"], secpolicy_id_dict)
        if "alarmtemplate_id" in site:
            site["alarmtemplate_id"] = replace_id(site["alarmtemplate_id"], alarmtemplate_id_dict)
        if "sitegroup_ids" in site:
            site["sitegroup_ids"] = replace_id(site["sitegroup_ids"], sitegroup_id_dict)
        ids = common_restore('orgs',  org_id, 'sites', site)
        site_id_dict.update(ids)
        new_site_id = ids[next(iter(ids))]

        settings = clean_ids(data["settings"])
        if "site_id" in settings: del settings["site_id"]
        mist_lib.requests.sites.settings.update(
            mist_session, new_site_id, settings)

        if "maps" in data:
            for sub_data in data["maps"]:
                sub_data["site_id"] = new_site_id
                ids = common_restore('sites', new_site_id, 'maps', sub_data)
                map_id_dict.update(ids)


                old_map_id = next(iter(ids))
                new_map_id = ids[old_map_id]
                image_name = "%s_url_%s.jpg" %(image_prefix, old_map_id)
                image_name = "%s_org_%s_site_%s_map_%s.png" %(image_prefix, old_org_id, old_site_id, old_map_id)
                if os.path.isfile(image_name):
                    console.info("Image %s will be restored to map %s" %(image_name, new_map_id))
                    mist_lib.requests.sites.maps.add_image(mist_session, new_site_id, new_map_id, image_name)
                else:
                    console.info("No image found for old map id %s" % old_map_id)


        if "assetfilters" in data:
            for sub_data in data["assetfilters"]:
                common_restore('sites', new_site_id, 'assetfilters', sub_data)

        if "assets" in data:
            for sub_data in data["assets"]:
                common_restore('sites', new_site_id, 'assets', sub_data)

        if "beacons" in data:
            for sub_data in data["beacons"]:
                sub_data["map_id"] = replace_id(sub_data["map_id"], map_id_dict)
                common_restore('sites', new_site_id, 'beacons', sub_data)

        if "psks" in data:
            for sub_data in data["psks"]:
                sub_data["site_id"] = new_site_id
                common_restore('sites', new_site_id, 'psks', sub_data)

        if "rssizones" in data:
            for sub_data in data["rssizones"]:
                common_restore('sites', new_site_id, 'rssizones', sub_data)

        if "vbeacons" in data:
            for sub_data in data["vbeacons"]:
                sub_data["map_id"] = replace_id(sub_data["map_id"], map_id_dict)
                common_restore('sites', new_site_id, 'vbeacons', sub_data)

        if "webhooks" in data:
            for sub_data in data["webhooks"]:
                common_restore('sites', new_site_id, 'webhooks', sub_data)

        if "wxtunnels" in data:
            for sub_data in data["wxtunnels"]:
                ids = common_restore('sites', new_site_id,'wxtunnels', sub_data)
                wxtunnel_id_dict.update(ids)

        if "zones" in data:
            for sub_data in data["zones"]:
                sub_data["map_id"] = replace_id(sub_data["map_id"], map_id_dict)
                common_restore('sites', new_site_id, 'zones', sub_data)
        
        if "wlans" in data:
            for sub_data in data["wlans"]:
                wlan_restore('sites', new_site_id, sub_data)

        if "wxtags" in data:
            for sub_data in data["wxtags"]:
                if sub_data["match"] == "wlan_id":
                    replace_id(sub_data["values"], wlan_id_dict)
                ids = common_restore('sites', new_site_id, 'wxtags', sub_data)
                wxtags_id_dict.update(ids)

        if "wxrules" in data:
            for sub_data in data["wxrules"]:
                if "src_wxtags" in sub_data:
                    sub_data["src_wxtags"] = replace_id(sub_data["src_wxtags"], wxtags_id_dict)
                if "dst_allow_wxtags" in sub_data:
                    sub_data["dst_allow_wxtags"] = replace_id(sub_data["dst_allow_wxtags"], wxtags_id_dict)
                if "dst_deny_wxtags" in sub_data:
                    sub_data["dst_deny_wxtags"] = replace_id(sub_data["dst_deny_wxtags"], wxtags_id_dict)
                common_restore('sites', new_site_id, 'wxrules', sub_data)

    for data in org["templates"]:
        if "applies" in data:
            if "org_id" in data["applies"]:
                data["applies"]["org_id"] = org_id
            if "site_ids" in data["applies"]:
                data["applies"]["site_ids"] = replace_id(data["applies"]["site_ids"], site_id_dict)
            if "sitegroup_ids" in data["applies"]:
                data["applies"]["sitegroup_ids"] = replace_id(data["applies"]["sitegroup_ids"], sitegroup_id_dict)
        if "exceptions" in data:
            if "site_ids" in data["exceptions"]:
                data["exceptions"]["site_ids"] = replace_id(data["exceptions"]["site_ids"], site_id_dict)
            if "sitegroup_ids" in data["exceptions"]:
                data["exceptions"]["sitegroup_ids"] = replace_id(data["exceptions"]["sitegroup_ids"], sitegroup_id_dict)
        if "deviceprofile_ids" in data:
            data["deviceprofile_ids"] = replace_id(data["deviceprofile_ids"], deviceprofile_id_dict)
        ids = common_restore('orgs', org_id, 'templates', data)
        template_id_dict.update(ids)

    for data in org["wlans"]:
        wlan_restore('orgs', org_id, data)


#### SCRIPT ENTRYPOINT ####

mist_session = mist_lib.Mist_Session(session_file)
if org_id == "":
    org_id = cli.select_org(mist_session)

print(""" 
__          __     _____  _   _ _____ _   _  _____ 
\ \        / /\   |  __ \| \ | |_   _| \ | |/ ____|
 \ \  /\  / /  \  | |__) |  \| | | | |  \| | |  __ 
  \ \/  \/ / /\ \ |  _  /| . ` | | | | . ` | | |_ |
   \  /\  / ____ \| | \ \| |\  |_| |_| |\  | |__| |
    \/  \/_/    \_\_|  \_\_| \_|_____|_| \_|\_____|

This script is still in BETA. It won't hurt your original
organization, but the restoration may partially fail. 
It's your responsability to validate the importation result!


""")
resp = "x"
while not resp in ["y", "n", ""]:
    resp = input("Do you want to continue to import the configuration into the organization %s (y/N)? " %org_id).lower()

if resp == "y":
    restore_org(backup["org"])
    print('')
    console.info("Restoration succeed!")
else:
    console.warning("Interruption... Exiting...")
exit(0)
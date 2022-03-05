import json
from urllib.request import urlopen
from urllib.error import HTTPError
import os
import wget
import re
import sys
import subprocess
from xml.dom import minidom
import platform

class PlexUpdate:

    ''' constructor '''
    def __init__(self, xml_file):
        self.xml_file = xml_file

    ''' result request '''
    def result(self, message):
        print(message, "\n")

    ''' header '''
    def header(self, item):
        print("[ " + item + " ]")
    
    ''' header fail '''
    def header_fail(self, item):
        print("FAIL : " + item + "")
    
    ''' Get token value '''
    def get_plex_token(self):
        parsing_plex_file=minidom.parse(self.xml_file)
        first_child=parsing_plex_file.getElementsByTagName("Preferences")
        token = False
        for token_value in first_child:
            if token_value.getAttribute("PlexOnlineToken"):
                token = token_value.getAttribute("PlexOnlineToken")
        return token

    ''' Retrieving Plex json file '''
    def retrieve_version_data(self):
        if self.get_plex_token() is False:
            data_json = self.header_fail('Token is unable')
            sys.exit()
        else:
            try:
                plex_url='http://plex.tv/api/downloads/5.json?channel=plexpass&X-Plex-Token='+self.get_plex_token()
                response=urlopen(plex_url)
                data_json = json.loads(response.read())
            except HTTPError:
                self.header_fail("Url not found")
                sys.exit()
        return data_json

    ''' Get operating system version '''
    def get_os_version(self):
        file_version ='/etc/VERSION'
        try:
            parse_file = {k:v for k, v in (l.split('=') for l in open(file_version))}
            syno_major_version = parse_file.get('majorversion').rstrip("\n").strip('"') # give 7
            if syno_major_version == "7":
                syno_os_version = 'Synology (DSM '+syno_major_version+')' 
            else:
                syno_os_version = 'Synology'
            return syno_os_version
        except IOError:
            self.header_fail("File {} not found".format(file_version))
            sys.exit()

    ''' Get CPU architecture '''
    def get_cpu_arch(self):
        syno_cpu_arch = 'linux-'+platform.machine() #aarch64 for example
        return syno_cpu_arch

    ''' Get Plex version available from Plex API '''
    def get_available_version(self):
        json_file = self.retrieve_version_data()
        syno_os_version = self.get_os_version()
        available_version = re.search('\d.+\.\d+',json_file["nas"][syno_os_version]["version"])
        return available_version.group(0)

    ''' Get current Plex version installed on NAS '''
    def get_installed_version(self):
        extract_version = re.split("-", os.popen('synopkg version PlexMediaServer').read())
        installed_version = extract_version[0]
        return installed_version

    ''' Get URL for download SPK package '''
    def get_url_package(self):
        json_file = self.retrieve_version_data()
        syno_os_version = self.get_os_version()
        available_version = json_file["nas"][syno_os_version]["releases"]
        for build in available_version:
            if build["build"] == self.get_cpu_arch():
                url = build["url"]
        return url

    ''' Verify version between local version server and API version available '''
    def verify_plex_version_is_up_to_date(self):
        if self.get_available_version() != self.get_installed_version():
            print("New plex version available...downloading")
            result = self.download_new_version()
            return result
        else:
            result = self.result("Plex is up to date")
            sys.exit()
    
    ''' Download SPK package from URL '''
    def download_new_version(self):
        spk_file = self.get_url_package()
        wget.download(spk_file)
        return print('\n')

    ''' Get package name after downloading '''
    def get_package_name(self):
        package_name = re.split("/", self.get_url_package())
        return package_name[6]

    ''' Install new version of Plex Package '''
    def install_package(self):
        try:
            subprocess.run(['/usr/syno/bin/synopkg','install', self.get_package_name()], stdout=subprocess.DEVNULL)
            self.result("Package successfully installed")
        except subprocess.CalledProcessError:
           self.header_fail("Error to download package")
           sys.exit()

    ''' Stop plex server before install the new version '''
    def stop_plex_service(self):
        try:
            subprocess.run(['/usr/syno/bin/synopkg','stop', 'PlexMediaServer'], stdout=subprocess.DEVNULL)
            self.result("Plex server stop successfull")
        except subprocess.CalledProcessError:
           self.header_fail("Error to stop plex server")
           sys.exit()

    ''' Start plex server after install the new version '''
    def start_plex_service(self):
        try:
            subprocess.run(['/usr/syno/bin/synopkg','start', 'PlexMediaServer'], stdout=subprocess.DEVNULL)
            self.result("Plex server start successfull")
        except subprocess.CalledProcessError:
           self.header_fail("Error to start plex server")
           sys.exit()
    
    ''' Remove spk file '''
    def clean_directory(self):
        try:
            args = ('/bin/rm','-f','PlexMediaServer-*')
            subprocess.run('%s %s %s' % args, shell=True)
            self.result("Directory clean successfully")
        except subprocess.CalledProcessError:
           self.header_fail("Directory not cleaned")
           sys.exit()

def search_file_for_retrieve_token(filename, search_path):
    result = []
    for root, files in os.walk(search_path):
        if filename in files:
            result.append(os.path.join(root, filename))
    return result

search_file_for_retrieve_token("Preferences.xml","/")
MyPlex = PlexUpdate("/volume1/PlexMediaServer/AppData/Plex Media Server/Preferences.xml")
if __name__ == '__main__':
    MyPlex.header("Get installed version")
    print(MyPlex.get_installed_version(), "\n")

    MyPlex.header("Get available version")
    print(MyPlex.get_available_version(), "\n")

    MyPlex.header("Check version is up to date")
    MyPlex.verify_plex_version_is_up_to_date()

    MyPlex.header("Stop Plex service")
    MyPlex.stop_plex_service()

    MyPlex.header("Install Plex package version {}".format(MyPlex.get_available_version()))
    MyPlex.install_package()

    MyPlex.header("Start Plex service")
    MyPlex.start_plex_service()

    MyPlex.header("Clean directory")
    MyPlex.clean_directory()

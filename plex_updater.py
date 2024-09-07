import os
import wget
import re
import sys
import subprocess
from xml.dom import minidom
import platform
import requests

class PlexUpToDateException(Exception):
    pass

class PlexUpdater:

    def __init__(self, xml_file):
        """
        Initializes a new instance of the Plex class.

        Parameters:
        xml_file (str): The path to the XML file.

        """
        self.xml_file = xml_file

    def result(self, message):
        """
        Prints the given message and a new line.
        Parameters:
        - message (str): The message to be printed.
        Returns:
        None
        """
        
        print(message, "\n")

    def header(self, item):
        """
        Prints the header for the given item.
        Parameters:
        - item (str): The item to be displayed in the header.
        Returns:
        None
        """
        print(f"[{item}]")
    
    def header_fail(self, item):
        """ 
        Docstring for the header_fail method.

        Parameters:
        - item (str): The item that failed.

        Returns:
        None

        Description:
        This method is called when the header fails for a specific item. It prints a message indicating the failure.

        Example:
        header_fail("example_item")
        Output: FAIL : example_item
        """
        """ header fail."""
        print(f"FAIL : {item}")
    
    def get_plex_token(self):
        """
        Retrieves the Plex token from the XML file.

        Returns:
            str: The Plex token value if found, False otherwise.
        """
        parsing_plex_file=minidom.parse(self.xml_file)
        first_child=parsing_plex_file.getElementsByTagName("Preferences")
        token = False
        for token_value in first_child:
            if token_value.getAttribute("PlexOnlineToken"):
                token = token_value.getAttribute("PlexOnlineToken")
        return token

    def retrieve_version_data(self):
        if self.get_plex_token() is False:
            self.header_fail('Token is unable')
            sys.exit(0)
        else:
            try:
                plex_url = f"https://plex.tv/api/downloads/5.json?channel=plexpass&X-Plex-Token={self.get_plex_token()}"
                response = requests.get(plex_url)
                response.raise_for_status()
                data_json = response.json()
            except requests.exceptions.HTTPError as http_err:
                self.header_fail(f"HTTP error occurred: {http_err}")
                sys.exit(0)
            except Exception as err:
                self.header_fail(f"Other error occurred: {err}")
                sys.exit(0)
        return data_json

    def get_os_version(self):
        """
        Retrieves the operating system version of the Synology device.

        Returns:
            str: The operating system version of the Synology device. If the major version is 7, it returns 'Synology (DSM 7)'. Otherwise, it returns 'Synology'.
        
        Raises:
            IOError: If the VERSION file is not found.
        """
        file_version ='/etc/VERSION'
        try:
            parse_file = {k:v for k, v in (l.split('=') for l in open(file_version))}
            syno_major_version = parse_file.get('majorversion').rstrip("\n").strip('"') # give 7
            syno_os_version = 'Synology'
            if syno_major_version == "7":
                syno_os_version = f"Synology (DSM {syno_major_version})" 
            return syno_os_version
        except IOError:
            self.header_fail("File {} not found".format(file_version))
            sys.exit(0)

    def get_cpu_arch(self):
        """
        Returns the CPU architecture of the system.

        Returns:
            str: The CPU architecture of the system, in the format 'linux-<arch>'.
        """
        syno_cpu_arch = f"linux-{platform.machine()}" #aarch64 for example
        return syno_cpu_arch

    def get_available_version(self):
        """
        Retrieves the available version of Plex from the version data file.

        Returns:
            str: The available version of Plex.
        """
        json_file = self.retrieve_version_data()
        syno_os_version = self.get_os_version()
        available_version = re.search('\d.+\.\d+',json_file["nas"][syno_os_version]["version"])
        return available_version.group(0)

    def get_installed_version(self):
        """
        Retrieves the installed version of Plex Media Server.

        Returns:
            str: The installed version of Plex Media Server.
        """
        extract_version = re.split("-", os.popen('synopkg version PlexMediaServer').read())
        installed_version = extract_version[0]
        return installed_version

    def get_url_package(self):
        """
        Retrieves the URL package based on the CPU architecture and Synology OS version.

        Returns:
            str: The URL package for the specified CPU architecture and Synology OS version.
        """
        json_file = self.retrieve_version_data()
        syno_os_version = self.get_os_version()
        available_version = json_file["nas"][syno_os_version]["releases"]
        
        url = None
        try:
            for build in available_version:
                if build["build"] == self.get_cpu_arch():
                    url = build["url"]
        except KeyError as error:
            self.header_fail(f"KeyError: {error}")
            sys.exit(0)
        return url

    def verify_plex_version_is_up_to_date(self):
        """
        Verifies if the Plex version is up to date.

        Returns:
            bool: True if the Plex version is up to date, False otherwise.
        """
        
        if self.get_available_version() != self.get_installed_version():
            print("New plex version available...downloading")
            result = self.download_new_version()
            return result
        else:
            self.result("Plex is up to date")
            sys.exit(0)
    
    def download_new_version(self):
        """
        Downloads the new version of the Plex package.

        Raises:
            ValueError: If the URL package is not found.
        """
        
        spk_file = self.get_url_package()
        if spk_file is None:
            self.header_fail("Failed to download new version: URL package not found for the specified CPU architecture and Synology OS version")
            sys.exit(0)
        wget.download(spk_file)
        print('\n')
       
    def get_package_name(self):
        """
        Returns the package name extracted from the URL package.

        Returns:
            str: The package name extracted from the URL package.
        """
        package_name = re.split("/", self.get_url_package())
        return package_name[6]


    def install_package(self):
        """
        Install the package using the specified package name.

        Raises:
            subprocess.CalledProcessError: If there is an error while downloading the package.

        Returns:
            None
        """
        try:
            subprocess.run(['/usr/syno/bin/synopkg','install', self.get_package_name()], stdout=subprocess.DEVNULL)
            self.result("Package successfully installed")
        except subprocess.CalledProcessError:
           self.header_fail("Error to download package")
           sys.exit(0)

    def stop_plex_service(self):
        """
        Stops the Plex Media Server service.

        Raises:
            subprocess.CalledProcessError: If there is an error while stopping the Plex server.

        Returns:
            None
        """
        try:
            subprocess.run(['/usr/syno/bin/synopkg','stop', 'PlexMediaServer'], stdout=subprocess.DEVNULL)
            self.result("Plex server stop successfull")
        except subprocess.CalledProcessError:
           self.header_fail("Error to stop plex server")
           sys.exit(0)


    def start_plex_service(self):
        """
        Starts the Plex Media Server service.

        Raises:
            subprocess.CalledProcessError: If there is an error starting the Plex server.

        Returns:
            None
        """
        try:
            subprocess.run(['/usr/syno/bin/synopkg','start', 'PlexMediaServer'], stdout=subprocess.DEVNULL)
            self.result("Plex server start successfull")
        except subprocess.CalledProcessError:
           self.header_fail("Error to start plex server")
           sys.exit(0)
    
    def clean_directory(self):
        """
        Cleans the directory by removing all files with the name 'PlexMediaServer-*'.

        Raises:
            subprocess.CalledProcessError: If the directory cannot be cleaned.

        Returns:
            None
        """
        try:
            args = ('/bin/rm','-f','PlexMediaServer-*')
            subprocess.run('%s %s %s' % args, shell=True)
            self.result("Directory clean successfully")
        except subprocess.CalledProcessError:
           self.header_fail("Directory not cleaned")
           sys.exit(0)

    def search_file_for_retrieve_token(self, filename, search_path):
        """
        Search for a file with the given filename in the specified search path.

        Parameters:
        - filename (str): The name of the file to search for.
        - search_path (str): The path to search for the file in.

        Returns:
        - list: A list of file paths where the file was found.
        """
        result = []
        for root, dirs, files in os.walk(search_path):
            if filename in files:
                result.append(os.path.join(root, filename))
        return result

    def update(self):
        """
        Updates the Plex package to the latest available version.

        Steps:
        1. Get the installed version of Plex.
        2. Get the latest available version of Plex.
        3. Check if the installed version is up to date.
        4. Stop the Plex service.
        5. Install the latest available version of Plex.
        6. Start the Plex service.
        7. Clean the directory.

        Returns:
        None
        """
        self.header("Get installed version")
        print(self.get_installed_version(), "\n")

        self.header("Get available version")
        print(self.get_available_version(), "\n")

        self.header("Check version is up to date")
        self.verify_plex_version_is_up_to_date()

        self.header("Stop Plex service")
        self.stop_plex_service()

        self.header("Install Plex package version {}".format(self.get_available_version()))
        self.install_package()

        self.header("Start Plex service")
        self.start_plex_service()

        self.header("Clean directory")
        self.clean_directory()

if __name__ == '__main__':
    my_plex = PlexUpdater("/volume1/PlexMediaServer/AppData/Plex Media Server/Preferences.xml")
    my_plex.search_file_for_retrieve_token("Preferences.xml","/")
    my_plex.update()

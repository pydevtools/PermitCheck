from __future__ import absolute_import

import os
import requests
from xml.dom import minidom
import xml.etree.ElementTree as ET

from permitcheck.utils import read_json, write_json, get_basedir, get_lines


class XML:
    """
    A class for handling XML operations related to licenses.

    Methods:
        save: Saves the provided licenses to an XML file.
    """

    @classmethod
    def save(cls, licenses_iter, fname='licenses.xml'):
        """
        This method saves an licenses to an XML file.

        Args:
            licenses (list): A dictionary contains license information.
            fname (str, optional): filename to save the XML data. Defaults to 'licenses.xml'.

        Returns:
            None

        Raises:
            None
        """
        license_set = set()
        root = ET.Element("")
        for licenses in licenses_iter:
            for license in licenses:
                for key, value in license.items():
                    if key not in license_set:
                        license_set.add(key)
                        license_element = ET.SubElement(root, "license")
                        ET.SubElement(license_element, "id").text = key
                        ET.SubElement(license_element, "name").text = value

        # Convert to XML string
        sorted_licenses = sorted(root.findall('license'), key=lambda x: x.find('id').text)

        # Build a new XML structure with sorted licenses
        sorted_root = ET.Element('licenses')
        for license in sorted_licenses:
            sorted_root.append(license)

        xml_string = ET.tostring(sorted_root, encoding='unicode')
        xml_string = minidom.parseString(xml_string).toprettyxml(indent="  ")

        # Save to a file
        fpath = os.path.join(os.path.dirname(__file__), fname)
        with open(fpath, "w") as xml_file:
            xml_file.write(xml_string)
        print(f"file saved: {fname} under {os.path.dirname(__file__)}")


class JSON:
    fname = 'licenses.json'
    @classmethod
    def save(cls, licenses_iter, fname=None):
        if not fname:
            fname = cls.fname

        data = {}
        for licenses in licenses_iter:
            for license in licenses:
                data |= license
        # Save to a file
        fpath = os.path.join(os.path.dirname(__file__), fname)
        write_json(fpath, data)
        print(f"file saved: {fname} under {os.path.dirname(__file__)}")


class License:
    """
    A class to handle operations related to software licenses from an external API.

    Methods:
        fetch: Retrieves a list of open-source licenses.

    """
    basedir = get_basedir()
    resources = f"{basedir}/license/resources.txt"
    license_file = f"{basedir}/license/{JSON.fname}"
    licenses = {}
    spdx_set = set()

    @classmethod
    def fetch(cls, resources=None):
        """
        This method sends a GET request to the Open Source Initiative's licenses API
        and returns the licenses in JSON format if the request is successful. 
        If the request fails, it logs an error message and returns None.

        Returns:
            dict or None: A dictionary containing the open-source licenses if the request is successful, 
            otherwise None.

        Raises:
            None
        """
        if not resources:
            resources = cls.resources
        urls = get_lines(resources)

        def extract_license_data(data):
            if isinstance(data, dict) and "licenses" in data:
                # SPDX style with "licenses" key
                return [{license.get("licenseId"): license.get("name")} for license in data["licenses"]]
            elif isinstance(data, list) and "key" in data[0]:
                # GitHub style with "key" and "name"
                return [{license.get("key"): license.get("name")} for license in data]
            elif isinstance(data, list) and "id" in data[0]:
                # Other source with "id" and "name"
                return [{license.get("id"): license.get("name")} for license in data]
            else:
                return []

        # print(urls)
        for url in urls:
            response = requests.get(url)

            if response.status_code == 200:
                yield extract_license_data(response.json())
            else:
                print(f"Failed to fetch licenses: {response.status_code}")
        return None

    @classmethod
    def get(cls, license_file=None, is_print=True): 
        # TODO: need to add filter to print matching, similar keys only
        if not license_file:
            license_file = cls.license_file

        if not os.path.isfile(license_file):
            main()

        cls.licenses = read_json(license_file)
        cls._create_spdx_set()
        if not is_print:
            return cls.spdx_set

        # ANSI escape codes for colors
        COLORS = [
            "\033[31m",  # Red
            "\033[38;5;214m",  # Orange
            "\033[33m",  # Yellow
            "\033[32m",  # Green
            "\033[34m",  # Blue
            "\033[35m",  # Magenta (Indigo)
            "\033[38;5;171m",  # Violet
        ]
        RESET = "\033[0m"
        def pretty(k, v, color):
            return f"{color}{k:<35} {v}{RESET}"


        print(f"\033[34m{'SPDX Code':<35} Full Name{RESET}")
        print("-" * 70)
        color_index = 0
        for k, v in cls.licenses.items():
            print(pretty(k, v, COLORS[color_index]))
            color_index = (color_index + 1) % len(COLORS)

    @classmethod
    def _create_spdx_set(cls):
        full_set = lambda s: {'-'.join(s.split('-')[:i+1]) for i in range(len(s.split('-')))}

        for spdx in cls.licenses:
            cls.spdx_set |= full_set(spdx)


def main():
    licenses = License.fetch()
    JSON.save(licenses)
    # XML.save(licenses) # absolute code

if __name__ == "__main__":
    main()
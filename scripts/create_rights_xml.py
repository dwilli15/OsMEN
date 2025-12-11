#!/usr/bin/env python3
"""Create rights.xml from fulfillment response"""

import sys
import xml.etree.ElementTree as ET


def create_rights_xml(fulfillment_path, output_path):
    with open(fulfillment_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse
    root = ET.fromstring(content)

    # Find licenseToken element
    license_token = None
    for elem in root.iter():
        if elem.tag.endswith("licenseToken"):
            license_token = elem
            break

    if license_token is None:
        print("ERROR: No licenseToken found")
        return False

    # Serialize licenseToken
    license_str = ET.tostring(license_token, encoding="unicode")

    # Create rights.xml with proper Adobe namespace
    rights_xml = (
        """<?xml version="1.0" encoding="UTF-8"?>
<adept:rights xmlns:adept="http://ns.adobe.com/adept">
"""
        + license_str.replace("ns0:", "adept:").replace("xmlns:ns0", "xmlns:adept")
        + """
</adept:rights>"""
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rights_xml)

    print(f"Created: {output_path}")
    return True


if __name__ == "__main__":
    fulfillment = r"D:\OsMEN\content\ebooks\drm_free\fulfillment_response.xml"
    output = r"D:\OsMEN\content\ebooks\drm_free\rights.xml"
    create_rights_xml(fulfillment, output)
    create_rights_xml(fulfillment, output)

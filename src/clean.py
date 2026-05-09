#!/usr/bin/env python3

# Imports
from pathlib import Path


# Clean XML file
def clean_xml_file(xml_path: str):

    xml_file = Path(xml_path)

    # Read file contents
    with open(xml_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Remove non-XML lines before first XML tag
    cleaned_lines = []

    found_xml = False

    for line in lines:

        stripped_line = line.strip()

        if stripped_line.startswith('<?xml') or stripped_line.startswith('<'):

            found_xml = True

        if found_xml:
            cleaned_lines.append(line)

    # Join cleaned content
    cleaned_content = ''.join(cleaned_lines)

    # Replace invalid ampersands
    cleaned_content = cleaned_content.replace('&', '&amp;')

    # Prevent double replacement
    cleaned_content = cleaned_content.replace('&amp;amp;', '&amp;')

    # Overwrite cleaned XML
    with open(xml_file, 'w', encoding='utf-8') as file:
        file.write(cleaned_content)

    print(f'[+] Cleaned XML file: {xml_path}')
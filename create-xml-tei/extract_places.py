#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Places Parser Module
Reads and parses the Lieux.xml (places) database file
Provides PlacesParser class for extracting place information
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional

class Place:
    """Represents a single place entity from Lieux.xml"""
    
    def __init__(self, xml_element: ET.Element, ns: Dict[str, str]):
        """Initialize place from XML element"""
        self.xml_element = xml_element
        self.ns = ns
        self.place_id = ""
        self.place_name = ""
        self.xml_id = ""
        self.base_id = 0
        
        # Parse XML attributes
        self._parse_xml()
    
    def _parse_xml(self):
        """Parse XML element to extract place information"""
        # Get place ID - check for xml:id first, then id
        self.place_id = self.xml_element.get('{http://www.w3.org/XML/1998/namespace}id', '') or self.xml_element.get('id', '')
        self.xml_id = self.place_id
        
        # Get place name from various possible locations
        name_elem = self.xml_element.find('.//tei:placeName', self.ns)
        if name_elem is not None and name_elem.text:
            self.place_name = name_elem.text.strip()
        else:
            # Fallback to finding name in other elements
            for elem in self.xml_element.findall('.//tei:name', self.ns):
                if elem.text and elem.text.strip():
                    self.place_name = elem.text.strip()
                    break
            
            if not self.place_name:
                # Use ID as fallback name
                self.place_name = self.place_id
    
    def __repr__(self):
        return f"Place({self.place_name}, id={self.place_id})"

class PlacesParser:
    """Parser for Lieux.xml places database"""
    
    def __init__(self, xml_file: str):
        """Initialize parser with XML file path"""
        self.xml_file = xml_file
        self.places: List[Place] = []
        self.places_dict: Dict[str, Place] = {}
        
        if not os.path.exists(xml_file):
            print(f"Warning: Places XML file not found: {xml_file}")
            return
            
        self._load_xml()
    
    def _load_xml(self):
        """Load and parse the XML file"""
        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()
            
            # Define the TEI namespace
            ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
            
            # Parse places - look for place elements using the namespace
            for place_elem in root.findall('.//tei:place', ns):
                place = Place(place_elem, ns)
                self.places.append(place)
                if place.place_name:
                    self.places_dict[place.place_name.lower()] = place
                
        except ET.ParseError as e:
            print(f"Error parsing places XML: {e}")
        except Exception as e:
            print(f"Error loading places: {e}")
    
    def parse_places(self) -> List[Place]:
        """Return list of all parsed places"""
        return self.places
    
    def get_place_by_name(self, name: str) -> Optional[Place]:
        """Get a place by its name (case-insensitive)"""
        return self.places_dict.get(name.lower())
    
    def get_place_by_id(self, place_id: str) -> Optional[Place]:
        """Get a place by its ID"""
        for place in self.places:
            if place.place_id == place_id:
                return place
        return None
    
    def __len__(self):
        return len(self.places)
    
    def __repr__(self):
        return f"PlacesParser({len(self.places)} places from {self.xml_file})"


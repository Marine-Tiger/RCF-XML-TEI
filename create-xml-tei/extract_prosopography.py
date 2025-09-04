#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract person data from Prosopographie.xml into Pydantic classes
"""

import xml.etree.ElementTree as ET
from typing import List, Optional
from pydantic import BaseModel, Field


class Person(BaseModel):
    """Pydantic model for a person in the TEI prosopography"""
    xml_id: str = Field(..., description="XML ID attribute")
    base_id: Optional[int] = Field(None, description="Base unifiée ID")
    full_name: Optional[str] = Field(None, description="Full registered name")
    family_name: Optional[str] = Field(None, description="Family name")
    first_name: Optional[str] = Field(None, description="First name")
    gender: Optional[str] = Field(None, description="Gender")
    occupation: Optional[str] = Field(None, description="Occupation type")
    person_type: Optional[str] = Field(None, description="Person type from ana attribute")

    def __str__(self):
        return f"{self.full_name} ({self.xml_id})"


class ProsopographyParser:
    """Parser for TEI prosopography XML files"""
    
    def __init__(self, xml_file_path: str):
        self.xml_file_path = xml_file_path
        self.namespace = {'tei': 'http://www.tei-c.org/ns/1.0'}
        
    def parse_persons(self) -> List[Person]:
        """Parse the XML file and extract all persons into Pydantic objects"""
        persons = []
        
        ET.register_namespace('', 'http://www.tei-c.org/ns/1.0')
        
        try:
            tree = ET.parse(self.xml_file_path)
            root = tree.getroot()
            
            persons_xml = root.findall('.//tei:person', self.namespace)
            
            for person_elem in persons_xml:
                person_data = self._extract_person_data(person_elem)
                persons.append(person_data)
                
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
        except FileNotFoundError:
            print(f"File not found: {self.xml_file_path}")
            
        return persons
    
    def _extract_person_data(self, person_elem: ET.Element) -> Person:
        """Extract data from a single person element"""
        xml_id = person_elem.get('{http://www.w3.org/XML/1998/namespace}id', '')
        person_type = person_elem.get('ana', '')
        
        idno_elem = person_elem.find('tei:idno[@type="base_unifiée"]', self.namespace)
        base_id = None
        if idno_elem is not None and idno_elem.text:
            try:
                base_id = int(idno_elem.text.strip())
            except ValueError:
                base_id = None
        
        full_name = None
        family_name = None
        first_name = None
        
        pers_name = person_elem.find('tei:persName', self.namespace)
        if pers_name is not None:
            reg_elem = pers_name.find('tei:reg', self.namespace)
            if reg_elem is not None and reg_elem.text:
                full_name = reg_elem.text.strip()
                
            surname_elem = pers_name.find('tei:surname[@type="nom_famille"]', self.namespace)
            if surname_elem is not None and surname_elem.text:
                family_name = surname_elem.text.strip()
                
            forename_elem = pers_name.find('tei:forename', self.namespace)
            if forename_elem is not None and forename_elem.text:
                first_name = forename_elem.text.strip()
        
        gender = None
        gender_elem = person_elem.find('tei:gender', self.namespace)
        if gender_elem is not None and gender_elem.get('type'):
            gender = gender_elem.get('type')
        
        occupation = None
        occupation_elem = person_elem.find('tei:occupation', self.namespace)
        if occupation_elem is not None and occupation_elem.get('type'):
            occupation = occupation_elem.get('type')
        
        return Person(
            xml_id=xml_id,
            base_id=base_id,
            full_name=full_name,
            family_name=family_name,
            first_name=first_name,
            gender=gender,
            occupation=occupation,
            person_type=person_type
        )
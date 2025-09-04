import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any
from groq import Groq
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import traceback
load_dotenv()


# Pydantic models for LLM structured output
class DateEntity(BaseModel):
    """Model for a date entity with original text and ISO format"""
    original: str = Field(description="The original date text as it appears (e.g., '5e janvier 1699')")
    iso_format: str = Field(description="The date in ISO format YYYY-MM-DD (e.g., '1699-01-05')")


class TimeEntity(BaseModel):
    """Model for a time entity with original text and ISO format"""
    original: str = Field(description="The original time text as it appears (e.g., 'dix heures')")
    iso_format: str = Field(description="The time in ISO format HH:MM:SS (e.g., '10:00:00')")


class PlaceEntity(BaseModel):
    """Model for a place entity with original text only"""
    original: str = Field(description="The original place name as it appears (e.g., 'galleries du Louvre')")


class ExtractedEntities(BaseModel):
    """Model for extracted entities from text"""
    names: List[str] = Field(description="List of person names, place names, and organization names")
    dates: List[DateEntity] = Field(description="List of date mentions with original text and ISO format")
    times: List[TimeEntity] = Field(description="List of time mentions with original text and ISO format")
    places: List[PlaceEntity] = Field(description="List of place mentions with original text and place ID")


class NERMatcher:
    """Handles NER extraction and matching against prosopography names, dates, times, and places"""
    
    def __init__(self, prosopography_file: str, places_file: str):
        # self.client = OpenAI(
        #     base_url="https://openrouter.ai/api/v1",
        #     api_key="xxx",
        # )
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
        self.prosopography_file = prosopography_file
        self.places_file = places_file
        
        # Load prosopography parser
        try:
            from extract_prosopography import ProsopographyParser
            self.prosoparser = ProsopographyParser(prosopography_file)
            self.prosopography_names = self._load_prosopography_names()
        except Exception as e:
            print(f"Warning: Could not load prosopography: {e}")
            self.prosoparser = None
            self.prosopography_names = {}
        
        # Load places parser
        try:
            from extract_places import PlacesParser
            self.placesparser = PlacesParser(places_file)
            self.places_data = self._load_places_data()
            # print("SELF PLACEDATA", self.places_data)
        except Exception as e:
            print(f"Warning: Could not load places: {e}")
            self.placesparser = None
            self.places_data = {}
    
    def _load_prosopography_names(self) -> Dict[str, Any]:
        """Load all names from prosopography for matching"""
        try:
            if not self.prosoparser:
                return {}
            persons = self.prosoparser.parse_persons()
            name_dict = {}
            
            for person in persons:
                if hasattr(person, 'full_name') and person.full_name:
                    clean_name = self._clean_name(person.full_name)
                    name_dict[clean_name.lower()] = person
                    
            return name_dict
        except Exception as e:
            print(f"Error loading prosopography: {e}")
            return {}
    
    def _load_places_data(self) -> Dict[str, Any]:
        """Load all places from places database for matching"""
        try:
            if not self.placesparser:
                return {}
            places = self.placesparser.parse_places()
            place_dict = {}
            
            for place in places:
                if hasattr(place, 'place_name') and place.place_name:
                    place_dict[place.place_name.lower()] = place
                    
            return place_dict
        except Exception as e:
            print(f"Error loading places: {e}")
            return {}
    
    def _clean_name(self, name: str) -> str:
        """Clean name strings for matching"""
        if not name:
            return ""
        return name.replace("Mademoiselle", "").replace("Monsieur", "").strip()
    
    def extract_entities(self, text: str) -> ExtractedEntities:
        """Extract all entities (names, dates, times, places) from text using Groq LLM with structured output"""
        
        prompt = f"""
        Extract ALL entities from the following French historical text and categorize them:
        
        1. Names: Extract all person names (e.g., "Lavoy", "Poisson", "Baron"), place names, and organization names (e.g., "Compagnie")
        
        2. Dates: Extract all date mentions with:
           - original: exactly as it appears in the text (e.g., "5e janvier 1699")
           - iso_format: converted to ISO format YYYY-MM-DD (e.g., "1699-01-05")
           
           French months: janvier=01, février/febvrier=02, mars=03, avril=04, mai/may=05, juin=06, 
                         juillet=07, août=08, septembre=09, octobre=10, novembre=11, décembre=12
           
           Examples:
           - "5e janvier 1699" → iso_format: "1699-01-05"
           - "14me janvier 1699" → iso_format: "1699-01-14"
           - "premier jour de febvrier 1699" → iso_format: "1699-02-01"
        
        3. Times: Extract all time mentions with:
           - original: exactly as it appears in the text (e.g., "dix heures")
           - iso_format: converted to ISO format HH:MM:SS (e.g., "10:00:00")
           
           French numbers: une=01, deux=02, trois=03, quatre=04, cinq=05, six=06, sept=07, 
                          huit=08, neuf=09, dix=10, onze=11, douze=12
        
           Examples:
           - "dix heures" → iso_format: "10:00:00"
           - "avant dix heures" → iso_format: "10:00:00"
           - "après midy" → iso_format: "12:00:00"
        
        4. Places: Extract all place mentions with:
            - original: exactly as it appears in the text (e.g., "galleries du Louvre")
        
        Places to match against: Théâtre du guénégaud, Galeries du Louvre, etc.
        
        Return a JSON object with four lists:
        {{
            "names": ["name1", "name2", ...],
            "dates": [
                {{"original": "5e janvier 1699", "iso_format": "1699-01-05"}},
                {{"original": "14me janvier 1699", "iso_format": "1699-01-14"}}
            ],
            "times": [
                {{"original": "dix heures", "iso_format": "10:00:00"}},
                {{"original": "après midy", "iso_format": "12:00:00"}}
            ],
            "places": [
                {{"original": "galleries du Louvre"}},
                {{"original": "Théâtre du guénégaud"}}
            ]
        }}
        
        Text to analyze:
        {text}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                # model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert in named entity recognition for French historical texts. Extract all entities and return them in the specified JSON format with proper ISO date/time conversions and place IDs. Be thorough and extract ALL occurrences."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=30000,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "extracted_entities",
                        "schema": ExtractedEntities.model_json_schema()
                    }
                }
            )
            
            content = response.choices[0].message.content.strip()
            try:
                entities_dict = json.loads(content)
                return ExtractedEntities(**entities_dict)
            except Exception as e:
                print(f"Error parsing structured response: {e}")
                return ExtractedEntities(names=[], dates=[], times=[], places=[])
                
        except Exception as e:
            traceback()
            print(f"Error extracting entities: {e}")
            return ExtractedEntities(names=[], dates=[], times=[], places=[])
    
    def match_names(self, extracted_names: List[str]) -> Dict[str, Any]:
        """Match extracted names against prosopography database"""
        matches = {"exact": [], "fuzzy": [], "unmatched": []}
        
        for name in extracted_names:
            # Skip empty names
            if not name:
                continue
                
            name_clean = self._clean_name(name).lower()
            
            if name_clean in self.prosopography_names:
                person = self.prosopography_names[name_clean]
                matches["exact"].append({
                    "name": name,
                    "matched": {
                        "full_name": person.full_name if hasattr(person, 'full_name') else name,
                        "xml_id": person.xml_id if hasattr(person, 'xml_id') else None,
                        "base_id": person.base_id if hasattr(person, 'base_id') else 0
                    }
                })
            else:
                # Fuzzy matching for names
                best_match = None
                best_score = 0
                for pros_name, person in self.prosopography_names.items():
                    # Calculate similarity score
                    if name_clean in pros_name or pros_name in name_clean:
                        score = len(name_clean) / len(pros_name) if len(pros_name) > 0 else 0
                        if score > best_score:
                            best_score = score
                            best_match = person
                
                if best_match and best_score > 0.5:
                    matches["fuzzy"].append({
                        "name": name,
                        "matched": {
                            "full_name": best_match.full_name if hasattr(best_match, 'full_name') else name,
                            "xml_id": best_match.xml_id if hasattr(best_match, 'xml_id') else None,
                            "base_id": best_match.base_id if hasattr(best_match, 'base_id') else 0
                        }
                    })
                else:
                    matches["unmatched"].append(name)
        
        return matches
    
    def match_places(self, extracted_places: List[PlaceEntity]) -> Dict[str, Any]:
        """Match extracted places against places database"""
        matches = {"exact": [], "fuzzy": [], "unmatched": []}
        
        for place_entity in extracted_places:
            # Skip if it's a generic term
            if place_entity.original.lower() in ["compagnie", "société"]:
                matches["unmatched"].append(place_entity.original)
                continue
                
            place_lower = place_entity.original.lower()
            
            if place_lower in self.places_data:
                place = self.places_data[place_lower]
                matches["exact"].append({
                    "name": place_entity.original,
                    "matched": {
                        "place_name": place.place_name if hasattr(place, 'place_name') else place_entity.original,
                        "xml_id": place.xml_id if hasattr(place, 'xml_id') else None,
                        "place_id": place.place_id if hasattr(place, 'place_id') else None,
                        "base_id": place.base_id if hasattr(place, 'base_id') else 0
                    }
                })
            else:
                # Simple fuzzy matching for places
                best_match = None
                best_score = 0
                for place_name, place in self.places_data.items():
                    if place_lower in place_name or place_name in place_lower:
                        score = len(place_lower) / len(place_name) if len(place_name) > 0 else 0
                        if score > best_score:
                            best_score = score
                            best_match = place
                
                if best_match and best_score > 0.5:
                    matches["fuzzy"].append({
                        "name": place_entity.original,
                        "matched": {
                            "place_name": best_match.place_name if hasattr(best_match, 'place_name') else place_entity.original,
                            "xml_id": best_match.xml_id if hasattr(best_match, 'xml_id') else None,
                            "place_id": best_match.place_id if hasattr(best_match, 'place_id') else None,
                            "base_id": best_match.base_id if hasattr(best_match, 'base_id') else 0
                        }
                    })
                else:
                    matches["unmatched"].append(place_entity.original)
        
        return matches
    
    def generate_tei_xml(self, file_path: str, text: str, entities: ExtractedEntities, matches: Dict[str, Any]) -> str:
        """Generate TEI XML from text, entities, and matches including places"""
        try:
            # Create root TEI with proper namespaces including place references
            tei = ET.Element("TEI", xmlns="http://www.tei-c.org/ns/1.0")
            
            # Header with place references
            tei_header = ET.SubElement(tei, "teiHeader")
            file_desc = ET.SubElement(tei_header, "fileDesc")
            title_stmt = ET.SubElement(file_desc, "titleStmt")
            title = ET.SubElement(title_stmt, "title")
            title.text = f"Feuillets des années 1699, coté R52_0"
            
            # Add encoding description with place prefix definitions
            encoding_desc = ET.SubElement(tei_header, "encodingDesc")
            list_prefix_def = ET.SubElement(encoding_desc, "listPrefixDef")
            
            # Add prefix definition for prosopography
            prefix_def = ET.SubElement(list_prefix_def, "prefixDef")
            prefix_def.set("matchPattern", "([a-zA-Z0-20]+)")
            prefix_def.set("replacementPattern", "../Indexes/Prosopographie.xml#$1")
            prefix_def.set("ident", "pros")
            p_desc = ET.SubElement(prefix_def, "p")
            p_desc.text = "Le préfix 'pros' pointe vers les éléments person dans le fichier Prosopographie."
            
            # Add prefix definition for places
            prefix_def = ET.SubElement(list_prefix_def, "prefixDef")
            prefix_def.set("matchPattern", "([a-zA-Z0-20]+)")
            prefix_def.set("replacementPattern", "../Indexes/Lieux.xml#$1")
            prefix_def.set("ident", "lieu")
            p_desc = ET.SubElement(prefix_def, "p")
            p_desc.text = "Le préfix 'lieu' pointe vers les éléments place dans le fichier Lieux."
            
            # Source description
            source_desc = ET.SubElement(file_desc, "sourceDesc")
            ms_desc = ET.SubElement(source_desc, "msDesc")
            ms_desc.set("facs", "https://flipbooks.cfregisters.org/R52_0_1699/index.html")
            ms_id = ET.SubElement(ms_desc, "msIdentifier")
            inst = ET.SubElement(ms_id, "institution")
            inst.text = "Bibliothèque-musée de la Comédie-Française"
            repo = ET.SubElement(ms_id, "repository")
            repo.text = "Assemblées (délibérations)"
            idno = ET.SubElement(ms_id, "idno")
            idno.text = "R52_0_1699"
            
            # Text body with place references
            text_elem = ET.SubElement(tei, "text")
            body = ET.SubElement(text_elem, "body")
            
            # Process text with all entities
            lines = text.strip().split('\n')
            
            # Create divisions based on dates
            current_div = None
            current_date_when = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Process line with all entities
                p_elem = ET.SubElement(body, "p")
                self._add_line_with_all_entities(p_elem, line, entities, matches)
            
            # Convert to string
            ET.register_namespace('', "http://www.tei-c.org/ns/1.0")
            tei_str = ET.tostring(tei, encoding='unicode', method='xml')
            
            # Add XML declaration
            xml_header = '''<?xml version="1.0" encoding="UTF-8"?>
<?xml-model href="../ODD_comite.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>
<?xml-model href="../ODD_comite.rng" type="application/xml" schematypens="http://purl.oclc.org/dsdl/schematron"?>
'''
            tei_str = xml_header + tei_str
            
            # Save TEI XML
            tei_file = Path(file_path).stem + ".xml"
            with open(tei_file, 'w', encoding='utf-8') as f:
                f.write(tei_str)
            
            return tei_file
            
        except Exception as e:
            print(f"Error generating TEI XML: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _add_line_with_all_entities(self, p_elem: ET.Element, line: str, entities: ExtractedEntities, matches: Dict[str, Any]):
        """Add a line of text to a paragraph element with all entity markup including places"""
        # Create a mapping of all entities and their positions
        entity_positions = []
        
        # Map names
        name_matches = matches["names"]
        for match in name_matches["exact"] + name_matches["fuzzy"]:
            name = match["name"]
            start = 0
            while True:
                pos = line.lower().find(name.lower(), start)
                if pos == -1:
                    break
                entity_positions.append({
                    "start": pos,
                    "end": pos + len(name),
                    "type": "name",
                    "text": line[pos:pos + len(name)],
                    "data": match["matched"]
                })
                start = pos + len(name)
        
        # Map dates
        for date_entity in entities.dates:
            start = 0
            while True:
                pos = line.lower().find(date_entity.original.lower(), start)
                if pos == -1:
                    break
                entity_positions.append({
                    "start": pos,
                    "end": pos + len(date_entity.original),
                    "type": "date",
                    "text": line[pos:pos + len(date_entity.original)],
                    "iso_format": date_entity.iso_format
                })
                start = pos + len(date_entity.original)
        
        # Map times
        for time_entity in entities.times:
            start = 0
            while True:
                pos = line.lower().find(time_entity.original.lower(), start)
                if pos == -1:
                    break
                entity_positions.append({
                    "start": pos,
                    "end": pos + len(time_entity.original),
                    "type": "time",
                    "text": line[pos:pos + len(time_entity.original)],
                    "iso_format": time_entity.iso_format
                })
                start = pos + len(time_entity.original)
        
        # Map places - need to find the matched place data
        place_matches = matches.get("places", {})
        all_place_matches = place_matches.get("exact", []) + place_matches.get("fuzzy", [])
        
        for place_entity in entities.places:
            # Find the matched data for this place
            matched_data = None
            for place_match in all_place_matches:
                if place_match["name"].lower() == place_entity.original.lower():
                    matched_data = place_match["matched"]
                    break
            
            start = 0
            while True:
                pos = line.lower().find(place_entity.original.lower(), start)
                if pos == -1:
                    break
                entity_positions.append({
                    "start": pos,
                    "end": pos + len(place_entity.original),
                    "type": "place",
                    "text": line[pos:pos + len(place_entity.original)],
                    "original": place_entity.original,
                    "data": matched_data  # Store the matched data
                })
                start = pos + len(place_entity.original)
        
        # Remove overlapping entities (prefer longer matches)
        entity_positions.sort(key=lambda x: (x["start"], -x["end"]))
        filtered_positions = []
        last_end = -1
        for entity in entity_positions:
            if entity["start"] >= last_end:
                filtered_positions.append(entity)
                last_end = entity["end"]
        
        # Build the paragraph content
        if not filtered_positions:
            p_elem.text = line
            return
        
        # Add text and entities
        last_pos = 0
        for i, entity in enumerate(filtered_positions):
            # Add text before entity
            if entity["start"] > last_pos:
                text_before = line[last_pos:entity["start"]]
                if i == 0:
                    p_elem.text = text_before
                else:
                    # Add as tail of previous element
                    if len(p_elem) > 0:
                        p_elem[-1].tail = text_before
            
            # Add entity element
            if entity["type"] == "name":
                elem = ET.SubElement(p_elem, "persName")
                elem.set("ref", f"pros:{entity['data']['xml_id']}")
                elem.text = entity["text"]
            elif entity["type"] == "date":
                elem = ET.SubElement(p_elem, "date")
                elem.set("when", entity["iso_format"])
                elem.text = entity["text"]
            elif entity["type"] == "time":
                elem = ET.SubElement(p_elem, "time")
                elem.set("when", entity["iso_format"])
                elem.text = entity["text"]
            elif entity["type"] == "place":
                elem = ET.SubElement(p_elem, "placeName")
                print("MATCHED ", entity)
                # Use the stored matched data
                if entity.get("data"):
                    place_xml_id = entity["data"].get("xml_id") or entity["data"].get("place_id")
                    if place_xml_id:
                        elem.set("ref", f"lieu:{place_xml_id}")
                elem.text = entity["text"]
            
            last_pos = entity["end"]
        
        # Add remaining text
        if last_pos < len(line):
            if len(p_elem) > 0:
                p_elem[-1].tail = line[last_pos:]
            else:
                p_elem.text = line[last_pos:]
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process a file and extract all entities including places"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            print("Extracting entities from text...")
            # Extract all entities using structured output
            entities = self.extract_entities(text)
            
            print(f"Found {len(entities.names)} names, {len(entities.dates)} dates, {len(entities.times)} times, {len(entities.places)} places")
            
            # Match entities against databases
            name_matches = self.match_names(entities.names)
            place_matches = self.match_places(entities.places)
            
            matches = {
                "names": name_matches,
                "places": place_matches
            }
            
            # Generate TEI XML
            print("Generating TEI XML...")
            tei_file = self.generate_tei_xml(file_path, text, entities, matches)
            
            # Convert to dictionary for JSON serialization
            entities_dict = {
                "names": entities.names,
                "dates": [{"original": d.original, "iso_format": d.iso_format} for d in entities.dates],
                "times": [{"original": t.original, "iso_format": t.iso_format} for t in entities.times],
                "places": [{"original": p.original} for p in entities.places]
            }
            
            return {
                "file": file_path,
                "entities": entities_dict,
                "matches": matches,
                "tei_file": tei_file,
                "summary": {
                    "total_names": len(entities.names),
                    "total_dates": len(entities.dates),
                    "total_times": len(entities.times),
                    "total_places": len(entities.places),
                    "exact_matches": len(matches["names"]["exact"]) + len(matches["places"]["exact"]),
                    "fuzzy_matches": len(matches["names"]["fuzzy"]) + len(matches["places"]["fuzzy"]),
                    "unmatched": len(matches["names"]["unmatched"]) + len(matches["places"]["unmatched"])
                }
            }
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return None

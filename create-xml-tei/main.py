#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Named Entity Recognition extraction using Groq client with Pydantic structured output
Extracts names, dates, times, and places from text and matches against prosopography names
Generates TEI XML output automatically
"""

import os
import sys
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse
from groq import Groq
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from datetime import datetime
import traceback
from openai import OpenAI

from ner_matcher import NERMatcher

def main():
    """Main function for processing with place support"""
    parser = argparse.ArgumentParser(description="NER extraction and TEI XML generation with place support")
    parser.add_argument("file", help="Text file to process")
    parser.add_argument("--prosopography", default="./Indexes/Prosopographie.xml", 
                       help="Path to prosopography XML file")
    parser.add_argument("--places", default="./Indexes/Lieux.xml", 
                       help="Path to places XML file")
    
    args = parser.parse_args()
        
    print(f"Processing file: {args.file}")
    matcher = NERMatcher(args.prosopography, args.places)
    result = matcher.process_file(args.file)
    
    if not result:
        print("Failed to process file")
        return
    
    print(f"\n=== NER Extraction Results (with Places) ===")
    print(f"Processed file: {result['file']}")
    print(f"Total names extracted: {result['summary']['total_names']}")
    print(f"Total dates extracted: {result['summary']['total_dates']}")
    print(f"Total times extracted: {result['summary']['total_times']}")
    print(f"Total places extracted: {result['summary']['total_places']}")
    print(f"Exact matches: {result['summary']['exact_matches']}")
    print(f"Fuzzy matches: {result['summary']['fuzzy_matches']}")
    print(f"Unmatched: {result['summary']['unmatched']}")
    
    # Display examples
    if result['entities']['places']:
        print("\nExample places extracted:")
        for place in result['entities']['places'][:3]:
            print(f"  '{place['original']}'")
    
    # Save results
    output_file = f"{Path(args.file).stem}_resultats_ner.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved: {output_file}")
    print(f"TEI XML generated: {result['tei_file']}")


if __name__ == "__main__":
    main()
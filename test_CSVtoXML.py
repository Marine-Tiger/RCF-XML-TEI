import pandas as pd
import xml.etree.ElementTree as ET
from collections import defaultdict

# Chemins des fichiers
xlsx_path = "./Index_schema/Définitions.xlsx"  # Remplacez par le chemin réel si nécessaire
tei_path = "./Index_schema/Glossaire.xml"      # Chemin du fichier XML existant
output_path = "./Index_schema/Glossaire_output.xml"  # Fichier de sortie

# Charger le fichier Excel
xls = pd.ExcelFile(xlsx_path)

# Charger le fichier XML existant
tree = ET.parse(tei_path)
root = tree.getroot()

# Définition de l'espace de noms TEI
ns = {"tei": "http://www.tei-c.org/ns/1.0"}

# Trouver la section glossaire dans le XML existant
tei_body = root.find(".//tei:body", ns)
glossaire_div = tei_body.find(".//tei:div[@type='glossaire']", ns) if tei_body is not None else None

if glossaire_div is None:
    raise ValueError("Le fichier TEI ne contient pas la section <div type='glossaire'> attendue.")

# Dictionnaire pour suivre les identifiants uniques par préfixe
id_counters = defaultdict(int)

def generate_xml_id(entry):
    """Génère un ID unique basé sur les 4 premières lettres du mot + un compteur."""
    key = entry[:4].upper()  # Prendre les 4 premières lettres en minuscules
    id_counters[key] += 1
    return f"{key}{id_counters[key]}"

# Parcourir chaque onglet (lettre) du fichier Excel
for sheet_name in xls.sheet_names:
    # Charger les données de l'onglet
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # Renommer les colonnes pour simplifier
    df = df.rename(columns={
        df.columns[0]: "Entrée",
        df.columns[1]: "Définition",
        df.columns[3]: "Rédacteur"
    })[["Entrée", "Définition", "Rédacteur"]].dropna(how="all")  # Nettoyage

    # Vérifier si la lettre a déjà un <div> dans le TEI
    div_letter = glossaire_div.find(f".//tei:div[@type='{sheet_name}']", ns)
    if div_letter is None:
        div_letter = ET.SubElement(glossaire_div, "div", {"type": sheet_name})  # Créer si absent
    
    # Vérifier s'il y a déjà une liste <list>
    list_el = div_letter.find("tei:list", ns)
    if list_el is None:
        list_el = ET.SubElement(div_letter, "list")

    # Ajouter les entrées du glossaire
    for _, row in df.iterrows():
        if pd.notna(row["Entrée"]):
            xml_id = generate_xml_id(row["Entrée"])
            item = ET.SubElement(list_el, "item", {"xml:id": xml_id})
            ET.SubElement(item, "label", {"source": "url "}).text = row["Entrée"]
            # ET.SubElement(item, "gloss").text = row["Définition"] if pd.notna(row["Définition"]) else ""

            # # Ajouter les rédacteurs
            # if pd.notna(row["Rédacteur"]):
            #     redacteurs = [name.strip() for name in row["Rédacteur"].split("/") if name.strip()]
            #     for redacteur in redacteurs:
            #         ET.SubElement(item, "persName", {"type": "redacteur.rice"}).text = redacteur

# Enregistrer proprement le namespace TEI sans alias "ns0"
ET.register_namespace("", "http://www.tei-c.org/ns/1.0")

# Sauvegarder le fichier TEI proprement
tree.write(output_path, encoding="utf-8", xml_declaration=True)

print(f"Fichier TEI mis à jour et sauvegardé sous : {output_path}")

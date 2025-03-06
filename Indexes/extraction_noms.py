from bs4 import BeautifulSoup as bs
import json

with open("Prosopographie.xml", mode="r", encoding="utf-8") as f:
    soup = bs(f.read(), features="xml")

dico_familles = {}

personnes = soup.findAll('person')

for personne in personnes:
    id = personne["xml:id"]
    noms = personne.findAll('surname', {"type":["nom_famille", "nom_usage"]})
    for nom_obj in noms:
        nom = nom_obj.text.strip()
        if nom == "":
            continue
        if nom not in dico_familles:
            dico_familles[nom] = []
        dico_familles[nom].append({"id": id,"type": nom_obj["type"]})

for nom_famille, liste_noms in dico_familles.copy().items():
    if len(liste_noms) < 2:
        del dico_familles[nom_famille]

with open("dico_familles.json", 'w', encoding="utf-8") as f:
    json.dump(dico_familles, f, indent=4, ensure_ascii=False)
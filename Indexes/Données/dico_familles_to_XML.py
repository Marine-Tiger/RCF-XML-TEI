import json
from bs4 import BeautifulSoup as bs

with open("dico_familles.json", 'r', encoding="utf-8") as f:
    dico_familles = json.load(f)

with open("output_noms_template.xml", mode="r", encoding="utf-8") as f:
    soup = bs(f.read(), features="xml")

listPerson = soup.find('listPerson')

for nom_famille, liste_noms in dico_familles.items():
    personGroup= soup.new_tag('personGrp', attrs={'ana': nom_famille})
    for personne in liste_noms:
        person = soup.new_tag('persName', attrs={'ref': personne["id"], 'type':personne['type']})
        personGroup.append(person)
    listPerson.append(personGroup)

with open("output_noms.xml", mode="w", encoding="utf-8") as f:
    result = str(soup.prettify())
    f.write(result)
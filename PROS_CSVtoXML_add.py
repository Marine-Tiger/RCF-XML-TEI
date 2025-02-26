from bs4 import BeautifulSoup as bs
import pandas as pd
from tqdm.auto import tqdm

ANA = "comédien.ne CF"

with open("prosopographie_16e-17e.xml", mode="r", encoding="utf-8") as f:
    soup = bs(f.read(), features="xml")

df = pd.read_csv("Pensionnaires_19e.csv").fillna("")
df2 = pd.read_csv("Sociétaires_19e.csv").fillna("")

df["type"] = "pensionnaire"
df2["type"] = "societaire"

df = pd.concat((df, df2))

persons = soup.findAll("person")


xml_ids = {p["xml:id"] for p in persons}

listPerson = soup.find("listPerson")
assert listPerson, soup

pbar = tqdm(df.iterrows(), total = df.shape[0])
for i, row in pbar:
    name_start, int_id = row.NOM.replace(" ", "")[:4].upper(), 1
    xml_id = name_start + str(int_id)
    while True:
        if xml_id in xml_ids:
            int_id += 1 
            xml_id = name_start + str(int_id)
        else:
            xml_ids.add(xml_id)
            break
    pbar.set_postfix(id=xml_id)

    # person = soup.new_tag("person", attrs={"xml:id" : xml_id, "ana": ANA})  # , "CF:id": row[0]})
    person = soup.new_tag("person", attrs={"xml:id" : xml_id})
    person["ana"] = ANA

    persName = soup.new_tag("persName")

    reg = soup.new_tag("reg")
    reg.string = row.NOM
    persName.append(reg)

    prenom = row.PRENOM

    forename = soup.new_tag("forename")
    forename.string = prenom
    persName.append(forename)

    
    surname = soup.new_tag("surname")
    surname.string = prenom
    persName.append(surname)

    person.append(persName)

    gender = soup.new_tag("gender", attrs={"type": row.SEXE})
    person.append(gender)

    dates_cf = row["DATES CF"].split(" | ")
    dates_cf = [e.split("-") if "-" in e else e for e in dates_cf] 

    if len(dates_cf) > 1:
        start_dates = dates_cf[0]
        end_dates = dates_cf[-1]

        start = start_dates[0] if isinstance(start_dates, list) else start_dates
        start = start.strip(".")

        end = end_dates[-1] if isinstance(end_dates, list) else end_dates
        end = end.strip(".")

        when_date = None
        for date in dates_cf:
            if len(date) == 3 :
                when_date = date[1]

    elif len(dates_cf) == 1:
        dates = dates_cf[0]
        if len(dates) == 2:
            start, end = dates
        elif len(dates) == 3:
            start, when_date, end = dates
        elif len(dates) == 1:
            start = dates[0]
            end = dates[0]
        elif isinstance(dates, str):
            start = dates
            end = dates
        else:
            raise ValueError(f"{dates = }, {len(dates) = }")
            
    else:
        raise ValueError
    
    if row.type == "pensionnaire":
        occupation_1 = soup.new_tag("occupation", attrs={"type":"pensionnaire", "from": start, "to": end})
        person.append(occupation_1)


    elif row.type == "societaire":

        occupation_1 = soup.new_tag("occupation", attrs={"type":"acteur.rice", "from": start, "to": end})
        person.append(occupation_1)

        occupation_2 = soup.new_tag("occupation", attrs={"type":"sociétariat", "when": when_date})
        person.append(occupation_2)

    listPerson.append(person)

result = str(soup.prettify())

print(result)

with open("./Indexes/Prosopographie.xml", mode="w", encoding="utf-8") as f:
    f.write(result)


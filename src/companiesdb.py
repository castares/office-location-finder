from pymongo import MongoClient
import os
from dotenv import load_dotenv
import pandas as pd
import json
from bson.json_util import loads, dumps
import companiesdb as comp


load_dotenv()

connectionURL = os.getenv("MONGODB_URL")
client = MongoClient()
print(f'Conected to mongodb in --> {connectionURL}')


def getClient():
    return client


def connectCollection(database, collection="companies"):
    # connects to a mongodb using pymongo
    # and returns a given collection from a given database.
    db = client[database]
    coll = db[collection]
    return db, coll


# def target_offices(offices, country_code, foundation_year, money_raised):
#     target_offices = pd.DataFrame(offices.find({
#         "$and": [
#             {"properties.country": f"{country_code}"},
#             {"properties.foundation_year": {"$gt": foundation_year}},
#             {"properties.company_money_raised": {"$gte": f"${money_raised}M"}}
#         ]
#     }))
#     print(type(target_offices))
#
#     return target_offices

# # # TODO: Change to dataframe to_json and orient=records
def target_offices(offices, country_code, foundation_year, money_raised):
    target_offices = list(offices.find({
        "$and": [
            {"properties.country": f"{country_code}"},
            {"properties.foundation_year": {"$gt": foundation_year}},
            {"properties.company_money_raised": {"$gte": f"${money_raised}M"}}
        ]
    }))
    output_file = dumps(target_offices)
    with open("../output/target_offices.json", "w") as file:
        file.write(output_file)
    return target_offices


def near_offices(offices, geometry, max_distance=2000):
    # Finds values in the offices companies.offices collection
    # matching the given geometry and distance in meters values.
    return list(offices.find({"geometry.coordinates": {"$near": {"$geometry": geometry,
                                                                 "$maxDistance": max_distance
                                                                 }}
                              }))


def old_companies(near_offices, year):
    # Given a list of companies, returns the ones founded before the given year.
    old_companies = []
    for office in near_offices:
        if office["properties"]["foundation_year"] != None and office["properties"]["foundation_year"] < year:
            old_companies.append(office)
    return old_companies


def tech_startups(near_offices, year, target_offices):
    # Given a list of companies, returns the ones founded before the given year.
    tech_startups = []
    categories = ["web", "software", "mobile", "ecommerce", "games_video",
                  "biotech", "network_hosting", "cleantech", "hardware"]
    for office in near_offices:
        if office in target_offices and office["properties"]["category"] in categories:
            tech_startups.append(office)
    return tech_startups


def offices_filter(target_companies, offices):
    near_count = []
    old_count = []
    tech_startups_count = []
    names = []
    result = []
    for e in target_companies:
        near = near_offices(offices, e["geometry"])
        near_count.append(len(near))
        old = old_companies(near, 2003)
        old_count.append(len(old))
        tech_startup = tech_startups(near, 2009, target_companies)
        tech_startups_count.append(len(tech_startup))
        names.append(e["properties"]["name"])
        res = {
            "reference": e["properties"]["name"],
            "near_companies": near,
            "old_companies": old,
            "tech_startups": tech_startup
        }
        result.append(res)
    df = pd.DataFrame({
        "Name": names,
        "Companies Close": near_count,
        "Corporations Close": old_count,
        "Tech Startups": tech_startups_count
    })
    df.to_csv("../output/ranking.csv", index=False)
    output_file = dumps(result)
    with open("../output/filtered_offices.json", "w") as file:
        file.write(output_file)
    print(df)
    return result, df


def main():
    db, offices = connectCollection("companies", "offices")
    target = target_offices(offices, "GBR", 2008, 1)
    result, df = offices_filter(target, offices)


if __name__ == "__main__":
    main()

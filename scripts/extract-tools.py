#! /usr/bin/env python
import os
import urllib
import json
import yaml
import pymongo
from dotenv import load_dotenv

# Environment variables
load_dotenv()
DATABASE = os.getenv('DATABASE', "")
DATABASE_USER = os.getenv('DATABASE_USER', "")
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', "")
DATABASE_URL = os.getenv('DATABASE_URL', "")
DATABASE_CONN_URL = "mongodb+srv://{username}:{password}@{dburl}/{dbname}?retryWrites=true&w=majority"

DATABASE_CONN = DATABASE_CONN_URL.format(
    username = urllib.parse.quote_plus(DATABASE_USER),
    password=urllib.parse.quote_plus(DATABASE_PASSWORD),
    dburl=DATABASE_URL,
    dbname=DATABASE)

# Client Connection
client = pymongo.MongoClient(DATABASE_CONN)
db = client[DATABASE]


def extract_tools():
    # Tools Collection
    TOOLS = []
    tools = db.tools.find({ '$and': [{ 'type': 'tool'},{ 'activeflag': 'active'}] })
    for tool in tools:
        t = {
            '@schema': {
                "type": tool['type']
            },
            '_id': int(float(tool['id'])),
            'type': "",
            'name': tool['name'],
            'link': tool['link'],
            'authors': tool.get('authors', []),
            'uploader': tool.get('uploader', ""),
            'issued': str(tool['createdAt']) if tool.get('createdAt', 0) else str(tool['updatedon']),
            'modified': str(tool['updatedAt']),
            
            'description': tool['description'],
            'license': tool['license'],
            'views': tool['counter'],
            'category': tool['categories']['category'],
            'relations': []
        }
        # Convert LongInts
        t['authors'] = [int(float(a)) for a in t['authors']]
        if t['uploader'] != "": t['uploader'] = int(float(t['uploader']))
        # Extract Results/Insights
        if tool.get('resultsInsights', "") != "":
            t['description'] = t['description'] + "\n\n### Results & Insights\n\n" + tool['resultsInsights']
        
        # Extract keywords
        keywords = tool['tags']['topics']
        keywords.extend(tool['tags']['features'])
        t['keywords'] = keywords

        # Extract Programming languages
        progLangs = []
        for lang in tool.get('programmingLanguage', []):
            d = {
                "name": lang['programmingLanguage'],
                'version': lang['version'],
            }
            progLangs.append(d)
        t['programming_languages'] = progLangs

        # Extract Relations
        for project in tool.get('projectids', []):
            d = {
                "type": "project",
                "id": str(project),
                "description": "",
            }
            t['relations'].append(d)
        for dataset in tool.get('datasetids', []):
            d = {
                "type": "dataset",
                "id": str(dataset),
                "description": "",
            }
            t['relations'].append(d)
        for tool in tool.get('toolids', []):
            d = {
                "type": "tool",
                "id": str(tool),
                "description": "",
            }
            t['relations'].append(d)
        TOOLS.append(t)
    return TOOLS

def export_json(tools, filename):
    # Write to tools.json
    print("Writing to:", filename)
    with open(filename, 'w') as tools_json:
        json.dump({
            'count': len(tools),
            'tools': tools
        }, tools_json, indent=2)

def export_yaml(tools, filename):
    # Write to tools.yaml
    print("Writing to:", filename)
    with open(filename, 'w') as tools_yaml:
        yaml.dump({
            'count': len(tools),
            'tools': tools
        }, tools_yaml)

def main():
    tools = extract_tools()
    print("Extracted Tools:", len(tools))

    export_json(tools, '_data/tools.json')
    export_yaml(tools, '_data/tools.yaml')



if __name__ == '__main__':
    main()
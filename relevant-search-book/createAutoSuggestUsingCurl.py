import requests
import json
#delete the existing index
requests.delete('http://localhost:9200/autocomplete_test')


#add a new index
configData = '\n{\n  "settings" : {\n    "index" : {\n      "analysis" : {\n        "analyzer" : {\n          "autocomplete_analyzer" : {\n            "type" : "custom",\n            "tokenizer" : "lowercase",\n            "filter"    : ["asciifolding", "title_ngram"]\n          }\n        },\n        "filter" : {\n          "title_ngram" : {\n            "type" : "nGram",\n            "min_gram" : 3,\n            "max_gram" : 5\n          }\n        }\n      }\n    }\n  },\n \n  "mappings": {\n    "suggestions": {\n      "properties": {\n        "suggestions": {\n          "type": "text",\n          "analyzer": "autocomplete_analyzer",\n          "boost": 10\n        }\n      }\n    }\n  }\n}\n'
requests.put('http://localhost:9200/autocomplete_test', data=configData)


#add data
#data = '{ "suggestions" : "Pump" }'
# data = '[{"suggestions" : "Pump Bearing"},' \
#        '{"suggestions" : "Pump Condensor"},' \
#        '{"suggestions" : "flux Pump"}]'


'''
Bulk ingestion of the data
'''
def getAutoSuggestInitialize():
    fname = "/Users/305015992/pythonProjects/elastic-search/relevant-search-book/" + "associations.txt"
    lines = [line.rstrip('\n') for line in open(fname)]
    return(lines)

lines=getAutoSuggestInitialize()
count=1
assocDict={}
for ll in lines:
    assocDict[count]={"suggestions":ll}
    count+=1

print(assocDict)



bulkCases=''
for case in assocDict.items():
    addCmd = {"index": {"_index": "autocomplete_test",  # E
                        "_type": "suggestions",
                        "_id": case[0]}}

    bulkCases += json.dumps(addCmd) + "\n" + json.dumps(case[1]) + "\n"


print(bulkCases)




#requests.post('http://localhost:9200/autocomplete_test/suggestions', data=data)
requests.post('http://localhost:9200/_bulk', data=bulkCases)


#print(json.dumps(data))


#query
'''Use + in case you want both'''
params = (
    ('q', 'suggestions:bear+pum'),
    ('pretty', 'True'),
)

httpResp=requests.get('http://localhost:9200/autocomplete_test/_search', params=params)
print(json.loads(httpResp.text))
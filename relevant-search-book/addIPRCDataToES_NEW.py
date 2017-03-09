import json
import requests
import mysql.connector

'''Making use of the mysql database to take care of the new cases'''



'''
Function Name:getIntiialize
Purpose: Reading teh normalized cases based on teh equipment type
Variables:
    -conn: the connection object
    -equipmentType: The category of cases

'''

def getIntiialize():

    '''
    Use the database to fetch the Workorders that you want to analyze. Currently they are based on the equipment type
    '''
    cnx = mysql.connector.connect(user='root', password='root', host='localhost', port='3306', database='iprc')

    result = []
    try:
        cursor = cnx.cursor()
        cursor.execute("""SELECT iprc_cases_raw.`id`, `title`, `description`, `possibleCause`, `recommendedAction`,
        `customerResponse`,`category`,iprc_cases_raw.assetId,iprc_assets_raw.id,iprc_assets_raw.equipmentType
         from iprc_assets_raw,iprc_cases_raw where iprc_cases_raw.assetId=iprc_assets_raw.id """)
        rows = cursor.fetchall()
        #print(result)
    finally:
        cnx.close()

    cases = {}
    causes={}
    # display the rows
    for row in rows:
        #cases[row[0]]={"id":row[0],"details":row[1],"possibleCause":row[3],"equipmentType":row[5]}
        cases[row[0]] = {"id": row[0], "title":row[1],"details": row[2], "possibleCause": row[3],"recommendedAction":row[4],
                         "equipmentType": row[9],"assetId":row[8]}

    return(cases)


def getAutoSuggestInitialize():
    fname = "/Users/305015992/pythonProjects/elastic-search/relevant-search-book/" + "associations.txt"
    lines = [line.rstrip('\n') for line in open(fname)]
    return(lines)





cases=getIntiialize()


lines=getAutoSuggestInitialize()
count=1
assocDict={}
for ll in lines:
    assocDict[count]={"suggestions":ll}
    count+=1

print(assocDict)



print(json.dumps(cases))

# for case in cases.items():
#      print(case[0])


def reindex(analysisSettings={}, mappingSettings={}, casesDict={}):
    #analysisSettings=an
    settings = { #A
        "settings": {
            "number_of_shards": 1, #B
            "index": {
                "analysis" : analysisSettings, #C
            }}}

    if mappingSettings:
        settings['mappings'] = mappingSettings #C

    ##Delete the existing index
    resp = requests.delete("http://localhost:9200/iprc") #D
    print(resp)
    ###creating index based on the settings
    resp = requests.put("http://localhost:9200/iprc",data=json.dumps(settings))
    print(resp)
    ##once the index has been defined, we want to pouplate it using the bulk command.. we define _index to point to the
    ##index we want to update
    bulkCases = ""
    print("building...")
    #for id, movie in enumerate(movieDict):
    for case in casesDict.items():
        addCmd = {"index": {"_index": "iprc", #E
                            "_type": "cases",
                            "_id": case[0]}}
        bulkCases += json.dumps(addCmd) + "\n" + json.dumps(case[1]) + "\n"
    print(bulkCases)

    print("indexing...")
    #this will post the request
    resp = requests.post("http://localhost:9200/_bulk", data=bulkCases)


def reindexAutoComplete(analysisSettings={},mappingSettings={},suggestDict={}):
    settings = {  # A
        "settings": {
            "number_of_shards": 1,  # B
            "index": {
                "analysis": analysisSettings,  # C
            }}}

    if mappingSettings:
        settings['mappings'] = mappingSettings  # C

    ##Delete the existing index
    resp = requests.delete("http://localhost:9200/autosuggest")  # D
    print(resp)
    ###creating index based on the settings
    resp = requests.put("http://localhost:9200/autosuggest", data=json.dumps(settings))
    print(resp)
    ##once the index has been defined, we want to pouplate it using the bulk command.. we define _index to point to the
    ##index we want to update
    bulkCases = ""
    print("building...")
    # for id, movie in enumerate(movieDict):
    for case in suggestDict.items():
        addCmd = {"index": {"_index": "autosuggest",  # E
                            "_type": "suggestions",
                            "_id": case[0]}}

        bulkCases += json.dumps(addCmd) + "\n" + json.dumps(case[1]) + "\n"

    print("indexing...")
    # this will post the request
    resp = requests.post("http://localhost:9200/_bulk", data=bulkCases)


def search(query):
    url = 'http://localhost:9200/iprc/cases/_search'
    httpResp = requests.get(url, data=json.dumps(query)) #A
    print(json.loads(httpResp.text))
    searchHits = json.loads(httpResp.text)['hits']
    print("Num\tRelevance Score\t\tDetails" )#B

    for idx, hit in enumerate(searchHits['hits']):
            #print(hit)
            print("%s\t%s\t\t%s\t\t%s" % (idx + 1,hit['_id'], hit['_score'], hit['_source']['details']))
            if("title" in hit['highlight']):
                print("%s"%hit['highlight']['title'])
            if ("details" in hit['highlight']):
                print("%s" % hit['highlight']['details'])


#in the highlight section you need to list down the fields where to highlight. I tried with _all but not working.
#For now not sure how it will be dynamic
def constructQueryString(usersSearch,queryFields):
    query = {
        'query': {
            'multi_match': {
                'query': usersSearch,  # search string for entered by the user
                'fields':queryFields ,  # this is the boosting of the title
            }
        },
            'highlight': {
                 # 'pre_tags' : ['<pre>', '<pre>'],
                 # 'post_tags' : ['<post>', '</post>'],
                'fields' : {
                           'title' : {},
                            'details':{}
                         }
            },

        'size': '100'  # number of the results
    }

    return(query)

def explainInvertedIndex(data,analyzer):
    url = 'http://localhost:9200/iprc/_analyze?format=yaml&analyzer='+analyzer
    httpResp = requests.get(url, data=data)  # A
    print(httpResp.text)




# analysis_with_autocomplete={
#     "filter": {
#       "shingle_2": {
#         "type":"shingle",
#         "output_unigrams":"false"
#       }
#     },
#     "analyzer": {
#         "completion_analyzer": {
#             "tokenizer":
#               "standard",
#             "filter": [
#               "standard",
#               "lowercase",
#               "shingle_2"]
#         }
#     }
# }


analysis_english = {
    "analyzer" : {
      "default" : {
        "type" : "english"
        }}}

lstOfSynonyms=["brg,brgs=>bearing,bearings","drm=>drum","dsh=>desuperheater"]



'''This is to add the synonyms...make sure that the synonym stuff happens first in the filter chain'''
analysis_with_synonym={
    "filter": {
        "english_stop": {
            "type": "stop",
            "stopwords": "_english_"
        },
        "english_stemmer": {
            "type": "stemmer",
            "language": "english"
        },
        "english_possessive_stemmer": {
            "type": "stemmer",
            "language": "possessive_english"
        },
        "retail_syn_filter":{
            "type": "synonym",
             # "synonyms":[
             #     "brg,brgs=>bearing,bearings",
             #     "drm=>drum"
             #
             # ]
            "synonyms":lstOfSynonyms
        }
    },
    "analyzer": {
        "english_clone_with_synonym": {
            "tokenizer": "standard",
            "filter": [
                "retail_syn_filter",
                "english_possessive_stemmer",

                "english_stop",
                "english_stemmer"
            ]
        }
    }
}
# mappingSettings_with_synonym = {
#     'cases': {
#         'properties': {
#             "title": {
#                 'type': 'string',
#                  'analyzer': 'english_clone',
#                 'copy_to': ["completion"]
#
#                 },
#             "details": {
#                 'type': 'string',
#                  'analyzer': 'english_clone'
#
#                 },
#
#             "completion": {
#                 "type": "string",
#                 "analyzer": "completion_analyzer"
#             }
#
#             }
#         }
#     }

mappingSettings_with_synonym = {
    'cases': {
        'properties': {
            "details": {
                'type': 'string',
                 'analyzer': 'english_clone_with_synonym'

                }
            }
        }
    }






'''With the bigrams'''
#this is the analyzer which will create bigrams while anayzing
analysisSettings_with_bigrams = {
   "analyzer" : {
      "default" : {
        "type" : "english"
      },
      "english_bigrams": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "standard",
            "lowercase",
            "porter_stem",
            "bigram_filter"
          ]
      }
    },
  "filter": {
    "bigram_filter": {
        "type": "shingle",
        "max_shingle_size":2,
        "min_shingle_size":2,
        "output_unigrams":"false"
    }
  }
}
#here we are definign that we want two fields one is the details and the other is the details.bigrammed whihc is analyzed by english_bigrams
#analyzer
mappingSettings_with_bigrams = {
    'cases': {
        'properties': {
            "details": {
                'type': 'string',
                 'analyzer': 'english',
                'fields':{
                       'bigrammed':{
                            'type': 'string',
                            'analyzer': 'english_bigrams'
                       }
                    }
                }
            }
        }
    }





'''This is for autocompleteion..we will create a seperate index using the title and details fields'''
analysis_with_autocomplete={
    "filter": {
            "title_ngram" : {
            "type" : "nGram",
            "min_gram" : 3,
            "max_gram" : 5
          }
    },
    "analyzer": {
        "autocomplete_analyzer": {
            "type" : "custom",
            "tokenizer" : "english",
            "filter"    : ["asciifolding", "title_ngram"]
        }
    }
}

mappingSettings_with_autocomplete = {
    'suggestions': {
        'properties': {
            "suggestions": {
                'type': 'text',
                 'analyzer': 'autocomplete_analyzer'

                }
            }
        }
    }





#using the standard analyzer os brg and brgs are both different
reindex(casesDict=cases)
search(constructQueryString("brg",['details']))

#using the english analyzer..this will remove the extra s...so the cases with brg and brgs will both come or tag and tags will both come
reindex(analysisSettings=analysis_english,mappingSettings=None,casesDict=cases)
search(constructQueryString("tags",['details']))

#this query will have different output if you use the bigrams versus not the bigrams
reindex(analysisSettings=analysisSettings_with_bigrams,mappingSettings=mappingSettings_with_bigrams,casesDict=cases)
search(constructQueryString("drum level",['details.bigrammed^10', 'details']))

#in this scenario the brgs is getthig translated to bearing..check the effect of adding lowercase in the analyzer
reindex(analysisSettings=analysis_with_synonym,mappingSettings=mappingSettings_with_synonym,casesDict=cases)
search(constructQueryString("dsh",['title','details']))

#https://gist.github.com/justinvw/5025854...talks about the autocompletion

#reindexAutoComplete(analysisSettings=analysis_with_autocomplete,mappingSettings=mappingSettings_with_autocomplete,suggestDict=assocDict)



##Note I guess all I need to do is to create a good analyzer that takes care of the acronym, synonyms

# bulkCases=''
# for case in assocDict.items():
#     addCmd = {"index": {"_index": "autocomplete_test",  # E
#                         "_type": "suggestions",
#                         "_id": case[0]}}
#
#     bulkCases += json.dumps(addCmd) + "\n" + json.dumps(case[1]) + "\n"
#
#
# print(bulkCases)
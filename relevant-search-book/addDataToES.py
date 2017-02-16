import requests
import json


# Optional, enable client-side caching for TMDB
# Requires: https://httpcache.readthedocs.org/en/latest/
#from httpcache import CachingHTTPAdapter
#tmdb_api.mount('https://', CachingHTTPAdapter())
#tmdb_api.mount('http://', CachingHTTPAdapter())

# Some utilities for flattening the explain into something a bit more
# readable. Pass Explain JSON, get something readable (ironically this is what Solr's default output is :-p)
def flatten(l):
    [item for sublist in l for item in sublist]

def simplerExplain(explainJson, depth=0):
    result = " " * (depth * 2) + "%s, %s\n" % (explainJson['value'], explainJson['description'])
    #print json.dumps(explainJson, indent=True)
    if 'details' in explainJson:
        for detail in explainJson['details']:
            result += simplerExplain(detail, depth=depth+1)
    return result


def extract():
    f = open('/Users/305015992/pythonProjects/elastic-search/relevant-search-book/tmdb.json')
    if f:
         return json.loads(f.read())
    return {}



'''The function that is pushing the data to the elastic search'''
def reindex(analysisSettings={}, mappingSettings={}, movieDict={}):
    settings = { #A
        "settings": {
            "number_of_shards": 1, #B
            "index": {
                "analysis" : analysisSettings, #C
            }}}

    if mappingSettings:
        settings['mappings'] = mappingSettings #C

    ##Delete the existing index
    resp = requests.delete("http://localhost:9200/tmdb") #D

    ###creating index based on the settings
    resp = requests.put("http://localhost:9200/tmdb",
                        data=json.dumps(settings))

    ##once the index has been defined, we want to pouplate it using the bulk command.. we define _index to point to the
    ##index we want to update
    bulkMovies = ""
    print("building...")
    #for id, movie in enumerate(movieDict):
    for movie in movieDict.items():
        addCmd = {"index": {"_index": "tmdb", #E
                            "_type": "movie",
                            "_id": movie[0]}}
        bulkMovies += json.dumps(addCmd) + "\n" + json.dumps(movie[1]) + "\n"

    print("indexing...")
    #this will post the request
    resp = requests.post("http://localhost:9200/_bulk", data=bulkMovies)


'''Query function'''
def search(query):
    url = 'http://localhost:9200/tmdb/movie/_search'
    httpResp = requests.get(url, data=json.dumps(query)) #A
    searchHits = json.loads(httpResp.text)['hits']
    print("Num\tRelevance Score\t\tMovie Title\t\tOverview" )#B

    for idx, hit in enumerate(searchHits['hits']):
            print("%s\t%s\t\t%s\t\t%s" % (idx + 1, hit['_score'], hit['_source']['title'],hit['_source']['overview']))



'''Explain  query'''
def explainQuery(usersSearch):
    query = {
        'query': {
            'multi_match': {
                'query': usersSearch,  # search string for entered by the user
                'fields': ['title^10', 'overview'],  # this is the boosting of the title
            },
        }
    }

    #this url will be used to explain how the query will be parsed
    url = 'http://localhost:9200/tmdb/movie/_validate/query?explain'
    httpResp = requests.get(url, data=json.dumps(query))  # A
    print(json.loads(httpResp.text))


'''Explain inverted index for sentences'''
def explainInvertedIndex(data,analyzer):
    url = 'http://localhost:9200/tmdb/_analyze?format=yaml&analyzer='+analyzer
    httpResp = requests.get(url, data=data)  # A
    print(httpResp.text)


'''This function will return the JSON encoded user search string. The fields that will be considered are title and overview'''
def constructQueryString(usersSearch):
    query = {
        'query': {
            'multi_match': {
                'query': usersSearch,  # search string for entered by the user
                'fields': ['title^10', 'overview'],  # this is the boosting of the title
            },
        },
        'size': '100'  # number of the results
    }

    return(query)

def constructQueryStringChanged(usersSearch):
    query = {
        'query': {
            'multi_match': {
                'query': usersSearch,  # search string for entered by the user
                'fields': ['title'],  # this is the boosting of the title
            },
        },
        'size': '100'  # number of the results
    }

    return(query)



'''Execute'''

movieDict=extract()
# type(movieDict)
# count=0
# for movie in movieDict.items():
#     count=count+1
#     print(json.dumps(movie[1]))
#     if(count>10):
#         break

reindex(movieDict=movieDict)


usersSearch = 'basketball with cartoon aliens'
#usersSearch='hollywood'


# query = {
#     'query': {
#         'multi_match': {
#             'query': usersSearch, #search string for entered by the user
#             'fields': ['title^10', 'overview'], #this is the boosting of the title
#         },
#     },
#     'size': '100' #number of the results
# }

# json.dumps(query)

search(constructQueryString(usersSearch))
explainQuery(usersSearch)
#standard analyzer will not remove the stopwords
explainInvertedIndex("Fire with Fire brgs","standard")
#english analyzer will remove the stopwords
explainInvertedIndex("Fire with Fire brgs flies","english")


##reindexing to remove the stopwords and introduce stemming
movieDict=extract()

#for both the title and the overview we are applying an anlyzer that will remove the stopwords and perform stemming
mappingSettings = {
       'movie': {
            'properties': {
               'title': { #A
                   'type': 'string',
                   'analyzer': 'english'
               },
            'overview': {
                   'type': 'string',
                   'analyzer': 'english'
               }
            }
       }
}
reindex(mappingSettings=mappingSettings,movieDict=movieDict)

search(constructQueryString(usersSearch))

#############DO NOT USE THE FOLLOWING########


settings= \
    {
    "analysis": {
      "analyzer": {
        "standard_clone": {
          "tokenizer": "standard",
          "filter": [
            "standard",
            "lowercase",
            "stop"]
            }
            }
        }
    }

mappingSettings = {
       'movie': {
            'properties': {
               'title': { #A
                   'type': 'string',
                   'analyzer': 'standard_clone'
               }
            }
    }
}


reindex(analysisSettings=settings,mappingSettings=mappingSettings,movieDict=movieDict)
search(constructQueryStringChanged("mr. weirdlove: don't worry, I'm learning to start loving bombs"))

explainInvertedIndex("this is it","standard_clone")
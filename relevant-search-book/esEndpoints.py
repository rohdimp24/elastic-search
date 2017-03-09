from flask import Flask
import os
import pandas as pd
import scipy as sp
import numpy as np
import re
import csv
import json
import requests
import urllib
from flask_cors import CORS, cross_origin

# import psycopg2
import pickle
from sklearn.cluster import KMeans
app = Flask(__name__)

port = int(os.getenv("PORT", 64781))

#esServer="http://3.204.155.7:9200/"
esServer="http://localhost:9200/"

CORS(app)

'''
Function Name:getIntiialize
Purpose: Reading teh normalized cases based on teh equipment type
Variables:
    -conn: the connection object
    -equipmentType: The category of cases

'''
@app.route('/autocomplete/<string:query>')
def getAutoCompleteSuggestions(query):
    queryparam="suggestions:"+query
    params = (
        ('q', queryparam),
        ('pretty', 'True'),
    )
    #params={'q' : query, 'pretty' : "True"}

    #print(urllib.urlencode(params))
    httpResp = requests.get(esServer+'autocomplete_test/_search', params=params)
    jsonRes=json.loads(httpResp.text)
    res=jsonRes['hits']['hits']
    #print(res)
    arrSuggestions=[]
    for node in res:
        arrSuggestions.append(node['_source']['suggestions'])

    output=';'.join(arrSuggestions)
    print(output)
    return(output)

#
# @app.route('/autocomplete/<string:query>')
# def getAutoCompleteSuggestions(query):
#     queryparam="suggestions:"+query
#     params = (
#         ('q', queryparam),
#         ('pretty', 'True'),
#     )
#     #params={'q' : query, 'pretty' : "True"}
#
#     #print(urllib.urlencode(params))
#     httpResp = requests.get(esServer+'autocomplete_test/_search', params=params)
#     jsonRes=json.loads(httpResp.text)
#     print(jsonRes)
#     return(httpResp.text)


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

def search(query):
    url = esServer+'iprc/cases/_search'
    httpResp = requests.get(url, data=json.dumps(query)) #A
    print(json.loads(httpResp.text))
    return(httpResp.text)
    # searchHits = json.loads(httpResp.text)['hits']
    # print("Num\tRelevance Score\t\tDetails" )#B
    #
    # for idx, hit in enumerate(searchHits['hits']):
    #         #print(hit)
    #         print("%s\t%s\t\t%s\t\t%s" % (idx + 1,hit['_id'], hit['_score'], hit['_source']['details']))
    #         if("title" in hit['highlight']):
    #             print("%s"%hit['highlight']['title'])
    #         if ("details" in hit['highlight']):
    #             print("%s" % hit['highlight']['details'])


@app.route('/searchcases/<string:query>')
def getSearchResultsFromES(query):
    #url = 'http://localhost:9200/iprc/cases/_search'
    #httpResp = requests.get(url, data=json.dumps(query))  # A

    #print(json.dumps(constructQueryString(query,['title','details'])))
    #httpResp = requests.get(url, data=json.dumps(constructQueryString(query,['title','details'])))  # A
    #print(httpResp)
    #print(json.loads(httpResp.text))
    #return(httpResp.text)
    res=json.loads(search(constructQueryString(query,['title','details'])))
    return(json.dumps(res['hits']['hits']))



if __name__ == '__main__':
    #getAutoCompleteSuggestions("pump")
    #getSearchResultsFromES("pump")
    app.run(host='0.0.0.0', port=port)

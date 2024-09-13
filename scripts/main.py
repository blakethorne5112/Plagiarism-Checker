# -*- coding: utf-8 -*-
# Master script for the plagiarism-checker
# Coded by: Shashank S Rao

# Import other modules
from cosineSim import *
from htmlstrip import *
from extractdocx import *

# Import required modules
import codecs
import traceback
import sys
import operator
import urllib.parse
import urllib.request
import json as simplejson
import re

# Given a text string, remove all non-alphanumeric
# characters (using Unicode definition of alphanumeric).
def getQueries(text, n):
    sentenceEnders = re.compile('[.!?]')
    sentenceList = sentenceEnders.split(text)
    sentencesplits = []
    for sentence in sentenceList:
        x = re.compile(r'\W+', re.UNICODE).split(sentence)
        x = [ele for ele in x if ele != '']
        sentencesplits.append(x)
    finalq = []
    for sentence in sentencesplits:
        l = len(sentence)
        l = l // n
        index = 0
        for i in range(l):
            finalq.append(sentence[index:index + n])
            index = index + n - 1
        if index != len(sentence):
            finalq.append(sentence[len(sentence) - index:len(sentence)])
    return finalq

# Search the web for the plagiarised text
# Calculate the cosine similarity of the given query vs matched content on Google
# This is returned as 2 dictionaries
def searchWeb(text, output, c):
    try:
        text = text.encode('utf-8')
    except:
        pass
    query = urllib.parse.quote_plus(text)
    if len(query) > 60:
        return output, c
    
    # Using Google APIs for searching web
    base_url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q='
    url = base_url + '%22' + query + '%22'
    request = urllib.request.Request(url, None, {'Referer': 'Google Chrome'})
    response = urllib.request.urlopen(request)
    results = simplejson.load(response)

    try:
        if len(results) and 'responseData' in results and 'results' in results['responseData'] and results['responseData']['results']:
            for ele in results['responseData']['results']:
                Match = results['responseData']['results'][0]
                content = Match['content']
                if Match['url'] in output:
                    output[Match['url']] += 1
                    c[Match['url']] = (c[Match['url']] * (output[Match['url']] - 1) + cosineSim(text, strip_tags(content))) / output[Match['url']]
                else:
                    output[Match['url']] = 1
                    c[Match['url']] = cosineSim(text, strip_tags(content))
    except:
        return output, c
    return output, c

# Use the main function to scrutinize a file for plagiarism
def main():
    # n-grams N VALUE SET HERE
    n = 9
    if len(sys.argv) < 3:
        print("Usage: python main.py <input-filename>.txt <output-filename>.txt")
        sys.exit()

    if sys.argv[1].endswith(".docx"):
        t = docxExtract(sys.argv[1])
    else:
        try:
            with open(sys.argv[1], 'r', encoding='utf-8') as t:
                t = t.read()
        except FileNotFoundError:
            print("Invalid Filename")
            print("Usage: python main.py <input-filename>.txt <output-filename>.txt")
            sys.exit()

    queries = getQueries(t, n)
    q = [' '.join(d) for d in queries]
    found = []

    # Using 2 dictionaries: c and output
    # output is used to store the URL as key and the number of occurrences of that URL in different searches as value
    # c is used to store URL as key and sum of all the cosine similarities of all matches as value
    output = {}
    c = {}
    i = 1
    count = len(q)
    if count > 100:
        count = 100

    for s in q[:100]:
        output, c = searchWeb(s, output, c)
        msg = "\r{}/{} completed...".format(i, count)
        sys.stdout.write(msg)
        sys.stdout.flush()
        i += 1

    with open(sys.argv[2], "w", encoding='utf-8') as f:
        for ele in sorted(c.items(), key=operator.itemgetter(1), reverse=True):
            f.write(str(ele[0]) + " " + str(ele[1] * 100.00))
            f.write("\n")

    print("\nDone!")


if __name__ == "__main__":
    try:
        main()
    except:
        # Writing the error to stdout for better error detection
        error = traceback.format_exc()
        print("\nUh Oh!\n" + "Plagiarism-Checker encountered an error!:\n" + error)

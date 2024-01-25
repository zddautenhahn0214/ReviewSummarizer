#ReviewSummarizer project.
#1/20/2024
#Zach Datuenhahn
#This uses openAI API Key, so don't upload that again lol

import gzip  
import json
import PySimpleGUI as sg
from openai import OpenAI
import os
import re

# import inspect
# print(inspect.getframeinfo(inspect.currentframe()).lineno)


#get the meta data for some company based on search
def findMetaData(path, search, key='name'):
    g = gzip.open(path, 'r')
    #first strip chars othre than aA-zZ
    searchName = re.sub('[\W_]+', '', search)
    searchName = searchName.lower()
    
    #list to store results in to rerturn
    results = []
    #lots of duplicate results in the data, only add if unique ID
    resultsID = []
    
    #once the enough results have been found return
    #will count down after each result, so set number of results here
    resultLimit = 10
    #if no search specified return all results until limit
    for l in g:
        #get name of comapny thne also remove extra chars for compaison
        companyName = json.loads(l)[key]
        #skip if no data in requested field
        if not companyName:
            continue
        companyName = re.sub('[\W_]+', '', companyName)
        #make lower case for easier search
        companyName = companyName.lower()
        
        if searchName:
            if searchName in companyName:
                # print(json.loads(l))
                #only add if not a duplicate
                if json.loads(l)["gmap_id"] not in resultsID:
                    #return once resultLimit reached
                    resultLimit = resultLimit - 1
                    resultsID.append(json.loads(l)["gmap_id"])
                    results.append(json.loads(l))
        else:
            if json.loads(l)["gmap_id"] not in resultsID:
                #return once resultLimit reached
                resultLimit = resultLimit - 1
                resultsID.append(json.loads(l)["gmap_id"])
                results.append(json.loads(l))
            
        #leave loop once finished with this company
        if resultLimit < 0:
            break
    return results
    

#Data can be treated as python dictionary objects. A simple script to read any of the above the data is as follows:
def parse(path, specific_gmap_id):
    g = gzip.open(path, 'r')
    #list to store reviews in to be returned at end
    reviews = []
    #once the company has been found and parsed, break the loop to save time
    found_gmap_id = False
    for l in g:
        if specific_gmap_id:
            if json.loads(l)['gmap_id'] == specific_gmap_id:
                # print(json.loads(l))
                found_gmap_id = True
                reviews.append(json.loads(l))
            #leave loop once finished with this company
            elif found_gmap_id:
                break
        else:
            reviews.append(json.loads(l))
    return reviews


#testing some openAI API function calls   
def askGPT(reviewData):
    
    client = OpenAI()
    
    # reviewData = ""
    
    #instructions given to gpt 
    systemInstructions = "Read the provided reviews. List as bullet points, Then list the issues that would be the highest priority to investigate and fix, and finally provide what the average person would rate the entity on a scale of 1-5 given the reviews. We have to determine what the most common complaints and praises are in these reviews. What information should the average person take from these reviews that they could responsibly share with others without giving a warped view? Lets work this out step by step"

    print("systemInstructions: ", systemInstructions)
    print()
    # print("reviewData: ", reviewData)
    
    
    #consider messing with temperature:  number(between 0 and 1.)   Optional Defaults to 0 
    #"If set to 0, the model will use log probability to automatically increase the temperature until certain thresholds are hit."
    completion = client.chat.completions.create(
      model="gpt-3.5-turbo-1106",
      messages=[
        {"role": "system", "content": systemInstructions},
        {"role": "user", "content": reviewData}
      ]
    )
    
    print(completion)
    print()
    print(completion.choices[0].message.content)
    
    completionText = str(completion.choices[0].message.content)
    completion = str(completion)
    with open("completionRaw.txt", "a") as outfile:
        outfile.write(completion)
        outfile.write("\n")
        
    with open("completion.txt", "a") as outfile:
        outfile.write(completionText)
        outfile.write("\n")
        
    # this didnt work
    # print(completion.choices[0].message["content"])
    

#function that calls the search function for metadata and also defines what to search fro and in what field
def metaSearch():

    #search for metadata
    pathToMetaData = "meta-Missouri.json.gz"
    search = "door sys"
    #serach key is 'name' by default
    key = ""
    
    if key:
        results = findMetaData(pathToData, search, key)
        for i in results:
            print(i['name'], i['gmap_id'], i[key])
            print()
    else:
        results = findMetaData(pathToData, search)
        for i in results:
            print(i['name'], i['gmap_id'])
            print()
            

def main():
    #normal review data path
    pathToData = "review-Missouri.json.gz"
    #review meta data path
    pathToMetaData = "meta-Missouri.json.gz"
    #if you want to look at a specific company list it's gmap_id here, else leave blank for all
    doorSystemsID = "0x87c11ff8ff703cb5:0x9ac3ae467ab58bd7"
    specific_gmap_id = "0x87c11ff8ff703cb5:0x9ac3ae467ab58bd7"
    specific_gmap_id = doorSystemsID
    
    #limit the number of characters in each batch of reviews
    #if adding the next review would exceed this limit pause and continue then start over where left off.
    reviewCharLimit = 8192
   
    dataList = parse(pathToData, specific_gmap_id)
    
    # print(dataList)
    dataObjLen = len(dataList)
    print("dataObjLen: ", dataObjLen)
    
    #just get the review's text data to send to gpt.
    reviewText = ""
    
    #count number of reviews with text
    count = 0
    reviewCharCount = 0
    #loop through data
    for review in dataList:
        # print(review)
        #only print reviews with text
        print(review['time'])
        if review['text']:
            # print(review['text'])
            # print()
            #clean review data and make each review seperate and obviously distinct.
            text = review['text']
            
            #remove characters that cant be encoded with ascii
            text = ascii(text)
            #remove {} from review to ensure no issues
            text = text.replace('{', '')
            text = text.replace('}', '')
            
            #check if the next review will exceed the limit(also add + for chacters being manually added)
            if (reviewCharCount + len(text) + 6) > reviewCharLimit:
                break
            reviewText = reviewText + "{" + text + "}, " + '\n\n'
            reviewCharCount = len(reviewText)
            
            count = count + 1
    
    print()
    
    #get meta data for same company id
    metaResults = findMetaData(pathToMetaData, specific_gmap_id, 'gmap_id')
    if len(metaResults) == 1:
        print('name:', metaResults[0]['name'])
        print('avg_rating: ', metaResults[0]['avg_rating'])
        print('num_of_reviews: ', metaResults[0]['num_of_reviews'])
        print('num of reviews with text: ', count)
    else:
        print(metaResults)
        print(len(metaResults))
    
    
    
    #send review text data to json and save it to file for me to look over 
    # reviewText = json.dumps(reviewText)
    # Writing to reviewText.json
    with open("reviewText.txt", "w") as outfile:
        outfile.write(reviewText)
        
    
    # #get meta data for company id if specified
    # if specific_gmap_id:
        # pathToData = "meta-Missouri.json.gz"
        # #if you want to look at a specific company list it's gmap_id here, else leave blank for all
        # specific_gmap_id = "0x87c0f1e8156a0aa7:0x6d2360d3b0f3846"
        # metaDataList = parse(pathToData, specific_gmap_id)
        # #should return one
        # if len(metaDataList) == 1:
            # print('name:', metaDataList[0]['name'])
            # print('avg_rating: ', metaDataList[0]['avg_rating'])
            # print('num_of_reviews: ', metaDataList[0]['num_of_reviews'])
            # print('num of reviews with text: ', count)
        # else:
            # print(metaDataList)
            # print(len(metaDataList))
        
    
    # print("reviewData: ", reviewText)
    # askGPT(reviewText)

   
def mainMenu():
    # Define the window's contents
    layout = [[sg.Text("What's your name?")],
              [sg.Input(key='-INPUT-')],
              [sg.Text(size=(40,1), key='-OUTPUT-')],
              [sg.Button('Ok'), sg.Button('Quit')]]

    # Create the window
    window = sg.Window('Review Summarizer', layout)

    # Display and interact with the Window using an Event Loop
    while True:
        event, values = window.read()
        # See if user wants to quit or window was closed
        if event == sg.WINDOW_CLOSED or event == 'Quit':
            break
        # Output a message to the window
        window['-OUTPUT-'].update('Hello ' + values['-INPUT-'] + "! Thanks for trying PySimpleGUI")

    # Finish up by removing from the screen
    window.close()
    

if __name__ == '__main__':
    reviewData = ""
    
    # askGPT(reviewData)
    
    # main()
    
    # metaSearch()
    
    mainMenu()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
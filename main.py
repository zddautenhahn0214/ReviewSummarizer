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




#define a few global variables
#put your files paths to data here, have to be .gz files unless you change the code
reviewDataFilePath = "review-Missouri.json.gz"
metaDataFilePath = "meta-Missouri.json.gz"

#list of keys in each json entry, change this if you have different keys
reviewKeyList = ["gmap_id", "user_id", "name", "time", "rating", "text", "pics", "resp"]
metaKeyList = ["name", "address", "gmap_id", "description", "latitude", "longitude", "category", "avg_rating", "num_of_reviews", "price", "hours", "MISC", "state", "relative_results", "url"]


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
    #counter to track number of lines checked so I can see the program didn't jsut crash
    counter = 0
    #if no search specified return all results until limit
    for l in g:
        counter = counter + 1
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
            
        #print every 10,000 lines checked
        if counter % 10000 == 0:
            print("Checking records... ", counter, " records checked so far")
        
        #leave loop once finished with this company
        if resultLimit < 0:
            break
    return results
    

#Data can be treated as python dictionary objects. A simple script to read any of the above the data is as follows:
def getReviewData(path, specific_gmap_id):
    g = gzip.open(path, 'r')
    #list to store reviews in to be returned at end
    reviews = []
    #counter to track number of lines checked so I can see the program didn't jsut crash
    counter = 0
    #once the company has been found and parsed, break the loop to save time
    found_gmap_id = False
    for l in g:
        counter = counter + 1
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
            
        #print every 10,000 lines checked
        if counter % 10000 == 0:
            print("Checking records... ", counter, " records checked so far ", json.loads(l)['gmap_id'])
            
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
    

#function that calls the search function for metadata and also defines what to search for and in what field
#default key and search to avoid breaking the code
def metaSearch(key='name', search='door system'):

    #search for metadata
    pathToMetaData = metaDataFilePath
    
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
    pathToData = reviewDataFilePath
    #review meta data path
    pathToMetaData = metaDataFilePath
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
        # pathToData = reviewDataFilePath
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
    # Define the layout of the window
    layout = [
        # Menu bar at the top
        [sg.Menu([['File', ['Exit']]], tearoff=False)],
        [
            # Search bar, search key dropdown, and buttons on the left side
            sg.Column([
                [sg.Text('Data Search'), sg.Combo(['Meta Data', 'Review Data'], default_value='Meta Data', key='search_file', enable_events=True)],
                [sg.Text('Search: '), sg.InputText(key='search_bar', focus=True), sg.Combo(metaKeyList, default_value=metaKeyList[0], key='search_key', enable_events=True)],
                [sg.Text('Meta Data Search Results:')],
                [sg.Multiline(size=(50, 20), key='search_results')],
                [sg.Button('Prev'), sg.Button('Next'), sg.VerticalSeparator(), sg.Button('Clear'), sg.Button('Search'), sg.VerticalSeparator(), sg.Text('Results: 0', key='meta_search_num')]
            ]),
            # Multiline element to display reviews and summary on the right side
            sg.Column([
                #few blank lines for visual spacing
                [sg.Text('')],
                [sg.Text('')],
                [sg.Text('Review Data & Summary:')],
                [sg.Multiline(size=(50, 20), key='data_summary')],
                [sg.Button('Get Reviews', key='get_reviews'), sg.Button('Summarize'), sg.VerticalSeparator(), sg.Text('Results: 0', key='review_search_num')]
            ])
        ]
    ]

    # Create the window with the defined layout
    window = sg.Window('Review Summarizer', layout)

    # Event loop to handle events and user inputs
    while True:
        event, values = window.read()
        
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
            
        elif event == 'search_file':
            #swap the key vlaues from the drop down menue depending on which data set you are searching thorugh
            if values['search_file'] == 'Meta Data':
                window['search_key'].update(values=metaKeyList, set_to_index=0)
            elif values['search_file'] == 'Review Data':
                window['search_key'].update(values=["gmap_id"], set_to_index=0)
            
        elif event == 'search_key':
            # When a new key is selected, update the reviews_summary field with the new key's text
            window['reviews_summary'].update(values['search_key'])
        
        elif event == 'Clear':
            # This is where the function to clear the search would be called
            window['search_bar'].update('')       # Reset the search bar to default text
            window['search_results'].update('')        # Clear the meta data field
            window['meta_search_num'].update('Results: 0')   #reset displayed search results to zero
            window['data_summary'].update('')        # Clear the review data field
            window['review_search_num'].update('Results: 0')   #reset displayed review results to zero
            window['search_bar'].set_focus()      # Set focus back to the search bar
            
   
        #define function for Search button
        elif event == 'Search':
            
            #different search functions for different file types
            if values['search_file'] == 'Meta Data':
                #define needed vars
                pathToData = metaDataFilePath
                search = values['search_bar']
                key = values['search_key']
                #call the search function for meta data, requires path to file, search term, and key to search.
                #returns a list of json objects
                results = findMetaData(pathToData, search, key)
                print(pathToData, search, key, len(results))
                
                #reformat data for display purposes
                resultText = ""
                for i in results:
                    resultText = resultText + str(i) + '\n\n'
                #display results to correct window
                if resultText:
                    window['search_results'].update(resultText)
                else:
                    window['search_results'].update("No results found")
                
                #update search results number
                searchNumText = "Results: " + str(len(results))
                window['meta_search_num'].update(searchNumText)
                
                
            elif values['search_file'] == 'Review Data':
                #define needed vars
                pathToData = reviewDataFilePath
                companyID = values['search_bar']
                #get review data fro a specfic gmap_id
                #returns a list of json objects
                results = getReviewData(pathToData, companyID)
                print(pathToData, companyID, len(results))
                
                #reformat data for display purposes
                resultText = ""
                for i in results:
                    resultText = resultText + str(i) + '\n\n'
                #display results to correct window
                if resultText:
                    window['data_summary'].update(resultText)
                else:
                    window['data_summary'].update("No results found")
                
                #update search results number 
                searchNumText = "Results: " + str(len(results))
                window['review_search_num'].update(searchNumText)
                
                
            
        
        #get all the reviews for a specific gmap_id that have text
        elif event == 'get_reviews':   
            #define needed vars
            pathToData = reviewDataFilePath
            companyID = values['search_bar']
            #make sure there is something in there at least
            if companyID:
                # 0x87d8b617445d26e5:0x6e90d4b95168452e
                # 0x87c0e2ecff959bc9:0x7d916d9e85d2ed84
                # 0x87df2e32e108cc51:0xa5a4b329ef1fb75d 
                # 0x87df2e44fffdd56d:0x72c2d0894eab822a 
                # 0x87df2d5d987ab84b:0x1c7a333dd30d670f 
                # 0x87d8cb3b67b275a7:0x13d3b7087c062d4
                #validate gmap_id to make sure it fits format
                #strip chars other than numbers, letters, and ':'
                companyID = re.sub(r'[^a-zA-Z0-9:]', '', companyID)
                companyID = re.sub(r'^.*?0x', '0x', companyID)
                #remove everything in front of '0x' if there
                companyID
                #all gmap_ids start with "0x[16 chars]:[the rest]"
                #so must be minimum of 19 chars long
                if len(companyID) < 19:
                    window['data_summary'].update("Error: Invalid gmap_id, too short")
                else:
                    if companyID[:2] != "0x" or companyID[18] != ':':
                        window['data_summary'].update("Error: Invalid gmap_id")
                        
                    else:
                        #get review data fro a specfic gmap_id
                        #returns a list of json objects
                        print(pathToData, companyID)
                        results = getReviewData(pathToData, companyID)
                        print(pathToData, companyID, len(results))
                        
                        #reformat data for display purposes
                        resultText = ""
                        for i in results:
                            resultText = resultText + str(i) + '\n\n'
                        #display results to correct window
                        window['data_summary'].update(resultText)
                        
                        #update search results number
                        searchNumText = "Results: " + str(len(results))
                        window['review_search_num'].update(searchNumText)
                
            else:
                window['data_summary'].update("Error: No gmap_id")

        elif event == 'Prev':
            # This is where the function to go to the previous review would be called
            pass
        elif event == 'Next':
            # This is where the function to go to the next review would be called
            pass
        elif event == 'Summarize':
            # This is where the function to summarize the reviews would be called
            pass

    # Close the window
    window.close()

    

if __name__ == '__main__':
    reviewData = ""
    
    # askGPT(reviewData)
    
    # main()
    
    # metaSearch()
    
    mainMenu()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
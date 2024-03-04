#ReviewSummarizer project.
#1/20/2024
#Zach Datuenhahn
#This uses openAI API Key, so don't upload that again lol

import gzip  
import json
import ast
import PySimpleGUI as sg
from openai import OpenAI
import os
import re


#define a few global variables
#put your files paths to data here, have to be .gz files unless you change the code
reviewDataFilePath = "review-Missouri.json.gz"
metaDataFilePath = "meta-Missouri.json.gz"

#list of the available LLM models to use. Put the exact model name here to be passed to the api call.
modelList = ['gpt-3.5-turbo-0125', 'gpt-4-0125-preview']
#as of 3/4/2024 
#gpt-4-0125-preview has 128k context, returns 4096
#gpt-3.5-turbo-0125 has 16,385 tokens reuturns a max of 4096

#list of keys in each json entry, change this if you have different keys
metaKeyList = ["name", "address", "gmap_id", "description", "latitude", "longitude", "category", "avg_rating", "num_of_reviews", "price", "hours", "MISC", "state", "relative_results", "url"]


#limit on the number of meta search results displayed at one time
resultLimit = 20
#limit the number of total chracters returned from the reviews 
#since there is a token limit on what can be sent to the LLM models. For now manually change this as needed.
reviewCharLimit = 8192


#currently loading the file every search and searching through entire file each pagination
#terrible way to do it I'm sure, but the files are small enough to let me get away with it so I am for now
#get the meta data for some company based on search
#path is the file path for the file containting the meta data as a list of jsons
#search is the parameter the user passes for what they are looknig for
#key is which key of the json obj is being searched, defaults to 'name'
#pageNum is which page number the search results are on so they can be interated, 
#    defaults to 0 and is multplied by result limit
def findMetaData(path, search, key='name', pageNum=0):
    #this works for now, but I probably don't need to be opening the file over and over again for every search
    g = gzip.open(path, 'r')
    
    #validate that key is a key in the lsit of jsons from file
    line = json.loads(g.readline())
    if not (key in line):
        print(key, ' is not valid key and is not in first line\n')
        return []
        
    
    #first strip chars othre than aA-zZ
    searchDetail = re.sub('[\W_]+', '', search)
    searchDetail = searchDetail.lower()
    
    #list to store results in to rerturn
    results = []
    #lots of duplicate results in the data, only add if unique ID
    resultsID = []
    
    #once the enough results have been found return
    resultCount = 0
    #counter to track number of lines checked so I can see the program didn't jsut crash
    counter = 0
    for l in g:
        counter = counter + 1
        #get name of company then also remove extra chars for compaison, make sure it is a string
        companyDetail = str(json.loads(l)[key])
        #skip if no data in requested field
        if not companyDetail:
            continue
        companyDetail = re.sub('[\W_]+', '', companyDetail)
        #make lower case for easier search
        companyDetail = companyDetail.lower()
        
        #if no search term specified return all results
        if searchDetail:
            if searchDetail in companyDetail:
                #only add if not a duplicate
                if json.loads(l)["gmap_id"] not in resultsID:
                    #return once resultLimit reached
                    resultCount = resultCount + 1
                    
                    #only return results after skipping pageNum*reviewLim results first
                    if resultCount > resultLimit*pageNum:
                        resultsID.append(json.loads(l)["gmap_id"])
                        results.append(json.loads(l))
        else:
            if json.loads(l)["gmap_id"] not in resultsID:
                #return once resultLimit reached
                resultsID.append(json.loads(l)["gmap_id"])
                results.append(json.loads(l))
            
        #print every 10,000 lines checked
        if counter % 10000 == 0:
            print("Checking meta records... ", counter, " records checked so far")
        
        #leave loop once result limit is hit
        if len(results) >= resultLimit:
            break
    return results
    

#Data can be treated as python dictionary objects. A simple script to read any of the above the data is as follows:
def getReviewData(path, specific_gmap_id, reviewsToSkip=0):
    g = gzip.open(path, 'r')
    #list to store reviews in to be returned at end
    reviews = []
    #counter to track number of lines checked so I can see the program didn't just crash
    counter = 0
    #track the number of characters in the text field of the review, since that is what will be sent to the AI.
    charTextCount = 0
    #once the company has been found and parsed, break the loop to save time
    found_gmap_id = False
    #bool to check if more reviews exist, for pagiantion purposes
    nextReviewExists = False
    for l in g:
        counter = counter + 1
        if specific_gmap_id:
            currentRecord = json.loads(l)
            if currentRecord['gmap_id'] == specific_gmap_id:
                #for now only return reviews that contain text data, may add a toggle to see all later
                if currentRecord['text']:
                    #only add after skipping to correct result number
                    if reviewsToSkip > 0:
                        reviewsToSkip = reviewsToSkip - 1
                    else:
                        #first check that adding this record wont exceed the char limit, if so then exit loop
                        if (charTextCount + len(str(currentRecord['text'])) + 6) >= reviewCharLimit:
                            nextReviewExists = True
                            break
                        #count number of chars in review text. Also add 6 for the "{}, \n\n" that will be added
                        charTextCount = charTextCount + len(str(currentRecord['text'])) + 6
                        # print(json.loads(l))
                        found_gmap_id = True
                        reviews.append(currentRecord)
            #leave loop once finished with this company
            elif found_gmap_id:
                break
            
        #print every 10,000 lines checked
        if counter % 10000 == 0:
            pass
            print("Checking review records... ", counter, " records checked so far ")
            
            
    return reviews, counter, charTextCount, nextReviewExists


#testing some openAI API function calls   
def askLLM(reviewData, titleText, modelChoice="gpt-3.5-turbo-1106"):
    
    client = OpenAI()
    
    # reviewData = ""
    #this is a bool toggle for letting me test the UI without needing to constanttly spend money calling the GPT API
    #True False
    testUI = True
    completion = ''
    completionText = ''
    print("modelChoice type: ", type(modelChoice))
    print("modelChoice: ", modelChoice)
    
    
    #instructions given to gpt 
    systemInstructions = "Read the provided reviews. List as bullet points, Then list the issues that would be the highest priority to investigate and fix, and finally provide what the average person would rate the entity on a scale of 1-5 given the reviews. We have to determine what the most common complaints and praises are in these reviews. What information should the average person take from these reviews that they could responsibly share with others without giving a warped view? Lets work this out step by step"

    
    #don't call api if testing UI
    if testUI:   
        #output which model is being used and exactly what would be sent to it 
        completionText = "Model Chosen: " + modelChoice + '\nText That sent to LLM:\n\n' + reviewData
        
    else:
        #consider messing with temperature:  number(between 0 and 1.)   Optional Defaults to 0 
        #"If set to 0, the model will use log probability to automatically increase the temperature until certain thresholds are hit."
        completion = client.chat.completions.create(
          model=modelChoice,
          messages=[
            {"role": "system", "content": systemInstructions},
            {"role": "user", "content": reviewData}
          ]
        )
        
    
    #only do run this when not testing the UI
    if not testUI:
        
        completionText = str(completion.choices[0].message.content)
        completion = str(completion)
        with open("completionRaw.txt", "a") as outfile:
            outfile.write(completion)
            outfile.write("\n")
            outfile.write("\n")
            
        with open("completion.txt", "a") as outfile:
            outfile.write(titleText)
            outfile.write(completionText)
            outfile.write("\n")
            outfile.write("\n")
        
    
    return completionText
            

   
def main():
    #layout vairables
    #vairable to change summzry data title length, if want to change later since it gets used for some math
    reviewTitleLength = 46
    # Define the layout of the window
    layout = [
        # Menu bar at the top
        [sg.Menu([['File', ['Exit']]], tearoff=False)],
        [
            # Search bar, search key dropdown, and buttons on the left side
            sg.Column([
                [sg.Text('Search: '), sg.InputText(key='search_bar', focus=True), sg.Combo(metaKeyList, default_value=metaKeyList[0], key='search_key', enable_events=True, readonly=True)],
                [sg.Text('Meta Data Search Results:')],
                [sg.Listbox(values=[], size=(30, 19), key='list_box_search_results', enable_events=True), sg.Multiline(size=(40, 20), disabled=True, key='search_results')],
                [sg.Button('Prev', key='Prev'), sg.Button('Next', key='Next'), sg.Text('Page Num: ', key='meta_page_num'), sg.VerticalSeparator(), sg.Button('Clear'), sg.Button('Search'), sg.VerticalSeparator(), sg.Text('Results: 0', key='meta_search_num')]
            ]),
            #spacer col in middle
             sg.Column([
                [sg.Text('', size=(10,28))]
             ]),
             
            #LLM model selection, company reviews, LLM summarry, and right side buttons
            sg.Column([
                #few blank lines for visual spacing
                [sg.Text('', size=(31,1)), sg.Text('LLM Model to Use:'), 
                sg.Combo(modelList, default_value=modelList[0], key='model_choice', enable_events=True, readonly=True)],
                [sg.Text('Review Data:', key='review_data_title', size=(reviewTitleLength,1)), sg.Text('Review Summary:', key='summary_title', size=(reviewTitleLength,1))],
                [sg.Multiline(size=(50, 20), disabled=True, key='review_results'), sg.Multiline(size=(40, 20), disabled=True, key='data_summary')],
                [sg.Button('Prev', key='prev_review'), sg.Button('Next', key='next_review'), 
                    sg.Text('', size=(5,1)),
                    sg.Button('Get Reviews', key='get_reviews'), 
                    sg.Text('', size=(28,1)),
                    sg.Button('Summarize', key='Summarize')],
                [sg.Text('Total Reviews: 0', key='total_review_num'), sg.VerticalSeparator(), 
                    sg.Text('Results: 0', key='review_results_num'), sg.VerticalSeparator(),
                    sg.Text('Text Char Count: 0', key='review_char_num')]
            ])
        ]
    ]

    # Create the window with the defined layout
    window = sg.Window('Review Summarizer', layout)
    #save search and key for pagination purposes since we are doing a new search every page lol
    search = ''
    key = ''
    pageNum = 0
    totalReviewNum = 0
    #save the last counter when searching for reviews to try and speed up the search a bit
    reviewCount = 0
    #bool to track if there is another review to be looked at for apgination purposes
    nextReviewExists = False
    #list of review counts since number of results is vairable depending on text length
    lastReviewCount = []

    # Event loop to handle events and user inputs
    while True:
        event, values = window.read()
        
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        
        #left most list box with search results. Can click on each result to get more detail
        elif event == 'list_box_search_results':
            #do nothing if no results
            if values['list_box_search_results']:
                selected_item = values['list_box_search_results'][0]  # Get the first item selected.
                window['search_results'].update(selected_item)
                
                #reformat data for display purposes
                resultText = ""
                for i in selected_item:
                    resultText = resultText + str(i) + ': ' + str(selected_item[i]) + '\n\n'
                #display results to correct window
                if resultText:
                    window['search_results'].update(resultText)
                else:
                    window['search_results'].update("No results found")
                            
            
            

            
        elif event == 'search_key':
            pass
        
        elif event == 'Clear':
            # Clear and reset vairable and UI fields 
            pageNum = 0
            totalReviewNum = 0
            nextReviewExists = False
            window['meta_page_num'].update('Page Num: ')        # reset the search page number
            window['total_review_num'].update('Total Reviews: 0')        # reset the review page number
            window['meta_search_num'].update('Results: 0')   #reset displayed search results to zero
            window['review_data_title'].update('Review Data:')        # reset the reviews title
            window['summary_title'].update('Review Summary:')        # reset the summary title
            window['search_bar'].update('')       # Reset the search bar to default text
            window['list_box_search_results'].update('')   #clear out listbox serch results
            window['search_results'].update('')        # Clear the meta data field
            window['data_summary'].update('')        # Clear the data summary field
            window['review_results'].update('')        # Clear the review data field
            window['review_results_num'].update('Results: 0')   #reset displayed review results to zero
            window['search_bar'].set_focus()      # Set focus back to the search bar
            window['review_char_num'].update("Text Char Count: 0")
            
   
        #define function for Search button, searching meta data
        elif event == 'Search':
            
            #clear some text when starting a new search
            pageNum = 0
            totalReviewNum = 0
            window['meta_page_num'].update('Page Num: ')        # reset the search page number
            window['total_review_num'].update('Total Reviews: 0')        # reset the review page number
            window['list_box_search_results'].update('')   #clear out listbox serch results
            window['search_results'].update('')        # Clear the meta data field
            window['meta_search_num'].update('Results: 0')   #reset displayed search results to zero
            # window['data_summary'].update('')        # Clear the review data field
            # window['review_results_num'].update('Results: 0')   #reset displayed review results to zero
            
            
            #call search function to find meta data based on user search parameters
            pathToData = metaDataFilePath
            search = values['search_bar']
            key = values['search_key']
            #call the search function for meta data, requires path to file, search term, and key to search.
            #returns a list of json objects
            results = findMetaData(pathToData, search, key)
            print('file:', pathToData, '\nsearchTerm:', search, '\nsearchKey:', key, '\nNumResults:', len(results))
            
            #update meta results list box with data
            window['list_box_search_results'].update(results)
            #update search results number
            searchNumText = "Results: " + str(len(results))
            window['meta_search_num'].update(searchNumText)
            
            
        elif event == 'Prev':
            #dont go backwards if first page
            if pageNum > 0:
                pageNum = pageNum - 1
                #clear some text when paginating
                window['list_box_search_results'].update('')   #clear out listbox serch results
                window['search_results'].update('')        # Clear the meta data field
                window['meta_search_num'].update('Results: 0')   #reset displayed search results to zero
                # window['data_summary'].update('')        # Clear the review data field
                # window['review_results_num'].update('Results: 0')   #reset displayed review results to zero
                
                
                #call search function to find meta data based on user search parameters
                pathToData = metaDataFilePath
                #get search and key from menu if none yet
                if not search:
                    search = values['search_bar']
                if not key:
                    key = values['search_key']
                #call the search function for meta data, requires path to file, search term, and key to search.
                #returns a list of json objects
                results = findMetaData(pathToData, search, key, pageNum)
                print('file:', pathToData, '\nsearchTerm:', search, '\nsearchKey:', key, '\nPageNum: ', pageNum, '\nNumResults:', len(results))
                
                #update meta results list box with data
                window['list_box_search_results'].update(results)
                #update search results number
                searchNumText = "Results: " + str(len(results))
                window['meta_search_num'].update(searchNumText)
                #update page number
                searchPageNumText = "Page Num: " + str(pageNum+1)
                window['meta_page_num'].update(searchPageNumText)
                
        elif event == 'Next':
            #only function when there are results to display/paginate through
            currentResultNum = int(window['meta_search_num'].get().split()[-1])
            if currentResultNum >= resultLimit:
                pageNum = pageNum + 1
                #clear some text when paginating
                window['list_box_search_results'].update('')   #clear out listbox serch results
                window['search_results'].update('')        # Clear the meta data field
                window['meta_search_num'].update('Results: 0')   #reset displayed search results to zero
                # window['data_summary'].update('')        # Clear the review data field
                # window['review_results_num'].update('Results: 0')   #reset displayed review results to zero
                
                
                #call search function to find meta data based on user search parameters
                pathToData = metaDataFilePath
                #get search and key from menu if none yet
                if not search:
                    search = values['search_bar']
                if not key:
                    key = values['search_key']
                #call the search function for meta data, requires path to file, search term, and key to search.
                #returns a list of json objects
                results = findMetaData(pathToData, search, key, pageNum)
                print('file:', pathToData, '\nsearchTerm:', search, '\nsearchKey:', key, '\nPageNum: ', pageNum, '\nNumResults:', len(results))
                
                #update meta results list box with data
                window['list_box_search_results'].update(results)
                #update search results number
                searchNumText = "Results: " + str(len(results))
                window['meta_search_num'].update(searchNumText)
                #update page number
                searchPageNumText = "Page Num: " + str(pageNum+1)
                window['meta_page_num'].update(searchPageNumText)
            
        
        
        #get all the reviews for a specific gmap_id that have text
        elif event == 'get_reviews':   
            #reset total reviews shown number
            totalReviewNum = 0
            window['total_review_num'].update('Total Reviews: 0')        # reset the total review number
            
            #define needed vars
            pathToData = reviewDataFilePath
            #get companyID from current selected meta data result
            companyID = ''
            #handle error, if wont work jsut do nothing
            try:
                companyID = values['list_box_search_results'][0]
                if companyID:
                    companyID = companyID['gmap_id']
            except:
                companyID = ''
            
            #make sure there is something in there at least
            if companyID:
                #validate gmap_id to make sure it fits format
                #strip chars other than numbers, letters, and ':'
                companyID = re.sub(r'[^a-zA-Z0-9:]', '', companyID)
                companyID = re.sub(r'^.*?0x', '0x', companyID)
                # #remove everything in front of '0x' if there
                # companyID
                #all gmap_ids start with "0x[16 chars]:[the rest]"
                #so must be minimum of 19 chars long
                if len(companyID) < 19:
                    window['review_results'].update("Error: Invalid gmap_id, too short")
                else:
                    if companyID[:2] != "0x" or companyID[18] != ':':
                        window['review_results'].update("Error: Invalid gmap_id")
                        
                    else:
                        #get review data for a specfic gmap_id
                        #returns a list of json objects and the last count
                        results, reviewCount, charCount, nextReviewExists = getReviewData(pathToData, companyID)
                        # print(pathToData, companyID, len(results), '  reviewCount: ', reviewCount, '  charCount: ', charCount, 'nextReviewExists: ', nextReviewExists)
                        
                        
                        #reformat data for display purposes
                        resultText = ""
                        for i in results:
                            resultText = resultText + str(i) + '\n\n'
                        #display results to correct window
                        window['review_results'].update(resultText)
                        
                        #update the total number of results Shown
                        totalReviewNum = len(results)
                        totalReviewNumText = "Total Reviews: " + str(totalReviewNum)
                        window['total_review_num'].update(totalReviewNumText)  
                        
                        #update search results number
                        searchNumText = "Results: " + str(len(results))
                        window['review_results_num'].update(searchNumText)
                        
                        #update search results number
                        charNumText = "Text Char Count: " + str(charCount)
                        window['review_char_num'].update(charNumText)
                        
                        
                        #change window title
                        #if error just display standard title text, but flipped so I know there was an error
                        try:
                            companyName = values['list_box_search_results'][0]['name']
                            titleText = "Reviews for " + companyName + ':\n'
                            #truncate if length of title exceeds reviewTitleLength
                            if len(titleText) >= reviewTitleLength:
                                titleText = titleText[:reviewTitleLength-3] + '...'
                            window['review_data_title'].update(titleText)
                        except:
                            window['review_data_title'].update("Review Summary & Data")
                            
                        
                
            else:
                window['review_results'].update("Error: No gmap_id")

            
        
        elif event == 'Summarize':
            # This is where the function to summarize the reviews would be called
            reviews = values['review_results']
            #if no reviews do nothing
            if reviews and reviews != "Error: No gmap_id":
                reviews = reviews.split('\n\n')
                
                #get just the text in each review to pass to AI for summary
                #count number of reviews with text
                count = 0
                reviewCharCount = 0
                #just get the review's text data to send to gpt.
                reviewText = ""
                textReviews = []
                for i in reviews:
                    #get just the text from the review json object
                    text = ast.literal_eval(i)['text']
                    
                    #remove characters that cant be encoded with ascii
                    # text = ascii(text)
                    
                    #check if the next review will exceed the limit(also add 6 for chacters being manually added)
                    if (reviewCharCount + len(text) + 6) > reviewCharLimit:
                        break
                    reviewText = reviewText + "{" + text + "}, " + '\n\n'
                    reviewCharCount = len(reviewText)
                    
                    count = count + 1
                
                
                #change title to reflect this is now the summary of the reviews review_results_num
                titleText = window['review_data_title'].get()
                titleText = titleText.replace('Reviews', 'Summary')
                
                #get which model the user chose to send the review data to
                modelChoice = values['model_choice']
                summaryResults = askLLM(reviewText, titleText, modelChoice)
                
                
                #change title now
                window['summary_title'].update(titleText)
                
                window['data_summary'].update(summaryResults)
                
                
                
        elif event == 'prev_review':
            #dont go backwards if first set of reviews
            currentResultNum = int(window['review_results_num'].get().split()[-1])
            if (totalReviewNum - currentResultNum) > 0:
                #update total review num
                totalReviewNum = totalReviewNum - currentResultNum
               
                
                #define needed vars
                pathToData = reviewDataFilePath
                companyID = values['review_results']
                #find first gmap_id, all ids will be the same since reviews come from the same company
                idIndex = companyID.find("gmap_id': '0")
                #if gmap_id is found then continue
                if idIndex != -1:
                    companyID = companyID[idIndex-1:companyID.find('}',idIndex)]
                    if companyID:
                        companyID = companyID[:-1]
                        
                        
                    
                    #make sure there is something in there at least
                    if companyID:
                        #validate gmap_id to make sure it fits format
                        #strip chars other than numbers, letters, and ':'
                        companyID = re.sub(r'[^a-zA-Z0-9:]', '', companyID)
                        companyID = re.sub(r'^.*?0x', '0x', companyID)
                        #all gmap_ids start with "0x[16 chars]:[the rest]"
                        #so must be minimum of 19 chars long
                        if len(companyID) < 19:
                            window['review_results'].update("Error: Invalid gmap_id, too short")
                        else:
                            if companyID[:2] != "0x" or companyID[18] != ':':
                                window['review_results'].update("Error: Invalid gmap_id")
                                
                            else:
                            
                                #update some text when paginating
                                window['review_results'].update('')   #clear out review results in prep to get new reults
                                totalReviewNumText = 'Total Reviews: ' + str(totalReviewNum)
                                window['total_review_num'].update(totalReviewNumText)   #reset displayed page number
                                window['review_results_num'].update('Results: 0')   #reset displayed number of results, since number shown depends on the char count in the reviews shown
                    
                                #get review data for a specfic gmap_id
                                #returns a list of json objects and the last count
                                temp = lastReviewCount.pop()
                                reviewsToSkip = totalReviewNum-temp
                                #set to 0 if go negative
                                if reviewsToSkip < 0:
                                    reviewsToSkip = 0
                                    
                                results, reviewCount, charCount, nextReviewExists = getReviewData(pathToData, companyID, reviewsToSkip)
                                
                                
                                
                                #reformat data for display purposes
                                resultText = ""
                                for i in results:
                                    resultText = resultText + str(i) + '\n\n'
                                #display results to correct window
                                window['review_results'].update(resultText)
                                
                                #update the total number of results Shown
                                totalReviewNumText = "Total Reviews: " + str(totalReviewNum)
                                window['total_review_num'].update(totalReviewNumText)  
                                
                                #update search results number
                                searchNumText = "Results: " + str(len(results))
                                window['review_results_num'].update(searchNumText)
                                
                                #update search results number
                                charNumText = "Text Char Count: " + str(charCount)
                                window['review_char_num'].update(charNumText)
                                
                                
                                #change window title
                                #if error just display standard title text, but flipped so I know there was an error
                                try:
                                    companyName = values['list_box_search_results'][0]['name']
                                    titleText = "Reviews for " + companyName + ':'
                                    #truncate if length of title exceeds reviewTitleLength
                                    if len(titleText) >= reviewTitleLength:
                                        titleText = titleText[:reviewTitleLength-3] + '...'
                                    window['review_data_title'].update(titleText)
                                except:
                                    window['review_data_title'].update("Review Summary & Data")
                                    
                                                            
                    else:
                        window['review_results'].update("Error: No gmap_id")
                    
                
                
        elif event == 'next_review':
            #if there is another review to look at
            currentResultNum = int(window['review_results_num'].get().split()[-1])
            if nextReviewExists:
                #define needed vars
                pathToData = reviewDataFilePath
                companyID = values['review_results']
                #find first gmap_id, all ids will be the same since reviews come from the same company
                idIndex = companyID.find("gmap_id': '0")
                #if gmap_id is found then continue
                if idIndex != -1:
                    companyID = companyID[idIndex-1:companyID.find('}',idIndex)]
                    if companyID:
                        companyID = companyID[:-1]
                        
                        
                    
                    #make sure there is something in there at least
                    if companyID:
                        #validate gmap_id to make sure it fits format
                        #strip chars other than numbers, letters, and ':'
                        companyID = re.sub(r'[^a-zA-Z0-9:]', '', companyID)
                        companyID = re.sub(r'^.*?0x', '0x', companyID)
                        #all gmap_ids start with "0x[16 chars]:[the rest]"
                        #so must be minimum of 19 chars long
                        if len(companyID) < 19:
                            window['review_results'].update("Error: Invalid gmap_id, too short")
                        else:
                            if companyID[:2] != "0x" or companyID[18] != ':':
                                window['review_results'].update("Error: Invalid gmap_id")
                                
                            else:
                            
                                #update some text when paginating
                                window['review_results'].update('')   #clear out review results in prep to get new reults
                                totalReviewNumText = 'Total Reviews: ' + str(totalReviewNum)
                                window['total_review_num'].update(totalReviewNumText)   #reset displayed page number
                                window['review_results_num'].update('Results: 0')   #reset displayed number of results, since number shown depends on the char count in the reviews shown
                                
                                #save the last result count to know how far pack to paginate
                                lastReviewCount.append(currentResultNum)
                    
                                #get review data for a specfic gmap_id
                                #returns a list of json objects and the last count
                                reviewsToSkip = totalReviewNum
                                results, reviewCount, charCount, nextReviewExists = getReviewData(pathToData, companyID, reviewsToSkip)
                                
                                
                                
                                #reformat data for display purposes
                                resultText = ""
                                for i in results:
                                    resultText = resultText + str(i) + '\n\n'
                                #display results to correct window
                                window['review_results'].update(resultText)
                                
                                #update the total number of results Shown
                                totalReviewNum = totalReviewNum + len(results)
                                totalReviewNumText = "Total Reviews: " + str(totalReviewNum)
                                window['total_review_num'].update(totalReviewNumText)  
                                
                                #update search results number
                                searchNumText = "Results: " + str(len(results))
                                window['review_results_num'].update(searchNumText)
                                
                                #update search results number
                                charNumText = "Text Char Count: " + str(charCount)
                                window['review_char_num'].update(charNumText)
                                
                                
                                #change window title
                                #if error just display standard title text, but flipped so I know there was an error
                                try:
                                    companyName = values['list_box_search_results'][0]['name']
                                    titleText = "Reviews for " + companyName + ':'
                                    #truncate if length of title exceeds reviewTitleLength
                                    if len(titleText) >= reviewTitleLength:
                                        titleText = titleText[:reviewTitleLength-3] + '...'
                                    window['review_data_title'].update(titleText)
                                except:
                                    window['review_data_title'].update("Review Summary & Data")
                                    
                                    
                                    
                        
                    else:
                        window['review_results'].update("Error: No gmap_id")
            

    # Close the window
    window.close()

    

if __name__ == '__main__':
    
    main()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
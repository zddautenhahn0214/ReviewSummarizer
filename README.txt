Imported:
gzip
json
PySimpleGUI
openai
os
re



I'm not going to upload the data since I got it from somewhere else
The data I used and based the structure on came from here:
https://datarepo.eng.ucsd.edu/mcauley_group/gdrive/googlelocal
UCTopic: Unsupervised Contrastive Learning for Phrase Representations and Topic Mining
Jiacheng Li, Jingbo Shang, Julian McAuley
Annual Meeting of the Association for Computational Linguistics (ACL), 2022

Personalized Showcases: Generating Multi-Modal Explanations for Recommendations
An Yan, Zhankui He, Jiacheng Li, Tianyang Zhang, Julian Mcauley
The 46th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR), 2023



Review data json keys are:
gmap_id - ID of the business
user_id - ID of the reviewer
name - name of the reviewer
time - time of the review (unix time)
rating - rating of the business
text - text of the review
pics - pictures of the review
resp - business response to the review including unix time and text of the response


Review meta data json keys are:
name - name of the business
address - address of the business
gmap_id - ID of the business
description - description of the business
latitude - latitude of the business
longitude - longitude of the business
category - category of the business
avg_rating - average rating of the business
num_of_reviews - number of reviews
price - price of the business
hours - open hours
MISC - MISC information
state - the current status of the business (e.g., permanently closed)
relative_results - relative businesses recommended by Google
url - URL of the business



Files:
main has all the code
in main you'll need to put the filepath to your data. I used a .gz file so you'll need to use that or modify the code. Not providing the data directy, but link is above
ReadME is this


gui guide:
https://github.com/PySimpleGUI/PySimpleGUI?tab=readme-ov-file


I'll post these so people can see my thought process if they want. These are just for me, so if they don't make sense to you don't worry about it.
Idea and personal notes:
have gpt read through the reviews written by people.
Have it summarize the key points found in the review, the most common, and maybe the notable outliers
Then it might be interesting to have it guess the average rating of the place given the text reviews.
Compare the guessed result with the actual to test for accuracy of the model.

might be a good idea to do smartGPT architecture here. So get the summary of the reviews from the model, then provide the model that summary and the reviews and ask if the summary is accurate, what it should include or not include, etc.


Synthetic data works for training models, what if you use the reviews to generate similar reviews to represent the overall sentiments of a set of say 10 reviews, to reduce the character inputs at a time, then you take those generated reviews and put all of them through the same process until you have one review that encapsulates all the others? You'd lose a lot of data, but that is good we just want to keep the highlights and general statements.
Or maybe each set of 10 reviews gets 3 bullet points to add to a list, then another agent reads and summarizes those bullet points?

The end goal is to get a technology that would allow citizens to give feedback to their local government while allowing the limited staff of that government to actually digest and use all of that data without excessive manpower. It would also be for the best if the feedback data and synthesized results were always public and easy to find(ideally on the government website) that way citizens could see what the most common issues are, have been, and how well the current local government is addressing those issues. More information is better.
If we applied this program to synthasizing citizen complaints/feedback, or really just feedback in general no need to limit it to just government, then it would be good to do multiple passes/varitents probably. One to get a general feel for things and the most common issues, one to get the outliers and extremes, and one to target overlooked minority but still improtant issues/feedback.

Might be the case that we will need to further define for the AI what we classify as 'important' when it reads through the feedback data. Probably would need to even be updated over time too therotically.



right now the pagination is super simple 'cause it works i guess' janky set up. Every time you paginate it will re search through the whole files but it knows to skip the firs x results it finds. It would be better to find all the results first, then smoothly paginate through those results. Or even better actually make and interface a real database for the searches rather than just looping through a simple python list. But this works with the files size I'm using so for now it's good enough.

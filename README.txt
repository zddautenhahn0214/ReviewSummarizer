Imported:
gzip
json
PySimpleGUI
openai
os
re



I'm not gonig to upload the data since I got it from somewhere else
The data I used and based the structure on came from here:
https://datarepo.eng.ucsd.edu/mcauley_group/gdrive/googlelocal
UCTopic: Unsupervised Contrastive Learning for Phrase Representations and Topic Mining
Jiacheng Li, Jingbo Shang, Julian McAuley
Annual Meeting of the Association for Computational Linguistics (ACL), 2022

Personalized Showcases: Generating Multi-Modal Explanations for Recommendations
An Yan, Zhankui He, Jiacheng Li, Tianyang Zhang, Julian Mcauley
The 46th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR), 2023



Review data json keys are:
user_id - ID of the reviewer
name - name of the reviwer
time - time of the review (unix time)
rating - rating of the business
text - text of the review
pics - pictures of the review
resp - business response to the review including unix time and text of the response
gmap_id - ID of the business


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



Idea and notes:
have gpt read through the reviews written by people.
Have it summarize the key points found in the review, the most common, and maybe the notable outliers
Then it might be interesting to have it guess the average rating of the place given thetext reviews.
Compare the guessed result with the actual to test for accuracy of the model.

might be a good idea to do smartGPT archetecture here. So get the summary of the reviews from the model, then provide the model that summary and the reviews and ask if the aummary is accurate, what it should include or not include, etc.


Synthetic data works for training models, what if you use the reviews to generate similar reviews to represent the overal sentiments of a set of say 10 reviews, to reduce the character inuputs at a time, then you take those generated reviews and put all of them through the same process untill you have on review that encapsolates all the others? You'd lose a lot of data, but that is good we just want to keep the highlights and general statements.
Or maybe each set of 10 reviews gets 3 bullet points to add to a list, then another agent reads and summarizes those bullet points?


If we applied this to synthasizing citizen complaints/feedback, or really just feedback in general no need to limit it to government, then it would be good to do multiple passes/varitents probably. One to get a general feel for things and the most common issues, one to get the outliers and extremes, and one to target overlooked minority but still improtant issues.

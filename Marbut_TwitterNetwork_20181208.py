# -*- coding: utf-8 -*-
"""
Created on Sat Nov 17 19:37:12 2018

@author: Administrator
"""

import TwitterFunctions as tf
from collections import defaultdict
import random
import pickle
import re

consumer_key=""
consumer_secret=""
access_token=""
access_token_secret=""

#%%
#create connection to twitter api
auth_api = tf.twitter_connect(consumer_key, consumer_secret, access_token, access_token_secret)

#get Hadley's account id
hadley = tf.get_user_object("@hadleywickham", auth_api)
hadleyid = hadley[0]
#%% find all of Hadley's followers
level1 = tf.get_follower_ids(hadleyid, auth_api) #returns 74,820 followers

#filter out followers who follow >100 or <25 accounts
followers = []
#split into batches of 100 for Twitter API
requests = [level1[i:i+100] for i in range(0, len(level1), 100)]
for request in requests:
    users = tf.get_users(request, auth_api)
    for user in users:
        if user[3] <= 100 and user[3] >=25:
            followers.append(user[0]) # returns 13,416 followers

#randomly select 5000 followers to explore network
rand_followers = random.sample(followers, 5000)

#%% for each of Hadley's followers, find all accounts they follow
# and tally up how many of Hadley's followers also follow each of these accounts
level2 = defaultdict(int)
for follower in rand_followers:
    try:
        for friend in tf.get_friend_ids(follower, auth_api):
            level2[friend] += 1
    except:
        print("Error. Skipping", follower)

with open("hadley_level2.pkl", "wb") as file:
    pickle.dump(level2, file)

#%%
#for all level2 followers with more than 5 common followers
accounts = [account for account in level2 if level2[account]>=5]

#separate into batches of 100 for twitter API
account_batches = [accounts[i:i+100] for i in range(0, len(accounts), 100)]

#collect account info for level2 accounts, calculate jaccard similarity
account_info = defaultdict(list)
for batch in account_batches:
    users = tf.get_users(batch, auth_api)
    for user in users:
        twitterid = user[0]
        common_followers = level2[twitterid]
        #4607 is the number of followers able to be scraped
        similarity_score = common_followers/(4607+user[2]-common_followers)
        info = [user[1:],[common_followers, similarity_score]]
        account_info[twitterid] = info

#%%
#save account_info dict as tsv for visualizations in R
with open("hadley_similar.txt", "w", encoding = "utf-8") as file:
    headers = ["twitterid", "handle", "followers", "friends", "desc", "website",
               "common_followers", "similarity_score"]
    file.write("\t".join(headers)+"\n")
    for account in account_info:
        desc = account_info[account][0][3]
        desc = re.sub("\r|\n|\t|CR|LF", "", desc)
        desc = re.sub(" +", " ", desc)
        row = [str(account),
               str(account_info[account][0][0]),
               str(account_info[account][0][1]),
               str(account_info[account][0][2]),
               str(desc),
               str(account_info[account][0][4]),
               str(account_info[account][1][0]),
               str(account_info[account][1][1])]
        file.write("\t".join(row)+"\n")
        
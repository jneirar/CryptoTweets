import tweepy
import os
import json

CONSUMER_KEY = os.environ.get('CONSUMER_KEY')
CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET')

# Auth twitter
def twitter_auth(callback_url):
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, callback_url)
    return auth

# Auth user from twitter
def twitter_auth_user(oauth_token, oauth_verifier):
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth_dict = { "oauth_token": oauth_token, "oauth_token_secret": oauth_verifier }
    auth.request_token = auth_dict
    auth.get_access_token(oauth_verifier)
    api = tweepy.API(auth)
    print("ACCESS TOKEN: ",auth.access_token)
    print("ACCESS SECRET: ", auth.access_token_secret)
    
    return api.verify_credentials(), auth.access_token, auth.access_token_secret

# Set access with token and secret
def twitter_set_access_token(access_token, access_token_secret):
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    return api

# Get user by id_user
def twitter_get_user_by_id(id_user, access_token, access_token_secret):
    api = twitter_set_access_token(access_token, access_token_secret)
    try:
        user = api.get_user(user_id=id_user)
        return user
    except Exception as ex:
        print(ex)
        return None

# Get user_id from username
def twitter_get_user_id_from_username(username, access_token, access_token_secret):
    api = twitter_set_access_token(access_token, access_token_secret)
    try:
        user = api.get_user(screen_name=username)
        return user
    except Exception as ex:
        print(ex)
        return None

# Get tweets from text
def twitter_get_tweets_from_text(text, access_token, access_token_secret):
    api = twitter_set_access_token(access_token, access_token_secret)
    tweets = api.search_tweets(q=text, count=100)
    tweets_list = []
    for tweet in tweets:
        tweets_list.append(tweet._json)
    return tweets_list

# Post tweet
def twitter_post_tweet(text, access_token, access_token_secret):
    api = twitter_set_access_token(access_token, access_token_secret)
    try:
        api.update_status(text)
        return True
    except Exception as ex:
        print(ex)
        return False


    
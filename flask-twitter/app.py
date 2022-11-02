from flask import Flask, request
from flask_cors import CORS, cross_origin
import tweepy
import json
import os
import psycopg2

# Twitter API credentials
CONSUMER_KEY = os.environ.get('CONSUMER_KEY')
CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET')

# PostgreSQL credentials
POSTGRES_HOST = 'localhost'
POSTGRES_PORT = '5433'
POSTGRES_USER = 'postgres'
POSTGRES_PASSWORD = 'postgres'
POSTGRES_DB = 'cryptotweets'

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/auth_twitter', methods = ["POST"])
@cross_origin()
def authorize_twitter():

    body = request.get_json()
    print(request.json)
    callback_url = body.get("callback_url")
    print(callback_url)
    
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, callback_url)

    try:
        redirect_url = auth.get_authorization_url()
        return json.dumps({"message":"success", "redirect_url": redirect_url })
    except tweepy.TweepError as ex:
        print(ex)
        return json.dumps({"message":"Failed to get request token", "redirect_url": None})


@app.route('/twitter_auth_callback', methods=["GET"])
@cross_origin()
def twitter_callback():
    try:
        oauth_token = request.args.get('oauth_token')
        oauth_verifier = request.args.get('oauth_verifier')

        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)

        auth_dict = { "oauth_token": oauth_token, "oauth_token_secret": oauth_verifier }
        print(auth_dict)
        auth.request_token = auth_dict
        auth.get_access_token(oauth_verifier)
        api = tweepy.API(auth)
        print(api)
        print("ACCESS TOKEN: ",auth.access_token)
        print("ACCESS SECRET: ", auth.access_token_secret)

        user = api.verify_credentials()
        username = user.screen_name
        user_id = user.id
        return json.dumps({"message":"success", "user_id": user_id, "username": username, "access_token": auth.access_token, "access_token_secret": auth.access_token_secret})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to get tokens"}), 500

# Endpoint to post a tweet, get acces_token and access_token_secret from header
@app.route('/post_tweet', methods=['POST'])
@cross_origin()
def post_tweet():
    print("POST TWEET")
    body = request.get_json()
    
    tweet = body.get("tweet")
    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")
    print("Access Token: ", access_token)
    print("Access Token Secret: ", access_token_secret)
    print("Tweet: ", tweet)

    try:
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
        api.update_status(tweet)
        return json.dumps({"message":"success"})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to post tweet"}), 500

# Endpoint to check if the user_id is in the postgresql database
@app.route('/check_user', methods=['POST'])
@cross_origin()
def check_user():
    body = request.get_json()
    user_id = body.get("user_id")
    print("User ID: ", user_id)
    try:
        # Check if user_id is in the database
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()
        print(user)
        cur.close()
        if user is None:
            return json.dumps({"message":"success", "user_exists": False})
        else:
            return json.dumps({"message":"success", "user_exists": True})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to check user"}), 500


# Endpoint to get the id user from the username
@app.route('/get_user_id', methods=['GET'])
@cross_origin()
def get_user_id():
    print("GET USER ID")
    body = request.get_json()
    username = body.get("username")
    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")
    print("Access Token: ", access_token)
    print("Access Token Secret: ", access_token_secret)
    print("Username: ", username)

    try:
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
        user = api.get_user(screen_name=username)
        return json.dumps({"message":"success", "user_id": user.id})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to get user id"}), 500

# Endpoint to get tweets that include a text
@app.route('/get_tweets', methods=['GET'])
@cross_origin()
def get_tweets():
    print("GET TWEETS")
    body = request.get_json()
    text = body.get("text")
    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")
    print("Access Token: ", access_token)
    print("Access Token Secret: ", access_token_secret)
    print("Text: ", text)

    try:
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
        tweets = api.search_tweets(q=text, count=100)
        tweets_list = []
        for tweet in tweets:
            tweets_list.append(tweet.text)
        return json.dumps({"message":"success", "tweets": tweets_list})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to get tweets"}), 500

if __name__ == '__main__':
    app.secret_key = "AUTH_KWESI_SECRET"
    
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        port=POSTGRES_PORT
    )
    app.run()
    print("Server closed")
    conn.close()
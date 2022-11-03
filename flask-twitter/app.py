from flask import Flask, request
from flask_cors import CORS, cross_origin
import tweepy
import json
import os
import psycopg2
from datetime import datetime

from twitter_functions import *
from encrypt_functions import *
from public_keys_github import *

# PostgreSQL credentials
POSTGRES_HOST = 'localhost'
POSTGRES_HOST = '172.25.64.1' #76.42
POSTGRES_PORT = '5432'
POSTGRES_USER = 'postgres'
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
POSTGRES_DB = 'cryptotweets'

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Auth twitter
@app.route('/auth_twitter', methods = ["POST"])
@cross_origin()
def authorize_twitter():
    print("AUTH TWITTER")
    body = request.get_json()
    callback_url = body.get("callback_url")
    
    auth = twitter_auth(callback_url)
    
    try:
        redirect_url = auth.get_authorization_url()
        return json.dumps({"message":"success", "redirect_url": redirect_url })
    except tweepy.TweepError as ex:
        print(ex)
        return json.dumps({"message":"Failed to get request token", "redirect_url": None})

# Auth callback
@app.route('/twitter_auth_callback', methods=["GET"])
@cross_origin()
def twitter_callback():
    try:
        oauth_token = request.args.get('oauth_token')
        oauth_verifier = request.args.get('oauth_verifier')

        user, access_token, access_token_secret = twitter_auth_user(oauth_token, oauth_verifier)
        
        username = user.screen_name
        user_id = user.id
        return json.dumps({"message":"success", "user_id": user_id, "username": username, "access_token": access_token, "access_token_secret": access_token_secret})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to get tokens"}), 500

# Endpoint to check if the user_id is in the postgresql database
@app.route('/check_user', methods=['GET'])
@cross_origin()
def check_user():
    body = request.get_json()
    user_id = body.get("user_id_twitter")
    try:
        # Check if user_id is in the database
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id_twitter = %s", (user_id,))
        user = cur.fetchone()
        print(user)
        cur.close()
        if user is None:
            return json.dumps({"message":"success", "user_exists": False})
        else:
            return json.dumps({"message":"success", "user_exists": True, "user_id": user[0], "user_id_twitter": user[1], "user_public_key": user[2]})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to check user"}), 500

# Endpoint to get users from my databes
@app.route('/get_users', methods=['GET'])
@cross_origin()
def get_users():
    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        cur.close()
        # Get twitter users from users
        
        twitter_users = []
        for user in users:
            twitter_user = twitter_get_user_by_id(user[1], access_token, access_token_secret)
            if(twitter_user is not None):
                twitter_users.append({"user_id": user[0], "user_id_twitter": user[1], "username": twitter_user.screen_name, "public_key": user[2]})
        return json.dumps({"message":"success", "users_number": len(twitter_users), "users": twitter_users})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to get users"}), 500

# Endpoint to get the id user from the username
@app.route('/get_user_id_from_username', methods=['GET'])
@cross_origin()
def get_user_id():
    body = request.get_json()
    username = body.get("username")
    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")
    
    user = twitter_get_user_id_from_username(username, access_token, access_token_secret)    
    if user is not None:
        return json.dumps({"message":"success", "user_id": user.id})
    else:
        return json.dumps({"message":"Failed to get user id from username"}), 500

# Endpoint to get tweets that include a text
@app.route('/get_tweets_from_text', methods=['GET'])
@cross_origin()
def get_tweets_from_text():
    body = request.get_json()
    text = body.get("text")
    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")
    tweets = twitter_get_tweets_from_text(text, access_token, access_token_secret)
    if tweets is not None:
        return json.dumps({"message":"success", "tweets_number": len(tweets), "tweets": tweets})
    else:
        return json.dumps({"message":"Failed to get tweets from text"}), 500

# Endpoint to post a tweet, get acces_token and access_token_secret from header
@app.route('/post_tweet', methods=['POST'])
@cross_origin()
def post_tweet():
    body = request.get_json()
    
    tweet = body.get("tweet")
    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")

    if twitter_post_tweet(tweet, access_token, access_token_secret):
        return json.dumps({"message":"success"})
    else:
        return json.dumps({"message":"Failed to post tweet"}), 500

# Endpoint to create a pair of keys for new user
@app.route('/create_keys', methods=['POST'])
@cross_origin()
def create_keys():
    body = request.get_json()
    user_id_twitter = body.get("user_id")
    user_username = body.get("user_username")
    try:
        # Generate keys
        private_key, public_key = generate_keys()
        # private key is a number, public key is a point
        private_key_string = private_key_to_string(private_key)
        public_key_string = public_key_to_string(public_key)

        # Save keys in the database
        cur = conn.cursor()
        cur.execute("INSERT INTO users (user_id_twitter, user_public_key) VALUES (%s, %s)", (user_id_twitter, public_key_string))
        conn.commit()
        cur.close()

        # save public key in the repository
        add_public_key(user_id_twitter, user_username, public_key_string)
        return json.dumps({"message":"success", "private_key": private_key_string, "public_key": public_key_string})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to create keys"}), 500

# Endpoint to post a tweet with public keys
@app.route('/post_tweet_with_keys', methods=['POST'])
@cross_origin()
def post_tweet_with_keys():
    body = request.get_json()
    tweet_to_post = {}
    tweet_to_post["tweet"] = body.get("tweet")
    tweet_to_post["public_key_sender"] = body.get("public_key_sender")
    tweet_to_post["public_key_receiver"] = body.get("public_key_receiver")
    tweet_to_post["user_id_sender"] = body.get("user_id_sender")
    tweet_to_post["user_id_receiver"] = body.get("user_id_receiver")

    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")
    try:
        # Post tweet with public keys
        confirmed, id = twitter_post_tweet_with_public_keys(tweet_to_post, access_token, access_token_secret)
        if confirmed:
            # Save tweet in the database
            cur = conn.cursor()
            cur.execute("INSERT INTO tweets (tweet_id_twitter, tweet_user_id_sender, tweet_user_id_receiver, tweet_nounce, tweet_mac, tweet_readed, tweet_timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s)", (id, tweet_to_post["user_id_sender"], tweet_to_post["user_id_receiver"], "nounce", "MAC", False, datetime.now()))
            conn.commit()
            cur.close()
            return json.dumps({"message":"success"})
        else:
            return json.dumps({"message":"Twitter post not confirmed"}), 500
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to post tweet with keys"}), 500

# Endpoint to search tweet by tweet_id
@app.route('/get_tweet_by_id', methods=['GET'])
@cross_origin()
def get_tweet_by_id():
    body = request.get_json()
    tweet_id = body.get("tweet_id")
    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")
    try:
        tweet = twitter_get_tweet_by_id(tweet_id, access_token, access_token_secret)
        if tweet is not None:
            print(tweet.full_text)
            return json.dumps({"message":"success", "tweet": tweet._json})
        else:
            return json.dumps({"message":"Failed to get tweet by id"}), 500
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to get tweet by id"}), 500

# Endpoint to get not readed tweets from database
@app.route('/get_not_readed_tweets', methods=['GET'])
@cross_origin()
def get_not_readed_tweets():
    body = request.get_json()
    user_id = body.get("user_id")
    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")
    try:
        # Get all not readed tweets from database
        cur = conn.cursor()
        cur.execute("SELECT * FROM tweets WHERE tweet_readed = FALSE AND tweet_user_id_receiver = %s", (user_id,))
        rows = cur.fetchall()
        cur.close()
        tweets = []
        # For each row obtained, get tweet from twitter and update database
        for row in rows:
            tweet_id_twitter = row[1]
            
            # Get tweet from twitter
            tweet = twitter_get_tweet_by_id(tweet_id_twitter, access_token, access_token_secret)
            tweets.append(tweet._json)
        return json.dumps({"message":"success", "tweets_number": len(tweets), "tweets": tweets})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to update not readed tweets"}), 500

# Endpoint to update not readed tweet from database
@app.route('/update_not_readed_tweets', methods=['POST'])
@cross_origin()
def update_not_readed_tweets():
    body = request.get_json()
    tweet_id = body.get("tweet_id")
    try:
        # Update not readed tweet from database
        cur = conn.cursor()
        cur.execute("UPDATE tweets SET tweet_readed = TRUE WHERE tweet_id_twitter = %s", (tweet_id,))
        conn.commit()
        cur.close()
        return json.dumps({"message":"success"})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to update not readed tweets"}), 500

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
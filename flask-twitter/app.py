from flask import Flask, request
from flask_cors import CORS, cross_origin
import tweepy
import json
import os
import psycopg2

from twitter_functions import *
from encrypt_functions import *
from public_keys_github import *

# PostgreSQL credentials
POSTGRES_HOST = 'localhost'
POSTGRES_HOST = '172.23.208.1'
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
            return json.dumps({"message":"success", "user_exists": True})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to check user"}), 500

# Endpoint to get users from my databes
@app.route('/get_users', methods=['GET'])
@cross_origin()
def get_users():
    print("GET USERS")
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
                twitter_users.append({"user_id": user[1], "username": twitter_user.screen_name, "public_key": user[2]})
        return json.dumps({"message":"success", "users": twitter_users})
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
    user_id = body.get("user_id")
    try:
        # Generate keys
        private_key, public_key = generate_keys()
        private_key_string = private_key_to_string(private_key)
        public_key_string = public_key_to_string(public_key)
        # private key is a number, public key is a point

        # Save keys in the database
        cur = conn.cursor()
        cur.execute("INSERT INTO users (user_id_twitter, user_public_key) VALUES (%s, %s)", (user_id, public_key_string))
        conn.commit()
        cur.close()
        return json.dumps({"message":"success", "private_key": private_key_string, "public_key": public_key_string})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to create keys"}), 500

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
from flask import Flask, request
from flask_cors import CORS, cross_origin
import tweepy
import json
import os
import psycopg2
from datetime import datetime

from twitter_functions import *
from public_keys_github import *

# PostgreSQL credentials
POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT')
POSTGRES_USER = os.environ.get('POSTGRES_USER')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
POSTGRES_DB = os.environ.get('POSTGRES_DB')

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


# Auth twitter
@app.route('/auth_twitter', methods=["POST"])
@cross_origin()
def authorize_twitter():
    print("AUTH TWITTER")
    body = request.get_json()
    callback_url = body.get("callback_url")

    auth = twitter_auth(callback_url)

    try:
        redirect_url = auth.get_authorization_url()
        return json.dumps({"message": "success", "redirect_url": redirect_url})
    except tweepy.TweepError as ex:
        print(ex)
        return json.dumps({"message": "Failed to get request token", "redirect_url": None})


# Auth twitter callback
@app.route('/twitter_auth_callback', methods=["GET"])
@cross_origin()
def twitter_callback():
    try:
        oauth_token = request.args.get('oauth_token')
        oauth_verifier = request.args.get('oauth_verifier')

        user, access_token, access_token_secret = twitter_auth_user(oauth_token, oauth_verifier)

        username = user.screen_name
        user_id = user.id_str
        return json.dumps({"message": "success", "user_id": user_id, "username": username, "access_token": access_token, "access_token_secret": access_token_secret})
    except Exception as ex:
        print(ex)
        return json.dumps({"message": "Failed to get tokens"}), 500


# Check if the user_id_twitter is already in the database
# Input: user_id_twitter
# Output: user_exists, user_id, user_id_twitter
def check_user():
    print(request)
    user_id_twitter = str(request.args.get("user_id_twitter"))
    try:
        # Check if user_id is in the database
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id_twitter = %s", (user_id_twitter,))
        user = cur.fetchone()
        print(user)
        cur.close()
        if user is None:
            return json.dumps({"message":"success", "user_exists": False})
        else:
            return json.dumps({"message":"success", "user_exists": True, "user_id": user[0], "user_id_twitter": user[1]})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to check user"}), 500


# Get users from database that exist in twitter
# Input: header (tokens)
# Output: users_number, users: list of users
# user: user_id, user_id_twitter, username, public_key
@app.route('/get_users', methods=['GET'])
@cross_origin()
def get_users():
    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")
    this_user_id = tweet_id = request.args.get("user_id")
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        cur.close()
        # Get twitter users from users
        twitter_users = []
        for user in users:
            twitter_user = twitter_get_user_by_id(user[1], access_token, access_token_secret)
            if (twitter_user is not None and user[1] != this_user_id):  #change from is not None
                twitter_users.append({"user_id": user[0], "user_id_twitter": user[1], "username": twitter_user.screen_name, #changed from "username": twitter_user.screen_name
                     "public_key": user[2]})
        return json.dumps({"message": "success", "users_number": len(twitter_users), "users": twitter_users})
    except Exception as ex:
        print(ex)
        return json.dumps({"message": "Failed to get users"}), 500


# Get the id user from the username in twitter
# Input: header (tokens), username
# Output: user_id_twitter
@app.route('/get_user_id_from_username', methods=['GET'])
@cross_origin()
def get_user_id():
    body = request.get_json()
    username = body.get("username")
    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")

    user = twitter_get_user_id_from_username(username, access_token, access_token_secret)
    if user is not None:
        return json.dumps({"message": "success", "user_id": user.id})
    else:
        return json.dumps({"message": "Failed to get user id from username"}), 500


# Get tweets that include a text
# Input: header (tokens), text
# Output: tweets_number, tweets: list of tweets
# tweet: tweet_id, user_id, user_id_twitter, username, text, date
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


# Create new user
# Input: user_id_twitter, user_username, user_public_key, user_private_key_hashed
# Output: 
@app.route('/create_user', methods=['POST'])
@cross_origin()
def create_keys():
    body = request.get_json()
    print(body)
    user_id_twitter = body.get('user_id_twitter')
    user_username = body.get('user_username')
    user_public_key = body.get("user_public_key")
    user_private_key_hashed = body.get("user_private_key_hashed")
    print("IDTWITTER:  ",user_id_twitter)
    try:
        # Save keys in the database
        cur = conn.cursor()
        cur.execute("INSERT INTO users (user_id_twitter, user_public_key, user_private_key_crypted) VALUES (%s, %s, %s)", (user_id_twitter, user_public_key, user_private_key_hashed))
        conn.commit()
        cur.close()

        # save public key in the repository
        #add_public_key(user_id_twitter, user_username, user_public_key)
        return json.dumps({"message":"success"})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to create keys"}), 500


# Post a crypted tweet
# Input: header (tokens), tweet_crypted, user_id_sender, user_id_receiver, tweet_nounce_ tweet_mac, private_key_hashed
# Output:
@app.route('/post_crypted_tweet', methods=['POST'])
@cross_origin()
def post_tweet_with_keys():
    body = request.get_json()
    print(body)
    tweet_to_post = {}
    tweet_to_post["tweet_crypted"] = body.get("tweet_crypted")
    tweet_to_post["user_id_sender"] = int(body.get("user_id_sender"))
    tweet_to_post["user_id_receiver"] =     int(body.get("user_id_receiver"))
    tweet_to_post["tweet_nounce"] = body.get("tweet_nounce")
    tweet_to_post["tweet_mac"] = body.get("tweet_mac")
    tweet_to_post["cypherdata"] = body.get("cipherdata")

    print(tweet_to_post)

    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")
    try:
        # Post tweet with public keys
        confirmed, id = twitter_post_crypted_tweet(tweet_to_post, access_token, access_token_secret)
        print(confirmed)
        print(id)
        if confirmed:
            # Save tweet in the database
            cur = conn.cursor()
            cur.execute("INSERT INTO tweets (tweet_id_twitter, tweet_user_id_sender, tweet_user_id_receiver, tweet_nounce, tweet_mac, tweet_readed, tweet_timestamp, cypherdata) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (str(id), tweet_to_post["user_id_sender"], tweet_to_post["user_id_receiver"], tweet_to_post["tweet_nounce"], tweet_to_post["tweet_mac"], False, datetime.now(), tweet_to_post["cypherdata"]))
            conn.commit()
            cur.close()
            return json.dumps({"message":"success"})
        else:
            return json.dumps({"message":"Twitter post not confirmed"}), 500
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to post crypted tweet"}), 500


# Search tweet by tweet_id
# Input: header (tokens), tweet_id
# Output: tweet
@app.route('/get_tweet_by_id', methods=['GET'])
@cross_origin()
def get_tweet_by_id():
    tweet_id = request.args.get("tweet_id")
    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")
    print("TWEET ID")
    print(tweet_id)

    try:
        tweet = twitter_get_tweet_by_id(tweet_id, access_token, access_token_secret)
        if tweet is not None:
            print(tweet.full_text)
            return json.dumps({"message": "success", "tweet": tweet._json})
        else:
            return json.dumps({"message": "Tweet not founded"}), 500
    except Exception as ex:
        print(ex)
        return json.dumps({"message": "Failed to get tweet by id"}), 500


# Get not readed tweets from database
# Input: header (tokens), user_id
# Output: tweets_number, tweets: list of tweets
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
            if tweet is None:
                continue
            tweets.append(tweet._json)
        return json.dumps({"message":"success", "tweets_number": len(tweets), "tweets": tweets})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to get not readed tweets"}), 500


# Update not readed tweet from database
# Input: tweet_id_twitter
# Output:
@app.route('/update_not_readed_tweet', methods=['POST'])
@cross_origin()
def update_not_readed_tweets():
    body = request.get_json()
    tweet_id_twitter = body.get("tweet_id_twitter")
    try:
        # Update not readed tweet from database
        print("Rows: ", tweet_id_twitter)
        cur = conn.cursor()
        cur.execute("SELECT * FROM tweets WHERE tweet_id_twitter = %s", (tweet_id_twitter,))
        rows = cur.fetchall()
        for row in rows:
            print(row)

        print("Start update")
        cur.execute("UPDATE tweets SET tweet_readed = TRUE WHERE tweet_id_twitter = %s", (tweet_id_twitter,))
        conn.commit()
        cur.close()
        return json.dumps({"message":"success"})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to update not readed tweets"}), 500


@app.route('/get_tweet_db_by_id', methods=['GET'])
@cross_origin()
def get_tweet_db_by_id():
    twitterID = request.args.get("tweet_id")
    print(twitterID)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tweets WHERE tweet_id_twitter = %s", (twitterID,))
        rows = cur.fetchall()
        tweet = rows[0]
        conn.commit()
        cur.close()
        return json.dumps({"message": "success", "tweet": tweet[:7]})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to load tweet"}), 500


# Get public key from a user_id
# Input: user_id
# Output: public_key
@app.route('/get_public_key', methods=['GET'])
@cross_origin()
def get_public_key():
    print(request)
    user_id = str(request.args.get("user_id"))
    print("User id: ", user_id)
    try:
        # Get public key from database
        cur = conn.cursor()
        command = "SELECT * FROM users WHERE user_id_twitter = '" + user_id + "'"
        cur.execute(command)
        rows = cur.fetchall()
        cur.close()
        if len(rows) == 0:
            return json.dumps({"message":"User not found"}), 500
        public_key = rows[0][2]
        print("PUBLIC KEY: ", public_key)
        return json.dumps({"message":"success", "public_key": public_key})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to get public key"}), 500


# Get private key hashed from a user_id
# Input: user_id
# Output: private_key_hashed
@app.route('/get_private_key_hashed', methods=['GET'])
@cross_origin()
def get_private_key_hashed():
    body = request.get_json()
    user_id = body.get("user_id")
    try:
        # Get private key hashed from database
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        rows = cur.fetchall()
        cur.close()
        if len(rows) == 0:
            return json.dumps({"message":"User not found"}), 500
        private_key_hashed = rows[0][3]
        return json.dumps({"message":"success", "private_key_hashed": private_key_hashed})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to get private key hashed"}), 500

# Get tweets with id sender or id receiver from a user_id
# Input: header (tokens), user_id
# Output: tweets_number, tweets: list of tweets
@app.route('/get_tweets_from_user_id', methods=['GET'])
@cross_origin()
def get_tweets_from_user_id():
    body = request.get_json()
    user_id = body.get("user_id")
    access_token = request.headers.get("access_token")
    access_token_secret = request.headers.get("access_token_secret")
    try:
        # Get all tweets from database
        cur = conn.cursor()
        cur.execute("SELECT * FROM tweets WHERE tweet_user_id_sender = %s OR tweet_user_id_receiver = %s", (user_id, user_id))
        rows = cur.fetchall()
        cur.close()
        tweets = []
        # For each row obtained, get tweet from twitter
        for row in rows:
            tweet_id_twitter = row[1]
            # Get tweet from twitter
            tweet = twitter_get_tweet_by_id(tweet_id_twitter, access_token, access_token_secret)
            if tweet is None:
                continue
            tweets.append({"tweet_database": row, "tweet_twitter": tweet._json})
        return json.dumps({"message":"success", "tweets_number": len(tweets), "tweets": tweets})
    except Exception as ex:
        print(ex)
        return json.dumps({"message":"Failed to get tweets from user id"}), 500


if __name__ == '__main__':
    app.secret_key = "AUTH_KWESI_SECRET"
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        port=POSTGRES_PORT
    )
    # if CryptoTweets_public repository does not exist, clone it and pull
    if not os.path.exists("CryptoTweets_public"):
        os.system("git clone https://github.com/jneirar/CryptoTweets_public.git")
    os.chdir("CryptoTweets_public")
    os.system("git pull")
    os.chdir("..")
    app.run()
    print("Server closed")
    conn.close()

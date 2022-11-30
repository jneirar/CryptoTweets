import os

# Function to add a public key to the file in CryptoTweets_public
def add_public_key(id_twitter, username_twitter, public_key):
    os.chdir("CryptoTweets_public")
    # git pull comand
    os.system("git pull")
    try:
        with open("public_keys.txt", "a") as file:
            file.write(id_twitter + "," + username_twitter + "," + public_key + "\n")
        # git add commit and push
        os.system("git add .")
        os.system("git commit -m \"Added public key for " + username_twitter + "\"")
        os.system("git push")
        os.chdir("..")
        return True
    except Exception as ex:
        print(ex)
        os.chdir("..")
        return False

# Function to modify a public key of the file in CryptoTweets_public
def modify_public_key(id_twitter, public_key):
    os.chdir("CryptoTweets_public")
    # git pull comand
    os.system("git pull")
    try:
        with open("public_keys.txt", "r") as file:
            lines = file.readlines()
        with open("public_keys.txt", "w") as file:
            for line in lines:
                if line.split(",")[0] == id_twitter:
                    file.write(id_twitter + "," + public_key + "\n")
                else:
                    file.write(line)
        # git add commit and push
        os.system("git add .")
        os.system("git commit -m \"Modified public key for " + id_twitter + "\"")
        os.system("git push")
        os.chdir("..")
        return True
    except Exception as ex:
        print(ex)
        os.chdir("..")
        return False

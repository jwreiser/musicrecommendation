from flask import Flask, request, redirect
from spotipy.oauth2 import SpotifyOAuth

import spotipy,traceback
import generateRecommendations

app = Flask(__name__)
scope = "user-read-playback-state,user-modify-playback-state,user-library-modify,user-follow-modify,user-library-read"


# Routes
@app.route("/")
def index():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! ROOT')
    auth = SpotifyOAuth(cache_path=".spotifycache", scope=scope)
    token_info = auth.get_cached_token()
    if not token_info:
        # If there isn't a cached token then you will be redirected to a page where you will be asked to login to spotify
        # After that procceed to /callback
        auth_url = auth.get_authorize_url()
        return redirect(auth_url)

    token = token_info['access_token']

    # At this point you can now create a Spotifiy instance with
    # spotipy.client.Spotify(auth=token)
    sp = spotipy.Spotify(auth=token)
    generateRecommendations.generate_recommendations(sp)
    return f"You now have an access token : {token}"

@app.route("/load/songs")
def load():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! LOAD SONGS')
    client_id='efcbfcfbfa624a9498f42a2a28475264'
    secret='4249cfd1b2e34183af5b3e2bdd073b99'
    auth = SpotifyOAuth(username="savecuomo",client_id=client_id,client_secret=secret, cache_path=".spotifycache", scope=scope)
    print(f'AUTH {auth}')
    try:
        token_info = auth.get_cached_token()
        print(f'TOKEN {token_info}')
        if not token_info:
            # If there isn't a cached token then you will be redirected to a page where you will be asked to login to spotify
            # After that procceed to /callback
            auth_url = auth.get_authorize_url()
            return redirect(auth_url)

        print('TOKEN2')
        token = token_info['access_token']
        print('TOKEN2')

        sp = spotipy.Spotify(auth=token, requests_timeout=15)
        print('SPOTIFY')
        print(f'!@@@@@@@sp {sp}')
        generateRecommendations.load_more_songs(sp, shouldUpdateDisplay=False)
        print('BAAAAAAAAAAAAAAAACK')
    except Exception as err:
        print(Exception, err)
        print(traceback.format_exc())


@app.route("/callback")
def callback():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! CALLBACK')
    url = request.url
    auth = SpotifyOAuth(cache_path=".spotifycache", scope=scope)
    code = auth.parse_response_code(url)
    token = auth.get_access_token(code)
    # Once the get_access_token function is called, a cache will be created making it possible to go through the route "/" without having to login anymore
    return redirect("/")

if __name__ == '__main__':
    app.run(port=5192, host="localhost", debug=True)
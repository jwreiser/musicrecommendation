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

@app.route("/player/previous")
def previous():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! previous')
    generateRecommendations.previous(get_spotify())

@app.route("/player/pause")
def pause():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! pause')
    generateRecommendations.pause(get_spotify())

@app.route("/player/play")
def play():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! play')
    generateRecommendations.play(get_spotify())
@app.route("/player/next")
def skip():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! next')
    generateRecommendations.skip_song(get_spotify())

@app.route("/basis/artists")
def basis_artists():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! basis artists')
    generateRecommendations.load_based_on_artists(get_spotify(), shouldUpdateDisplay=False)

@app.route("/basis/songs")
def basis_songs():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! basis songs')
    generateRecommendations.load_based_on_songs(get_spotify(), shouldUpdateDisplay=False)

@app.route("/basis/features")
def basis_features():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! basis features')
    generateRecommendations.load_audio_features(get_spotify(), shouldUpdateDisplay=False)

@app.route("/load/songs")
def load_songs():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! LOAD SONGS')
    return generateRecommendations.load_more_songs(get_spotify(), shouldUpdateDisplay=False)

@app.route("/load/artist")
def load_artist():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! LOAD artist')
    return generateRecommendations.add_artist_songs(get_spotify(), shouldUpdateDisplay=False)

@app.route("/load/album")
def load_album():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! LOAD album')
    generateRecommendations.load_album(get_spotify(), shouldUpdateDisplay=False)

@app.route("/load/playlist")
def load_playlist():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! LOAD playlist')
    generateRecommendations.load_random_similar_playlist(get_spotify(), shouldUpdateDisplay=False)
@app.route("/load/comedy")
def load_comedy():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! LOAD comedy')
    generateRecommendations.load_recent_comedy(get_spotify(), shouldUpdateDisplay=False)

@app.route("/artist/like")
def like_artist():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! LIKE ARTIST')
    generateRecommendations.like_artist(get_spotify(), shouldUpdateDisplay=False)

@app.route("/album/like")
def like_album():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! LIKE album')
    generateRecommendations.like_album(get_spotify(), shouldUpdateDisplay=False)
@app.route("/song/like")
def like_song():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! LIKE song')
    generateRecommendations.like_song(get_spotify(), shouldUpdateDisplay=False)
@app.route("/song/dislike")
def dislike_song():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! disLIKE song')
    generateRecommendations.dislike_song(get_spotify(), shouldUpdateDisplay=False)

@app.route("/artist/dislike")
def dislike_artist():
    print('INSIDE!!!!!!!!!!!!!!!!!!!!!! DISLIKE ARTIST')
    generateRecommendations.dislike_artist(get_spotify(), shouldUpdateDisplay=False)

def get_spotify():
    client_id='efcbfcfbfa624a9498f42a2a28475264'
    secret='4249cfd1b2e34183af5b3e2bdd073b99'
    auth = SpotifyOAuth(username="savecuomo",client_id=client_id,client_secret=secret, cache_path=".spotifycache", scope=scope)
    print(f'AUTH {auth}')
    sp=None
    try:
        token_info = auth.get_cached_token()
        print(f'TOKEN {token_info}')
        if not token_info:
            # If there isn't a cached token then you will be redirected to a page where you will be asked to login to spotify
            # After that procceed to /callback
            auth_url = auth.get_authorize_url()
            return redirect(auth_url)

        token = token_info['access_token']

        sp = spotipy.Spotify(auth=token, requests_timeout=15)
    except Exception as err:
        print(Exception, err)
        print(traceback.format_exc())
    return sp

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
import keyboard,requests, urllib3, spotipy
import time,random,traceback
import pandas as pd
from spotipy.oauth2 import SpotifyOAuth
import logging
import os

import track_util
# import tkinter as tk
# import tkinter.ttk as ttk
#
# window = tk.Tk()  # create parent window
# displayVar = tk.StringVar()
logging.basicConfig(level='DEBUG')

from track_util import get_next_songs,get_artists,build_songs_df,add_to_artists,get_songs_similar_to_artist,get_random_tracks_from_playlist,get_songs_by_audio_attributes,get_audio_attributes_from_playlist
#resources https://github.com/spotipy-dev/spotipy/issues/937
DATABASE_NAME='music_recommendation.db'
scope = "user-read-playback-state,user-modify-playback-state,user-library-modify,user-follow-modify,user-library-read"
playlist_id = "67t9aE3VRZZH5eIiYPVToA"

session = requests.Session()

retry = urllib3.Retry(
    total=0,
    connect=None,
    read=0,
    allowed_methods=frozenset(['GET', 'POST', 'PUT', 'DELETE']),
    status=0,
    backoff_factor=0.3,
    status_forcelist=(429, 500, 502, 503, 504),
    respect_retry_after_header=False  # <---
)

adapter = requests.adapters.HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

retry = urllib3.Retry(
    total=0,
    connect=None,
    read=0,
    allowed_methods=frozenset(['GET', 'POST', 'PUT', 'DELETE']),
    status=0,
    backoff_factor=0.3,
    status_forcelist=(429, 500, 502, 503, 504),
    respect_retry_after_header=False  # <---
)

adapter = requests.adapters.HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

#window = tk.Tk()  # create parent window
#displayVar = tk.StringVar()
recently_played=[]
playlist_df = pd.read_csv('biggest_chunk.csv')
unused_keys=['alt','up arrow','left arrow','down arrow','q','w','e','r','t','f','g','z','c','v','b','1','2','3','4','5','6','7','8','9','0','-','=',
             'y','u','i','o','p','h','j','k','l','[',']','\\',';','\'','n','m',',','/','enter']
#right arrow, s, a,d,x
def handleWindows(event,sp):
    print('in')

    try:
        not_done=True
        while not_done:
            if not keyboard.is_pressed("ctrl"):
                not_done=False
                break
            if keyboard.is_pressed("shift"):
                while True:
                    if not keyboard.is_pressed("ctrl"):
                        not_done = False
                        break
                    if keyboard.is_pressed("."):
                        print("right arrow")
                        skip_song(sp)
                        not_done=False
                        break

                    if keyboard.is_pressed("s"):
                        print("s")
                        like_song(sp)
                        not_done = False
                        break
                    if keyboard.is_pressed("a"):
                        print("a")
                        like_artist(sp)
                        not_done = False
                        break

                    if keyboard.is_pressed("d"):
                        print("d")
                        dislike_artist(sp)
                        not_done = False
                        break
                    if keyboard.is_pressed("q"):
                        print("z")
                        dislike_song(sp)
                        not_done = False
                        break
                    for key in unused_keys:
                        if keyboard.is_pressed(key):
                            print(key+' escaped')
                            not_done = False
                            break
            if keyboard.is_pressed("alt"):
                break
    except Exception as err:
        print(Exception, err)
        print(traceback.format_exc())
print('out')


def generate_recommendations(spotify=None):
    print(os.environ['CLIENT_ID'])
    print(os.environ['CLIENT_SECRET'])
    client_id='efcbfcfbfa624a9498f42a2a28475264'
    secret='4249cfd1b2e34183af5b3e2bdd073b99'

    if spotify is None:
        sp = spotipy.Spotify(client_credentials_manager=SpotifyOAuth(username='savecuomo', scope=scope,client_id=client_id,client_secret=secret),requests_timeout=60
                             ,requests_session=session
                             )
    else:
        sp=spotify

    keyboard.on_press_key("ctrl", lambda event: handleWindows(event,sp))
    play_next_song(sp, None)
    # create_gui(sp,displayVar)
    print('success')

def dislike_artist(sp):
    result = sp.currently_playing()
    add_to_artists(result,'disliked_artists')
    play_next_song(sp, result)

def load_audio_features(sp,shouldUpdateDisplay=True):
    genre,songs=get_songs_by_audio_attributes(sp,playlist_id)
    sp.start_playback(uris=songs)
    if shouldUpdateDisplay:
        updateDisplay(sp,genre)

    # get_audio_attributes_from_playlist(sp,playlist_id)
def add_artist_songs(sp):
    result = sp.currently_playing()
    track = result['item']
    tracks = sp.artist_top_tracks(track['artists'][0]['id'])
    track_util.play_tracks(sp,track,tracks['tracks'])
    updateDisplay(sp)
def like_artist(sp):
    result = sp.currently_playing()
    if result is not None:
        add_to_artists(result, 'artists')
        track = result['item']
        id=track['artists'][0]['id']
        sp.user_follow_artists(ids=[id])
        songs=get_songs_similar_to_artist(sp, id, True)
        sp.start_playback(uris=songs)
        updateDisplay(sp)
    else:
        play_next_song(playlist_df,result)

def like_album(sp):
    result = sp.currently_playing()
    track = result['item']
    sp.current_user_saved_albums_add(albums=[track['album']['id']])

def load_album(sp):
    result = sp.currently_playing()
    if result is not None:
        track = result['item']
        tracks=sp.album_tracks(track['album']['id'])['items']
        track_uris = [track['uri'] for track in tracks]
        songs_df = build_songs_df(result=None, temporary=False)
        tracks_list = []
        for current_track in track_uris:
            if current_track not in list(songs_df['song']) and current_track != track['uri']:
                tracks_list.append(current_track)
        sp.start_playback(uris=tracks_list)
        updateDisplay(sp)
def skip_song(sp):
    play_next_song(sp, result=None,temporary=True)

def dislike_song(sp):
    result = sp.currently_playing()
    build_songs_df(result,temporary=False)
    play_next_song(sp, result)

def load_more_songs(sp, shouldUpdateDisplay=True):
    print('CALLING::::::::::::::::::: get_next_songs')
    songs = get_next_songs(sp,playlist_df, result=None, temporary=False)
    if len(songs) > 0:
        sp.start_playback(uris=songs)
    if shouldUpdateDisplay:
        updateDisplay(sp)

def load_based_on_artists(sp, shouldUpdateDisplay=True):
    artists_df = get_artists(sp,include_disliked=False)
    songs_df = build_songs_df(result=None, temporary=False)
    base_artist_name=random.choice(artists_df['artist_name'])

    tracks = get_random_tracks_from_playlist(sp, playlist_id, 5)
    artists=[]
    for _ in range(5):
        random_track=random.choice(tracks)
        artists.append(random_track['track']['artists'][0]['id'])

    base_artist=sp.search(q=base_artist_name, limit=1, type='artist')['artists']['items'][0]
    songs=get_songs_similar_to_artist(sp, base_artist['id'], False,5)
    recommendations = sp.recommendations(seed_artists=artists, limit=5)
    for track in recommendations['tracks']:
        if track['uri'] not in list(songs_df['song']):
            if track['artists'][0]['name'] not in list(artists_df['artist_name']):
                songs.append(track['uri'])
    sp.start_playback(uris=songs)
    if shouldUpdateDisplay:
        updateDisplay(sp)

def load_based_on_songs(sp):
    songs_df=build_songs_df(result=None,temporary=False)
    artists_df=get_artists(sp,include_disliked=True)
    tracks = get_random_tracks_from_playlist(sp,playlist_id,5)
    track_uris = [track['track']['uri'] for track in tracks]
    songs = []
    recommendations=sp.recommendations(seed_tracks=track_uris, limit=20)
    for track in recommendations['tracks']:
        if track['uri'] not in list(songs_df['song']):
            if track['artists'][0]['name'] not in list(artists_df['artist_name']):

                songs.append(track['uri'])
    sp.start_playback(uris=songs)
    updateDisplay(sp)

def load_recent_comedy(sp,shouldUpdateDisplay=True):
    tracks=sp.search(q="genre:comedy AND year:2020-2024", limit=50, type='track')['tracks']['items']

    songs_df = build_songs_df(result=None, temporary=False)
    songs = []
    artists_df = get_artists(sp,include_disliked=True, include_liked=False)

    for track in tracks:
        if track['uri'] not in list(songs_df['song']):
            if track['artists'][0]['name'] not in list(artists_df['artist_name']):
                songs.append(track['uri'])

    if len(songs) > 0:
        sp.start_playback(uris=songs)

    if shouldUpdateDisplay:
        updateDisplay(sp)
def load_random_similar_playlist(sp,shouldUpdateDisplay=True):
    artists_df = get_artists(sp,include_disliked=False)
    query=random.choice(artists_df['artist_name'])
    for _ in range(3):#too big = no results
        query+=(" "+random.choice(artists_df['artist_name']))

    playlists=sp.search(q=query, limit=20, type='playlist')['playlists']['items']
    while len(playlists)<0:
        playlists = sp.search(q=query, limit=20, type='playlist')['playlists']['items']

    playlist = random.choice(playlists)
    songs_df = build_songs_df(result=None, temporary=False)
    songs = []
    artists_df = get_artists(sp,include_disliked=True, include_liked=False)
    playlist_items=sp.playlist_items(playlist['id'])['items']
    for item in playlist_items:
        track=item['track']
        if track['uri'] not in list(songs_df['song']):
            if track['artists'][0]['name'] not in list(artists_df['artist_name']):
                songs.append(track['uri'])

    if len(songs) > 0:
        sp.start_playback(uris=songs)

    if shouldUpdateDisplay:
        updateDisplay(sp)

def pause(sp):
    sp.pause_playback()

def previous(sp):
    sp.previous_track()
def play(sp):
    sp.start_playback()

def refresh_track_information(sp):
    updateDisplay(sp)

def like_song(sp):
    result = sp.currently_playing()
    if result is not None:
        songs_df=build_songs_df(result=None,temporary=False)  #stop saving these here as wastes space
        artists_df=get_artists(sp,include_disliked=True)
        track = result['item']
        sp.current_user_saved_tracks_add(tracks=[track['uri']])
        songs = []
        try:
            recommendations=sp.recommendations(seed_tracks=[track['uri']], limit=10)
            for track in recommendations['tracks']:
                if track['uri'] not in list(songs_df['song']):
                    if track['artists'][0]['name'] not in list(artists_df['artist_name']):
                        songs.append(track['uri'])
            sp.start_playback(uris=songs)
            updateDisplay(sp)

        except Exception as err:
            print(Exception, err)
            print(traceback.format_exc())


def play_next_song(sp,result,temporary=False):
    queue = sp.queue()
    play_from_queue=False
    artists_df = get_artists(sp,include_disliked=True)
    songs_preferences_df = build_songs_df(result=None, temporary=False)
    songs=[]
    if len(queue['queue']) > 0:
        current_uri = queue['currently_playing']['uri']
        next_uri = queue['queue'][0]['uri']
        if current_uri != next_uri:
            for track in queue['queue']:
                if (track['artists'][0]['name'] not in list(artists_df['artist_name']) and track['uri'] not in list(songs_preferences_df['song'])
                        and track['uri'] not in songs):
                    if not sp.current_user_saved_albums_contains(albums=[track['album']['uri']])[0] and  not sp.current_user_saved_tracks_contains(tracks=[track['uri']])[0]:
                        songs.append(track['uri'])
                        play_from_queue=True

    if not play_from_queue:
        songs = get_next_songs(sp,playlist_df,result,temporary)
    if len(songs) > 0:
        sp.start_playback(uris=songs)
    updateDisplay(sp)



def updateDisplay(sp,genre=None):
    time.sleep(3)
    result = sp.currently_playing()

    if result is not None:
        track = result['item']
        display=track['artists'][0]['name'] + " - " + track['album']['name'] + '-' + track['name']
        if genre is not None:
            display+=": "+genre
        # displayVar.set(display)

# window = tk.Tk()  # create parent window

# def create_gui(sp,displayVar):
#     displayLab = ttk.Label(window, textvariable=displayVar)
#
#     displayLab.grid(row=0, column=0, columnspan=4)
#     refresh_button = ttk.Button(window, text="REFRESH TRACK INFORMATION", command=lambda: refresh_track_information(sp))
#     refresh_button.grid(row=1, column=0, columnspan=4)
#
#     rownum = 2
#     like_artist_button = ttk.Button(window, text="LIKE ARTIST", command=lambda: like_artist(sp))
#     dislike_artist_button = ttk.Button(window, text="DISLIKE ARTIST", command=lambda: dislike_artist(sp))
#     like_song_button = ttk.Button(window, text="LIKE SONG", command=lambda: like_song(sp))
#     dislike_song_button = ttk.Button(window, text="DISLIKE SONG", command=lambda: dislike_song(sp))
#     like_artist_button.grid(row=rownum, column=0, padx=5, pady=5)
#     dislike_artist_button.grid(row=rownum, column=1, padx=5, pady=5)
#     like_song_button.grid(row=rownum, column=2, padx=5, pady=5)
#     dislike_song_button.grid(row=rownum, column=3, padx=5, pady=5)
#     rownum+=1
#
#     like_album_button = ttk.Button(window, text="LIKE ALBUM", command=lambda: like_album(sp))
#     like_album_button.grid(row=rownum, column=0, padx=5, pady=5)
#     load_album_button = ttk.Button(window, text="LOAD ALBUM", command=lambda: load_album(sp))
#     load_album_button.grid(row=rownum, column=1, padx=5, pady=5, columnspan=1)
#     add_artist_songs_button = ttk.Button(window, text="LOAD ARTIST", command=lambda: add_artist_songs(sp))
#     add_artist_songs_button.grid(row=rownum, column=2, padx=5, pady=5)
#     load_button = ttk.Button(window, text="MORE SONGS", command=lambda: load_more_songs(sp))
#     load_button.grid(row=rownum, column=3, padx=5, pady=5, columnspan=1)
#     rownum += 1
#
#
#     load_random_artist_button = ttk.Button(window, text="BASIS: ARTISTS", command=lambda: load_based_on_artists(sp))
#     load_random_artist_button.grid(row=rownum, column=0, padx=5, pady=5)
#     load_based_songs_button = ttk.Button(window, text="BASIS: SONGS", command=lambda: load_based_on_songs(sp))
#     load_based_songs_button.grid(row=rownum, column=1, padx=5, pady=5)
#     audio_features_button = ttk.Button(window, text="BASIC: AUDIO FEATURES", command=lambda: load_audio_features(sp))
#     audio_features_button.grid(row=rownum, column=2, padx=5, pady=5)
#     load_random_playlist_button = ttk.Button(window, text="LOAD PLAYLIST",command=lambda: load_random_similar_playlist(sp))
#     load_random_playlist_button.grid(row=rownum, column=3, padx=5, pady=5)
#     rownum += 1
#
#     load_recent_comedy_button = ttk.Button(window, text="RECENT COMEDY", command=lambda: load_recent_comedy(sp))
#     load_recent_comedy_button.grid(row=rownum, column=0, padx=5, pady=5, columnspan=4)
#     rownum += 1
#
#
#     prev_button = ttk.Button(window, text="PREV", command=lambda: previous(sp))
#     pause_button = ttk.Button(window, text="PAUSE", command=lambda: pause(sp))
#     play_button = ttk.Button(window, text="PLAY", command=lambda: play(sp))
#     skip_song_button = ttk.Button(window, text="NEXT", command=lambda: skip_song(sp))
#     prev_button.grid(row=rownum, column=0, padx=5, pady=5)
#     pause_button.grid(row=rownum, column=1, padx=5, pady=5)
#     play_button.grid(row=rownum, column=2, padx=5, pady=5)
#     skip_song_button.grid(row=rownum, column=3, padx=5, pady=5)
#     rownum += 1
#
#
#     window.mainloop()
if __name__ == '__main__':
    generate_recommendations()


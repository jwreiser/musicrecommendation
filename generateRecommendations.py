import random, requests, urllib3, spotipy,traceback
import time
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
from spotipy.oauth2 import SpotifyOAuth
import tkinter as tk
import tkinter.ttk as ttk
import logging
import os

logging.basicConfig(level='DEBUG')

from track_util import get_next_songs,get_artists,build_songs_df,add_to_artists,load_similar_to_artist
import itertools
from spotipy import util

DATABASE_NAME='music_recommendation.db'
scope = "user-read-playback-state,user-modify-playback-state,user-library-modify,user-follow-modify"
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

window = tk.Tk()  # create parent window
displayVar = tk.StringVar()
recently_played=[]
playlist_df = pd.read_csv('../spotify_million_playlist_dataset/src/1.csv')

def generate_recommendations(spotify=None):
    print(os.environ['CLIENT_ID'])
    print(os.environ['CLIENT_SECRET'])

    if spotify is None:
        sp = spotipy.Spotify(client_credentials_manager=SpotifyOAuth(username='savecuomo', scope=scope),requests_timeout=15
                             ,requests_session=session
                             )
    else:
        sp=spotify

    play_next_song(sp, None)
    create_gui(sp)
    print('success')

def dislike_artist(sp):
    result = sp.currently_playing()
    add_to_artists(result,'disliked_artists')
    play_next_song(sp, result)

def add_artist_songs(sp):
    result = sp.currently_playing()
    track = result['item']
    artist=track['artists'][0]['id']
    tracks = sp.artist_top_tracks(artist)
    tracks_list=[]
    songs_df = build_songs_df(result=None, temporary=False)
    for track in tracks['tracks']:
        if track['uri'] not in list(songs_df):
            tracks_list.append(track['uri'])
    sp.start_playback(uris=tracks_list)
    updateDisplay(sp)
def like_artist(sp):
    result = sp.currently_playing()
    if result is not None:
        add_to_artists(result, 'artists')
        track = result['item']
        id=track['artists'][0]['id']
        sp.user_follow_artists(ids=[id])
        load_similar_to_artist(sp,id,True)
        updateDisplay(sp)
    else:
        play_next_song(playlist_df,result)


def skip_song(sp):
    play_next_song(sp, result=None,temporary=True)

def dislike_song(sp):
    result = sp.currently_playing()
    build_songs_df(result,temporary=False)
    play_next_song(sp, result)

def load_more_songs(sp, shouldUpdateDisplay=True):
    songs = get_next_songs(sp,playlist_df, result=None, temporary=False)
    if len(songs) > 0:
        sp.start_playback(uris=songs)
    if shouldUpdateDisplay:
        updateDisplay(sp)

def load_similar_to_random_liked_artist(sp,shouldUpdateDisplay=True):
    artists_df = get_artists(sp,include_disliked=False)
    base_artist_name=random.choice(artists_df['artist_name'])
    base_artist=sp.search(q=base_artist_name, limit=1, type='artist')['artists']['items'][0]
    load_similar_to_artist(sp, base_artist['id'], False)
    if shouldUpdateDisplay:
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

def play(sp):
    sp.start_playback()

def refresh_track_information(sp):
    updateDisplay(sp)

def like_song(sp):
    result = sp.currently_playing()
    if result is not None:
        songs_df=build_songs_df(result,temporary=False)  # also done for the side effect of adding the song to the songs list
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
            sp.next_track()
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
                if track['artists'][0]['name'] not in list(artists_df['artist_name']) and track['uri'] not in list(
                    songs_preferences_df['song']):
                    songs.append(track['uri'])
                    play_from_queue=True

    if not play_from_queue:
        songs = get_next_songs(sp,playlist_df,result,temporary)
    if len(songs) > 0:
        sp.start_playback(uris=songs)
    updateDisplay(sp)






def updateDisplay(sp):
    time.sleep(3)
    result = sp.currently_playing()

    if result is not None:
        track = result['item']

        displayVar.set(track['artists'][0]['name']+" - "+track['name'])
def create_gui(sp):
    displayLab = ttk.Label(window, textvariable=displayVar)

    displayLab.grid(row=0, column=0, columnspan=4)
    refresh_button = ttk.Button(window, text="REFRESH TRACK INFORMATION", command=lambda: refresh_track_information(sp))
    refresh_button.grid(row=1, column=0, columnspan=4)

    rownum = 2
    like_artist_button = ttk.Button(window, text="LIKE ARTIST", command=lambda: like_artist(sp))
    dislike_artist_button = ttk.Button(window, text="DISLIKE ARTIST", command=lambda: dislike_artist(sp))
    like_song_button = ttk.Button(window, text="LIKE SONG", command=lambda: like_song(sp))
    dislike_song_button = ttk.Button(window, text="DISLIKE SONG", command=lambda: dislike_song(sp))
    like_artist_button.grid(row=rownum, column=0, padx=5, pady=5)
    dislike_artist_button.grid(row=rownum, column=1, padx=5, pady=5)
    like_song_button.grid(row=rownum, column=2, padx=5, pady=5)
    dislike_song_button.grid(row=rownum, column=3, padx=5, pady=5)
    rownum+=1


    load_button = ttk.Button(window, text="LOAD MORE SONGS", command=lambda: load_more_songs(sp))
    load_recent_comedy_button = ttk.Button(window, text="LOAD RECENT COMEDY",command=lambda: load_recent_comedy(sp))
    load_button.grid(row=rownum, column=0, padx=5, pady=5,columnspan=2)
    load_recent_comedy_button.grid(row=rownum, column=2, padx=5, pady=5,columnspan=2)
    rownum += 1

    add_artist_songs_button = ttk.Button(window, text="LOAD SONGS FROM CURRENT ARTIST", command=lambda: add_artist_songs(sp))
    add_artist_songs_button.grid(row=rownum, column=0, padx=5, pady=5,columnspan=4)
    rownum += 1

    load_random_artist_button = ttk.Button(window, text="LOAD SONGS SIMILAR TO RANDOM LIKED ARTIST", command=lambda: load_similar_to_random_liked_artist(sp))
    load_random_artist_button.grid(row=rownum, column=0, padx=5, pady=5,columnspan=4)
    rownum += 1

    load_random_playlist_button = ttk.Button(window, text="LOAD RECOMMENDED PLAYLIST",command=lambda: load_random_similar_playlist(sp))
    load_random_playlist_button.grid(row=rownum, column=0, padx=5, pady=5, columnspan=4)
    rownum += 1

    pause_button = ttk.Button(window, text="PAUSE", command=lambda: pause(sp))
    play_button = ttk.Button(window, text="PLAY", command=lambda: play(sp))
    skip_song_button = ttk.Button(window, text="SKIP SONG", command=lambda: skip_song(sp))
    exit_button = ttk.Button(window, text="EXIT", command=window.quit)
    pause_button.grid(row=rownum, column=0, padx=5, pady=5)
    play_button.grid(row=rownum, column=1, padx=5, pady=5)
    skip_song_button.grid(row=rownum, column=2, padx=5, pady=5)
    exit_button.grid(row=rownum, column=3, padx=5, pady=5)

    window.mainloop()

if __name__ == '__main__':
    generate_recommendations()
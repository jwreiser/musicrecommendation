import sqlite3
import spotipy
import time
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
from spotipy.oauth2 import SpotifyOAuth
from tkinter import *
from track_util import get_next_song,get_artists
DATABASE_NAME='music_recommendation.db'
CLIENT_ID = "55162db19c664ca687cdbfe436d98817" # enter your own here
CLIENT_SECRET = "fce642d4ef6f43bdb782181e7ec7fecb" # enter your own here
scope = "user-read-playback-state,user-modify-playback-state,user-library-modify"
#sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(CLIENT_ID,CLIENT_SECRET))
sp = spotipy.Spotify(client_credentials_manager=SpotifyOAuth(CLIENT_ID,CLIENT_SECRET,redirect_uri="http://localhost:5000",scope=scope))
#sp=spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(CLIENT_ID,CLIENT_SECRET))
#sp = spotipy.Spotify(auth_manager=SpotifyOAuth(CLIENT_ID,CLIENT_SECRET,scope=scope,redirect_uri=None))
playlist_id = "67t9aE3VRZZH5eIiYPVToA"

root = Tk()  # create parent window
displayVar = StringVar()



def playback_done(track):
  print("Playback done for track:", track.name)
def analyze_playlist(playlist_id):
    print(sp.me())

    playlist_df = pd.read_csv('../spotify_million_playlist_dataset/src/1.csv')
    play_next_song(playlist_df, None)
    create_gui(playlist_df)
    sp.on(spotipy.event.PLAYBACK_DONE, playback_done)
    print('success')


def like_artist(playlist_df):
    result = sp.currently_playing()
    artists=get_artists(result)
    if result is not None:
        track = result['item']
        sp.user_follow_artists(ids=[track['artists'][0]['id']])

    play_next_song(playlist_df, result,artists)

def dislike_artist(playlist_df):
    result = sp.currently_playing()
    artists=get_artists(result)
    play_next_song(playlist_df, result,artists=artists)

def skip_song(playlist_df):
    result = sp.currently_playing()
    play_next_song(playlist_df, result,temporary=True)
def dislike_song(playlist_df):
    result = sp.currently_playing()
    play_next_song(playlist_df, result)

def skip_song(playlist_df):
    result = sp.currently_playing()
    if result is not None:
        track = result['item']
    play_next_song(playlist_df, result,temporary=True)


def like_song(playlist_df):
    result = sp.currently_playing()
    if result is not None:
        track = result['item']
        sp.current_user_saved_tracks_add(tracks=[track['uri']])

    play_next_song(playlist_df, result)


def play_next_song(playlist_df,result,temporary=False,artists=None):
    song = get_next_song(playlist_df,result,temporary,artists)
    if(song is not None):
        desired_list = [song]
        sp.start_playback(uris=desired_list)
        updateDisplay()






def updateDisplay():
    time.sleep(1)
    result = sp.currently_playing()

    if result is not None:
        track = result['item']

        displayVar.set(track['artists'][0]['name']+" - "+track['name'])
def create_gui(playlist_df):
    displayLab = Label(root, textvariable=displayVar)

    displayLab.pack()
    # use Button and Label widgets to create a simple TV remote
    dislike_artist_button = Button(root, text="DISLIKE ARTIST", command=lambda: dislike_artist(playlist_df))
    dislike_artist_button.pack()

    like_artist_button = Button(root, text="LIKE ARTIST", command=lambda: like_artist(playlist_df))
    like_artist_button.pack()

    dislike_song_button = Button(root, text="DISLIKE SONG", command=lambda: dislike_song(playlist_df))
    dislike_song_button.pack()

    skip_song_button = Button(root, text="SKIP SONG", command=lambda: skip_song(playlist_df))
    skip_song_button.pack()

    like_song_button = Button(root, text="LIKE SONG", command=lambda: like_song(playlist_df))
    like_song_button.pack()

    turn_off = Button(root, text="EXIT", command=root.quit)
    turn_off.pack()

    root.mainloop()

if __name__ == '__main__':
    analyze_playlist(playlist_id)
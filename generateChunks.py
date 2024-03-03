"""
    pretty prints the MPD

    usage:
        python print.py path-mpd/
"""
import sys
import json
import time
import os
#import spotipy
#import spotipy.util as util
import pandas as pd # for later

def process_playlists(path):
    filenames = os.listdir(path)
    playlist_features_list = ["playlist_name","pid","num_artists","artist_name", "track_uri", "artist_uri", "track_name", "album_uri", "album_name"]
    playlist_df = pd.DataFrame(columns=playlist_features_list)

    for filename in sorted(filenames):
        print(filename)
        if filename.startswith("mpd.slice.") and filename.endswith(".json"):
            fullpath = os.sep.join((path, filename))
            f = open(fullpath)
            js = f.read()
            f.close()
            mpd_slice = json.loads(js)
            for playlist in mpd_slice["playlists"]:
                #160 takes too much memory to be in the top chunk
                #175 fine too little memory
                if playlist['num_artists']>=170:
                    playlist_df=build_dataframe(playlist,playlist_df)
    print(playlist_df.head())
    playlist_df.to_csv("largeplaylists.csv")


def build_dataframe(playlist,playlist_df):
    # Create empty dataframe

    playlist_features = {}

    # Loop through every track in the playlist, extract features and append the features to the playlist df


    for track in playlist['tracks']:
        # Create empty dict
        playlist_features = {}
        #["playlist_name", "pid", "num_artists", "artist_name", "track_uri", "artist_uri", "track_name", "album_uri","album_name"]
        playlist_features["playlist_name"] = playlist["name"]
        playlist_features["pid"] = playlist["pid"]
        playlist_features["num_artists"] = playlist["num_artists"]

        playlist_features["artist_name"] = track["artist_name"]
        playlist_features["track_uri"] = track["track_uri"]
        playlist_features["artist_uri"] = track["artist_uri"]
        playlist_features["track_name"] = track["track_name"]
        playlist_features["album_uri"] = track["album_uri"]
        playlist_features["album_name"] = track["album_name"]

        # Concat the dfs
        track_df = pd.DataFrame(playlist_features, index=[0])
        playlist_df = pd.concat([playlist_df, track_df], ignore_index=True)
    return playlist_df;

def print_playlist(playlist):
    print("=====", playlist["pid"], "====")
    print("name:          ", playlist["name"])
    ts = time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime(playlist["modified_at"])
    )

    print("last_modified: ", ts)
    print("num edits: ", playlist["num_edits"])
    print("num followers: ", playlist["num_followers"])
    print("num artists: ", playlist["num_artists"])
    print("num albums: ", playlist["num_albums"])
    print("num tracks: ", playlist["num_tracks"])
    print()
    for i, track in enumerate(playlist["tracks"]):
        print(
            "   %3d %s - %s - %s"
            % (i + 1, track["track_name"], track["album_name"], track["artist_name"])
        )
    print()




process_playlists('D:/development/data/spotify_million_playlist_dataset/data')
import sqlite3
import pandas as pd
DATABASE_NAME='music_recommendation.db'

def get_artists(result=None):
    conn = sqlite3.connect(DATABASE_NAME)

    if table_exists(conn, 'artists'):
        query = conn.execute(''' SELECT artist_name FROM artists ''')
        artist_df = pd.DataFrame.from_records(query.fetchall(), columns=['artist_name'])

        if (result is not None):
            track = result['item']
          #  new_row = {'artist_name':track['artists'][0]['name'] }
            if track['artists'][0]['name'] not in list(artist_df['artist_name']):
                artist_df.loc[len(artist_df)] = track['artists'][0]['name']
                artist_df.to_sql('artists', conn, if_exists='replace', index=False)
    elif result is not None:
        track = result['item']
        artist_df = pd.DataFrame([track['uri']], columns=["artist_name"])
        artist_df.to_sql('artists', conn, if_exists='replace', index=False)
    else:
        artist_df = get_artists_from_playlist()

    conn.close()
    return artist_df;

def table_exists(conn,table_name):
    query = 'SELECT COUNT(*) FROM sqlite_master WHERE type=\'table\' AND name=?'
    cursor = conn.cursor()
    cursor.execute(query, (table_name,))
    result = cursor.fetchone()[0]
    return result == 1

def get_artists_from_playlist(sp,playlist_id):
    artists=[]
    conn = sqlite3.connect(DATABASE_NAME)

    print('getting playlist')
    # Loop through every track in the playlist, extract features and append the features to the playlist df
    playlist = sp.playlist(playlist_id)['tracks']
    print('got playlist')
    tracks = playlist['items']
    numItems = 0
    while playlist['next']:
        playlist = sp.next(playlist)
        tracks.extend(playlist['items'])
        numItems += 100
        print(f"Got {numItems}")

    for track in tracks:
        # Get metadata
        for artist in track["track"]["album"]["artists"]:
            if artist['name'] not in artists:
                artists.append(artist['name'])
        for artist in track["track"]["artists"]:
            if artist['name'] not in artists:
                artists.append(artist['name'])
    artists_df= pd.DataFrame(artists, columns=["artist_name"])
    artists_df.to_sql('artists', conn, if_exists='append', index=False)
    conn.close()
    return artists_df


def build_songs_df(result,temporary):
    conn = sqlite3.connect(DATABASE_NAME)
    if table_exists(conn, 'songs'):
        query = conn.execute(''' SELECT song FROM songs ''')
        songs_df = pd.DataFrame.from_records(query.fetchall(), columns=['song'])

        if result is not None and not temporary:
            track = result['item']
            #new_row = {'song': track['uri']}
            if track['uri'] not in list(songs_df['song']):
                songs_df.loc[len(songs_df)] = track['uri']
                songs_df.to_sql('songs', conn, if_exists='replace', index=False)
    elif result is not None and not temporary:
        track = result['item']
        songs_df = pd.DataFrame([track['uri']], columns=["song"])
        songs_df.to_sql('songs', conn, if_exists='replace', index=False)
    else:
        songs_df=pd.DataFrame()

    if table_exists(conn, 'tempsongs'):
        query = conn.execute(''' SELECT song FROM tempsongs ''')
        temp_songs_df = pd.DataFrame.from_records(query.fetchall(), columns=['song'])
        if result is not None and temporary:
            track = result['item']
            temp_songs_df.loc[len(temp_songs_df)] = track['uri']
            temp_songs_df.to_sql('tempsongs', conn, if_exists='replace', index=False)
        songs_df=pd.concat([temp_songs_df, songs_df])
    elif result is not None and temporary:
        track = result['item']
        temp_songs_df = pd.DataFrame([track['uri']], columns=["song"])
        temp_songs_df.to_sql('tempsongs', conn, if_exists='replace', index=False)
        songs_df=pd.concat([temp_songs_df, songs_df])

    conn.close()
    return songs_df;

def get_next_song(playlist_df,result,temporary=False,artists=None,current_track=None):
    tracks=filter_playlist_tracks_by_artist(playlist_df,artists)
    if artists is not None:
        songresult=None
    else:
        songresult=result
    songs_df = build_songs_df(songresult,temporary)
    song=None
    for track in tracks:
        if track not in list(songs_df['song']):
            song=track
            break

    return song

def filter_playlist_tracks_by_artist(playlist_df,artists):
    if(artists is not None):#save some time and reuse the one we've got
        artists_df =artists
    else:
        artists_df = get_artists()
    artists_playlist_df = playlist_df.merge(artists_df)
    merged_series = artists_playlist_df.value_counts('pid', sort=True)
    tracks = []
    for pid, _ in merged_series.items():
        tracks += playlist_to_tracks(playlist_df, pid, artists_df)
    return tracks
def playlist_to_tracks(playlist_df,pid,artists_df):
    current_playlist=playlist_df.loc[playlist_df['pid'] == pid]
    artists=list(artists_df['artist_name'])
    filtered_playlist = current_playlist.loc[~current_playlist['artist_name'].isin(artists)]
    return filtered_playlist['track_uri'].tolist()


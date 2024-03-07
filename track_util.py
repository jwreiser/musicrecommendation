import sqlite3,random,traceback
import pandas as pd
import  itertools
import logging
logging.basicConfig(level='DEBUG')

DATABASE_NAME='music_recommendation.db'
playlist_id = "67t9aE3VRZZH5eIiYPVToA"
MIN_MATCHING_ARTISTS=50

def get_artists(sp,include_disliked=True,include_liked=True):
    conn = sqlite3.connect(DATABASE_NAME)
    artist_df = None

    if include_liked and table_exists(conn, 'artists'):
        query = conn.execute(''' SELECT artist_name FROM artists ''')
        artist_df = pd.DataFrame.from_records(query.fetchall(), columns=['artist_name'])

    if include_disliked and table_exists(conn, 'disliked_artists'):
        query = conn.execute(''' SELECT artist_name FROM disliked_artists ''')
        disliked_artist_df = pd.DataFrame.from_records(query.fetchall(), columns=['artist_name'])
        artist_df=pd.concat([disliked_artist_df,artist_df])

    if artist_df is None:
        artist_df=get_artists_from_playlist(sp,conn,playlist_id)

    conn.close()
    return artist_df;

def add_to_artists(result,table_name):
    conn = sqlite3.connect(DATABASE_NAME)
    if result is not None and table_exists(conn, table_name):
        query = conn.execute('SELECT artist_name FROM '+table_name)
        artist_df = pd.DataFrame.from_records(query.fetchall(), columns=['artist_name'])
        track = result['item']
        if track['artists'][0]['name'] not in list(artist_df['artist_name']):
            artist_df.loc[len(artist_df)] = track['artists'][0]['name']
            artist_df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()


def table_exists(conn,table_name):
    query = 'SELECT COUNT(*) FROM sqlite_master WHERE type=\'table\' AND name=?'
    cursor = conn.cursor()
    cursor.execute(query, (table_name,))
    result = cursor.fetchone()[0]
    return result == 1

def get_artists_from_playlist(sp,conn,playlist_id):
    artists=[]

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

def get_next_songs(sp,playlist_df,result,temporary=False):
    tracks=filter_playlist_tracks_by_artist(sp,playlist_df)
    songs_preferences_df = build_songs_df(result,temporary)
    filtered_tracks=[song for song in tracks if song not in list(songs_preferences_df['song'])]
    songs=[]

    for _ in range(10):
        songs.append( random.choice(filtered_tracks))
    return songs

def filter_playlist_tracks_by_artist(sp,playlist_df):
    artists_df = get_artists(sp,include_disliked=False)
    artists_playlist_df = playlist_df.merge(artists_df)

#    merged=pd.merge(artists_playlist_df, disliked_artists_df, how='outer', indicator=True)
 #   liked_only_df=merged[merged['_merge'] == 'left_only']

    merged_series = artists_playlist_df.value_counts('pid', sort=True)

    tracks = []
    for pid, count in merged_series.items():
        if count > MIN_MATCHING_ARTISTS:
            tracks += playlist_to_tracks(sp,playlist_df, pid, artists_df)
    return tracks
def playlist_to_tracks(sp,playlist_df,pid,artists_df):
    current_playlist=playlist_df.loc[playlist_df['pid'] == pid]
    artists=list(artists_df['artist_name'])
    disliked_artists_df = get_artists(sp,include_disliked=True, include_liked=False)
    disliked_artists=list(disliked_artists_df['artist_name'])
    filtered_playlist = current_playlist.loc[~current_playlist['artist_name'].isin(artists)]
    filtered_playlist = filtered_playlist.loc[~current_playlist['artist_name'].isin(disliked_artists)]

    return filtered_playlist['track_uri'].tolist()

def load_similar_to_artist(sp,artist_id,filter_results):
    if filter_results:
        songs_df = build_songs_df(result=None, temporary=False)
        artists_df = get_artists(include_disliked=True)
    else:
        artists_df = get_artists(include_disliked=True,include_liked=False)
    recommended_artists = sp.artist_related_artists(artist_id)['artists']
    songs=[]
    for artist in recommended_artists:
        if artist['name'] not in list(artists_df):
            tracks = sp.artist_top_tracks(artist['id'])
            for track in itertools.islice(tracks['tracks'], 0, 4):
                if not filter_results or track['uri'] not in list(songs_df):
                    songs.append(track['uri'])
    try:
        recommendations = sp.recommendations(seed_artists=[artist_id], limit=10)
        for track in recommendations['tracks']:
            if not filter_results or track['uri'] not in list(songs_df):
                songs.append(track['uri'])
    except Exception as err:
        print(Exception, err)
        print(traceback.format_exc())
    sp.start_playback(uris=songs)
    sp.next_track()

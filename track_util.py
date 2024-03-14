import sqlite3,random,traceback
import matplotlib.pyplot as plt
import pandas as pd
import  itertools
import logging
import time
logging.basicConfig(level='DEBUG')

DATABASE_NAME='music_recommendation.db'
playlist_id = "67t9aE3VRZZH5eIiYPVToA"
MIN_MATCHING_ARTISTS=50

def get_artists(sp,include_disliked=True,include_liked=True):
    conn = sqlite3.connect(DATABASE_NAME)
    artist_df = None

    if include_liked and table_exists(conn, 'artists'):
        print('ARTISTS table exists')
        query = conn.execute(''' SELECT artist_name FROM artists ''')
        artist_df = pd.DataFrame.from_records(query.fetchall(), columns=['artist_name'])

    if include_disliked and table_exists(conn, 'disliked_artists'):
        print('DISLIKED ARTISTS table exists')
        query = conn.execute(''' SELECT artist_name FROM disliked_artists ''')
        disliked_artist_df = pd.DataFrame.from_records(query.fetchall(), columns=['artist_name'])
        artist_df=pd.concat([disliked_artist_df,artist_df])

    if artist_df is None:
        print('CALLING::::::::::::::::::: get_artists_from_playlist')
        artist_df=get_artists_from_playlist(sp,conn,playlist_id)
        print('CALLED::::::::::::::::::: get_artists_from_playlist')

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
    print('CALLING::::::::::::::::::: get_tracks_from_playlist')
    tracks = get_tracks_from_playlist(sp, playlist_id)
    print('CALLED::::::::::::::::::: get_tracks_from_playlist')

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

def get_tracks_from_playlist(sp,playlist_id):
    playlist = sp.playlist(playlist_id)['tracks']
    tracks = playlist['items']
    numItems = 0
    try:
        while playlist['next']:
            playlist = sp.next(playlist)
            tracks.extend(playlist['items'])
            numItems += 100
            print(f"Got {numItems}")
    except Exception as err:
        print(Exception, err)
        print(traceback.format_exc())

    return tracks

def get_songs_by_audio_attributes(sp, playlist_id):
    conn = sqlite3.connect(DATABASE_NAME)
    artists_df = get_artists(sp, include_disliked=False)
    songs_df = build_songs_df(result=None, temporary=False)

    if table_exists(conn, 'audio_attributes'):
        query = conn.execute(''' SELECT acousticness,danceability,energy,time_signature,key,mode,tempo,valence FROM audio_attributes ''')
        attributes_df = pd.DataFrame.from_records(query.fetchall(), columns=['acousticness','danceability','energy','time_signature','key','mode','tempo','valence'])
    else:
        attributes_df = get_audio_attributes_from_playlist(sp,playlist_id)
    conn.close()

    attributes_df=filter_data_frame_by_std(attributes_df,'time_signature')
    attributes_df = filter_data_frame_by_std(attributes_df, 'danceability')
    attributes_df = filter_data_frame_by_std(attributes_df, 'energy')
    attributes_df = filter_data_frame_by_std(attributes_df, 'acousticness')
    attributes=attributes_df.sample()
    genres=['acoustic','afrobeat','alternative','alt-rock','ambient','bluegrass','blues','bossanova','brazil','breakbeat',
            'british','chill','dancehall','dub','electro','electronic','funk','groove','grunge','guitar','happy','hard-rock',
            'hip-hop','idm','indian','indie','latin','latino','mpb','pagode','party','psych-rock',
            'r-n-b','reggae','rock','rock-n-roll','rockabilly','samba','singer-songwriter','ska','songwriter','soul','study',
            'summer','trance','trip-hop','work-out','world-music']
    genre=random.choice(genres)
    songs=[]
    recommendations = sp.recommendations(seed_genres=[genre],min_acousticness=attributes['acousticness']-.05,max_acousticness=attributes['acousticness']+.05
                                         ,min_danceability=attributes['danceability']-.05,max_danceability=attributes['danceability']+.05
                                         ,min_energy=attributes['energy']-.05,max_energy=attributes['energy']+.05
                                         # , target_key=attributes['key'] causes ambiguous error
                                         # , target_tempo=attributes['tempo'] causes ambiguous error
                                         # , target_valence=attributes['valence'] causes ambiguous error
                                         , target_signature=attributes['time_signature']
                                         # , target_mode=attributes['mode'] causes ambiguous error
                                         )
    for track in recommendations['tracks']:
        if track['uri'] not in list(songs_df['song']):
            if track['artists'][0]['name'] not in list(artists_df['artist_name']):
                songs.append(track['uri'])
    return [genre,songs]
def filter_data_frame_by_std(df,column_name):
    std = df[column_name].std()/2
    mean = df[column_name].mean()
    low = mean - std
    high = mean + std
    df = df.loc[df[column_name] >= low]
    return  df.loc[df[column_name] <= high]


def get_audio_attributes_from_playlist(sp,playlist_id):
    conn = sqlite3.connect(DATABASE_NAME)
    df = pd.DataFrame(columns=['acousticness','danceability','energy','key','mode','tempo','time_signature','valence'])
    count=0

    playlist = sp.playlist(playlist_id)['tracks']
    tracks = []
    for item in playlist['items']:
        tracks.append(item['track']['uri'])

    features_list = sp.audio_features(tracks=tracks)
    for features in features_list:
        df.loc[len(df.index)] = [features['acousticness'], features['danceability'], features['energy'],
                                 features['key'], features['mode'], features['tempo'], features['time_signature'], features['valence']]
    numItems = 0
    try:
        while playlist['next']:
            time.sleep(1)
            playlist = sp.next(playlist)

            tracks = []
            for item in playlist['items']:
                tracks.append(item['track']['uri'])

            numItems += 100

            features_list = sp.audio_features(tracks=tracks)
            for features in features_list:
                df.loc[len(df.index)] = [features['acousticness'], features['danceability'], features['energy'],
                                         features['key'], features['mode'], features['tempo'],
                                         features['time_signature'], features['valence']]

            print(f"Got {numItems}")
    except Exception as err:
        print(Exception, err)
        print(traceback.format_exc())

    df.to_sql('audio_attributes', conn, if_exists='replace', index=False)
    conn.close()
    return df
def get_random_tracks_from_playlist(sp, playlist_id,num_tracks):
    tracks = get_tracks_from_playlist(sp, playlist_id)
    result_tracks=[]
    for _ in range(num_tracks):
        result_tracks.append(random.choice(tracks))
    return result_tracks

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
    print('CALLING::::::::::::::::::: get_next_songs')
    tracks=filter_playlist_tracks_by_artist(sp,playlist_df)
    print('CALLING::::::::::::::::::: build_songs_df')
    songs_preferences_df = build_songs_df(result,temporary)
    print('CALLED::::::::::::::::::: build_songs_df')
    filtered_tracks=[song for song in tracks if song not in list(songs_preferences_df['song'])]
    songs=[]

    for _ in range(10):
        songs.append( random.choice(filtered_tracks))
    return songs

def filter_playlist_tracks_by_artist(sp,playlist_df):
    print('CALLING::::::::::::::::::: get_artists')
    artists_df = get_artists(sp,include_disliked=False)
    print('CALLED::::::::::::::::::: get_artists')
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

def get_songs_similar_to_artist(sp, artist_id, filter_out_liked, num_songs=10):
    if filter_out_liked:
        songs_df = build_songs_df(result=None, temporary=False)
        artists_df = get_artists(include_disliked=True)
    else:
        artists_df = get_artists(sp,include_disliked=True,include_liked=False)
    recommended_artists = sp.artist_related_artists(artist_id)['artists']
    songs=[]
    for artist in recommended_artists:
        if artist['name'] not in list(artists_df):
            tracks = sp.artist_top_tracks(artist['id'])
            for track in itertools.islice(tracks['tracks'], 0, (num_songs-1)):
                if not filter_out_liked or track['uri'] not in list(songs_df):
                    songs.append(track['uri'])
    try:
        recommendations = sp.recommendations(seed_artists=[artist_id], limit=num_songs)
        for track in recommendations['tracks']:
            if not filter_out_liked or track['uri'] not in list(songs_df):
                songs.append(track['uri'])
    except Exception as err:
        print(Exception, err)
        print(traceback.format_exc())
    return songs

def play_tracks(sp,track,tracks):
    songs_df = build_songs_df(result=None, temporary=False)
    tracks_list = []
    for current_track in tracks:
        if current_track['uri'] not in list(songs_df) and current_track['uri'] != track['uri']:
            tracks_list.append(current_track['uri'])
    sp.start_playback(uris=tracks_list)

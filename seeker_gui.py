import tkinter as tk
import tkinter.ttk as ttk

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

    like_album_button = ttk.Button(window, text="LIKE ALBUM", command=lambda: like_album(sp))
    like_album_button.grid(row=rownum, column=0, padx=5, pady=5)
    load_album_button = ttk.Button(window, text="LOAD ALBUM", command=lambda: load_album(sp))
    load_album_button.grid(row=rownum, column=1, padx=5, pady=5, columnspan=1)
    add_artist_songs_button = ttk.Button(window, text="LOAD ARTIST", command=lambda: add_artist_songs(sp))
    add_artist_songs_button.grid(row=rownum, column=2, padx=5, pady=5)
    load_button = ttk.Button(window, text="MORE SONGS", command=lambda: load_more_songs(sp))
    load_button.grid(row=rownum, column=3, padx=5, pady=5, columnspan=1)
    rownum += 1


    load_random_artist_button = ttk.Button(window, text="BASIS: ARTISTS", command=lambda: load_based_on_artists(sp))
    load_random_artist_button.grid(row=rownum, column=0, padx=5, pady=5)
    load_based_songs_button = ttk.Button(window, text="BASIS: SONGS", command=lambda: load_based_on_songs(sp))
    load_based_songs_button.grid(row=rownum, column=1, padx=5, pady=5)
    audio_features_button = ttk.Button(window, text="BASIC: AUDIO FEATURES", command=lambda: load_audio_features(sp))
    audio_features_button.grid(row=rownum, column=2, padx=5, pady=5)
    load_random_playlist_button = ttk.Button(window, text="LOAD PLAYLIST",command=lambda: load_random_similar_playlist(sp))
    load_random_playlist_button.grid(row=rownum, column=3, padx=5, pady=5)
    rownum += 1

    load_recent_comedy_button = ttk.Button(window, text="RECENT COMEDY", command=lambda: load_recent_comedy(sp))
    load_recent_comedy_button.grid(row=rownum, column=0, padx=5, pady=5, columnspan=4)
    rownum += 1


    prev_button = ttk.Button(window, text="PREV", command=lambda: previous(sp))
    pause_button = ttk.Button(window, text="PAUSE", command=lambda: pause(sp))
    play_button = ttk.Button(window, text="PLAY", command=lambda: play(sp))
    skip_song_button = ttk.Button(window, text="NEXT", command=lambda: skip_song(sp))
    prev_button.grid(row=rownum, column=0, padx=5, pady=5)
    pause_button.grid(row=rownum, column=1, padx=5, pady=5)
    play_button.grid(row=rownum, column=2, padx=5, pady=5)
    skip_song_button.grid(row=rownum, column=3, padx=5, pady=5)
    rownum += 1


    window.mainloop()
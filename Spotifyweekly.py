from dotenv import load_dotenv
import spotipy 
import time 
from spotipy.oauth2 import SpotifyOAuth
import os
from flask import Flask, request, url_for, session, redirect # usando flask por caus do OAuth do spotify


load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'ADFefefn@123qkfjn'
TOKEN_INFO = 'valor inicial'

# HOME ROUTE
@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

# REDIRECT ROUTE
@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('save_discover_weekly', _external = True))

# SAVE DISCOVER WEEKLEY
@app.route('/saveDiscoverWeekly')
def save_discover_weekly():
    try: 
        # get the token info from the session
        token_info = get_token()
    except:
        # if the token info is not found, redirect the user to the login route
        print('User not logged in')
        return redirect("/")

    # create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.current_user()['id']

    # get the user's playlists
    current_playlists =  sp.current_user_playlists()['items']
    discover_weekly_playlist_id = None
    saved_weekly_playlist_id = None

    # find the Discover Weekly and Saved Weekly playlists
    for playlist in current_playlists:
        if(playlist['name'] == 'Discover Weekly'):
            discover_weekly_playlist_id = playlist['id']
        if(playlist['name'] == 'Saved Weekly'):
            saved_weekly_playlist_id = playlist['id']
    
    # if the Discover Weekly playlist is not found, return an error message
    if not discover_weekly_playlist_id:
        return 'Discover Weekly not found.'
    if not saved_weekly_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Saved Weekly', True)
        saved_weekly_playlist_id = new_playlist['id']
    
    # get the tracks from the Discover Weekly playlist
    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)
    song_uris = []
    for song in discover_weekly_playlist['items']:
        song_uri= song['track']['uri']
        song_uris.append(song_uri)
    
    # add the tracks to the Saved Weekly playlist
    sp.user_playlist_add_tracks(user_id, saved_weekly_playlist_id, song_uris, None)

    # return a success message
    return ('Discover Weekly songs added successfully')




def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        # if the token info is not found, redirect the user to the login route
        redirect(url_for('login', _external=False))
    
    # check if the token is expired and refresh it if necessary
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info    

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = client_id, 
        client_secret = client_secret,
        redirect_uri = url_for('redirect_page', _external = True),
        scope = 'user-library-read playlist-modify-public playlist-modify-private'
        )


app.run(debug=True)
        



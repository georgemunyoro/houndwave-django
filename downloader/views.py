from django.shortcuts import render
from django.http import HttpResponse
from spotipy.oauth2 import SpotifyClientCredentials
from youtube_search import YoutubeSearch
from houndwave.settings import CLIENT_ID, CLIENT_SECRET
import mimetypes
import urllib
import eyed3
import json
import spotipy
import shutil
import youtube_search
import youtube_dl


def home(request):
    return render(request, 'downloader/home.html')


def download_file(request, id):
    print(id)

    creds = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    spotify = spotipy.Spotify(client_credentials_manager=creds)

    SAVE_DIR = './downloads/'
    filename = f'{id}.mp3'

    track = spotify.track(id)

    title = track['name']
    artist = ', '.join([artist['name'] for artist in track['artists']])
    album = track['album']['name']
    date = track['album']['release_date']
    image_url = track['album']['images'][0]['url']

    # Search YouTube and download mp3 file

    yt_res = YoutubeSearch(artist + ' ' + title, max_results=1).to_json()
    yt_res = json.loads(yt_res)
    yt_id  = yt_res['videos'][0]['id']

    ydl_opts = {
        'outtmpl': SAVE_DIR + u'%(id)s.%(ext)s',
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    print(yt_res)

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        print(['http://www.youtube.com'+yt_res['videos'][0]['url_suffix']])
        ydl.download(['http://www.youtube.com'+yt_res['videos'][0]['url_suffix']])

    # embed metadata

    track_file = eyed3.load(f'{SAVE_DIR}{yt_id}.mp3')

    track_file.tag.artist = str(artist)
    track_file.tag.album  = str(album)
    track_file.tag.album_artist = str(track['album']['artists'][0]['name'])
    track_file.tag.title = str(title)
    track_file.tag.track_num = int(track['track_number'])

    # Retrieve image data
    data = urllib.request.urlopen(image_url).read()
    track_file.tag.images.set(3, data, "image/jpeg", u"")

    track_file.tag.save()

    shutil.move(f'{SAVE_DIR}{yt_id}.mp3', f'{SAVE_DIR}{artist} - {title}.mp3')

    print(title)
    print(album)
    print(date)
    print(artist)
    print(image_url)

    print('-'*50)

    file = open(f'{SAVE_DIR}{artist} - {title}.mp3', 'rb').read()
    response = HttpResponse(file, content_type='audio/mpeg')
    response['Content-Disposition'] = f"attachment; filename=%s" % f'"{artist} - {title}.mp3"'
    return response


def search(request):
    creds = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    spotify = spotipy.Spotify(client_credentials_manager=creds)

    query = request.GET.get('q')

    try:
        metadata = spotify.search(query)['tracks']['items']

        results = [{
            'id': result['id'],
            'title': result['name'],
            'artists': ', '.join([artist['name'] for artist in result['artists']]),
            'album': result['album']['name'],
            'date': result['album']['release_date'],
            'image': result['album']['images'][0]['url'],
        } for result in metadata]

        print('SEARCH |', query)
        return render(request, 'downloader/search.html', {'results': results})

    except:
        pass


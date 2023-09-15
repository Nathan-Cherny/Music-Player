from flask import Flask, request, render_template
import os
import json
import matplotlib.pyplot as plt
import pydub
import shutil
from webbrowser import open as openurl
import math
from yt_dlp import YoutubeDL

app = Flask(__name__)
newSongType = 'm4a'
newChangedSongType = "mp3"
static = 'static/'
os.chdir(os.getcwd())

class Playlist:
    categories = [
        "clips",
        "songs",
        "speed"
    ]
    playlistDir = static + "playlists/"

def getSongsJSON():
    data = loadJson('data.json')
    songs = {}
    for playlist in data:
        for section in data[playlist]:
            for song in data[playlist][section]:
                songs[song] = data[playlist][section][song]
    
    return songs

def cropAudio(form):
    # audio is file name, like bob.mp3

    beginning = form['start']
    end = form['end']
    song = form['songSelector']
    name = form['name']

    audio = getSongLocFiles(song)
    loc = audio.split("/")
    fileType = audio.split(".")[1]
    audiosegment = pydub.AudioSegment.from_file(audio, fileType)
    audiosegment = audiosegment[convert(beginning)*1000:convert(end)*1000]
    loc[3] = Playlist.categories[0]
    loc[4] = name + "." + newChangedSongType
    audiosegment.export("/".join(loc), format=newChangedSongType)
    addOtherSectionJson(loc)

def getSongLocFiles(songName):
    files = getMusicFiles()
    for playlist in files:
        for section in files[playlist]:
            for song in files[playlist][section]:
                if song == songName:                  
                    return f"{Playlist.playlistDir}{playlist}/{section}/{songName}"

def graphPlayed():
    songs = getSongsJSON()

    songs = sorted(
        songs.items(),
        key = lambda kv: kv[1]['played']
    )

    print(songs)

    x = [i[0].split(".")[0] for i in songs]
    y = [i[1]['played'] for i in songs]

    print(x, y)

    plt.barh(x, y)
    plt.show()

def convert(time):
    time = time.split(":")

    seconds = time[1]

    if seconds[0] == 0:
        seconds = seconds[1]

    minutes = int(time[0])
    seconds = int(seconds)
    minutes *= 60
    return minutes + seconds

def createNewPlaylist(name):
    path = os.path.join(Playlist.playlistDir, name)
    os.mkdir(path)
    for category in Playlist.categories:
        dirPath = os.path.join(path, category)
        os.mkdir(dirPath)
    newJsonPlaylist(name, loadJson('data.json'), getMusicFiles())

def dumpJson(file, data):
    with open(file, "w") as file:
        json.dump(data, file, indent=4)

def loadJson(file):
    with open(file, "r") as file:
        return json.load(file)
    
def newJsonSong():
    return {
        "played": 0,
        "bookmarks": [],
        "otherVersion": None
    }

def newJsonPlaylist(playlist, jsonData, data):
    jsonData[playlist] = {}
    playlistData = data[playlist]
    for category in playlistData:
        jsonData[playlist][category] = {}
        for mp3 in playlistData[category]:
            jsonData[playlist][category][mp3] = newJsonSong()
    dumpJson('data.json', jsonData)

def resetJson(check): # must pass true to do this, just want a really simple double check bc this is working with live data
    if check:
        data = getMusicFiles()
        jsonData = {}

        for playlist in data:
            newJsonPlaylist(playlist, jsonData, data)

        dumpJson('data.json', jsonData)

def addOtherSectionJson(loc):
    data = loadJson("data.json")
    song = loc[4]
    data[loc[2]][loc[3]][song] = newJsonSong()
    dumpJson("data.json", data)

def addSongJson(form, cropped):

    section = "songs"

    fileType = newSongType
    if cropped:
        fileType = cropped

    song = form['song'] + "." + fileType
    playlist = form['playlist']

    data = loadJson('data.json')
    data[playlist][section][song] = newJsonSong()    
    dumpJson('data.json', data)

def speedSong(form):
    song = form['songSelector']
    loc = getSongLocFiles(song)
    sound = pydub.AudioSegment.from_file(loc)

    new_frame_rate = int(sound.frame_rate * float(form['speed']))

    speedName = f"[SPEED] {math.trunc(float(form['speed']) * 100)}% {song}"

    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * float(form['speed']))
    })

    sound = sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

    loc = loc.split("/")
    loc[-1] = speedName

    print(loc)

    loc[3] = Playlist.categories[2]

    loc = "/".join(loc)

    sound.export(loc, format="MP3")
    addOtherSectionJson(loc.split("/"))

def addSongMP3(form):
    rtrn = None
    section = "songs"
    playlist = form['playlist']

    oldcwd = os.getcwd()

    os.chdir(f"{os.getcwd()}\static\playlists\{playlist}\{section}")

    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': f"{form['song']}.{newSongType}"
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download(form['url'])

    audio = pydub.AudioSegment.from_file(f"{form['song']}.{newSongType}", newSongType)

    if form['start'] or form['end'] or form['fade']:
        
        if form['start'] and form['end']:    
            start = int(convert(form['start'])) * 1000
            end = int(convert(form['end'])) * 1000

            fileType = "mp3" # pydub doesnt work with m4a for some reason

            audio = audio[start:end]

        if form['fade']:
            print(int(form['fade']))
            audio = audio.fade_out(int(form['fade']) * 1000)

        audio.export(f"{form['song']}.{fileType}", format=fileType)
        rtrn = fileType
        os.remove(f"{form['song']}.{newSongType}")

    os.chdir(oldcwd)
    return rtrn

def delSongMP3(form):
    section = form['section']
    playlist = form['playlist']
    song = form['song']

    location = f"{os.getcwd()}\static\playlists\{playlist}\{section}"
    path = os.path.join(location, song)
    os.remove(path)

def delSongJson(form):
    section = form['section']
    playlist = form['playlist']
    song = form['song']

    data_ = loadJson('data.json')
    data_[playlist][section].pop(song)
    dumpJson('data.json', data_)

def delSong(form):
    delSongMP3(form)
    delSongJson(form)

def addSong(form):
    cropped = addSongMP3(form)
    addSongJson(form, cropped)

def tallyPlay(form):
    section = form['section']
    song = form['song']
    playlist = form['playlist']

    data = loadJson('data.json')
    data[playlist][section][song]['played'] += 1
    dumpJson('data.json', data)

def delAllInDir(dir_):
    for d in os.listdir(dir_):
        path = dir_ + "/" + d
        if len(d.split(".")) == 1:
            delAllInDir(path)
        else:
            os.remove(path)
    os.rmdir(dir_)

def addBookmark(form):
    section = form['section']
    song = form['song']
    playlist = form['playlist']

    data = loadJson('data.json')
    data[playlist][section][song]['bookmarks'].append(form['bmtime'])
    dumpJson('data.json', data)

def deletePlaylist(playlist):
    delAllInDir(Playlist.playlistDir + playlist)
    data = loadJson('data.json')
    data.pop(playlist)
    dumpJson('data.json', data)

def getMusicFiles(): # goes through the folders in static and places mp3s in respective dir in a dict
    allFiles = {}
    playlistDir = os.listdir(static + "playlists")
    for playlist in playlistDir:
        playlistFiles = {}
        files = os.listdir(f"{static}/playlists/{playlist}")
        for file in files:
            if len(file.split(".")) == 1: # if there's no period in the file name, which means its a folder
                playlistFiles[file] = [] # specifying this new directory in the dict
                mp3s = os.listdir(f"{static}/playlists/{playlist}/{file}") # looping through the mp3s in the current folder and respectively adding
                for mp3 in mp3s:
                    playlistFiles[file].append(mp3)
        allFiles[playlist] = playlistFiles
    return allFiles

@app.route('/', methods=['POST', 'GET'])
def main():
    if request.method == "POST":
        match request.form['id']:
            case "songCounter":
                tallyPlay(request.form)
            case "addSong":
                addSong(request.form)
            case "deletePlaylist":
                deletePlaylist(request.form['playlist'])
            case "addPlaylist":
                createNewPlaylist(request.form['name'])
            case "addBookmark":
                addBookmark(request.form)
            case "otherVersion": # WIP kind not that important right now
                print(request.form['song1'])
            case "delSong":
                delSong(request.form)
            case "cropAudio":
                cropAudio(request.form)
            case "speedSong":
                speedSong(request.form)
            case "resetJSON":
                resetJson(True)
    return render_template('main.html', files=getMusicFiles(), json=getSongsJSON())


port = 8001

openurl(f"http://127.0.0.1:{port}/")
app.run(port=port)


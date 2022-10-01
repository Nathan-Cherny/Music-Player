from flask import Flask, render_template, url_for, request
import os
import webbrowser
import json
from pydub import AudioSegment

songDir = os.getcwd() + "/static"
allSongs = os.listdir(songDir)

songs = []
clips = []

for song in allSongs:
    if song.split(".")[1] == "mp3":
        if "[CLIP]" in song:
            clips.append(song)
        else:
            songs.append(song)

loc = os.getcwd() + "\\static\\"

app = Flask(__name__)

with open("data.json", "r") as f:
    rawJSON = json.load(f)

"""
# making JSON

def thing():
    rawJSON = []
    for song in allSongs:
        data = {
            'name': song.split(".")[0],
            'location': 0,
            'played': 0
            }
        rawJSON.append(data)
    return rawJSON

with open("data.json", "w") as file:
    json.dump(thing(), file, indent=4)
"""

def fractureSong(request):

    song = request.form['song'] + ".mp3"
    start = int(request.form['start'])
    end = int(request.form['end'])
    clipName = "[CLIP] " + request.form['name']

    location = loc + song
    dub = AudioSegment.from_mp3(location)
    fractured = dub[start * 1000 : end * 1000]
    fractured.export(f"static\{clipName}.mp3", format='mp3')

def addNewSong(request):
    os.system(f"youtube-dl -o {loc}%(NA)s.%(ext)s -f bestaudio -x --audio-format mp3 {request.form['url']}")
    old = loc + "\\NA.mp3" # is always set to NA for some reason when its not %(title)s
    new = loc + f"\\{request.form['name']}.mp3\\"
    os.rename(old, new)


@app.route('/', methods=['POST', 'GET'])
def main():
    if request.method == "POST":
        print(request.form['btn'])
        if request.form['btn'] == "newSong":
            addNewSong(request)
        elif request.form['btn'] == "newClip":
            fractureSong(request)

    return render_template('main.html', songs=songs, clips=clips)

webbrowser.open("http://127.0.0.1:5000/")
app.run()

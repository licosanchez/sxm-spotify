import requests
import json
import datetime
import spotipy
import sys
import spotipy.util as util
import time
import spotipy.oauth2 as oauth2
import ast

#spotify IDs
scope="playlist-modify-private playlist-modify-public"
redirect_uri="http://localhost:8000"
username=""
client_id=""    
client_secret=""
playlist_id=""
blacklist=["Courtney Barnett","Panda Bear","Run the Jewels","Car Seat Headrest"]
count=0
recent=[]

def scrape():
  #checks the siriusxm website 2 minute ago to see what's playing
  now= datetime.datetime.now()
  if now.hour <20:
    #Need to change time zone 5 hours in the future.  Keep the same day if before 19:00
    url= "https://www.siriusxm.com/metadata/pdt/en-us/json/channels/leftofcenter/timestamp/%02d-%02d-%02d:%02d:00" % (now.month,now.day,now.hour+4,now.minute-2)
  else:
    #Change to tomorrow if the current time is after 19:00
    url= "https://www.siriusxm.com/metadata/pdt/en-us/json/channels/leftofcenter/timestamp/%02d-%02d-%02d:%02d:00" % (now.month,now.day+1,now.hour-20,now.minute-2)
  headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36','Origin':'siriusxm.com'}
  try:
    #Download the metadata from siriusxm
    response = requests.get(url, headers=headers).json()
    if response['channelMetadataResponse']['status']==1:
      artist=response['channelMetadataResponse']['metaData']['currentEvent']['artists']['name']
      if artist.find("/")>0:
        #print(artist+" is being truncated")
        artist=artist[0:artist.find("/")]
      track=response['channelMetadataResponse']['metaData']['currentEvent']['song']['name']
      if track.find("(")>0:
        #print(track+" is being truncated")
        track=track[0:track.find("(")]
      if track.find("EXCLUSIVE")>0:
        track=track[0:track.find("EXCLUSIVE")]
      artisttrack=[artist,track]
      #print(artisttrack)
      return artisttrack
    else:
      #JSON returned an error messsage
      #print ("JSON data is empty")
      #print (response)
      #print (url)
      return ["No Artist","No Track"]
  except:
    #No response
    #print ("Couldn't download JSON data")
    return ["No Artist","No Track"]

def find_track(artist,track):
  #Search spotify library for the artist and track scraped from siriusxm
  try:
    results = sp.search(q="artist:" + artist + " track:" + track)
    if len(results["tracks"]["items"]) > 0:
      info = results["tracks"]["items"][0]["uri"]
      return info
    else:
      #no items returned from Spotify
      print("\033[91mCan't find %s by %s in Spotify library\033[0m" % (track, artist))
      return "not found"
  except:
    return "not found"
    
def track_in_playlist(newtrack):
  new=newtrack[0]
  try:
    last_ten=sp.user_playlist_tracks(username,playlist_id,limit=10,offset=290)
    for count in range(9):
      if last_ten['items'][count]['track']['uri'] == new:
        return False
  except:
    return False
  return True

#initial login to spotify
token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
sp=spotipy.Spotify(auth=token)

while True:
  count += 1
  if count == 50:
    #refresh token after 50 minutes
    with open(".cache-swqa990p0ibsp58oz6q7e8gd7") as cache:
      for line in cache:
        string=ast.literal_eval(line)
        #file converted from a string to a dictionary
        sp_oauth=oauth2.SpotifyOAuth(client_id,client_secret,redirect_uri,scope)
        try:
          token_data=sp_oauth.refresh_access_token(string['refresh_token'])
          token=token_data['access_token']
          sp=spotipy.Spotify(auth=token)
          print ('\033[92m'+"Refreshing Token"+'\033[0m')
          count=0
        except:
          count=49
  artisttrack=scrape()
  if artisttrack[0] in blacklist:
    print("\033[37m\033[41m"+artisttrack[0]+" has been blacklisted\033[0m")
  if artisttrack not in recent and artisttrack[0] not in blacklist and artisttrack[0] != "No Artist":
    recent.append(artisttrack)
    if len(recent)>9:
      del recent[0]
    current_song=[find_track(artisttrack[0],artisttrack[1])]
    if track_in_playlist(current_song) == True and current_song != ["not found"]:
      #add the song to the playlist if it hasn't been added recently
      print ("Adding %s by %s to playlist" % (artisttrack[1], artisttrack[0]))
      try:
        sp.user_playlist_add_tracks(username,playlist_id,current_song)
        #since we added a track to the end, remove the first song of the playlist
        track_one=sp.user_playlist_tracks(username,playlist_id,limit=1)
        sp.user_playlist_remove_specific_occurrences_of_tracks(username,playlist_id,[{"uri":track_one['items'][0]['track']['uri'],"positions":[0]}])
      except:
        print('\033[91m'+"Can't add song to playlist"+'\033[0m')
    #elif current_song == ["not found"]:
      #print ("Song not found")
    #else:
      #print ("%s by %s was added already" % (artisttrack[1], artisttrack[0]))
  #else:
    #print ("error scraping")
  time.sleep(60)


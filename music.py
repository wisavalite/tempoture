import os, json, urllib, urllib2, pyechonest, cgi, re
from rdioapi import oauth2 as oauth
from flask import Flask, render_template, redirect, url_for, request, session
from flask_oauth import OAuth
from pyechonest import config
config.ECHO_NEST_API_KEY="echo_nest_api_key"

app = Flask(__name__)

oauth = OAuth()
rdio = oauth.remote_app('rdio',
    base_url='http://api.rdio.com/1/',
    request_token_url='http://api.rdio.com/oauth/request_token',
    access_token_url='http://api.rdio.com/oauth/access_token',
    authorize_url='https://www.rdio.com/oauth/authorize',
    consumer_key='rdio_consumer_key',
    consumer_secret='rdio_secret_key'
)

@rdio.tokengetter
def get_rdio_token(token=None):
    return session.get('rdio_token')

@app.route('/login')
def login():
    return rdio.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))

@app.route('/oauth-authorized')
@rdio.authorized_handler
def oauth_authorized(resp):
    next_url = request.args.get('next') or url_for('weather')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    session['rdio_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    return redirect(next_url)
    
# save weather condition keywords
currentAttributes = []

@app.route('/')
def weather():
    try:
        headers = { 'User-Agent' : 'Custom' }
        request = urllib2.Request('http://api.wunderground.com/api/secret_key_goes_here/geolookup/conditions/forecast/q/autoip.json', None, headers)
        testRequest = urllib2.urlopen(request)
        json_string = testRequest.read()
        parsed_json = json.loads(json_string)
        location = parsed_json['location']['city']
        temp_f = parsed_json['current_observation']['temp_f']
        weather = parsed_json['current_observation']['weather']
        currentAttributes.append(weather)
        icon = parsed_json['forecast']['txt_forecast']['forecastday'][0]['icon_url']
        txt = parsed_json['forecast']['txt_forecast']['forecastday'][0]['fcttext']
        songs = weather_to_song(weather)
        songIDs = []
        for song in songs:
            id_string = song['foreign_ids'][0]['foreign_id']
            #print id_string
            songIDs.append(re.search('streaming\:song\:(t\d*)', id_string).group(1))
        print songIDs
        testRequest.close()
    except urllib2.URLError, e:
        "Failed to connect to WU."
    
    try:
        headers = { 'User-Agent' : 'Mozilla/5.0' }
        request = urllib2.Request('http://developer.echonest.com/api/v4/song/search?api_key=secret_key_goes_here&style=rock&min_danceability=0.65&min_tempo=140&results=5')
        musicRequest = urllib2.urlopen(request)
        json_string = musicRequest.read()
        parsed_json = json.loads(json_string)
        musicRequest.close()
    except urllib2.URLError, e:
        "Failed to connect to Echo."
    
    return render_template('main.html',location=location, temp_f=temp_f, txt=txt, json_string=json_string, songs=songs, icon=icon)

@app.route('/testsss', methods=['GET'])
def music(style=None, mood=None, 
            max_tempo=None, min_tempo=None, 
            song_min_hotttnesss=None, artist_min_hotttnesss=None, 
            max_danceability=None, min_danceability=None, 
            max_energy=None, min_energy=None):
    api_call = "http://developer.echonest.com/api/v4/song/search?api_key=%s" % config.ECHO_NEST_API_KEY
# cut off
"""
    locals_list = [] 
    for local in locals():
        locals_list.append(local)
        value in locals(), locals().values():
        apicall += "&%s=%s" % (parameter, value)
    
    try:
        headers = { 'User-Agent': 'Custom' }
        request = urllib2.Request(apicall, None, headers)
        testRequest= urllib2.urlopen(request)
        json_string = testRequest.read()
        parsed_json = json.loads(json_string)
        print parsed_json
    except urllib2.URLError, e:
        "Failed to connect to WU."

    testRequest.close()
    return locals_list
"""
# cut off

def weather_to_song(weather):
	try:
		# Regex out any potential light or heavy prefixes
		simple_weather = re.search('[Light|Heavy]? ?([A-Za-z]*)$', weather).group(1)
		
		# Probably makes more sense to make this global or class variable	
		weather_mood_dict = {
			"Drizzle" : ['calming', 'peaceful', 'light', 'soothing', 'reflective', 'sentimental'],
			"Rain" : ['calming', 'intimate', 'passionate', 'meditation', 'sexy'],
			"Ice Crystals" : ['cold', 'sophisticated'],
			"Ice Pellets" : ['bouncy', 'cold'],
			"Hail" : ['bouncy', 'intense', 'rebellious'],
			"Mist" : ['ambient'], 
			"Fog" : ['ominous'], 
			"Fog Patches" : ['ominous'], 
			"Haze" : ['trippy', 'industrial', 'hypnotic'],
			"Spray" : ['gentle', 'gleeful', 'reflective', 'joyous'],
			"Blowing Snow" : ['cold', 'eerie'],
			"Rain Mist" : ['calming', 'soothing', 'cool', 'mellow', 'gentle', 'whimsical'],
			"Rain Showers" : ['dramatic', 'gentle', ''], 
			"Snow Showers" : ['cold'] ,  
			"Ice Pellet Showers" : ['harsh', 'cold'],
			"Hail Showers" : ['harsh', 'cold'],
			"Small Hail Showers" : ['cold'],
			"Thunderstorm" : ['aggressive'],
			"Thunderstorms and Rain" : ['aggressive', 'manic'],
			"Thunderstorms and Snow" : ['aggressive', 'manic'],
			"Thunderstorms with Hail" : ['aggressive', 'harsh', 'rebellious'],
			"Thunderstorms with Small Hail" : ['aggressive'],
			"Freezing Drizzle" : ['cold', 'quiet'],
			"Freezing Rain" : ['cold', 'intense', 'mystical'],
			"Freezing Fog" : ['intense', 'complex', 'cold', 'ominous', 'haunting'],
			"Patches of Fog" : ['ominous', 'haunting'],
			"Shallow Fog" : ['ominous', 'haunting'],
			"Partial Fog" : ['ominous', 'haunting'],
			"Overcast" : ['gloomy', 'eerie'],
			"Clear" : ['happy', 'carefree', 'energetic', 'fun', 'gleeful', 'joyous', 'light', 'lively'],
			"Partly Cloudy" : ['laid-back', 'quiet', 'smooth'],
			"Mostly Cloudy" : ['sad', 'mellow', 'poignant', 'gloomy'],
			"Scattered Clouds" : ['laid-back', 'quiet', 'smooth', 'happy', 'carefree'],
			"Small Hail" : ['cold', 'aggressive'],
			"Unknown Precipitation" : ['futuristic', 'trippy', 'strange', 'spiritual', 'theater'],
			"Unknown" : ['futuristic', 'trippy', 'strange', 'mystical', 'theater']
		}

		songs = []
		#get songs of top hotttnesss with the moods attached to the weather
		for mood in weather_mood_dict[simple_weather]:
			#make the request
			url = "http://developer.echonest.com/api/v4/song/search?api_key=secret_key_goes_here&bucket=id:rdio-us-streaming&limit=true&results=100&mood=%s"% mood
			request = urllib2.Request(url)
			testRequest = urllib2.urlopen(request)	
			json_string = testRequest.read()
			parsed_json = json.loads(json_string)
			#append songs
			songs += parsed_json['response']['songs']
		return songs
	except:
		songs = ['Excepted']
		return songs

if __name__ == "__main__":
    app.secret_key = 'app_secret_key'
    app.run(debug = True)

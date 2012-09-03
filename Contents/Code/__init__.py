# -*- coding: latin-1 -*-
RE_SHOWS	= Regex('var groups = (\[\[{.+}\]\]);', Regex.DOTALL)
RE_GENRES	= Regex('var genres = (\[.+?\]);', Regex.DOTALL)
RE_COUNTRIES	= Regex('var countries = (\[.+?\]);', Regex.DOTALL)
RE_SUMMARY 	= Regex('"Description":"(.+?)"')
RE_THUMB 	= Regex('<meta property="og:image" content="(.+?)"')
RE_SEASON 	= Regex('Saison ([0-9]+)')
RE_EP_NUM 	= Regex('Épisode ([0-9]+)')

# Plugin parameters
PLUGIN_TITLE		= "TOU.TV"
PLUGIN_PREFIX   	= "/video/TOU.TV"
PLUGIN_URL		= "http://www.tou.tv/"
PLUGIN_CONTENT_URL 	= 'http://release.theplatform.com/content.select?pid=%s&format=SMIL'
SEASON_INFO_URL		= 'http://www.tou.tv/Emisode/GetVignetteSeason?emissionId=%s&season=%s'

# Plugin resources
PLUGIN_ICON_DEFAULT	= "icon-default.png"
PLUGIN_ARTWORK		= "art-default.jpg"

MONTHS = [{"french" : "janvier", "english": "January"},{"french" : u"février", "english": "February"},{"french" : "mars", "english": "March"},
	{"french" : "avril", "english": "April"},{"french" : "mai", "english": "May"},{"french" : "juin", "english": "June"},
	{"french" : "juillet", "english": "July"},{"french" : u"août", "english": "August"},{"french" : "septembre", "english": "September"},
	{"french" : "octobre", "english": "October"},{"french" : "novembre", "english": "November"},{"french" : u"décembre", "english": "December"}]

####################################################################################################

def Start():
	Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, PLUGIN_TITLE, PLUGIN_ICON_DEFAULT, PLUGIN_ARTWORK)
	Plugin.AddViewGroup("InfoList", viewMode = "InfoList", mediaType = "items")
	
	# Set the default ObjectContainer attributes
	ObjectContainer.title1    = PLUGIN_TITLE
	ObjectContainer.view_group = "InfoList"
	ObjectContainer.art       = R(PLUGIN_ARTWORK)
	
	# Default icons for DirectoryObject in case there isn't an image
	DirectoryObject.thumb = R(PLUGIN_ICON_DEFAULT)
	
	# Set the default cache time
	HTTP.CacheTime = 1800
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12'

###################################################################################################

def MainMenu():
	oc = ObjectContainer()

	oc.add(DirectoryObject(key=Callback(AllShows), title=u"Toutes les émissions"))
	oc.add(DirectoryObject(key=Callback(BrowseByGenre), title="Parcourir par genre"))
	oc.add(DirectoryObject(key=Callback(BrowseByCountry), title="Parcourir par pays"))
	oc.add(DirectoryObject(key=Callback(BrowseAlphabetically), title=u"Parcourir par ordre alphabétique"))
	
	return oc

####################################################################################################

def GetShowList():
	
	raw_data = HTTP.Request(PLUGIN_URL + "repertoire").content
	show_data = RE_SHOWS.search(raw_data).group(1)
	shows = JSON.ObjectFromString(show_data)
	
	return shows

####################################################################################################

def AllShows():
	oc = ObjectContainer(title2 = u"Toutes les émissions")
	
	shows = GetShowList()
	for group in shows:
		for show in group:
			oc.add(DirectoryObject(key=Callback(Show, show=show), title = show["Title"]))
	
	return oc

####################################################################################################

def BrowseByGenre():
	oc = ObjectContainer(title2 = "Parcourir par genre")
	
	raw_data = HTTP.Request(PLUGIN_URL + "/repertoire").content
	genres_data = RE_GENRES.search(raw_data).group(1)
	genres = JSON.ObjectFromString(genres_data)
	
	for genre in genres:
		oc.add(DirectoryObject(key=Callback(Genre, genre=genre), title=genre['Title']))
	
	return oc

####################################################################################################

def Genre(genre):
	oc = ObjectContainer(title2 = genre['Title'])
	shows = GetShowList()
	for group in shows:
		for show in group:
			if show['GenreId'] == genre['Id']:
				oc.add(DirectoryObject(key=Callback(Show), title = show["Title"]))
	
	return oc

####################################################################################################

def BrowseByCountry():
	oc = ObjectContainer(title2 = "Parcourir par pays")
	
	raw_data = HTTP.Request(PLUGIN_URL + "/repertoire").content
	countries_data = RE_COUNTRIES.search(raw_data).group(1)
	countries = JSON.ObjectFromString(countries_data)
	
	for country in countries:
		oc.add(DirectoryObject(key=Callback(Country, country=country), title=country['CountryValue']))
	
	return oc

####################################################################################################

def Country(country):
	oc = ObjectContainer(title2 = country['CountryValue'])
	shows = GetShowList()
	for group in shows:
		for show in group:
			if show['CssCountry'] == country['CountryKey']:
				oc.add(DirectoryObject(key=Callback(Show), title = show["Title"]))
	
	return oc

####################################################################################################

def BrowseAlphabetically():
	oc = ObjectContainer(title2 = u"Parcourir par ordre alphabétique")
	
	for letters in ["0-9", "ABC", "DEF", "GHI", "JKL", "MNO", "PQR", "STU", "VWXYZ"]:
		oc.add(DirectoryObject(key=Callback(Letters, letters=letters), title=letters))
	
	return oc

####################################################################################################

def Letters(letters):
	oc = ObjectContainer(title2 = letters)
	shows = GetShowList()
	if letters == "0-9":
		letters = "0123456789"
	index=0
	while index < len(letters):
		letter = letters[index]
		for group in shows:
			for show in group:
				if show['GroupeId'] == letter:
					oc.add(DirectoryObject(key=Callback(Show), title = show["Title"]))
		index = index + 1
	
	return oc

####################################################################################################

def Show(show):
	oc = ObjectContainer(title2 = show['Title'])
	
	#try:
		
	data     = HTML.ElementFromURL(PLUGIN_URL + show["Url"])
	raw_data = HTTP.Request(PLUGIN_URL + show["Url"]).content
	
	if len(show['EpisodeCountBySeason']) == 1 and  show['EpisodeCountBySeason'][0]['EpisodeCount'] == 1:
		movie_title   = show['Title']
		movie_date    = Datetime.ParseDate(data.xpath('//meta[@name="dc.date.created"]')[0].get('content').split('|')[0]).date()
		movie_summary = data.xpath('//meta[@property="og:description"]')[0].get('content')
		movie_url = PLUGIN_URL + show['Url']
		movie_duration = int(data.xpath('//meta[@property="video:duration"]')[0].get('content'))*1000
		try:
			movie_thumb = data.xpath('//meta[@property="og:image"]')[0].get('content').replace('_L.jpeg','_A.jpeg')
		except:
			movie_thumb = None
			
		oc.add(MovieObject(url=movie_url, title=movie_title, originally_available_at=movie_date, summary=movie_summary, duration=movie_duration, thumb=Resource.ContentsOfURLWithFallback(url=movie_thumb, fallback=PLUGIN_ICON_DEFAULT)))
	else:
		showId = data.xpath('//meta[@name="ProfilingEmisodeToken"]')[0].get('content').split('.')[0]
			
		try:
			season_thumb = RE_THUMB.findall(raw_data)[0]
		except:
			season_thumb = None
			pass
		
		index = 0
		for season in show['EpisodeCountBySeason']:
			oc.add(DirectoryObject(key=Callback(Season, show=show, showId=showId, index=index), title=season['SeasonNumber'], thumb=Resource.ContentsOfURLWithFallback(url=season_thumb, fallback=PLUGIN_ICON_DEFAULT)))
			index = index + 1
	#except:
	#	return ObjectContainer(header="Emission vide", message=u"Cette émission n'a aucun contenu.")
		
	return oc

####################################################################################################

def Season(show, showId, index):
	oc = ObjectContainer(title1 = show["Title"], title2 = show['EpisodeCountBySeason'][index]['SeasonNumber'])

	episodes = JSON.ObjectFromURL(SEASON_INFO_URL % (showId, show['EpisodeCountBySeason'][index]['SeasonNumber']))
	for episode in episodes[0]['EpisodeVignetteList']:
		url=episode['DetailsViewUrl']
		if not url.startswith(PLUGIN_URL):
			url = PLUGIN_URL + url.lstrip('/')
		title=episode['EpisodeUrlEntity']['episode']
		try:
			ep_index = int(RE_EP_NUM.search(episode['DetailsViewSaison']).group(1))
		except:
			ep_index = None
		if title.startswith(u"Épisode"):
			if title.partition(':')[2] != '':
				title = title.partition(':')[2].strip()	
		date = TranslateDate(episode['DetailsViewDateEpisode'])
		summary = episode['DetailsFullDescription']
		thumb = episode['DetailsViewImageUrlL'].replace('_L.jpeg','_A.jpeg')
		duration = Datetime.MillisecondsFromString(episode['DetailsViewDureeEpisode'])
		oc.add(EpisodeObject(url=url, title=title, show=show['Title'], index=ep_index, season=show['EpisodeCountBySeason'][index]['SeasonNumber'], originally_available_at=date, summary=summary, thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=PLUGIN_ICON_DEFAULT)))
	
	if len(oc) == 0:
		return ObjectContainer(header="Saison vide", message="Cette saison n'a aucun contenu.")
	
	return oc

####################################################################################################

def TranslateDate(date):
	for month in MONTHS:
		date = date.replace(month['french'], month['english'])
	return Datetime.ParseDate(date).date()
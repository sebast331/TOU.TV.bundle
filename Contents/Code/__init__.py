# -*- coding: latin-1 -*-
RE_SUMMARY = Regex('"Description":"(.+?)"')
RE_THUMB = Regex('<meta property="og:image" content="(.+?)"')
RE_SEASON = Regex('Saison ([0-9]+)')
RE_EP_NUM = Regex('Épisode ([0-9]+)')

# Plugin parameters
PLUGIN_TITLE		= "TOU.TV"
PLUGIN_PREFIX   	= "/video/TOU.TV"
PLUGIN_URL		= "http://www.tou.tv"
PLUGIN_CONTENT_URL 	= 'http://release.theplatform.com/content.select?pid=%s&format=SMIL'

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

	shows = []
	raw_data = HTTP.Request(PLUGIN_URL + "/repertoire").content
	raw_data = raw_data.replace("style=\"display:none;\"/>", "style=\"display:none;\">")
	data     = HTML.ElementFromString(raw_data)
	
	for c in data.xpath("//h1[@class = 'titreemission']/.."):
		show = {}
		show["title"]      = c.find("h1").text
		show["genre"]      = c.xpath("span[@class = 'genre']")[0].text
		show["url"]        = c.get("href")
		
		try:
			show["numseasons"] = int(c.xpath("span[@class = 'nbsaison']")[0].text)
		except:
			show["numseasons"] = 0
		
		shows.append(show)
	
	shows.sort(lambda x, y: cmp(x["title"].lower(), y["title"].lower()))
	
	oc.add(DirectoryObject(key=Callback(AllShows, shows=shows), title=u"Toutes les émissions"))
	oc.add(DirectoryObject(key=Callback(BrowseByGenre, shows=shows), title="Parcourir par genre"))
	
	return oc

####################################################################################################

def AllShows(shows):
	oc = ObjectContainer(title2 = u"Toutes les émissions")
	
	for show in shows:
		oc.add(DirectoryObject(key=Callback(Show, show=show, title=show["title"]), title = show["title"]))
	
	return oc

####################################################################################################

def BrowseByGenre(shows):
	oc = ObjectContainer(title2 = "Parcourir par genre")
	
	genres = {}
	
	for show in shows:
		if show["genre"] not in genres:
			genres[show["genre"]] = []
		genres[show["genre"]].append(show)
	
	keys = genres.keys()
	keys.sort(lambda x, y: cmp(x.lower(), y.lower()))
	
	for key in keys:
		oc.add(DirectoryObject(key=Callback(Genre, genre=genres[key], title=key), title=key))
	
	return oc

####################################################################################################

def Genre(genre, title):
	oc = ObjectContainer(title2 = title)
	
	for show in genre:
		oc.add(DirectoryObject(key=Callback(Show, show=show, title=show["title"]), title = show["title"]))
	
	return oc

####################################################################################################

def Show(show, title):
	oc = ObjectContainer(title2 = title)
	
	try:
		data     = HTML.ElementFromURL(PLUGIN_URL + show["url"])
		raw_data = HTTP.Request(PLUGIN_URL + show["url"]).content
		
		if show["numseasons"] == 0:
			movie_title   = data.xpath("//h1[@class = 'emission']")[0].text
			movie_date    = TranslateDate(data.xpath("//div[@class = 'specs']/p[@id = 'MainContent_ctl00_PDateEpisode']/strong")[0].text)
			movie_summary = RE_SUMMARY.findall(raw_data)[0]
			movie_url = PLUGIN_URL + show['url']
			try:
				movie_thumb = RE_THUMB.findall(raw_data)[0]
			except:
				movie_thumb = None
			
			oc.add(MovieObject(url=movie_url, title=movie_title, originally_available_at=movie_date, summary=movie_summary, thumb=Resource.ContentsOfURLWithFallback(url=movie_thumb, fallback=PLUGIN_ICON_DEFAULT)))
		else:
			season_summary = data.xpath("//div[@id = 'detailsemission']/p")[0].text
			
			try:
				season_thumb = RE_THUMB.findall(raw_data)[0]
			except:
				season_thumb = None
				pass
			
			show["seasons"] = {}
			
			for c in data.xpath("//div[@class = 'blocepisodeemission']"):
				floatimg      = c.xpath("div[@class = 'floatimg']")[0]
				floatinfos    = c.xpath("div[@class = 'floatinfos']")[0]
				
				season_name = floatinfos.xpath("p")[0].text
				if season_name not in show["seasons"]:
					show["seasons"][season_name] = []
				
				episode = {}
				episode["name"]     = floatimg.find("a").find("img").get("alt")
				episode["url"]      = floatimg.find("a").get("href")
				episode["thumb"]    = floatimg.find("a").find("img").get("src")
				episode["date"]     = floatinfos.find("div").find("strong").text
				episode["summary"]  = floatinfos.xpath("p")[1].text
				show["seasons"][season_name].append(episode)
			
			season_names = show["seasons"].keys()
			season_names.sort(lambda x, y: cmp(x.lower(), y.lower()))
			
			for season_name in season_names:
				oc.add(DirectoryObject(key=Callback(Season, show_title=show["title"], season=show["seasons"][season_name], season_name=season_name), title=season_name, summary=season_summary, thumb=Resource.ContentsOfURLWithFallback(url=season_thumb, fallback=PLUGIN_ICON_DEFAULT)))
	except:
		return ObjectContainer(header="Emission vide", message=u"Cette émission n'a aucun contenu.")
		
	return oc

####################################################################################################

def Season(show_title, season, season_name):
	oc = ObjectContainer(title1 = show_title, title2 = season_name)
	
	season.sort(lambda x, y: cmp(x["url"], y["url"]))
	
	try:
		season_num = int(RE_SEASON.search(season_name).group(1))
	except:
		season_num = None
	
	for episode in season:
		url=episode['url']
		if not url.startswith(PLUGIN_URL):
			url = PLUGIN_URL + url
		title=episode["name"]
		try:
			ep_index = int(RE_EP_NUM.search(title).group(1))
		except:
			ep_index = None
		if title.startswith(u"Épisode"):
			if title.partition(':')[1] != '':
				title = title.partition(':')[2]
		date = TranslateDate(episode["date"])
		summary = episode["summary"]
		thumb = episode["thumb"]
		oc.add(EpisodeObject(url=url, title=title, show=show_title, index=ep_index, season=season_num, originally_available_at=date, summary=summary, thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=PLUGIN_ICON_DEFAULT)))
	
	if len(oc) == 0:
		return ObjectContainer(header="Saison vide", message="Cette saison n'a aucun contenu.")
	
	return oc

####################################################################################################

def TranslateDate(date):
	for month in MONTHS:
		date = date.replace(month['french'], month['english'])
	return Datetime.ParseDate(date).date()
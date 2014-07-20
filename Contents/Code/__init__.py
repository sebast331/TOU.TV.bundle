# import
import re

# Plugin Preferences
PLUGIN_NAME             = "ICI TOU.TV"
PLUGIN_TITLE            = "TOU.TV"
PLUGIN_PREFIX           = "/video/TOU.TV"

# API URL
URL_CARROUSEL           = "http://api.tou.tv/v1/toutvapiservice.svc/json/GetCarrousel?playlistName=Carrousel%20Accueil"
URL_ALL_SHOWS           = "http://api.tou.tv/v1/toutvapiservice.svc/json/GetPageRepertoire"
URL_SHOW                = "http://api.tou.tv/v1/toutvapiservice.svc/json/GetPageEmission?emissionId=%s"
URL_ACCUEIL				= "http://api.tou.tv/v1/toutvapiservice.svc/json/GetPageAccueil"

# make sure to replace artwork with what you want
# these filenames reference the example files in
# the Contents/Resources/ folder in the bundle
#ART  = 'art-default.jpg'
#ICON = 'icon-default.png'

####################################################################################################

def Start():

    ## make this plugin show up in the 'Video' section
    ## in Plex. The L() function pulls the string out of the strings
    ## file in the Contents/Strings/ folder in the bundle
    ## see also:
    ##  http://dev.plexapp.com/docs/mod_Plugin.html
    ##  http://dev.plexapp.com/docs/Bundle.html#the-strings-directory
    Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, PLUGIN_TITLE)

    # Default Object Container
    ObjectContainer.title1 = PLUGIN_TITLE
    
    # Default HTTP
    #HTTP.CacheTime = CACHE_1HOUR
    HTTP.CacheTime = 0

def MainMenu():

    oc = ObjectContainer()

    # Main Menu
    oc.add(DirectoryObject(key=Callback(CarrouselMenu), title=u"En vedette"))
    oc.add(DirectoryObject(key=Callback(ListShowsMenu, title=u"Toutes les �missions"), title=u"Toutes les �missions"))
    oc.add(DirectoryObject(key=Callback(SelectionsMenu, sectionName="SelectionADecouvrir", sectionTitle=u"S�lections � d�couvrir"), title=u"S�lections � d�couvrir"))
    oc.add(DirectoryObject(key=Callback(GenresListMenu), title=u"Parcourir par genre"))
    oc.add(DirectoryObject(key=Callback(LetterListMenu), title=u"Parcourir par ordre alphab�tique"))
    # Search
    oc.add(InputDirectoryObject(key=Callback(ListShowsMenu, title="Resultats de recherche: "), title="Search Title", summary="The description of what you are searching for..."))

 
    return oc

######################################################
#	Displays the list of shows that matches the conditions
@route(PLUGIN_PREFIX + '/ListShowsMenu')
def ListShowsMenu(title, genre=None, titleRegex=None, query=""):

    oc = ObjectContainer(title2 = title + query)

    # Query is the result of a search and should be the regex
    if (query != ""):
    	titleRegex = query

    # Get the AllShows
    shows = JSON.ObjectFromURL(URL_ALL_SHOWS)['d']['Emissions']
    for show in shows:
    	if (
    			(genre == None or genre == show['Genre'])
    		and (titleRegex == None or re.compile(titleRegex, re.IGNORECASE).search(show['Titre']))
    		):
    		# Display the show that matches the conditions
	        thumb = Resource.ContentsOfURLWithFallback(url=show['ImageJorC'])
	        oc.add(DirectoryObject(key=Callback(ShowMenu, show=show), title = show['Titre'], thumb = thumb, art = thumb))

    return oc

######################################################
#   Displays a list of season of 
@route(PLUGIN_PREFIX + '/ShowMenu', show=list)

def ShowMenu(show):

    oc = ObjectContainer(title2 = show['Titre'])

    # Get the objects
    dataEmission = JSON.ObjectFromURL(URL_SHOW % str(show['Id']))
    jsonEmission = dataEmission['d']['Emission']
    jsonEpisodes = dataEmission['d']['Episodes']

    # Add the items to the ObjectContainer
    #   If a unique episode, allow to play immediately
    #   If not a unique episode, display a season menu
    if jsonEpisodes[0]['IsUniqueEpisode'] == True:
        return EpisodesMenu(showId=show['Id'], season=jsonEpisodes[0]['SeasonNumber'])
    else:
        for season in show['NombreEpisodesParSaison']:
            seasonTitle = 'Saison %s (%s episodes)' % (str(season['Key']), str(season['Value']))
            oc.add(DirectoryObject(key=Callback(EpisodesMenu, showId=show['Id'], season=season['Key']), title=seasonTitle))
        return oc


##########################################
#   Displays the list of shows
##########################################
@route(PLUGIN_PREFIX + '/EpisodesMenu', showId=str, season=int)
def EpisodesMenu(showId, season=-1):
    jsonShows = JSON.ObjectFromURL(URL_SHOW % showId)
    jsonEmission = jsonShows['d']['Emission']
    jsonEpisodes = jsonShows['d']['Episodes']

    oc = ObjectContainer(title2 = "%s - Saison %s" % (jsonEmission['Title'], str(season)) )

    for show in jsonEpisodes:
        if (show['SeasonNumber'] == season or season == -1):
            movieTitle = show['Title']
            movieSummary = show['Description']
            movieYear = int(show['Year'])
            movieUrl = show['Url'].lstrip('/')
            movieDuration = int(show['Length'])
            movieId = show['TitleID']
            try:
                movieThumb = show['ImageThumbMoyenL']
            except:
                movieThumb = None
            try:
                movieArt = show['ImagePromoLargeL']
            except:
                movieArt = None

            ### TODO: PLAY VIDEO
            oc.add(MovieObject(key=movieId, rating_key=movieId, title=movieTitle, summary=movieSummary, year=movieYear, duration=movieDuration, thumb=Resource.ContentsOfURLWithFallback(url=movieThumb), art=Resource.ContentsOfURLWithFallback(url=movieArt)))

    return oc



##########################################
#   Displays the list of shows
##########################################
@route(PLUGIN_PREFIX + '/SelectionsMenu')
def SelectionsMenu(sectionName, sectionTitle):
    jsonShows = JSON.ObjectFromURL(URL_ACCUEIL)
    jsonEpisodes = jsonShows['d'][sectionName.split('/')[0]]['Episodes']

    oc = ObjectContainer(title2 = unicode(sectionTitle))

    for show in jsonEpisodes:
        movieTitle = show['Title']
        movieSummary = show['Description']
        movieYear = int(show['Year'])
        movieUrl = show['Url'].lstrip('/')
        movieDuration = int(show['Length'])
        movieId = show['TitleID']
        try:
            movieThumb = show['ImageThumbMoyenL']
        except:
            movieThumb = None
        try:
            movieArt = show['ImagePromoLargeL']
        except:
            movieArt = None

        ### TODO: PLAY VIDEO
        oc.add(MovieObject(key=movieId, rating_key=movieId, title=movieTitle, summary=movieSummary, year=movieYear, duration=movieDuration, thumb=Resource.ContentsOfURLWithFallback(url=movieThumb), art=Resource.ContentsOfURLWithFallback(url=movieArt)))

    return oc


######################################
@route(PLUGIN_PREFIX + '/GenresListMenu')
def GenresListMenu():
	json = JSON.ObjectFromURL(URL_ACCUEIL)
	jsonGenres = json['d']['Genres']

	oc = ObjectContainer(title2 = u"Parcourir par genre")

	for genre in jsonGenres:
		oc.add(DirectoryObject(key=Callback(ListShowsMenu, title=genre['Title'], genre=genre['Title']), title=genre['Title']))

	return oc


######################################
@route(PLUGIN_PREFIX + '/CarrouselMenu')
def CarrouselMenu():
	json = JSON.ObjectFromURL(URL_CARROUSEL)
	jsonCarrousel = json['d']

	oc = ObjectContainer(title2 = u"En vedette")

	for show in jsonCarrousel:
		oc.add(MovieObject(key=show['EmissionId'], rating_key=show['EmissionId'], title=show['title'], summary=show['subTitle'], thumb=Resource.ContentsOfURLWithFallback(url=show['imgNR']), art=Resource.ContentsOfURLWithFallback(url=show['imgLR'])))

	return oc


######################################
@route(PLUGIN_PREFIX + '/LetterListMenu')
def LetterListMenu():
	oc = ObjectContainer(title2 = u"Parcourir par ordre alphab�tique")

	for letters in ["0-9", "ABC", "DEF", "GHI", "JKL", "MNO", "PQR", "STU", "VWXYZ"]:
		oc.add(DirectoryObject(key=Callback(ListShowsMenu, title=letters, titleRegex="^[%s]" % letters), title=letters))

	return oc
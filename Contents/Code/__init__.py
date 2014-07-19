# Plugin Preferences
PLUGIN_NAME             = "ICI TOU.TV"
PLUGIN_TITLE            = "TOU.TV"
PLUGIN_PREFIX           = "/video/TOU.TV"

# API URL
URL_CARROUSEL           = "http://api.tou.tv/v1/toutvapiservice.svc/json/GetCarrousel?playlistName=Carrousel%20Accueil"
URL_ALL_SHOWS           = "http://api.tou.tv/v1/toutvapiservice.svc/json/GetPageRepertoire"
URL_SHOW                = "http://api.tou.tv/v1/toutvapiservice.svc/json/GetPageEmission?emissionId=%s"

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
    HTTP.CacheTime = CACHE_1HOUR

def MainMenu():
    Log('Entering MainMenu')
    oc = ObjectContainer()

    # Main Menu
    oc.add(DirectoryObject(key=Callback(AllShows), title=u"Toutes les émissions"))
 
    return oc

######################################################
@route(PLUGIN_PREFIX + '/AllShows')
def AllShows():
    Log('Entering AllShows')
    oc = ObjectContainer(title2 = u"Toutes les émissions")

    # Get the AllShows
    shows = JSON.ObjectFromURL(URL_ALL_SHOWS)['d']['Emissions']
    for show in shows:
        thumb = Resource.ContentsOfURLWithFallback(url=show['ImageJorC'])
        oc.add(DirectoryObject(key=Callback(ShowMenu, show=show), title = show['Titre'], thumb = thumb, art = thumb))

    return oc

######################################################
#   Displays a list of season of 
@route(PLUGIN_PREFIX + '/ShowMenu', show=list)

def ShowMenu(show):

    Log("Entering ShowMenu")
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
@route(PLUGIN_PREFIX + '/EpisodesMenu', showId=int, season=int)
def EpisodesMenu(showId, season):
    jsonShows = JSON.ObjectFromURL(URL_SHOW % str(showId))
    jsonEmission = jsonShows['d']['Emission']
    jsonEpisodes = jsonShows['d']['Episodes']

    oc = ObjectContainer(title2 = "%s - Saison %s" % (jsonEmission['Title'], str(season)) )

    for show in jsonEpisodes:
        if show['SeasonNumber'] == season:
            movieTitle = show['Title']
            movieSummary = show['Description']
            movieYear = int(show['Year'])
            movieUrl = show['Url'].lstrip('/')
            movieDuration = int(show['Length'])
            try:
                movieThumb = show['ImageThumbMoyenL']
            except:
                movieThumb = None
            try:
                movieArt = show['ImagePromoLargeL']
            except:
                movieArt = None

            ### TODO: PLAY VIDEO
            oc.add(MovieObject(key='a' + str(show['PID']), rating_key='b' + str(show['PID']), title=movieTitle, summary=movieSummary, year=movieYear, duration=movieDuration, thumb=Resource.ContentsOfURLWithFallback(url=movieThumb), art=Resource.ContentsOfURLWithFallback(url=movieArt)))

    return oc
# -*- coding: utf-8 -*-
import sys,re,os
import urllib,urllib2
import urlparse
import xbmc,xbmcgui,xbmcaddon
import xbmcplugin
import db, PhantomCommon, views

sysaddon     = sys.argv[0]
addon_handle = int(sys.argv[1])
args         = urlparse.parse_qs(sys.argv[2][1:])
my_addon     = xbmcaddon.Addon()
addonName    = my_addon.getAddonInfo('name')
PATH         = my_addon.getAddonInfo('path')
DATAPATH     = xbmc.translatePath(my_addon.getAddonInfo('profile')).decode('utf-8')
RESOURCES    = PATH+'/resources/'
FANART       = ''
cm           = PhantomCommon.common()

import resources.lib.segos as segos
segos.COOKIEFILE = os.path.join(DATAPATH,'segos.cookie')

def log(msg):
        xbmc.log(msg,level=xbmc.LOGNOTICE)

def addItem(name, exLink = None, mode = 'folder', iconImage = 'DefaultFolder.png', infoLabels = None, isFolder = False, isPlayable = False, fanart = FANART, contextmenu = None, list_type = None, params = {}):
    u = build_url({'mode': mode, 'name': name, 'exLink': exLink, 'list_type': list_type, 'params': params})
    liz = xbmcgui.ListItem(name)
    if not infoLabels:
        infoLabels={"title": name}
    liz.setInfo(type="video", infoLabels=infoLabels)
    if isPlayable:
        liz.setProperty('IsPlayable', 'true')

    art_keys=['thumb','poster','banner','fanart','clearart','clearlogo','landscape','icon']
    art = dict(zip(art_keys,[iconImage for x in art_keys]))
    art['landscape'] = fanart if fanart else art['landscape']
    art['fanart'] = fanart if fanart else art['landscape']
    liz.setArt(art)

    if contextmenu:
        contextMenuItems = contextmenu
        liz.addContextMenuItems(contextMenuItems)

    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u,listitem=liz, isFolder=isFolder)
    return ok



def encoded_dict(in_dict):
    out_dict = {}

    for k, v in in_dict.iteritems():
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):
            v.decode('utf8')
        out_dict[k] = v

    return out_dict

def build_url(query):
    return sysaddon + '?' + urllib.urlencode(encoded_dict(query))

def ListItems(exLink, list_type = None):
    films,pagination = segos.scanPage(exLink)


    if pagination[0]:
        addItem(name='[COLOR blue]<< Poprzednia strona (%d) <<[/COLOR]' %pagination[0][1], exLink=pagination[0][0], list_type = list_type, mode='page:ListItems')

    for f in films:
        if 'page=seriale' in f.get('url'):
            addItem(name='[COLOR orange]'+f.get('title')+'[/COLOR]', exLink=f.get('url',''), mode='getEpisodes', iconImage=f.get('img',''), infoLabels=f, isFolder=True, contextmenu=contextmenu(exLink,f.get('title'),list_type))
        else:
            addItem(name=f.get('title'), exLink=f.get('url',''), mode='getLinks', iconImage=f.get('img',''), infoLabels=f, isPlayable=True, contextmenu=contextmenu(exLink,f.get('title'),list_type))

    if pagination[1]:
        addItem(name='[COLOR blue]>> Następna strona (%d) >>[/COLOR]' %pagination[1][1], exLink=pagination[1][0], list_type = list_type, mode='page:ListItems')

    xbmcplugin.setContent(addon_handle, 'movies')
    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED, label2Mask = "%P, %Y")
    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.endOfDirectory(addon_handle)
    views.setView(list_type, {'skin.confluence': 50})

def getEpisodes(exLink):
    episodes = segos.getEpisodes(exLink)
    if not episodes:
        xbmcgui.Dialog().ok('[COLOR red]Problem[/COLOR]','')
        return

    items = len(episodes)

    for e in episodes:
        addItem(name=e.get('title'), exLink=e.get('url',''), mode='getLinks', iconImage=e.get('img'), infoLabels=e, isPlayable=True)
    xbmcplugin.endOfDirectory(addon_handle)
    xbmcplugin.setContent(addon_handle, 'episodes')

def getLinks(exLink):
    rurl,err = segos.getVideoUrl(exLink)
    if rurl:
        if '.mp4' in rurl or '.avi' in rurl or '.mkv' in rurl:
            if 'http' in rurl:
                stream_url = rurl
            else:
                stream_url = 'https://segos.es/' + rurl
        else:
            import resolveurl as urlresolver
            try:
                stream_url = urlresolver.resolve(rurl)
            except Exception,e:
                stream_url=''
                xbmcgui.Dialog().ok('[COLOR red]Problem[/COLOR]','Nie udało się odnaleźć źródła',str(e))

        xbmcplugin.setResolvedUrl(addon_handle, True, xbmcgui.ListItem(path=stream_url))
    elif err:
        xbmcgui.Dialog().ok('[COLOR red]Problem[/COLOR]',err)
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem(path=''))
    else:
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem(path=''))

def contextmenu(url,title_cln,list_type):
        contextmenu = []
        contextmenu.append(('Informacja', 'XBMC.Action(Info)'),)
        contextmenu.append(('Ustaw widok domyślny', 'RunPlugin(%s?mode=addView&list_type=%s)' % (sysaddon,list_type)))
        return contextmenu

def login():
    login = my_addon.getSetting('login')
    user = my_addon.getSetting('s_user')
    password = my_addon.getSetting('s_pass')

    if login == 'true':
        data = segos.getLogin(user,password)

        if data:
            addItem(name="Zalogowany: [B]"+user+"[/B]")
            try:
                exec(db.getq('s1.001'))
            except:
                pass
        else:
            xbmcgui.Dialog().ok('[COLOR red]Problem[/COLOR]','Nie udało się zalogować')


mode = args.get('mode', None)
fname = args.get('foldername',[''])[0]
exLink = args.get('exLink',[''])[0]
list_type = args.get('list_type',[''])[0]
params = args.get('params',[{}])[0]


sortV = my_addon.getSetting('sortV')
sortN = my_addon.getSetting('sortN') if sortV else 'Domyślne'
if not sortV: sortV=''




if mode is None:
    login()
    addItem(name="[COLOR blue]Filmy[/COLOR]",exLink='https://segos.es/?page=filmy%s&nr=1' %(sortV), mode='ListItems', isFolder=True, list_type='filmy')
    addItem(name="      Gatunek", mode='gat', isFolder=True)
    addItem(name="[COLOR blue]Bajki[/COLOR]",exLink='https://segos.es/?page=bajki%s&nr=1' %sortV, mode='ListItems', isFolder=True, list_type='bajki')
    addItem(name="[COLOR blue]Seriale[/COLOR]",exLink='https://segos.es/?page=seriale%s&nr=1' %sortV, mode='ListItems', isFolder=True, list_type='seriale')
    addItem(name="Sortowanie: [B]"+sortN+"[/B]",mode='filtr:sort')
    addItem(name="Ustawienia",mode='Settings')
    addItem(name="Szukaj",mode='SzukajFilmy', isFolder = True)
    xbmcplugin.endOfDirectory(addon_handle)



elif 'filtr' in mode[0]:
    _type = mode[0].split(":")[-1]

    if _type=='sort':
        label=['Domyślnie','Tytył (rosnąco)','Rok (rosnąco)','Data dodania (rosnąco)','Tytył (malejąco)','Rok (malejąco)','Data dodania (malejąco)']
        value=['','&sortby=title&according=asc','&sortby=year&according=asc','&sortby=date&according=asc','&sortby=title&according=desc','&sortby=year&according=desc','&sortby=date&according=desc']
        msg = 'Sortowanie'
        s = xbmcgui.Dialog().select(msg,label)
        if s > -1:
            my_addon.setSetting(_type+'V',value[s])
            my_addon.setSetting(_type+'N',label[s])
            xbmc.executebuiltin('XBMC.Container.Refresh')

elif mode[0] =='gat':
    data = segos.Gatunek()
    if data:
        for item in data:
            addItem(name=item[1],exLink=item[0] + '%s&nr=1' % sortV, mode='ListItems', list_type='filmy', isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] =='SzukajFilmy':
    d = xbmcgui.Dialog().input('Podaj tytuł szukanego filmu', type=xbmcgui.INPUT_ALPHANUM)
    if d:
        rurl = 'https://segos.es/?search=' + d.strip().replace(' ','+') +'&nr=1'
        ListItems(rurl)

elif mode[0].startswith('page'):
    tmp, nmode = mode[0].split(':')
    url = build_url({'mode': nmode, 'foldername': '', 'exLink': exLink, 'list_type':list_type, 'params': params})
    xbmc.executebuiltin('XBMC.Container.Refresh(%s)'% url)

elif mode[0] == 'ListItems':            ListItems(exLink,list_type)
elif mode[0] == 'getEpisodes':          getEpisodes(exLink)
elif mode[0] == 'getLinks':             getLinks(exLink)
elif mode[0] == 'Settings':
    my_addon.openSettings()
    xbmc.executebuiltin('XBMC.Container.Refresh()')
elif mode[0]=='addView':
    views.addView(list_type)


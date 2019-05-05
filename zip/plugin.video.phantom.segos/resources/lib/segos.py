# -*- coding: utf-8 -*-
import urllib2,urllib
import re,os
import cookielib
import requests
import urlparse
import xbmc,xbmcgui,xbmcaddon
import db, PhantomCommon
import cloudflare6

#-----------------------------------------------
my_addon     = xbmcaddon.Addon()
DATAPATH     = xbmc.translatePath(my_addon.getAddonInfo('profile')).decode('utf-8')
COOKIEFILE = os.path.join(DATAPATH,'segos.cookie')
cm = PhantomCommon.common()

scraper = cloudflare6.create_scraper()
scraper.cookies = cookielib.LWPCookieJar(COOKIEFILE)
BASEURL='http://segos.es/'
TIMEOUT = 10

UA      = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'
#------------------------------------------------

def log(msg):
        xbmc.log(msg,level=xbmc.LOGNOTICE)


class NoRedirection(urllib2.HTTPErrorProcessor):
    def http_response(self, request, response):
        return response

def getUrl(url,data=None,header={},useCookies=True,saveCookie=True):
    if COOKIEFILE and (useCookies or saveCookie):
        cj = cookielib.LWPCookieJar()

        if useCookies==True and os.path.exists(COOKIEFILE):
            cj.load(COOKIEFILE)

        opener = urllib2.build_opener(NoRedirection,urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)

    if not header:
        header = {'User-Agent':UA,'referer':'https://segos.es/'}

    if useCookies:
        header.update({"Cookie": cookieString(COOKIEFILE)})

    req = urllib2.Request(url,data,headers=header)

    response = urllib2.urlopen(req,timeout=TIMEOUT)
    try:

        response = urllib2.urlopen(req,timeout=TIMEOUT)
        link =  response.read()
        response.close()

        if COOKIEFILE and saveCookie:
            dataPath=os.path.dirname(COOKIEFILE)
            if not os.path.exists(dataPath): os.makedirs(dataPath)
            if cj: cj.save(COOKIEFILE)

    except urllib2.HTTPError as e:
        link = ''

    return link

def getUrl_old(url):
    if os.path.isfile(COOKIEFILE):
        s.cookies.load()
    aa=s.cookies
    content=s.get(url,verify=False).text
    return content

def cookieString(COOKIEFILE):
    sc=''
    if os.path.isfile(COOKIEFILE):
        cj = cookielib.LWPCookieJar()
        cj.load(COOKIEFILE)
        sc=''.join(['%s=%s;'%(c.name, c.value) for c in cj])
    return sc

def getLogin(u='',p=''):
    try:
        url ='http://segos.es/'
        scraper.get(url).text
        params = (('page', 'login'),)
        data = 'login=%s&password=%s&loguj='%(u,p)
        scraper.headers.update({'content-type': 'application/x-www-form-urlencoded',})
        response = scraper.post('https://segos.es/?page=login',data=data,allow_redirects=False)
        scraper.cookies.save()
        content=scraper.get(BASEURL).text
    except:
        content=''
    out = True if content.find('Wyloguj')>0 else False
    return out

def scanPage(url, data = None):
    content = getUrl(url,data,useCookies=True)
    prevPage = False
    nextPage = False
    cookstr = urllib.quote(cookieString(COOKIEFILE))
    out = []

    cpage = int(re.search('nr=(\d+)',url).group(1))
    if content.find('nr=%d'%(cpage+1))>0:
        nextPage = (re.sub('nr=\d+','nr=%d'%(cpage+1),url),cpage+1)
    if cpage > 1:
        prevPage = (re.sub('nr=\d+','nr=%d'%(cpage-1),url),cpage-1)

    subsets = re.compile('div style="overflow:(.*?)<div class="clearfix">', re.DOTALL).findall(content)
    for subset in subsets:
        match = re.search('href="\?page=(.*?)">(.*?)\((.*?)\)<',subset)
        img = re.search('src="(.*?)"', subset)
        if match and img:
            if '/' in match.group(2):
                titles = match.group(2).split('/ ')
                title = titles[0]
                title_oryg = titles[-1]
            else:
                title = match.group(2)
                title_org = ''
            plot = re.compile('<b>Opis</b>: (.*?)<', re.DOTALL).findall(subset)
            if "http" in img.group(1):
               img = img.group(1).replace('.6.','.3.')
            else:
               img = BASEURL + img.group(1)+'|User-Agent='+urllib.quote(UA)+'&Referer='+BASEURL+'&Cookie='+cookstr
            genre = re.compile('category=[^"]+">(.*?)</a>').findall(subset)
            langs = re.search('src="/images/langs/(.*?).png">',subset)
            quality = ' HD' if subset.find('src="/images/hd.')>-1 else ''
            code = langs.group(1) if langs else ''
            one = {'url'   : BASEURL+'/?page='+match.group(1),
                'title'  : match.group(2),
                'plot'   : plot[0],
                'img'    : img,
                'genre' : ', '.join(genre) if genre else '',
                'year'   : match.group(3),
                'code'   : code.strip(),
                'isFolder':False,
                }
            out.append(one)
    return out,(prevPage,nextPage)

def getEpisodes(url):
    content = getUrl(url)
    out=[]
    episodes = re.compile('- <a href="(.*?)">(.*?) <img src="/images/langs/(.*?)\.png',re.DOTALL).findall(content)

    for episode in episodes:
        h = BASEURL + episode[0]
        season = re.search('&s=(.*?)&',episode[0])

        title =  'Sezon %s %s  %s' % (season.group(1), episode[1].replace('</a>\n',' '), episode[2])
        out.append({
            'url'   : h,
            'title' : title,
            'img'   : '',
            })

    return out

def getVideoUrl(url):
    tab_s = []
    video_link=''
    err = ''
    href=''
    content = getUrl(url)
    subsets = re.compile('<tr\n(.*?)</tr>',re.DOTALL).findall(content)
    opis = re.compile('Opis</b>: (.*?)</p>',re.DOTALL).findall(content)
    for subset in subsets:
        line = re.compile('<td(.*?)</td>',re.DOTALL).findall(subset)
        if len(line)>4:
                lang = re.search('/images/langs/(.*?).png">',line[0])
                lang = lang.group(1) if lang else ''
                quality = line[1].split('>')[-1]
                server = re.search('src="/images/servers/(.*?)"',line[2])
                server = server.group(1).split('.')[0] if server else '?'
                access = line[3].split('>')[-1].strip()
                href = re.compile('href="(.*?)"><').findall(subset)
                if href:
                    link=urlparse.urljoin(BASEURL,href[0])
                    label = '%s | %s | %s | %s'%(lang,quality,server,access)
                    tab_s.append({'label':label, 'link':link})
    t = [ x.get('label') for x in tab_s]
    select = xbmcgui.Dialog().select("Wybór źródła", t)
    if select > -1:
        stream_url = tab_s[select].get('link')
        content = getUrl(stream_url)
        match = re.compile('16:9 aspect ratio -->(.*?)overflow: auto',re.DOTALL).findall(content)
        vlink = re.search('src="(.*?)"',match[0])
        if vlink:
            video_link = vlink.group(1)
            try:
                exec(db.getq('s2.001'))
            except:
                pass
        else:
            video_link = False
            err = re.search('Ten link jest tylko(.*?)\.',match[0]).group(0)
    return video_link, err

def Gatunek(url='http://segos.es/?page=filmy'):
    gat=[]
    content = getUrl(url)
    idx=content.find('<h4>Kategorie</h4>')
    if idx:
        gat = re.compile('<li><a href="(.*?)">(.*?)</a></li>').findall(content[idx:-1])
        if gat:
            gat = [(BASEURL+x[0],x[1].strip()) for x in gat]
    return gat


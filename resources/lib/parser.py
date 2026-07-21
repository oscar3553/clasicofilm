import re, urllib.request, urllib.parse, json, xbmc, xbmcgui

UA_STR = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def log(msg):
    xbmc.log(f"[Clasicofilm Parser] {msg}", xbmc.LOGINFO)

def fetch(url, headers=None):
    if headers is None:
        headers = {'User-Agent': UA_STR}
    try:
        req = urllib.request.Request(url, headers=headers)
        return urllib.request.urlopen(req, timeout=15).read().decode('utf-8', 'ignore')
    except Exception as e:
        log(f"Error cargando URL ({url}): {e}")
        return ""

def extract(post_url):
    h = fetch(post_url)
    streams = []
    
    # Extraer Dzen.ru
    dzen_links = set(re.findall(r'https://dzen\.ru/embed/[^"\'\>\s]+', h))
    for link in dzen_links:
        streams.append(('Dzen', link))
        
    # Extraer Mail.ru
    mail_links = set(re.findall(r'https://my\.mail\.ru/video/embed/[^"\'\>\s]+', h))
    for link in mail_links:
        streams.append(('Mail.ru', link))
        
    return streams

def resolve_dzen(url):
    h = fetch(url)
    m = re.search(r'"url":"(http[^"]+?\.m3u8[^"]*?)"', h)
    if m:
        return m.group(1).replace('\\\\', '').replace('\\', '')
    return None

def resolve_mailru(url):
    # Ventana emergente para ver la URL del Embed que recibe
    xbmcgui.Dialog().ok("DIAGNOSTICO MAIL.RU", f"URL Embed recibida:\n{url}")
    
    headers = {
        'User-Agent': UA_STR,
        'Referer': 'https://my.mail.ru/'
    }
    
    html = fetch(url, headers=headers)
    
    if not html:
        xbmcgui.Dialog().ok("DIAGNOSTICO MAIL.RU", "El HTML extraido está VACÍO (posible bloqueo de IP/User-Agent)")
        return None

    # Muestra los primeros 200 caracteres del HTML para comprobar que responde la web
    xbmcgui.Dialog().ok("DIAGNOSTICO MAIL.RU", f"HTML recibido correctamente ({len(html)} bytes).\nBuscando patrones .mpd / .mp4...")

    # 1. Buscar .mpd
    mpd_match = re.search(r'"(https?:\\?/\\?/[^"]+?\.mpd[^"]*)"', html)
    if mpd_match:
        mpd_url = mpd_match.group(1).replace('\\/', '/')
        if mpd_url.startswith('//'): mpd_url = 'https:' + mpd_url
        return mpd_url

    # 2. Buscar .mp4
    mp4_match = re.search(r'"(https?:\\?/\\?/[^"]+?\.mp4[^"]*)"', html)
    if mp4_match:
        mp4_url = mp4_match.group(1).replace('\\/', '/')
        if mp4_url.startswith('//'): mp4_url = 'https:' + mp4_url
        return mp4_url

    xbmcgui.Dialog().ok("DIAGNOSTICO MAIL.RU", "No se encontró ningún enlace .mpd ni .mp4 dentro del HTML.")
    return None

import re, urllib.request, urllib.parse, json, xbmc

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
        
    log(f"Enlaces extraidos del post: {streams}")
    return streams

def resolve_dzen(url):
    h = fetch(url)
    m = re.search(r'"url":"(http[^"]+?\.m3u8[^"]*?)"', h)
    if m:
        return m.group(1).replace('\\\\', '').replace('\\', '')
    return None

def resolve_mailru(url):
    log(f"Resolviendo Mail.ru HTML Embed: {url}")
    
    headers = {
        'User-Agent': UA_STR,
        'Referer': 'https://my.mail.ru/'
    }
    
    # 1. Obtener el HTML directamente de la URL del Embed
    html = fetch(url, headers=headers)
    if not html:
        return None

    # 2. Buscar manifest .mpd o enlaces de video en el HTML/JSON embebido
    mpd_match = re.search(r'"(https?:\\?/\\?/[^"]+?\.mpd[^"]*)"', html)
    if mpd_match:
        mpd_url = mpd_match.group(1).replace('\\/', '/')
        if mpd_url.startswith('//'):
            mpd_url = 'https:' + mpd_url
        log(f"MPD encontrado directamente en HTML: {mpd_url}")
        return mpd_url

    # 3. Si no hay .mpd, buscar enlaces .mp4 directos de Mail.ru
    mp4_match = re.search(r'"(https?:\\?/\\?/[^"]+?\.mp4[^"]*)"', html)
    if mp4_match:
        mp4_url = mp4_match.group(1).replace('\\/', '/')
        if mp4_url.startswith('//'):
            mp4_url = 'https:' + mp4_url
        log(f"MP4 encontrado en HTML: {mp4_url}")
        return mp4_url

    return None

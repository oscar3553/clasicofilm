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
    log(f"Resolviendo Mail.ru MPD: {url}")
    
    headers = {
        'User-Agent': UA_STR,
        'Referer': 'https://my.mail.ru/'
    }
    
    # Extraer ID del video de la URL embebida
    video_id = url.split('/')[-1]
    api_url = f"https://my.mail.ru/v/api/video/item/{video_id}"

    json_data = fetch(api_url, headers=headers)
    if not json_data:
        log("No se obtuvieron datos de la API de Mail.ru")
        return None

    try:
        data = json.loads(json_data)
        
        # Buscar la URL que contiene stream.mpd en la respuesta JSON
        videos = data.get('videos', [])
        for v in videos:
            stream_url = v.get('url', '')
            if 'stream.mpd' in stream_url or stream_url.endswith('.mpd'):
                if stream_url.startswith('//'):
                    stream_url = 'https:' + stream_url
                log(f"URL MPD encontrada: {stream_url}")
                return stream_url
                
        # Si no lo encuentra en 'videos', buscar mediante expresion regular en todo el JSON
        match = re.search(r'"(https?:\\?/\\?/[^"]+stream\.mpd[^"]*)"', json_data)
        if match:
            mpd_url = match.group(1).replace('\\/', '/')
            log(f"URL MPD encontrada por Regex: {mpd_url}")
            return mpd_url

    except Exception as e:
        log(f"Error procesando JSON de Mail.ru: {e}")

    return None

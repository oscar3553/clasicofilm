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
        'Referer': 'https://my.mail.ru/',
        'Accept': 'application/json, text/javascript, */*; q=0.01'
    }
    
    # Extraer ID del video limpiando slashes y parametros extra
    clean_url = url.split('?')[0].rstrip('/')
    video_id = clean_url.split('/')[-1]
    
    log(f"ID de video Mail.ru extraido: {video_id}")
    
    api_url = f"https://my.mail.ru/v/api/video/item/{video_id}"

    json_data = fetch(api_url, headers=headers)
    if not json_data:
        log("No se obtuvieron datos de la API de Mail.ru")
        return None

    try:
        data = json.loads(json_data)
        
        # Opcion A: Buscar en el listado 'videos' del JSON
        videos = data.get('videos', [])
        for v in videos:
            stream_url = v.get('url', '')
            if 'stream.mpd' in stream_url or '.mpd' in stream_url:
                if stream_url.startswith('//'):
                    stream_url = 'https:' + stream_url
                log(f"URL MPD encontrada en JSON: {stream_url}")
                return stream_url
                
        # Opcion B: Buscar cualquier URL .mpd mediante Regex si falla la estructura
        match = re.search(r'"(https?:\\?/\\?/[^"]+?\.mpd[^"]*)"', json_data)
        if match:
            mpd_url = match.group(1).replace('\\/', '/')
            if mpd_url.startswith('//'):
                mpd_url = 'https:' + mpd_url
            log(f"URL MPD encontrada por Regex: {mpd_url}")
            return mpd_url

    except Exception as e:
        log(f"Error procesando JSON de Mail.ru: {e}")

    return None

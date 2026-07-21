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
        
    return streams

def resolve_dzen(url):
    h = fetch(url)
    m = re.search(r'"url":"(http[^"]+?\.m3u8[^"]*?)"', h)
    if m:
        return m.group(1).replace('\\\\', '').replace('\\', '')
    return None

def resolve_mailru(url):
    log(f"Resolviendo Mail.ru: {url}")
    
    # 1. Extraer el ID numérico largo del final de la URL
    clean_url = url.split('?')[0].rstrip('/')
    video_id = clean_url.split('/')[-1]
    
    # 2. Consultar la API de metadatos de Mail.ru con las cabeceras necesarias
    api_url = f"https://my.mail.ru/v/api/video/item/{video_id}"
    headers = {
        'User-Agent': UA_STR,
        'Referer': url,
        'Accept': 'application/json'
    }
    
    json_str = fetch(api_url, headers=headers)
    if not json_str:
        return None
        
    try:
        data = json.loads(json_str)
        
        # Buscar el manifiesto .mpd o enlaces .mp4 dentro del objeto videos
        videos = data.get('videos', [])
        for v in videos:
            v_url = v.get('url', '')
            if '.mpd' in v_url or 'stream.mpd' in v_url:
                if v_url.startswith('//'): v_url = 'https:' + v_url
                return v_url
                
        # Si no hay mpd en el listado, buscar por regex en la respuesta JSON
        m = re.search(r'"(https?:\\?/\\?/[^"]+?\.mpd[^"]*)"', json_str)
        if m:
            mpd_url = m.group(1).replace('\\/', '/')
            if mpd_url.startswith('//'): mpd_url = 'https:' + mpd_url
            return mpd_url
            
        # Como última alternativa, extraer el enlace mp4 de mayor calidad
        if videos:
            best_url = videos[-1].get('url', '')
            if best_url.startswith('//'): best_url = 'https:' + best_url
            return best_url

    except Exception as e:
        log(f"Error parseando JSON Mail.ru: {e}")
        
    return None

import re, urllib.request, urllib.parse, json, xbmc

UA_STR = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def log(msg):
    xbmc.log(f"[Clasicofilm Parser] {msg}", xbmc.LOGINFO)

def fetch(url, headers=None, data=None):
    if headers is None:
        headers = {'User-Agent': UA_STR}
    try:
        req = urllib.request.Request(url, headers=headers, data=data)
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
    log(f"Resolviendo Mail.ru Embed ID: {url}")
    
    # 1. Extraer ID del video de la URL
    clean_url = url.split('?')[0].rstrip('/')
    video_id = clean_url.split('/')[-1]
    
    headers = {
        'User-Agent': UA_STR,
        'Referer': url,
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    # 2. Intentar llamada POST a la API de Mail.ru
    post_data = urllib.parse.urlencode({'id': video_id}).encode('utf-8')
    api_url = f"https://my.mail.ru/v/api/video/item/{video_id}"
    
    res_str = fetch(api_url, headers=headers, data=post_data)
    
    # Si la petición POST no trae datos, probamos GET con parámetro
    if not res_str or len(res_str) < 50:
        log("Probando llamada de respaldo GET a API Mail.ru...")
        api_url_alt = f"https://my.mail.ru/v/api/video/item/?id={video_id}"
        res_str = fetch(api_url_alt, headers=headers)

    if not res_str:
        log("No se obtuvo respuesta de Mail.ru")
        return None

    try:
        # A. Intentar extraer URL .mpd mediante Expresión Regular directa
        mpd_match = re.search(r'"(https?:\\?/\\?/[^"]+?\.mpd[^"]*)"', res_str)
        if mpd_match:
            mpd_url = mpd_match.group(1).replace('\\/', '/')
            if mpd_url.startswith('//'): mpd_url = 'https:' + mpd_url
            log(f"MPD encontrado: {mpd_url}")
            return mpd_url

        # B. Si no hay MPD, parsear el JSON y buscar el enlace directo
        data = json.loads(res_str)
        videos = data.get('videos', [])
        
        for v in videos:
            v_url = v.get('url', '')
            if '.mpd' in v_url or 'stream.mpd' in v_url:
                if v_url.startswith('//'): v_url = 'https:' + v_url
                return v_url
                
        if videos:
            best_url = videos[-1].get('url', '')
            if best_url.startswith('//'): best_url = 'https:' + best_url
            log(f"MP4/Stream alternativo encontrado: {best_url}")
            return best_url

    except Exception as e:
        log(f"Error parseando respuesta Mail.ru: {e}")
        
    return None

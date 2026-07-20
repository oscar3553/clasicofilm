import re, urllib.request, urllib.parse, json, http.cookiejar, xbmc

UA_STR = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def log(msg):
    xbmc.log(f"[Clasicofilm Parser] {msg}", xbmc.LOGINFO)

def extract(post_url):
    req = urllib.request.Request(post_url, headers={'User-Agent': UA_STR})
    try:
        h = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
    except Exception as e:
        log(f"Error cargando el post: {e}")
        return []

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
    req = urllib.request.Request(url, headers={'User-Agent': UA_STR})
    try:
        h = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
        m = re.search(r'"url":"(http[^"]+?\.m3u8[^"]*?)"', h)
        if m:
            return m.group(1).replace('\\\\', '').replace('\\', '')
    except:
        pass
    return None

def resolve_mailru(url):
    log(f"Resolviendo Mail.ru: {url}")
    
    # Crear un conector con soporte para guardar Cookies
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    headers = {
        'User-Agent': UA_STR,
        'Referer': 'https://my.mail.ru/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    try:
        # Paso 1: Cargar la pagina Embed para obtener cookies de sesion de Mail.ru
        req = urllib.request.Request(url, headers=headers)
        html = opener.open(req, timeout=20).read().decode('utf-8', 'ignore')
        
        # Buscar las fuentes de video directas inyectadas en la página embed
        # Mail.ru guarda las fuentes en un objeto JS con la estructura "metadataUrl" o "videos"
        meta_match = re.search(r'"metadataUrl"\s*:\s*"([^"]+)"', html)
        video_json_str = None
        
        if meta_match:
            meta_api_url = meta_match.group(1)
            if meta_api_url.startswith('//'):
                meta_api_url = 'https:' + meta_api_url
            
            # Consultar la URL de metadatos obtenida conservando las cookies de sesión
            req_meta = urllib.request.Request(meta_api_url, headers=headers)
            video_json_str = opener.open(req_meta, timeout=20).read().decode('utf-8', 'ignore')
        else:
            # Si no hay metadataUrl, buscar array directo de "videos"
            v_match = re.search(r'"videos"\s*:\s*(\[[^\]]+\])', html)
            if v_match:
                video_json_str = f'{{"videos": {v_match.group(1)}}}'

        if not video_json_str:
            log("No se encontro metadata de video en el HTML de Mail.ru")
            return None

        # Paso 2: Procesar JSON de videos
        data = json.loads(video_json_str)
        videos = data.get('videos', [])
        
        if not videos:
            log("Array de videos vacio")
            return None
            
        # Elegir la máxima calidad disponible (ejemplo 720p, 480p)
        best_video = sorted(videos, key=lambda x: int(str(x.get('key', '0')).replace('p', '') or 0), reverse=True)[0]
        stream_url = best_video.get('url')
        
        if stream_url:
            if stream_url.startswith('//'):
                stream_url = 'https:' + stream_url
            
            # Extraer las cookies para pasárselas a Kodi
            cookie_header = "; ".join([f"{c.name}={c.value}" for c in cj])
            
            # Construir la URL final con cabeceras para Kodi
            kodi_headers = {
                'User-Agent': UA_STR,
                'Referer': 'https://my.mail.ru/',
                'Cookie': cookie_header
            }
            final_url = stream_url + '|' + urllib.parse.urlencode(kodi_headers)
            log(f"URL final generada con exito: {stream_url}")
            return final_url

    except Exception as e:
        log(f"Error procesando Mail.ru: {e}")

    return None

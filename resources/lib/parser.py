import re, urllib.request, json, urllib.parse, xbmc

UA_STR = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
UA = {'User-Agent': UA_STR}

def log(msg):
    xbmc.log(f"[Clasicofilm Parser] {msg}", xbmc.LOGINFO)

def fetch(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        return urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
    except Exception as e:
        log(f"Error descargando {url}: {e}")
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
    log(f"Resolviendo Mail.ru para URL: {url}")
    
    # Obtener el ID del iframe
    m = re.search(r'/embed/(\d+)', url)
    if not m:
        log("No se pudo extraer el ID numerico de Mail.ru")
        return None
    video_id = m.group(1)
    
    videos = []
    
    # Método 1: Leer el código fuente del iframe embed directamente
    embed_url = f"https://my.mail.ru/video/embed/{video_id}"
    embed_html = fetch(embed_url)
    
    # Buscar el bloque JSON que Mail.ru inyecta en el reproductor (metadata / video sources)
    json_match = re.search(r'"videos"\s*:\s*(\[[^\]]+\])', embed_html)
    if json_match:
        try:
            videos = json.loads(json_match.group(1))
            log(f"Videos encontrados via HTML Embed: {len(videos)}")
        except Exception as e:
            log(f"Error procesando JSON de embed HTML: {e}")

    # Método 2: Si el método 1 falla, probar la API de metadatos
    if not videos:
        meta_url = f"https://my.mail.ru/v/api/video/item/{video_id}"
        data_str = fetch(meta_url)
        if data_str:
            try:
                data = json.loads(data_str)
                videos = data.get('videos', [])
                log(f"Videos encontrados via API: {len(videos)}")
            except Exception as e:
                log(f"Error procesando JSON de API: {e}")

    if not videos:
        log("No se pudo obtener ninguna fuente de video valida para Mail.ru")
        return None

    # Seleccionar la mejor calidad disponible
    try:
        best_video = sorted(videos, key=lambda x: int(str(x.get('key', '0')).replace('p', '') or 0), reverse=True)[0]
    except:
        best_video = videos[0]

    stream_url = best_video.get('url')
    if stream_url:
        if stream_url.startswith('//'):
            stream_url = 'https:' + stream_url
            
        log(f"Enlace de streaming obtenido: {stream_url}")
        
        # Formatear cabeceras para Kodi
        headers = {
            'User-Agent': UA_STR,
            'Referer': 'https://my.mail.ru/'
        }
        return stream_url + '|' + urllib.parse.urlencode(headers)

    return None

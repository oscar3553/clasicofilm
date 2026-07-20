import re, urllib.request, json, urllib.parse

UA_STR = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
UA = {'User-Agent': UA_STR}

def fetch(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        return urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
    except:
        return ""

def extract(post_url):
    h = fetch(post_url)
    streams = []
    
    # Extraer Dzen.ru
    dzen_links = set(re.findall(r'https://dzen\.ru/embed/[^"\'\>\s]+', h))
    for link in dzen_links:
        streams.append(('Dzen', link))
        
    # Extraer Mail.ru (soporta varios formatos de enlace embed)
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
    # Extrae el ID del video
    m = re.search(r'/embed/(\d+)', url)
    if not m:
        return None
    video_id = m.group(1)
    
    videos = []
    
    # Intento 1: API Directa de Mail.ru
    meta_url = f"https://my.mail.ru/v/api/video/item/{video_id}"
    data_str = fetch(meta_url)
    try:
        data = json.loads(data_str)
        videos = data.get('videos', [])
    except:
        videos = []
        
    # Intento 2: Si la API no devuelve vídeos, parsear el HTML de la página embed
    if not videos:
        embed_html = fetch(f"https://my.mail.ru/video/embed/{video_id}")
        m_json = re.search(r'"videos"\s*:\s*(\[[^\]]+\])', embed_html)
        if m_json:
            try:
                videos = json.loads(m_json.group(1))
            except:
                pass

    if videos:
        # Ordenar por mejor calidad (ej. 1080p > 720p > 480p)
        try:
            best_video = sorted(videos, key=lambda x: int(str(x.get('key', '0')).replace('p', '') or 0), reverse=True)[0]
        except:
            best_video = videos[0]
            
        stream_url = best_video.get('url')
        if stream_url:
            if stream_url.startswith('//'):
                stream_url = 'https:' + stream_url
            
            # Añadir cabeceras para que el reproductor de Kodi supere la protección del servidor CDN
            headers = {
                'User-Agent': UA_STR,
                'Referer': 'https://my.mail.ru/'
            }
            return stream_url + '|' + urllib.parse.urlencode(headers)

    return None

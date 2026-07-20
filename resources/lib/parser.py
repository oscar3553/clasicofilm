import re, urllib.request, json

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

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
        
    # Extraer Mail.ru / my.mail.ru
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
    # Extrae el ID del video desde la URL de Mail.ru y consulta su metadata JSON
    m = re.search(r'/embed/([^"\'\>\s]+)', url)
    if not m:
        return None
    video_id = m.group(1)
    
    meta_url = f"https://my.mail.ru/v/api/video/item/{video_id}"
    data_str = fetch(meta_url)
    try:
        data = json.loads(data_str)
        videos = data.get('videos', [])
        if videos:
            # Seleccionamos la máxima calidad disponible
            best_video = sorted(videos, key=lambda x: int(x.get('key', '0').replace('p', '') or 0), reverse=True)[0]
            stream_url = best_video.get('url')
            if stream_url:
                if stream_url.startswith('//'):
                    stream_url = 'https:' + stream_url
                return stream_url
    except:
        pass
    return None

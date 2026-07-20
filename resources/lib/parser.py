import re, urllib.request, xbmc
import resolveurl

UA_STR = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def log(msg):
    xbmc.log(f"[Clasicofilm Parser] {msg}", xbmc.LOGINFO)

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA_STR})
        return urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
    except Exception as e:
        log(f"Error cargando pagina: {e}")
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
    log(f"Resolviendo Mail.ru mediante ResolveURL para URL: {url}")
    try:
        # Comprueba si ResolveURL reconoce y gestiona el enlace
        if resolveurl.relevanturl(url):
            resolved_url = resolveurl.resolve(url)
            log(f"ResolveURL obtuvo con exito el enlace: {resolved_url}")
            return resolved_url
        else:
            log("ResolveURL indica que no es un enlace compatible")
    except Exception as e:
        log(f"Error procesando Mail.ru con ResolveURL: {e}")
        
    return None

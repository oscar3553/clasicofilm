import urllib.parse, xbmcplugin, xbmcgui, xbmc
from .feed import latest, labels, by_label, search
from .parser import extract, resolve_dzen, resolve_mailru

HANDLE = None

def movie_item(m, argv):
    label = f"[COLOR gold]{m['title']}[/COLOR]"
    if m['year']: label += f" ({m['year']})"
    li = xbmcgui.ListItem(label=label)
    
    li.setInfo('video', {
        'title': m['title'], 'plot': m['plot'], 'director': m['director'], 
        'cast': m['cast'], 'mediatype': 'movie', 'year': int(m['year']) if m['year'] else 0
    })
    
    li.setArt({
        'thumb': m['image'], 'poster': m['image'], 
        'icon': 'special://home/addons/plugin.video.clasicofilm/icon.png',
        'fanart': 'special://home/addons/plugin.video.clasicofilm/fanart.jpg'
    })
    
    li.setProperty('IsPlayable', 'false')
    u = f"{argv[0]}?action=info_and_play&url={urllib.parse.quote(m['url'])}"
    xbmcplugin.addDirectoryItem(HANDLE, u, li, False)

def run(argv):
    global HANDLE
    HANDLE = int(argv[1]); p = urllib.parse.parse_qs(argv[2][1:]); a = p.get('action', [''])[0]
    
    if a == 'info_and_play':
        xbmc.executebuiltin('Action(Info)') # Forzamos la ficha al hacer click
        url_post = urllib.parse.unquote(p['url'][0])
        
        # 1. Extraer todos los servidores disponibles en el post
        src = extract(url_post)
        
        if not src:
            xbmcgui.Dialog().notification("Clasicofilm", "No se encontraron servidores", xbmcgui.NOTIFICATION_ERROR)
            return

        selected_stream = None

        # 2. Si hay más de un servidor, mostrar menú de selección
        if len(src) > 1:
            options = [f"Servidor: {name}" for name, url in src]
            idx = xbmcgui.Dialog().select("Selecciona Servidor", options)
            if idx == -1:
                return # El usuario canceló el menú
            selected_stream = src[idx]
        else:
            selected_stream = src[0]

        srv_name, srv_url = selected_stream
        final_url = None
        is_mpd = False

        # 3. Resolver la URL según el servidor elegido
        if srv_name == 'Mail.ru':
            final_url = resolve_mailru(srv_url)
            is_mpd = True
        elif srv_name == 'Dzen':
            final_url = resolve_dzen(srv_url)

        # 4. Enviar a reproducir en Kodi
        if final_url:
            item = xbmcgui.ListItem(path=final_url)
            
            # Configurar InputStream Adaptive si es Mail.ru (.mpd)
            if is_mpd or '.mpd' in final_url:
                item.setProperty('inputstream', 'inputstream.adaptive')
                item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                headers = "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)&Referer=https://my.mail.ru/"
                item.setProperty('inputstream.adaptive.stream_headers', headers)
            
            xbmcplugin.setResolvedUrl(HANDLE, True, item)
        else:
            xbmcgui.Dialog().notification("Clasicofilm", f"Error al resolver {srv_name}", xbmcgui.NOTIFICATION_ERROR)
            
        return
        
    if a == 'latest':
        items, n_url = latest(p.get('next_page', [None])[0])
        xbmcplugin.setContent(HANDLE, 'movies')
        for m in items: movie_item(m, argv)
        if n_url:
            u = f"{argv[0]}?action=latest&next_page={urllib.parse.quote(n_url)}"
            xbmcplugin.addDirectoryItem(HANDLE, u, xbmcgui.ListItem(label='[COLOR gold]➡ SIGUIENTE PÁGINA[/COLOR]'), True)
        xbmcplugin.endOfDirectory(HANDLE); return

    if a == 'genres':
        for l in labels():
            li = xbmcgui.ListItem(label=f"[COLOR gold]•[/COLOR] {l}")
            li.setArt({'icon': 'special://home/addons/plugin.video.clasicofilm/icon.png'})
            xbmcplugin.addDirectoryItem(HANDLE, f"{argv[0]}?action=genre&name={urllib.parse.quote(l)}", li, True)
        xbmcplugin.endOfDirectory(HANDLE); return

    if a == 'genre':
        name = p['name'][0]
        items, n_url = by_label(name, p.get('next_page', [None])[0])
        xbmcplugin.setContent(HANDLE, 'movies')
        for m in items: movie_item(m, argv)
        xbmcplugin.endOfDirectory(HANDLE); return

    if a == 'search':
        kb = xbmcgui.Dialog().input('Buscar película...', type=xbmcgui.INPUT_ALPHANUM)
        if kb:
            items, _ = search(kb)
            xbmcplugin.setContent(HANDLE, 'movies')
            for m in items: movie_item(m, argv)
            xbmcplugin.endOfDirectory(HANDLE)
        return

    # MENÚ PRINCIPAL
    menu = [('🎬 ÚLTIMAS NOVEDADES', 'latest'), ('🎭 GÉNEROS', 'genres'), ('🔍 BUSCAR', 'search')]
    for label, act in menu:
        li = xbmcgui.ListItem(label=label)
        li.setArt({'icon': 'special://home/addons/plugin.video.clasicofilm/icon.png'})
        xbmcplugin.addDirectoryItem(HANDLE, f"{argv[0]}?action={act}", li, True)
    xbmcplugin.endOfDirectory(HANDLE)

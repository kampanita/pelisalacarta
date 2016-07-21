# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# tvalacarta
# XBMC Launcher (xbmc / xbmc-dharma / boxee)
# http://blog.tvalacarta.info/plugin-xbmc/
# ------------------------------------------------------------

import os
import re
import sys
import urllib2

from core import channeltools
from core import config
from core import logger
from core import scrapertools
from core.item import Item
from platformcode import library
from platformcode import xbmctools


def start():
    ''' Primera funcion que se ejecuta al entrar en el plugin.
    Dentro de esta funcion deberian ir todas las llamadas a las
    funciones que deseamos que se ejecuten nada mas abrir el plugin.

    '''
    logger.info("pelisalacarta.platformcode.launcher start")

    # Test if all the required directories are created
    config.verify_directories_created()

def run():
    logger.info("pelisalacarta.platformcode.launcher run")

    # Extract item from sys.argv
    if sys.argv[2]:
      item = Item().fromurl(sys.argv[2])
      params = ""

    else:
      item = Item(action= "selectchannel")
      params = ""

    logger.info(item.tostring())

    server_white_list = []
    server_black_list = []
    if config.get_setting('filter_servers') == 'true':
        server_white_list, server_black_list = set_server_list()

    try:
        # Default action: open channel and launch mainlist function
        if ( item.action=="selectchannel" ):
            import channelselector
            itemlist = channelselector.mainlist(params, item.url, item.category)

            # Verifica actualizaciones solo en el primer nivel
            if config.get_setting("updatecheck2") == "true":
              logger.info("channelselector.mainlist Verificar actualizaciones activado")
              from core import updater
              try:
                version = updater.checkforupdates()

                if version:
                  import xbmcgui
                  advertencia = xbmcgui.Dialog()
                  advertencia.ok("Versión "+version+" disponible","Ya puedes descargar la nueva versión del plugin\ndesde el listado principal")
                  itemlist.insert(0,Item(title="Descargar version "+version, version=version, channel="updater", action="update", thumbnail=channelselector.get_thumbnail_path() + "Crystal_Clear_action_info.png"))
              except:
                import xbmcgui
                advertencia = xbmcgui.Dialog()
                advertencia.ok("No se puede conectar","No ha sido posible comprobar","si hay actualizaciones")
                logger.info("channelselector.mainlist Fallo al verificar la actualización")

            else:
              logger.info("channelselector.mainlist Verificar actualizaciones desactivado")

            xbmctools.renderItems(itemlist, item)

        # Actualizar version
        elif (item.action=="update"):

            from core import updater
            updater.update(item)
            if config.get_system_platform()!="xbox":
                import xbmc
                xbmc.executebuiltin( "Container.Refresh" )

        elif (item.action=="channeltypes"):
            import channelselector
            itemlist = channelselector.channeltypes(params,item.url,item.category)

            xbmctools.renderItems(itemlist, item)

        elif (item.action=="listchannels"):
            import channelselector
            itemlist = channelselector.listchannels(params,item.url,item.category)

            xbmctools.renderItems(itemlist, item)

        # El resto de acciones vienen en el parámetro "action", y el canal en el parámetro "channel"
        else:

            if item.action=="mainlist":
                # Parental control
                can_open_channel = False

                # If it is an adult channel, and user has configured pin, asks for it
                if channeltools.is_adult(item.channel) and config.get_setting("adult_pin")!="":

                    import xbmc
                    keyboard = xbmc.Keyboard("","PIN para canales de adultos",True)
                    keyboard.doModal()

                    if (keyboard.isConfirmed()):
                        tecleado = keyboard.getText()
                        if tecleado==config.get_setting("adult_pin"):
                            can_open_channel = True

                # All the other cases can open the channel
                else:
                    can_open_channel = True

                if not can_open_channel:
                    return

            if item.action=="mainlist" and config.get_setting("updatechannels")=="true":
                try:
                    from core import updater
                    actualizado = updater.updatechannel(item.channel)

                    if actualizado:
                        import xbmcgui
                        advertencia = xbmcgui.Dialog()
                        advertencia.ok("plugin",channel_name,config.get_localized_string(30063))
                except:
                    pass

            # La acción puede estar en el core, o ser un canal regular. El buscador es un canal especial que está en pelisalacarta
            regular_channel_path = os.path.join(config.get_runtime_path(), 'channels', item.channel+".py")
            core_channel_path = os.path.join(config.get_runtime_path(), 'core', item.channel+".py")
            logger.info("pelisalacarta.platformcode.launcher regular_channel_path=%s" % regular_channel_path)
            logger.info("pelisalacarta.platformcode.launcher core_channel_path=%s" % core_channel_path)

            if (item.channel == "personal" or item.channel == "personal2" or item.channel == "personal3" or
                    item.channel == "personal4" or item.channel == "personal5"):
                import channels.personal as channel
            elif os.path.exists(regular_channel_path):
                channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])

            elif os.path.exists(core_channel_path):
                channel = __import__('core.%s' % item.channel, fromlist=["core.%s" % item.channel])

            logger.info("pelisalacarta.platformcode.launcher running channel {0} {1}".format(
                channel.__name__, channel.__file__))

            generico = False
            # Esto lo he puesto asi porque el buscador puede ser generico o normal, esto estará asi hasta que todos los canales sean genericos
            if item.category == "Buscador_Generico":
                generico = True
            else:
                try:
                    generico = channel.isGeneric()
                except:
                    generico = False

            if not generico:
                logger.info("pelisalacarta.platformcode.launcher xbmc native channel")
                if item.action == "strm":

                    xbmctools.playstrm(params, item.url, item.category)
                else:
                    getattr(channel, item.action)(params, item.url, item.category)
            else:
                logger.info("pelisalacarta.platformcode.launcher multiplatform channel")

                if item.action == "play":
                    logger.info("pelisalacarta.platformcode.launcher play")
                    # logger.debug(str(item.infoLabels))

                    # Marcar como vistos los items del canal Biblioteca
                    id_video = 0
                    category = ''
                    if 'infoLabels' in item:
                        if 'episodeid' in item.infoLabels and item.infoLabels['episodeid']:
                            category = 'Series'
                            id_video = item.infoLabels['episodeid']
                        elif 'movieid' in item.infoLabels and item.infoLabels['movieid']:
                            category = 'Movies'
                            id_video = item.infoLabels['movieid']

                    # Si el canal tiene una acción "play" tiene prioridad
                    if hasattr(channel, 'play'):
                        logger.info("pelisalacarta.platformcode.launcher executing channel 'play' method")
                        itemlist = channel.play(item)
                        if len(itemlist) > 0:
                            item = itemlist[0]
                            xbmctools.play_video(item)
                            if id_video != 0:
                                library.mark_as_watched(category, id_video)
                        else:
                            import xbmcgui
                            ventana_error = xbmcgui.Dialog()
                            ok = ventana_error.ok("plugin", "No hay nada para reproducir")
                    else:
                        logger.info("pelisalacarta.platformcode.launcher no channel 'play' method, executing core method")
                        xbmctools.play_video(item)
                        if id_video != 0:
                            library.mark_as_watched(category, id_video)

                elif item.action == "play_from_library":
                    play_from_library(item, channel, server_white_list, server_black_list)

                elif item.action == "add_pelicula_to_library":
                    add_pelicula_to_library(item)

                elif item.action == "add_serie_to_library":
                    add_serie_to_library(item, channel)

                elif item.action=="download_all_episodes":
                    import downloadtools
                    downloadtools.download_all_episodes(item,channel)

                elif item.action=="search":
                    logger.info("pelisalacarta.platformcode.launcher search")
                    import xbmc
                    keyboard = xbmc.Keyboard("")
                    keyboard.doModal()
                    if (keyboard.isConfirmed()):
                        tecleado = keyboard.getText()
                        tecleado = tecleado.replace(" ", "+")
                        itemlist = channel.search(item,tecleado)
                    else:
                        itemlist = []
                    xbmctools.renderItems(itemlist, item)

                else:
                    if item.action != "findvideos":
                        try:
                            logger.info("pelisalacarta.platformcode.launcher executing channel '"+item.action+"' method")
                            itemlist = getattr(channel, item.action)(item)
                        except:
                            #Error al ejecutar la accion o item tipo Tag
                            logger.info("pelisalacarta.platformcode.launcher no se ha podido ejecutar la accion %s" %item.action)
                            return
                    else:

                        # Intenta ejecutar una posible funcion "findvideos" del canal
                        if hasattr(channel, 'findvideos'):
                            itemlist = getattr(channel, item.action)(item)

                            if config.get_setting('filter_servers') == 'true':
                                itemlist = filtered_servers(itemlist, server_white_list, server_black_list)

                        # Si no funciona, lanza el método genérico para detectar vídeos
                        else:
                            logger.info("pelisalacarta.platformcode.launcher no channel 'findvideos' method, executing core method")
                            from core import servertools
                            itemlist = servertools.find_video_items(item)
                            if config.get_setting('filter_servers') == 'true':
                                itemlist = filtered_servers(itemlist, server_white_list, server_black_list)

                        # Propagar las infoLabels
                        if 'infoLabels' in item:
                            item.infoLabels.pop('title') # Excepto el titulo
                            new_itemlist = itemlist[:]
                            itemlist = []
                            for i in new_itemlist:
                                itemlist.append(i.clone(infoLabels=item.infoLabels))


                        from platformcode import subtitletools
                        subtitletools.saveSubtitleName(item)

                    # Activa el modo biblioteca para todos los canales genéricos, para que se vea el argumento
                    import xbmcplugin

                    handle = sys.argv[1]
                    xbmcplugin.setContent(int( handle ),"movies")

                    # Añade los items a la lista de XBMC
                    if type(itemlist) == list and itemlist:
                      xbmctools.renderItems(itemlist, item)

    except urllib2.URLError,e:
        import traceback
        from pprint import pprint
        exc_type, exc_value, exc_tb = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        for line in lines:
            line_splits = line.split("\n")
            for line_split in line_splits:
                logger.error(line_split)

        import xbmcgui
        ventana_error = xbmcgui.Dialog()
        # Agarra los errores surgidos localmente enviados por las librerias internas
        if hasattr(e, 'reason'):
            logger.info("Razon del error, codigo: %d , Razon: %s" %(e.reason[0],e.reason[1]))
            texto = config.get_localized_string(30050) # "No se puede conectar con el sitio web"
            ok = ventana_error.ok ("plugin", texto)
        # Agarra los errores con codigo de respuesta del servidor externo solicitado
        elif hasattr(e,'code'):
            logger.info("codigo de error HTTP : %d" %e.code)
            texto = (config.get_localized_string(30051) % e.code) # "El sitio web no funciona correctamente (error http %d)"
            ok = ventana_error.ok ("plugin", texto)

    except:
        import traceback
        import xbmcgui
        logger.error('::ERROR::'+traceback.format_exc())
        
        patron = 'File "'+os.path.join(config.get_runtime_path(),"channels","").replace("\\","\\\\")+'([^.]+)\.py"'
        canal = scrapertools.find_single_match(traceback.format_exc(),patron)
        
        if canal:
            
            xbmcgui.Dialog().ok(
                "Error inesperado en el canal " + canal,
                "Esto suele pasar cuando hay un fallo de conexión, cuando la web del canal "
                "ha cambiado su estructura, o simplemente "
                "porque hay algo mal en pelisalacarta.\nPara saber más detalles, consulta el log.")
        else:
            xbmcgui.Dialog().ok(
                "Se ha producido un error en pelisalacarta",
                "Comprueba el log para ver mas detalles del error." )
             

        logger.info('pelisalacarta.launcher Comprobando de correo activado')
        if config.get_setting('sendlog') == 'true':
           logger.info('pelisalacarta.launcher Envio de correo activado')
           from core import pastebin
           import xbmc
           
           to = config.get_setting('mailuser')
                      
           subject = "Log KODI"
           text = "Attached Kodi log"
           
           if config.is_xbmc():
               # se usa xbmc y el special... para obtener el log           
               attach = xbmc.translatePath(os.path.join("special://logpath", 'kodi.log'))
               data = ''
               try:
               	   with open(attach, 'r') as myfile:
               	       i=0
               	       for line in myfile:
               	       	    if re.search('                                          ',line):
                                #capturo solo las lineas con error, para acortar el Log. No es muy elegante pero no veía otra manera sin tocar el logger.
                                data=data +str(i)+': '+ line.replace('                                          ','')
                                i=i+1
                                
                   # TODO Buscar Servidor Alternativo a PasteBin.
                   
                   
                   # Hecho, pero con mi "key" de desarrollador solo deja unos pocos envios cada 24 horas
                   # no es factible usar el servicio gratuito. Aunque funcionar, funciona.
                   #                   
                   #x = pastebin.PastebinAPI()
                   # 
                   #url=x.paste(api_dev_key='9a2671bc31c64d698cd908b024576239',  api_paste_code=data, api_user_key = None, paste_name = None, paste_format = None, paste_private = None, paste_expire_date = None)
                   
                   #xbmcgui.Dialog().ok("Apunta la URL del log: ",url)
                   #logger.info('pelisalacarta PASTEBIN: '+url)
                   
                   from core import sendmail
                   

                   try:
                   	   sendmail.mail(to, 'Log pelisalacarta', data)
                       #sendmail.mail(to, 'Log pelisalacarta', url)
                   except:
                   	   
                       logger.error(traceback.format_exc())
               	       logger.error('pelisalacarta.launcher Se ha producido un error enviando el correo')
                       xbmcgui.Dialog().ok(
                            "Se ha producido un error en pelisalacarta enviando el Log por mail",
                            "Comprueba el log para ver mas detalles del error." ) 
               
               except:
               	   logger.error(traceback.format_exc())
               	   logger.error('pelisalacarta.launcher Se ha producido un error enviando el correo')
                   xbmcgui.Dialog().ok(
                        "Se ha producido un error en pelisalacarta enviando el Log a Pastebin",
                        "Comprueba el log para ver mas detalles del error." ) 
            


def set_server_list():
    logger.info("pelisalacarta.platformcode.launcher.set_server_list start")
    server_white_list = []
    server_black_list = []

    if len(config.get_setting('whitelist')) > 0:
        server_white_list_key = config.get_setting('whitelist').replace(', ', ',').replace(' ,', ',')
        server_white_list = re.split(',', server_white_list_key)

    if len(config.get_setting('blacklist')) > 0:
        server_black_list_key = config.get_setting('blacklist').replace(', ', ',').replace(' ,', ',')
        server_black_list = re.split(',', server_black_list_key)

    logger.info("set_server_list whiteList %s" % server_white_list)
    logger.info("set_server_list blackList %s" % server_black_list)
    logger.info("pelisalacarta.platformcode.launcher.set_server_list end")

    return server_white_list, server_black_list

def filtered_servers(itemlist, server_white_list, server_black_list):
    logger.info("pelisalacarta.platformcode.launcher.filtered_servers start")
    new_list = []
    white_counter = 0
    black_counter = 0

    logger.info("filtered_servers whiteList %s" % server_white_list)
    logger.info("filtered_servers blackList %s" % server_black_list)

    if len(server_white_list) > 0:
        logger.info("filtered_servers whiteList")
        for item in itemlist:
            logger.info("item.title " + item.title)
            if any(server in item.title for server in server_white_list):
                # if item.title in server_white_list:
                logger.info("found")
                new_list.append(item)
                white_counter += 1
            else:
                logger.info("not found")

    if len(server_black_list) > 0:
        logger.info("filtered_servers blackList")
        for item in itemlist:
            logger.info("item.title " + item.title)
            if any(server in item.title for server in server_black_list):
                # if item.title in server_white_list:
                logger.info("found")
                black_counter += 1
            else:
                new_list.append(item)
                logger.info("not found")

    logger.info("whiteList server %s has #%d rows" % (server_white_list, white_counter))
    logger.info("blackList server %s has #%d rows" % (server_black_list, black_counter))

    if len(new_list) == 0:
        new_list = itemlist
    logger.info("pelisalacarta.platformcode.launcher.filtered_servers end")

    return new_list

def play_from_library(item, channel, server_white_list, server_black_list):
    logger.info("pelisalacarta.platformcode.launcher play_from_library")

    category = item.category

    logger.info("item.server=#"+item.server+"#")
    # Ejecuta find_videos, del canal o común
    try:
        itemlist = getattr(channel, "findvideos")(item)

        if config.get_setting('filter_servers') == 'true':
            itemlist = filtered_servers(itemlist, server_white_list, server_black_list)

    except:
        from core import servertools
        itemlist = servertools.find_video_items(item)

        if config.get_setting('filter_servers') == 'true':
            itemlist = filtered_servers(itemlist, server_white_list, server_black_list)

    if len(itemlist) > 0:
        # El usuario elige el mirror
        opciones = []
        for item in itemlist:
            opciones.append(item.title)

        import xbmcgui
        dia = xbmcgui.Dialog()
        seleccion = dia.select(config.get_localized_string(30163), opciones)
        elegido = itemlist[seleccion]

        if seleccion == -1:
            return
    else:
        elegido = item

    # Ejecuta el método play del canal, si lo hay
    try:
        itemlist = channel.play(elegido)
        item = itemlist[0]
    except:
        item = elegido
    logger.info("Elegido %s (sub %s)" % (item.title, item.subtitle))

    xbmctools.play_video(item, strmfile=True)
    library.mark_as_watched(category, 0)


def add_pelicula_to_library(item):
    logger.info("pelisalacarta.platformcode.launcher add_pelicula_to_library")

    new_item = item.clone(action="play_from_library", category="Cine")
    library.savelibrary(new_item)


def add_serie_to_library(item, channel):
    logger.info("pelisalacarta.platformcode.launcher add_serie_to_library, show=#"+item.show+"#")

    import xbmcgui

    # Esta marca es porque el item tiene algo más aparte en el atributo "extra"
    action = item.extra
    if "###" in item.extra:
        action = item.extra.split("###")[0]
        item.extra = item.extra.split("###")[1]

    # Obtiene el listado desde el que se llamó
    itemlist = getattr(channel, action)(item)

    # TODO arreglar progress dialog
    # Progreso
    p_dialog = xbmcgui.DialogProgress()
    ret = p_dialog.create('pelisalacarta', 'Añadiendo episodios...')
    p_dialog.update(0, 'Añadiendo episodio...')
    totalepisodes = len(itemlist)

    logger.info("[launcher.py] Total Episodios:"+str(totalepisodes))
    i = 0
    errores = 0
    nuevos = 0
    for item in itemlist:
        logger.info("title:: {}".format(item.title))
        i += 1
        p_dialog.update(i*100/totalepisodes, 'Añadiendo episodio...', item.title)
        logger.info("pelisalacarta.platformcode.launcher add_serie_to_library, title="+item.title)
        if p_dialog.iscanceled():
            return

        try:
            # Añade todos menos el que dice "Añadir esta serie..." o "Descargar esta serie..."
            if item.action != "add_serie_to_library" and item.action != "download_all_episodes":

                new_item = item.clone(action="play_from_library", category="Series")
                res = library.savelibrary(new_item)
                if res >= 0:
                    nuevos += res
                else:
                    errores += 1

        except IOError:
            import sys
            for line in sys.exc_info():
                logger.error("%s" % line)
            logger.info("pelisalacarta.platformcode.launcherError al grabar el archivo "+item.title)
            errores += 1

    p_dialog.close()

    # Actualizacion de la biblioteca
    itemlist = []
    if errores > 0:
        itemlist.append(Item(title="ERROR, la serie NO se ha añadido a la biblioteca o lo ha hecho incompleta",
                             channel=item.channel))
        logger.info("[launcher.py] No se pudo añadir "+str(errores)+" episodios")
    else:
        itemlist.append(Item(title="La serie se ha añadido a la biblioteca", channel=item.channel))
        logger.info("[launcher.py] Ningún error al añadir "+str(errores)+" episodios")

    xbmctools.renderItems(itemlist, item)

    library.save_tvshow_in_file(item)

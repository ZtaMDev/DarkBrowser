"""Translation module for internationalization support"""

# Spanish translations
ES_TRANSLATIONS = {
    # Menu items
    "File": "Archivo",
    "Edit": "Editar",
    "View": "Ver",
    "Tools": "Herramientas",
    "Help": "Ayuda",
    "New Tab": "Nueva Pestaña",
    "New Window": "Nueva Ventana",
    "New Incognito Window": "Nueva Ventana de Incógnito",
    "Find": "Buscar",
    "Settings": "Configuración",
    "Downloads": "Descargas",
    "History": "Historial",
    "Bookmarks": "Favoritos",
    "Extensions": "Extensiones",
    "About": "Acerca de",
    "Quit": "Salir",
    "Reload": "Recargar",
    "Force Reload": "Forzar Recarga",
    "Toggle Fullscreen": "Pantalla Completa",
    "Back": "Atrás",
    "Forward": "Adelante",
    
    # Settings page
    "Settings": "Configuración",
    "Search engine": "Buscador por defecto",
    "Home page": "Página de inicio",
    "Favorites bar": "Barra de favoritos",
    "Show": "Mostrar",
    "Hide": "Ocultar",
    "Language": "Idioma",
    "Clear data": "Limpiar datos",
    
    # Downloads page
    "Downloads": "Descargas",
    "Clear all": "Limpiar todo",
    "No downloads": "No hay descargas",
    "Open file": "Abrir archivo",
    "Open folder": "Abrir carpeta",
    "Remove": "Eliminar",
    
    # Home page
    "Home": "Inicio",
    "Quick Links": "Enlaces Rápidos",
    "Recent Tabs": "Pestañas Recientes",
    "Bookmarks": "Favoritos",
    
    # Tab context menu
    "Close": "Cerrar",
    "Close Others": "Cerrar Otras",
    "Close All": "Cerrar Todas",
    "Duplicate": "Duplicar",
    "Pin Tab": "Fijar Pestaña",
    "Unpin Tab": "Desfijar Pestaña",
    "Mute Tab": "Silenciar Pestaña",
    "Unmute Tab": "Activar Sonido",
    "Bookmark Tab": "Añadir a Favoritos",
    "Remove Bookmark": "Quitar de Favoritos",
    
    # Messages
    "New Tab": "Nueva Pestaña",
    "Loading...": "Cargando...",
    "Error": "Error",
    "Warning": "Advertencia",
    "Information": "Información",
    "Confirm": "Confirmar",
    "Cancel": "Cancelar",
    "OK": "Aceptar",
    "Yes": "Sí",
    "No": "No",
    
    # Other
    "Search": "Buscar",
    "URL": "URL",
    "Title": "Título",
    "Date": "Fecha",
    "Size": "Tamaño",
    "Status": "Estado",
    "Progress": "Progreso",
    "Speed": "Velocidad",
    "Time": "Tiempo",
    "Remaining": "Restante",
}

# English translations (default)
EN_TRANSLATIONS = {
    # Menu items
    "File": "File",
    "Edit": "Edit",
    "View": "View",
    "Tools": "Tools",
    "Help": "Help",
    "New Tab": "New Tab",
    "New Window": "New Window",
    "New Incognito Window": "New Incognito Window",
    "Find": "Find",
    "Settings": "Settings",
    "Downloads": "Downloads",
    "History": "History",
    "Bookmarks": "Bookmarks",
    "Extensions": "Extensions",
    "About": "About",
    "Quit": "Quit",
    "Reload": "Reload",
    "Force Reload": "Force Reload",
    "Toggle Fullscreen": "Toggle Fullscreen",
    "Back": "Back",
    "Forward": "Forward",
    
    # Settings page
    "Settings": "Settings",
    "Search engine": "Default search engine",
    "Home page": "Home page",
    "Favorites bar": "Favorites bar",
    "Show": "Show",
    "Hide": "Hide",
    "Language": "Language",
    "Clear data": "Clear data",
    
    # Downloads page
    "Downloads": "Downloads",
    "Clear all": "Clear all",
    "No downloads": "No downloads",
    "Open file": "Open file",
    "Open folder": "Open folder",
    "Remove": "Remove",
    
    # Home page
    "Home": "Home",
    "Quick Links": "Quick Links",
    "Recent Tabs": "Recent Tabs",
    "Bookmarks": "Bookmarks",
    
    # Tab context menu
    "Close": "Close",
    "Close Others": "Close Others",
    "Close All": "Close All",
    "Duplicate": "Duplicate",
    "Pin Tab": "Pin Tab",
    "Unpin Tab": "Unpin Tab",
    "Mute Tab": "Mute Tab",
    "Unmute Tab": "Unmute Tab",
    "Bookmark Tab": "Bookmark Tab",
    "Remove Bookmark": "Remove Bookmark",
    
    # Messages
    "New Tab": "New Tab",
    "Loading...": "Loading...",
    "Error": "Error",
    "Warning": "Warning",
    "Information": "Information",
    "Confirm": "Confirm",
    "Cancel": "Cancel",
    "OK": "OK",
    "Yes": "Yes",
    "No": "No",
    
    # Other
    "Search": "Search",
    "URL": "URL",
    "Title": "Title",
    "Date": "Date",
    "Size": "Size",
    "Status": "Status",
    "Progress": "Progress",
    "Speed": "Speed",
    "Time": "Time",
    "Remaining": "Remaining",
}

def get_translation(language: str, text: str) -> str:
    """Get translation for given language and text"""
    if language == "es":
        return ES_TRANSLATIONS.get(text, text)
    else:
        return EN_TRANSLATIONS.get(text, text)

def t(language: str, text: str) -> str:
    """Shorthand for get_translation"""
    return get_translation(language, text)

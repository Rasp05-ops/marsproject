from app.mcp_servers.academics import academics_server
from app.mcp_servers.cafeteria import cafeteria_server
from app.mcp_servers.events import events_server
from app.mcp_servers.library import library_server
from app.mcp_servers.notices import notices_server

SERVERS = {
    "library.search_books": library_server.search_books,
    "library.stats": library_server.stats,
    "cafeteria.get_menu": cafeteria_server.get_menu,
    "cafeteria.all_menus": cafeteria_server.all_menus,
    "events.list_events": events_server.list_events,
    "academics.summary": academics_server.summary,
    "academics.low_attendance": academics_server.low_attendance,
    "notices.list_notices": notices_server.list_notices,
}

"""
Cliente ligero para la Steam Web API.

La lógica de `get_owned_games` replica exactamente la función usada en
`Proyecto_dcd_apis_JMGO.ipynb` (celda "Tiempos Jugados por cada Jugador"),
para que las horas jugadas que ve el modelo en producción se calculen
igual que las horas usadas para entrenarlo (minutos -> horas, redondeo a 1 decimal).
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

STEAM_API_KEY = os.getenv("STEAM_API_KEY")

OWNED_GAMES_URL = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
PLAYER_SUMMARY_URL = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
VANITY_URL_RESOLVE = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"


class SteamAPIError(Exception):
    pass


def resolve_steam_id(user_input: str) -> str:
    """Acepta un SteamID64 numérico o un vanity name/URL y devuelve el SteamID64."""
    user_input = (user_input or "").strip()
    if not user_input:
        raise SteamAPIError("Ingresa un Steam ID o nombre de perfil.")

    # Si ya viene como URL, extraer el último segmento
    if "steamcommunity.com" in user_input:
        user_input = user_input.rstrip("/").split("/")[-1]

    if user_input.isdigit() and len(user_input) >= 15:
        return user_input

    if not STEAM_API_KEY:
        raise SteamAPIError("No se puede resolver el nombre de perfil: falta STEAM_API_KEY.")

    params = {"key": STEAM_API_KEY, "vanityurl": user_input, "format": "json"}
    response = requests.get(VANITY_URL_RESOLVE, params=params, timeout=10)
    response.raise_for_status()
    data = response.json().get("response", {})
    if data.get("success") == 1 and data.get("steamid"):
        return data["steamid"]

    raise SteamAPIError(
        "No se encontró un SteamID64 válido para ese usuario. "
        "Prueba con el ID numérico de 17 dígitos (ver https://steamid.io)."
    )


def get_owned_games(steam_id: str, api_key: str = None):
    """
    Devuelve (juegos, meta) donde:
    - juegos: lista de dicts {appid, nombre, horas_totales, horas_2_semanas}
    - meta: dict con 'private' (bool) y 'game_count' (int)

    Misma transformación que en el notebook de obtención de datos: las horas
    vienen en minutos desde la API y se convierten a horas con 1 decimal.
    """
    api_key = api_key or STEAM_API_KEY
    if not api_key:
        raise SteamAPIError("Falta configurar STEAM_API_KEY en el archivo .env")

    params = {
        "key": api_key,
        "steamid": steam_id,
        "include_appinfo": True,
        "include_played_free_games": True,
        "format": "json",
    }
    response = requests.get(OWNED_GAMES_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    resp = data.get("response", {})
    if "games" not in resp:
        return [], {"private": True, "game_count": 0}

    games = resp["games"]
    resultado = []
    for g in games:
        resultado.append({
            "appid": g.get("appid"),
            "nombre": g.get("name"),
            "horas_totales": round(g.get("playtime_forever", 0) / 60, 1),
            "horas_2_semanas": round(g.get("playtime_2weeks", 0) / 60, 1) if "playtime_2weeks" in g else 0.0,
        })
    return resultado, {"private": False, "game_count": resp.get("game_count", len(resultado))}


def get_player_summary(steam_id: str, api_key: str = None):
    api_key = api_key or STEAM_API_KEY
    if not api_key:
        raise SteamAPIError("Falta configurar STEAM_API_KEY en el archivo .env")

    params = {"key": api_key, "steamids": steam_id, "format": "json"}
    response = requests.get(PLAYER_SUMMARY_URL, params=params, timeout=15)
    response.raise_for_status()
    players = response.json().get("response", {}).get("players", [])
    return players[0] if players else None


def steam_header_image(appid) -> str:
    return f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg"


def steam_capsule_image(appid) -> str:
    return f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/capsule_231x87.jpg"

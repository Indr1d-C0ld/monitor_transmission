#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import subprocess
import time
import datetime
import geoip2.database
import os
import sys

# =============================================================================
# CONFIGURAZIONE
# =============================================================================

TRANSMISSION_REMOTE_PATH = "/usr/bin/transmission-remote"  # path al binario transmission-remote
RPC_HOST = "127.0.0.1:9091"  # host:porta del demone Transmission (di solito 9091)
RPC_USER = "pi"        # le credenziali RPC impostate in /etc/transmission-daemon/settings.json
RPC_PASS = ""
TORRENT_IDS = ["all"]        # Se vuoi monitorare TUTTI i torrent, usa ["all"]
                             # Altrimenti puoi specificare una lista di ID, es: ["1", "2"]

GEOIP_DB_PATH = "/home/pi/geolite2_db/GeoLite2-City.mmdb"  # Dove si trova il DB GeoLite2

REFRESH_INTERVAL = 30        # Secondi tra un aggiornamento e l'altro

# Regex: matcha un IP IPv4 in forma base
IP_REGEX = re.compile(r'(\d{1,3}\.){3}\d{1,3}')

def is_stdout_a_tty():
    return sys.stdout.isatty()

# =============================================================================
# COLORI PER L'OUTPUT (Palette Migliorata)
# =============================================================================

if is_stdout_a_tty():
	RESET = "\033[0m"
	BOLD = "\033[1m"
	RED = "\033[31m"
	GREEN = "\033[32m"
	YELLOW = "\033[33m"
	BLUE = "\033[34m"
	MAGENTA = "\033[35m"
	CYAN = "\033[36m"
	WHITE = "\033[37m"
	ORANGE = "\033[38;5;208m"  # Colore arancione
	LIGHT_BLUE = "\033[38;5;153m"  # Colore blu chiaro
	LIGHT_GREEN = "\033[38;5;120m"  # Colore verde chiaro
else:
	RESET = ""
	BOLD = ""
	RED = ""
	GREEN = ""
	YELLOW = ""
	BLUE = ""
	MAGENTA = ""
	CYAN = ""
	WHITE = ""
	ORANGE = ""
	LIGHT_BLUE = ""
	LIGHT_GREEN = ""

# =============================================================================
# STRUTTURE DI DATI PER LE STATISTICHE
# =============================================================================

"""
Struttura stats:
stats = {
  'peers': {
    'ip1': {
      'count': <numero volte che abbiamo visto ip1>,
      'geo_info': {...},  # country, city, lat, lon
      'last_seen': <timestamp ultimo avvistamento>
    },
    'ip2': {...},
    ...
  },
  'hours': { 0: 10, 1: 12, ... }   # conteggio per fascia oraria
}
"""

stats = {
    'peers': {},
    'hours': {}
}

# =============================================================================
# FUNZIONI
# =============================================================================

def get_peers_list(torrent_id="all"):
    """
    Esegue transmission-remote per ottenere i peer di uno specifico torrent
    (o "all") e restituisce l'output come lista di stringhe (righe).
    """
    cmd = [
        TRANSMISSION_REMOTE_PATH,
        RPC_HOST,
        "-n", f"{RPC_USER}:{RPC_PASS}",
        "-t", str(torrent_id),
        "-pi"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        return lines
    except subprocess.CalledProcessError as e:
        print(f"{RED}Errore nell'eseguire: {' '.join(cmd)}\n{e}{RESET}")
        return []

def parse_peers_from_lines(lines):
    """
    Cerca righe simili a:
      IP               Done ...
      203.0.113.125    60% ...
    Estrae l'IP e lo restituisce in una lista.
    """
    found_ips = []
    for line in lines:
        match = IP_REGEX.search(line)
        if match:
            ip_address = match.group(0)
            found_ips.append(ip_address)
    return found_ips

def get_geolocation_info(ip_address, geo_reader):
    """
    Utilizza la libreria geoip2 per ottenere informazioni geografiche di base (paese, città, lat/long).
    Restituisce un dizionario con le info richieste o None se non disponibili.
    """
    try:
        response = geo_reader.city(ip_address)
        country = response.country.name
        city = response.city.name
        latitude = response.location.latitude
        longitude = response.location.longitude
        return {
            'country': country if country else "N/A",
            'city': city if city else "N/A",
            'latitude': latitude,
            'longitude': longitude
        }
    except:
        # Se l'IP non è presente nel DB, o c'è un errore, restituiamo None
        return None

def update_stats_with_peers(peer_ips, geo_reader):
    """
    Aggiorna la struttura stats con la lista di IP dei peer trovati.
    """
    current_time = datetime.datetime.now()
    hour = current_time.hour

    # Contiamo in 'hours' quante volte c'è un avvistamento in questa fascia oraria
    stats['hours'][hour] = stats['hours'].get(hour, 0) + len(peer_ips)

    for ip in peer_ips:
        # Se non l'abbiamo mai visto, lo aggiungiamo
        if ip not in stats['peers']:
            geo_info = get_geolocation_info(ip, geo_reader)
            stats['peers'][ip] = {
                'count': 0,
                'geo_info': geo_info,
                'last_seen': current_time
            }
        stats['peers'][ip]['count'] += 1
        stats['peers'][ip]['last_seen'] = current_time

def print_stats():
    """
    Pulisce lo schermo e stampa un breve riepilogo delle statistiche raccolte con colori.
    """
    # Pulisce lo schermo
    os.system('clear')

    # Header
    print(f"{BOLD}{CYAN}=== Riepilogo statistiche ==={RESET}")

    total_connections = sum(peer_data['count'] for peer_data in stats['peers'].values())
    unique_ips = len(stats['peers'])
    print(f"{GREEN}Totale avvistamenti IP (connessioni): {RESET}{total_connections}")
    print(f"{GREEN}IP unici incontrati: {RESET}{unique_ips}")

    # Conteggio per paese
    country_count = {}
    for ip, data in stats['peers'].items():
        geo = data['geo_info']
        if geo:
            country = geo['country']
            country_count[country] = country_count.get(country, 0) + data['count']
        else:
            country_count['Sconosciuto'] = country_count.get('Sconosciuto', 0) + data['count']

    print(f"\n{BOLD}{ORANGE}Connessioni per Paese:{RESET}")
    sorted_countries = sorted(country_count.items(), key=lambda x: x[1], reverse=True)
    for country, count in sorted_countries:
        print(f" {MAGENTA}- {country}: {count}{RESET}")

    # Fasce orarie
    print(f"\n{BOLD}{LIGHT_BLUE}Connessioni per ora del giorno (0-23):{RESET}")
    for h in range(24):
        print(f" {LIGHT_GREEN}- {h:02d}: {stats['hours'].get(h, 0)}{RESET}")

    print(f"{BOLD}{CYAN}=== Fine riepilogo ==={RESET}\n")

def main():
    # Verifica se esiste il DB GeoLite2
    if not os.path.isfile(GEOIP_DB_PATH):
        print(f"{RED}ERRORE: File DB GeoLite2 non trovato in {GEOIP_DB_PATH}{RESET}")
        sys.exit(1)

    geo_reader = geoip2.database.Reader(GEOIP_DB_PATH)

    print(f"{BOLD}{GREEN}Inizio monitoraggio real-time...{RESET}")
    try:
        while True:
            all_peers = []
            for tid in TORRENT_IDS:
                lines = get_peers_list(tid)
                peer_ips = parse_peers_from_lines(lines)
                all_peers.extend(peer_ips)

            # Aggiorna le stats
            update_stats_with_peers(all_peers, geo_reader)

            # Mostra il riepilogo
            print_stats()

            # Attendi REFRESH_INTERVAL secondi prima della prossima lettura
            time.sleep(REFRESH_INTERVAL)

    except KeyboardInterrupt:
        print(f"{YELLOW}Terminazione da tastiera, stampo ultime statistiche...{RESET}")
        print_stats()

    finally:
        geo_reader.close()

if __name__ == "__main__":
    main()


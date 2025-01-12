### Presentazione ###

Questo script fornisce un efficace strumento per monitorare in tempo reale i peer connessi ai torrent 
gestiti da Transmission, offrendo una panoramica dettagliata delle connessioni e delle loro 
origini geografiche. Con le giuste configurazioni e eventuali personalizzazioni, può essere un potente 
strumento per analizzare e gestire meglio l'attività torrent sul tuo sistema.

### Panoramica del Codice ###

Il codice è strutturato in diverse sezioni principali:

    Configurazione: Definizione delle impostazioni e dei parametri necessari per il funzionamento dello script.
    Colori per l'Output: Configurazione dei colori per migliorare la leggibilità delle informazioni stampate nel 
    	terminale.
    Strutture di Dati per le Statistiche: Definizione delle strutture dati utilizzate per memorizzare le statistiche 
    	raccolte.
    Funzioni: Implementazione delle funzioni che eseguono operazioni specifiche come l'estrazione dei peer, la 
    	geolocalizzazione degli IP, l'aggiornamento delle statistiche e la stampa dei riepiloghi.
    Main: La funzione principale che gestisce il ciclo di monitoraggio continuo.

### Dettaglio delle Sezioni ###

1. Configurazione

Questa sezione definisce le variabili di configurazione necessarie per il corretto funzionamento dello script.

TRANSMISSION_REMOTE_PATH = "/usr/bin/transmission-remote"  # Path al binario transmission-remote
RPC_HOST = "127.0.0.1:9091"  # Host e porta del demone Transmission
RPC_USER = "pi"              # Username per l'autenticazione RPC
RPC_PASS = "******"          # Password per l'autenticazione RPC
TORRENT_IDS = ["all"]        # ID dei torrent da monitorare ("all" per tutti)
GEOIP_DB_PATH = "/home/pi/geolite2_db/GeoLite2-City.mmdb"  # Path al database GeoLite2
REFRESH_INTERVAL = 30        # Intervallo di aggiornamento in secondi
IP_REGEX = re.compile(r'(\d{1,3}\.){3}\d{1,3}')  # Regex per il matching degli indirizzi IPv4

Descrizione dei Parametri:

    TRANSMISSION_REMOTE_PATH: Percorso al comando transmission-remote, utilizzato per interagire con il demone 
    	Transmission.
    RPC_HOST: Indirizzo e porta del demone Transmission.
    RPC_USER & RPC_PASS: Credenziali per l'accesso RPC al demone Transmission.
    TORRENT_IDS: Lista degli ID dei torrent da monitorare. Utilizzare ["all"] per monitorare tutti i torrent.
    GEOIP_DB_PATH: Percorso al database GeoLite2 utilizzato per la geolocalizzazione degli indirizzi IP.
    REFRESH_INTERVAL: Intervallo di tempo (in secondi) tra un aggiornamento e l'altro delle statistiche.
    IP_REGEX: Espressione regolare per identificare indirizzi IPv4 nelle stringhe di output.

2. Colori per l'Output

Questa sezione configura i colori per l'output nel terminale, migliorando la leggibilità delle informazioni.

def is_stdout_a_tty():
    return sys.stdout.isatty()

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
    ORANGE = "\033[38;5;208m"
    LIGHT_BLUE = "\033[38;5;153m"
    LIGHT_GREEN = "\033[38;5;120m"
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

Funzionamento:

    Verifica se l'output standard (stdout) è un terminale interattivo (tty).
    Se sì, definisce sequenze di escape ANSI per vari colori e stili.
    Se no, assegna stringhe vuote, evitando di inserire caratteri di controllo non necessari.

3. Strutture di Dati per le Statistiche

Definisce le strutture dati utilizzate per memorizzare le statistiche raccolte.

stats = {
    'peers': {},
    'hours': {}
}

Struttura stats:

    peers: Dizionario che memorizza informazioni sui peer, indicizzati per indirizzo IP.
        count: Numero di volte che l'IP è stato visto.
        geo_info: Informazioni geografiche (paese, città, latitudine, longitudine).
        last_seen: Timestamp dell'ultimo avvistamento.
    hours: Dizionario che conta le connessioni per fascia oraria (0-23).

4. Funzioni

a. get_peers_list(torrent_id="all")

Esegue il comando transmission-remote per ottenere la lista dei peer di un torrent specifico o di 
	tutti i torrent.

def get_peers_list(torrent_id="all"):
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

Descrizione:

    Costruisce e esegue il comando transmission-remote con i parametri forniti.
    Raccoglie l'output e lo suddivide in linee.
    Gestisce eventuali errori di esecuzione, stampando un messaggio di errore colorato.

b. parse_peers_from_lines(lines)

Estrae gli indirizzi IP dalle linee di output ottenute dal comando transmission-remote.

def parse_peers_from_lines(lines):
    found_ips = []
    for line in lines:
        match = IP_REGEX.search(line)
        if match:
            ip_address = match.group(0)
            found_ips.append(ip_address)
    return found_ips

Descrizione:

    Itera su ogni linea dell'output.
    Utilizza la regex definita per identificare gli indirizzi IPv4.
    Raccoglie gli indirizzi IP trovati in una lista.

c. get_geolocation_info(ip_address, geo_reader)

Ottiene le informazioni geografiche di un indirizzo IP utilizzando il database GeoLite2.

def get_geolocation_info(ip_address, geo_reader):
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
        return None

Descrizione:

    Usa geo_reader per ottenere le informazioni sulla città relative all'IP.
    Estrae paese, città, latitudine e longitudine.
    Se l'IP non è presente nel database o si verifica un errore, restituisce None.

d. update_stats_with_peers(peer_ips, geo_reader)

Aggiorna le statistiche con la lista degli indirizzi IP dei peer trovati.

def update_stats_with_peers(peer_ips, geo_reader):
    current_time = datetime.datetime.now()
    hour = current_time.hour

    stats['hours'][hour] = stats['hours'].get(hour, 0) + len(peer_ips)

    for ip in peer_ips:
        if ip not in stats['peers']:
            geo_info = get_geolocation_info(ip, geo_reader)
            stats['peers'][ip] = {
                'count': 0,
                'geo_info': geo_info,
                'last_seen': current_time
            }
        stats['peers'][ip]['count'] += 1
        stats['peers'][ip]['last_seen'] = current_time

Descrizione:

    Ottiene il timestamp corrente e l'ora.
    Aggiorna il conteggio delle connessioni per l'ora corrente.
    Per ogni IP:
        Se è la prima volta che viene visto, recupera le informazioni geografiche e lo aggiunge 
        	al dizionario peers.
        Incrementa il conteggio delle connessioni e aggiorna l'ultimo avvistamento.

e. print_stats()

Stampa un riepilogo delle statistiche raccolte, utilizzando i colori configurati.

def print_stats():
    os.system('clear')

    print(f"{BOLD}{CYAN}=== Riepilogo statistiche ==={RESET}")

    total_connections = sum(peer_data['count'] for peer_data in stats['peers'].values())
    unique_ips = len(stats['peers'])
    print(f"{GREEN}Totale avvistamenti IP (connessioni): {RESET}{total_connections}")
    print(f"{GREEN}IP unici incontrati: {RESET}{unique_ips}")

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

    print(f"\n{BOLD}{LIGHT_BLUE}Connessioni per ora del giorno (0-23):{RESET}")
    for h in range(24):
        print(f" {LIGHT_GREEN}- {h:02d}: {stats['hours'].get(h, 0)}{RESET}")

    print(f"{BOLD}{CYAN}=== Fine riepilogo ==={RESET}\n")

Descrizione:

    Pulisce lo schermo del terminale.
    Stampa un'intestazione in grassetto e colore ciano.
    Calcola e stampa il totale delle connessioni e il numero di IP unici.
    Conta e stampa le connessioni per paese, ordinando i paesi in base al numero di connessioni.
    Stampa le connessioni per fascia oraria (0-23).
    Utilizza colori per evidenziare diverse sezioni e dati.

5. Main

La funzione principale che gestisce il ciclo di monitoraggio continuo.

def main():
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

            update_stats_with_peers(all_peers, geo_reader)

            print_stats()

            time.sleep(REFRESH_INTERVAL)

    except KeyboardInterrupt:
        print(f"{YELLOW}Terminazione da tastiera, stampo ultime statistiche...{RESET}")
        print_stats()

    finally:
        geo_reader.close()

if __name__ == "__main__":
    main()

Descrizione:

    Verifica del Database GeoLite2:
        Controlla se il file del database GeoLite2 esiste nel percorso specificato.
        Se non esiste, stampa un messaggio di errore e termina lo script.

    Inizializzazione del Lettore GeoIP:
        Crea un'istanza di geoip2.database.Reader per accedere alle informazioni geografiche 
        	degli IP.

    Ciclo di Monitoraggio:
        Entra in un ciclo infinito (while True) per eseguire il monitoraggio continuo.
        Per ogni ID di torrent specificato in TORRENT_IDS:
            Ottiene la lista dei peer tramite get_peers_list.
            Estrae gli indirizzi IP con parse_peers_from_lines.
            Aggiunge gli IP alla lista all_peers.
        Aggiorna le statistiche con update_stats_with_peers.
        Stampa il riepilogo delle statistiche con print_stats.
        Attende per l'intervallo di tempo definito in REFRESH_INTERVAL prima di ripetere.

    Gestione dell'Interruzione da Tastiera:
        Se l'utente interrompe lo script con Ctrl+C, stampa un messaggio di terminazione e mostra 
        	le ultime statistiche raccolte.

    Chiusura del Lettore GeoIP:
        Assicura che il lettore GeoIP venga chiuso correttamente al termine dello script.

### Dipendenze e Requisiti ###

Per eseguire correttamente questo script, è necessario assicurarsi di avere le seguenti dipendenze 
	e configurazioni:

    Python 3: Lo script è scritto in Python 3.

    Librerie Python:
        re: Per l'uso delle espressioni regolari.
        subprocess: Per eseguire comandi di sistema.
        time e datetime: Per la gestione del tempo.
        geoip2: Per la geolocalizzazione degli indirizzi IP.
        os e sys: Per operazioni di sistema.

    È possibile installare geoip2 tramite pip:

    pip install geoip2

    Transmission Remote:
        Assicurarsi che transmission-remote sia installato e accessibile nel percorso specificato 
        	(/usr/bin/transmission-remote).
        Configurare il demone Transmission con le credenziali RPC corrette (RPC_USER e RPC_PASS).

    Database GeoLite2:
        Scaricare il database GeoLite2 (ad esempio, GeoLite2-City.mmdb) da MaxMind e posizionarlo 
        	nel percorso specificato (/home/pi/geolite2_db/GeoLite2-City.mmdb).
        Assicurarsi che lo script abbia i permessi per leggere il file del database.

### Come Utilizzare lo Script ###

    Configurazione:
        Apri lo script in un editor di testo.
        Modifica le variabili di configurazione nella sezione CONFIGURAZIONE in base al tuo ambiente:
            Percorso a transmission-remote.
            Host e porta del demone Transmission.
            Credenziali RPC (RPC_USER e RPC_PASS).
            ID dei torrent da monitorare (TORRENT_IDS).
            Percorso al database GeoLite2 (GEOIP_DB_PATH).
            Intervallo di aggiornamento (REFRESH_INTERVAL).

    Esecuzione:

        Rendi lo script eseguibile (se non lo è già):

chmod +x tuo_script.py

Esegui lo script:

./tuo_script.py

In alternativa, puoi eseguirlo direttamente con Python:

        python3 tuo_script.py

    Monitoraggio:
        Lo script inizierà a monitorare i peer connessi ai torrent specificati, aggiornando le 
        	statistiche ad ogni intervallo definito.
        Le statistiche verranno visualizzate nel terminale con colori per una migliore leggibilità.
        Per terminare lo script, premi Ctrl+C. Le ultime statistiche verranno visualizzate prima 
        	della chiusura.

### Personalizzazioni e Miglioramenti ###

    Filtraggio degli IP: È possibile migliorare lo script aggiungendo filtri per escludere IP noti 
    	come proxy o VPN.
    Salvataggio delle Statistiche: Implementare la memorizzazione delle statistiche in un file o in 
    	un database per analisi successive.
    Notifiche: Aggiungere notifiche via email o altri mezzi quando si raggiungono determinate 
    	condizioni (ad esempio, un numero elevato di connessioni da un paese specifico).
    Interfaccia Web: Integrare un'interfaccia web per visualizzare le statistiche in modo più 
    	interattivo e accessibile da altri dispositivi.

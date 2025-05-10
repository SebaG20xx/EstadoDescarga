import requests
from datetime import datetime, timedelta, timezone
import pandas as pd
import ipaddress
import tweepy
import time
import pytz
import os
from dateutil.relativedelta import relativedelta

from dotenv import load_dotenv

load_dotenv()

IKYD_API_KEY = os.getenv("IKYD_API_KEY")
DJANGO_API_KEY = os.getenv("DJANGO_API_KEY")
DJANGO_URL = os.getenv("DJANGO_URL")
client= tweepy.Client(
    consumer_key = os.getenv("consumer_key"),
    consumer_secret = os.getenv("consumer_secret"),
    access_token = os.getenv("access_token"),
    access_token_secret = os.getenv("access_token_secret"),
)

IKYD_HOST = "api.antitor.com"

DIAS_RECIENTES = 30
MAX_PEER_DAYS = 30
TWITTER_MAX_CHARS = 280
CHILE_TZ = pytz.timezone("America/Santiago")
HISTORIAL_FILE = "historial.csv"


BASE_BLOCKS = [
    "163.247.0.0/16",
    "160.238.212.0/24", "160.238.214.0/24", "160.238.215.0/24", "200.10.182.0/24",
    "45.229.137.0/24", "45.230.22.0/24", "45.230.23.0/24",
    "200.10.251.0/24", "200.10.252.0/24", "200.10.253.0/24",
    "200.12.140.0/24", "200.12.141.0/24",
    "167.28.193.0/24", "170.233.152.0/24", "170.233.153.0/24"
]

RANGOS_INSTITUCIONES = {
    # El prefijo 163.247.0.0/16 considera todas las IPs de la Red de Conectividad del Estado
    # Este desglose está basado en http://red.gob.cl/subredes.html (https://archive.is/Fox4M)
    "163.247.40.0/24": "@MinagriCL",
    "163.247.41.0/24": "@MinisterioBBNN",
    "163.247.42.0/24": "@MinDefChile",
    "163.247.43.0/24": "@MEconomia",
    "163.247.44.0/24": "@Mineduc",
    "163.247.45.0/24": "@Min_Hacienda",
    "163.247.46.0/24": "@MinJuDDHH",
    "163.247.47.0/24": "@MinMineria_cl",
    "163.247.48.0/24": "@MOP_Chile",
    "163.247.49.0/24": "@MinDesarrollo",
    "163.247.50.0/24": "@MinRel_Chile",
    "163.247.51.0/24": "@MinisterioSalud",
    "163.247.52.0/24": "@MTTChile",
    "163.247.53.0/24": "@Minvu",
    # "163.247.54.0/24": "",
    "163.247.55.0/24": "@MinTrabChile",
    "163.247.56.0/24": "@VoceriaGobierno",
    "163.247.57.0/24": "@SegPres",
    "163.247.58.0/24": "@MinMujeryEG",
    "163.247.59.0/24": "@MinEnergia",
    "163.247.60.0/24": "@ContraloriaCL",
    "163.247.61.0/24": "@Fonasa",
    "163.247.62.0/24": "@IPSChile",
    "163.247.63.0/24": "@SII_Chile",
    "163.247.64.0/24": "@RegCivil_Chile",
    "163.247.65.0/24": "@TGRChile",
    # "163.247.66.0/24": "",
    # "163.247.67.0/24": "",
    # "163.247.68.0/24": "",
    # "163.247.69.0/24": "",
    "163.247.70.0/24": "@Min_Interior",
    "163.247.71.0/24": "@Presidencia_cl",
    # "163.247.72.0/24": "",
    # "163.247.73.0/24": "",
    # "163.247.74.0/24": "",
    # "163.247.75.0/24": "",
    # "163.247.76.0/24": "",
    # "163.247.77.0/24": "",
    "163.247.78.0/24": "@MMAChile",
    "163.247.79.0/24": "@SuperPensiones",
    "163.247.80.0/24": "Red de Salud @BdoMartorell @MinisterioSalud",
    
    "160.238.212.0/24": "@bcentralchile",
    "160.238.214.0/24": "@bcentralchile",
    "160.238.215.0/24": "@bcentralchile",
    "200.10.182.0/24" : "@bcentralchile",
    
    "45.229.137.0/24": "@TVN",
    "45.230.22.0/24" : "@TVN",
    "45.230.23.0/24" : "@TVN",
    
    "200.10.251.0/24": "@SII_Chile",
    "200.10.252.0/24": "@SII_Chile",
    "200.10.253.0/24": "@SII_Chile",
    
    "200.12.140.0/24": "@Enap_Informa",
    "200.12.141.0/24": "@Enap_Informa",
    
    "167.28.193.0/24" : "@BancoEstado",
    "170.233.152.0/24": "@BancoEstado",
    "170.233.153.0/24": "@BancoEstado"
}

def identificar_institucion(ip_str):
    ip = ipaddress.ip_address(ip_str)
    for cidr, nombre in RANGOS_INSTITUCIONES.items():
        if ip in ipaddress.ip_network(cidr):
            return nombre
    return None

def expand_blocks(blocks):
    subnets = []
    for block in blocks:
        net = ipaddress.ip_network(block)
        if net.prefixlen < 24:
            new_prefix = 18 if net.prefixlen == 16 else 24
            subnets.extend(net.subnets(new_prefix=new_prefix))
        else:
            subnets.append(net)
    return [str(subnet) for subnet in subnets]

def get_recent_active_ips(cidr, dias=DIAS_RECIENTES):
    institucion = RANGOS_INSTITUCIONES.get(cidr, "")
    label = f"{cidr} ({institucion})" if institucion else cidr

    print(f"\n Consultando bloque: {label}")
    url = f"https://{IKYD_HOST}/history/peers?cidr={cidr}&key={IKYD_API_KEY}"
    r = requests.get(url)

    recientes = []
    if r.status_code == 200:
        data = r.json()
        peers = data.get("peers", [])
        ahora = datetime.now(timezone.utc)
        for peer in peers:
            try:
                fecha = datetime.fromisoformat(peer["date"].replace("Z", "+00:00"))
                if fecha > ahora - timedelta(days=dias):
                    recientes.append(peer["ip"])
            except Exception as e:
                print(f"    Error con fecha en {peer['ip']}: {e}")
        print(f"    ↳ {len(recientes)} IPs activas encontradas")
    else:
        print(f"    Error al consultar bloque: status {r.status_code}")
    return recientes

def get_ip_history(ip):
    url = f"https://{IKYD_HOST}/history/peer?ip={ip}&days={MAX_PEER_DAYS}&contents=100&key={IKYD_API_KEY}"
    r = requests.get(url)
    print(f"Revisando IP: {ip} → status {r.status_code}")
    if r.status_code == 200:
        return r.json()
    return None

def fue_tuiteado(ip, torrent, historial):
    coincidencias = historial[(historial["ip"] == ip) & (historial["torrent"] == torrent)]
    if coincidencias.empty:
        return False, False
    fecha_ultima = pd.to_datetime(coincidencias.iloc[-1]["fecha_tweet"]).tz_localize(CHILE_TZ)
    ahora = datetime.now(CHILE_TZ)
    hace_dos_meses = ahora - relativedelta(months=2)

    if fecha_ultima < hace_dos_meses:
        return False, True  # fue hace más de 2 meses
    return True, False      # ya fue tuiteado recientemente



def publicar_tweet(texto):
    if len(texto) > TWITTER_MAX_CHARS:
        print("Tweet excede 280 caracteres, recortando nombre del torrent...")
        lineas = texto.split("\n")
        encabezado, torrent, fecha, enlace = lineas
        torrent = torrent[:100] + "..."
        texto = f"{encabezado}\n{torrent}\n{fecha}\n{enlace}"
    try:
        response = client.create_tweet(text=texto)
        tweet_id = response.data["id"]
        tweet_url = f"https://twitter.com/EstadoDescarga/status/{tweet_id}"
        print(f"Tweet publicado: {tweet_url}")
        return tweet_url
    except Exception as e:
        print(f"Error al tuitear: {e}")
        return None

def notificar_django(ip, torrent, fecha, institucion, enlace, enlace_tweet):
    url = DJANGO_URL
    if not institucion:
        institucion = "Estatal"
    headers = {
        "X-API-KEY": DJANGO_API_KEY
    }
    data = {
        "ip": ip,
        "torrent": torrent,
        "fecha_hora": fecha,
        "institucion": institucion,
        "enlace": enlace,
        "enlace_tweet": enlace_tweet
    }
    try:
        r = requests.post(url, json=data, headers=headers, timeout=5)
        if r.status_code == 201:
            print("Notificado a Django correctamente")
        else:
            print(f"Error al notificar a Django: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Error al conectar con Django: {e}")


while True:
    print("\n Iniciando nueva revisión...")
    if os.path.exists(HISTORIAL_FILE):
        try:
            historial = pd.read_csv(HISTORIAL_FILE)
            if historial.empty or not all(col in historial.columns for col in ["ip", "torrent", "fecha_tweet"]):
                raise ValueError("historial.csv inválido")
        except Exception:
            print("historial.csv está vacío o corrupto, inicializando de nuevo.")
            historial = pd.DataFrame(columns=["ip", "torrent", "fecha_tweet"])
    else:
        historial = pd.DataFrame(columns=["ip", "torrent", "fecha_tweet"])

    CIDR_BLOCKS = expand_blocks(BASE_BLOCKS)
    active_recent_ips = []
    for cidr in CIDR_BLOCKS:
        active_recent_ips.extend(get_recent_active_ips(cidr))
    active_recent_ips = list(set(active_recent_ips))

    results = []
    for ip in active_recent_ips:
        history = get_ip_history(ip)
        if history and "contents" in history:
            for content in history["contents"]:
                torrent_name = content.get("torrent", {}).get("name", "Nombre desconocido")
                start_date = content.get("startDate", "")
                if not start_date:
                    continue
                dt_utc = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                dt_local = dt_utc.astimezone(CHILE_TZ)
                institucion = identificar_institucion(ip)
                results.append({
                    "ip": ip,
                    "torrent": torrent_name,
                    "fecha": dt_local.strftime("%Y-%m-%d %H:%M:%S"),
                    "institucion": institucion if institucion else ""
                })

    df = pd.DataFrame(results)
    if df.empty:
        print("No se encontraron descargas recientes.")
    else:
        for _, fila in df.iterrows():
            ip = fila["ip"]
            torrent = fila["torrent"]
            fue_antes, fue_hace_mucho = fue_tuiteado(ip, torrent, historial)
            if fue_antes and not fue_hace_mucho:
                continue

            enlace = f"https://iknowwhatyoudownload.com/en/peer/?ip={ip}"
            if fila['institucion']:
                encabezado = f"La IP ({ip}) de {fila['institucion']} descargó:"
            else:
                encabezado = f"La IP {ip} descargó:"
            nota_pasado = "\n (Esto fue descargado en el pasado)" if fue_hace_mucho else ""
            tweet = f"{encabezado}\n{torrent}\n {fila['fecha']}{nota_pasado}\n {enlace}"

            print(f"\n Publicando tweet:\n{tweet}")
            tweet_url = publicar_tweet(tweet)
            if tweet_url:
                notificar_django(
                    ip=ip,
                    torrent=torrent,
                    fecha=fila["fecha"],
                    institucion=fila["institucion"],
                    enlace=enlace,
                    enlace_tweet=tweet_url
                )
            historial = pd.concat([historial, pd.DataFrame([{
                "ip": ip,
                "torrent": torrent,
                "fecha_tweet": datetime.now(CHILE_TZ).strftime("%Y-%m-%d %H:%M:%S")
            }])], ignore_index=True)
            historial.to_csv(HISTORIAL_FILE, index=False)
            time.sleep(5)

    print("Esperando 1 día")
    time.sleep(86400)

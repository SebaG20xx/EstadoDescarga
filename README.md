# Estado Descarga

Este bot detecta y publica **descargas de torrents realizadas desde las IP asociadas a instituciones del Estado de Chile**.  
Utiliza la [API de iknowwhatyoudownload.com](https://iknowwhatyoudownload.com/en/peer/) para consultar actividad reciente, filtra por rangos IP conocidos, y si encuentra algo ...  **lo postea automáticamente en Twitter**.

## Características

- Consulta una vez al día la API de iknowwhatyoudownload.com.
- Filtra resultados según IPs de organismos estatales (Banco Central, TVN, SII, ENAP, BancoEstado, etc.).
- Evita duplicados gracias a un historial local.
- Si una IP repite descarga tras más de 2 meses, se vuelve a publicar con una nota.
- Publica automáticamente en Twitter con un enlace al historial de descargas.

## Requisitos

- Python 3.9+
- Acceso a la API de [iknowwhatyoudownload.com](https://iknowwhatyoudownload.com/)
- Claves de Twitter API (v1.1)

## Instalación

```bash
git clone https://github.com/SebaG20xx/EstadoDescarga.git
cd EstadoDescarga
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows
pip install -r requirements.txt
```

Modifica el .env con tus credenciales

```
IKYD_API_KEY=...
CONSUMER_KEY=...
CONSUMER_SECRET=...
ACCESS_TOKEN=...
ACCESS_TOKEN_SECRET=...
DJANGO_API_KEY=...
DJANGO_URL=...
```

## Uso

```
python estadodescarga.py
```

El bot corre en un loop infinito. Usa tmux si lo quieres dejar en segundo plano


##  Formato de Tweets  
###  Estos son solo ejemplos. No han ocurrido… (~~aún~~)



> La IP (127.0.0.1) del @SII_Chile descargó:  
> The Wolf of Wall Street (2013)  
> https://iknowwhatyoudownload.com/en/peer/?ip=127.0.0.1  
```
```
> La IP (127.0.0.1) del @BancoEstado descargó:  
> Catch Me If You Can (2003)  
> https://iknowwhatyoudownload.com/en/peer/?ip=127.0.0.1  
---
Si ya se había detectado antes:
---
> La IP (127.0.0.1) del @bcentralchile descargó:  
> 'The.Big.Short.2015.1080p.BluRay.x264'  
> (Esto fue descargado en el pasado)  
> https://iknowwhatyoudownload.com/en/peer/?ip=127.0.0.1

## 🧠 Créditos

Creado por [SebaG20xx](https://github.com/SebaG20xx) aka *El Guevara*.  
Inspirado en el aburrimiento que tuve en [la madrugada del 22 de Febrero del 2022..](https://www.biobiochile.cl/especial/bbcl-investiga/noticias/cronicas/2022/02/22/de-peacemaker-a-eternals-descargas-ilegales-desde-redes-del-gobierno-bajo-la-lupa-de-contraloria.shtml)

## 🛡️ Disclaimer

Este bot muestra datos públicos, no nombres. No sabemos quién está detrás de cada IP, pero sí sabemos que salen del Estado. La idea no es acusar a nadie, sino mostrar cómo se usan los recursos públicos en redes P2P. La info viene de terceros, así que puede tener imprecisiones.

---


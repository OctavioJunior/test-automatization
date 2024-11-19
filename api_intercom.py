import requests
import logging
from datetime import datetime
from auth import headers

API_URL = "https://api.intercom.io/conversations/search"
RESULTS_PER_PAGE = 150


def date_to_timestamp(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return int(date_obj.timestamp())


def adjust_dates(start_date_str, end_date_str):
    start_date = f"{start_date_str} 00:00:00"
    end_date = f"{end_date_str} 23:59:59"
    return start_date, end_date


def normalize_date_format(date_str):
    """
    Normaliza a data para o formato esperado, removendo duplicação de horários e ajustando o separador.
    """
    # Remove horários duplicados
    if " " in date_str and date_str.count(":") > 3:
        date_str = date_str.rsplit(" ", 1)[0]  # Remove a última parte duplicada

    # Substitui 'T' por espaço, se necessário
    date_str = date_str.replace("T", " ")

    # Garante que está no formato correto
    try:
        datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValueError(f"Formato inválido detectado após normalização: {date_str}")

    return date_str


def fetch_all_conversations(start_date, end_date):
    # Normalizando datas antes de processar
    start_date = normalize_date_format(start_date)
    end_date = normalize_date_format(end_date)

    logging.info(f"Data inicial normalizada: {start_date}")
    logging.info(f"Data final normalizada: {end_date}")

    # Convertendo datas normalizadas para timestamps
    start_timestamp = date_to_timestamp(start_date)
    end_timestamp = date_to_timestamp(end_date)

    all_conversations = []
    payload = {
        "query": {
            "operator": "AND",
            "value": [
                {"field": "created_at", "operator": ">", "value": start_timestamp},
                {"field": "created_at", "operator": "<", "value": end_timestamp},
            ],
        },
        "pagination": {"per_page": RESULTS_PER_PAGE},
    }

    page = 1
    while True:
        logging.info(f"Iniciando requisição para a página {page}...")
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        logging.info(f"Status da resposta da página {page}: {response.status_code}")
        try:
            response.raise_for_status()
            data = response.json()
            conversations = data.get("conversations", [])
            logging.info(f"Página {page}: {len(conversations)} conversas encontradas.")
            all_conversations.extend(conversations)
        except requests.exceptions.HTTPError as e:
            logging.error(f"Erro na requisição na página {page}: {e}")
            break

        starting_after = data.get("pages", {}).get("next", {}).get("starting_after")
        if not starting_after:
            logging.info(f"Sem mais páginas. Finalizando a busca.")
            break

        payload["pagination"]["starting_after"] = starting_after
        page += 1

    return all_conversations

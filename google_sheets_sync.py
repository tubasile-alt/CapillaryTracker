import os
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

SPREADSHEET_NAME = "ICB - Registro de Cirurgias"
SHEET_CIRURGIAS = "Cirurgias"
SHEET_NECROSES = "Necroses"

SURGERY_HEADERS = [
    "ID", "Data", "Paciente", "Unidade", "Médico", "Equipe",
    "Hora Cirurgia", "Tempo Cirurgia", "Total Folículos",
    "Frente", "Densidade Sketch", "Coroa", "Scalpe",
    "Península Direita", "Península Esquerda",
    "Q1 Área", "Q1 Furos", "Q1 Fios", "Q1 Densidade", "Q1 Taxa Quebra",
    "Q2 Área", "Q2 Furos", "Q2 Fios", "Q2 Densidade", "Q2 Taxa Quebra",
    "Q3 Área", "Q3 Furos", "Q3 Fios", "Q3 Densidade", "Q3 Taxa Quebra",
    "Q4 Área", "Q4 Furos", "Q4 Fios", "Q4 Densidade", "Q4 Taxa Quebra",
    "Densidade Extração", "Retoque", "Tipo Implante",
    "Infiltração", "Sedação", "Sangramento", "Tadalafila", "Bloqueio Seringas",
    "Fonte 1", "Fonte 2", "Fonte 3", "Fonte 4", "Fonte 5",
    "Pelos Corporais",
    "Barba Furos", "Barba Fios", "Barba Comentários",
    "Peitoral Furos", "Peitoral Fios", "Peitoral Comentários",
    "Abdome Furos", "Abdome Fios", "Abdome Comentários",
    "Pernas Furos", "Pernas Fios", "Pernas Comentários",
    "Técnica", "Solução Frente",
    "Extra Pessoa 1", "Extra Pessoa 2", "Extra Pessoa 3",
    "Safira", "Transamin", "Diprospam", "Fumante", "Implante Secundário",
    "Data Cadastro"
]

NECROSE_HEADERS = [
    "ID", "ID Cirurgia", "Unidade", "Paciente", "Data Cirurgia",
    "Data Avaliação", "Médico Responsável", "Tem Necrose",
    "Grau Necrose", "Localização", "Nº Necroses",
    "1ª Faixa", "2ª Faixa", "3ª Faixa", "Coroa",
    "Tamanho 1 (cm)", "Tamanho 2 (cm)", "Tamanho 3 (cm)", "Tamanho 4 (cm)",
    "Descrição", "Tratamento", "Observações", "Status", "Data Resolução",
    "Data Cadastro"
]


def _get_access_token():
    hostname = os.environ.get("REPLIT_CONNECTORS_HOSTNAME")
    repl_identity = os.environ.get("REPL_IDENTITY")
    web_repl_renewal = os.environ.get("WEB_REPL_RENEWAL")

    if repl_identity:
        x_replit_token = f"repl {repl_identity}"
    elif web_repl_renewal:
        x_replit_token = f"depl {web_repl_renewal}"
    else:
        raise Exception("Token de autenticação Replit não encontrado")

    if not hostname:
        raise Exception("REPLIT_CONNECTORS_HOSTNAME não encontrado")

    resp = requests.get(
        f"https://{hostname}/api/v2/connection?include_secrets=true&connector_names=google-drive",
        headers={
            "Accept": "application/json",
            "X_REPLIT_TOKEN": x_replit_token
        },
        timeout=10
    )
    resp.raise_for_status()
    data = resp.json()
    item = data.get("items", [None])[0]
    if not item:
        raise Exception("Google Drive não conectado")

    settings = item.get("settings", {})
    token = settings.get("access_token") or settings.get("oauth", {}).get("credentials", {}).get("access_token")
    if not token:
        raise Exception("Access token do Google Drive não encontrado")
    return token


def _get_sheets_service():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials

    token = _get_access_token()
    creds = Credentials(token=token)
    service = build("sheets", "v4", credentials=creds)
    return service


def _get_drive_service():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials

    token = _get_access_token()
    creds = Credentials(token=token)
    service = build("drive", "v3", credentials=creds)
    return service


def _find_spreadsheet():
    drive = _get_drive_service()
    results = drive.files().list(
        q=f"name='{SPREADSHEET_NAME}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
        spaces="drive",
        fields="files(id, name)"
    ).execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    return None


def _create_spreadsheet():
    sheets = _get_sheets_service()
    body = {
        "properties": {"title": SPREADSHEET_NAME},
        "sheets": [
            {
                "properties": {"title": SHEET_CIRURGIAS, "index": 0},
                "data": [{
                    "startRow": 0,
                    "startColumn": 0,
                    "rowData": [{
                        "values": [{"userEnteredValue": {"stringValue": h}} for h in SURGERY_HEADERS]
                    }]
                }]
            },
            {
                "properties": {"title": SHEET_NECROSES, "index": 1},
                "data": [{
                    "startRow": 0,
                    "startColumn": 0,
                    "rowData": [{
                        "values": [{"userEnteredValue": {"stringValue": h}} for h in NECROSE_HEADERS]
                    }]
                }]
            }
        ]
    }
    result = sheets.spreadsheets().create(body=body).execute()
    spreadsheet_id = result["spreadsheetId"]
    logger.info(f"Planilha criada: {SPREADSHEET_NAME} (ID: {spreadsheet_id})")

    _format_header(sheets, spreadsheet_id)

    return spreadsheet_id


def _format_header(sheets, spreadsheet_id):
    try:
        resp = sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_ids = {s["properties"]["title"]: s["properties"]["sheetId"] for s in resp["sheets"]}

        requests_list = []
        for sheet_name, sheet_id in sheet_ids.items():
            requests_list.append({
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.1, "green": 0.3, "blue": 0.6},
                            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                            "horizontalAlignment": "CENTER"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                }
            })
            requests_list.append({
                "updateSheetProperties": {
                    "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
                    "fields": "gridProperties.frozenRowCount"
                }
            })

        sheets.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests_list}
        ).execute()
    except Exception as e:
        logger.warning(f"Erro ao formatar cabeçalho: {e}")


def _get_or_create_spreadsheet():
    spreadsheet_id = _find_spreadsheet()
    if not spreadsheet_id:
        spreadsheet_id = _create_spreadsheet()
    return spreadsheet_id


def _safe_str(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    return str(value)


def surgery_to_row(surgery):
    return [
        _safe_str(surgery.id),
        _safe_str(surgery.data),
        _safe_str(surgery.nome),
        _safe_str(surgery.unidade),
        _safe_str(surgery.medico),
        _safe_str(surgery.equipe),
        _safe_str(surgery.hora_cirurgia),
        _safe_str(surgery.tempo_cirurgia),
        _safe_str(surgery.total_foliculos),
        _safe_str(surgery.frente),
        _safe_str(surgery.densidade_scketh),
        _safe_str(surgery.coroa),
        _safe_str(surgery.scalpe),
        _safe_str(surgery.peninsula_direita),
        _safe_str(surgery.peninsula_esquerda),
        _safe_str(surgery.q1_area),
        _safe_str(surgery.q1_furos),
        _safe_str(surgery.q1_fios),
        _safe_str(surgery.q1_densidade),
        _safe_str(surgery.q1_taxa_quebra),
        _safe_str(surgery.q2_area),
        _safe_str(surgery.q2_furos),
        _safe_str(surgery.q2_fios),
        _safe_str(surgery.q2_densidade),
        _safe_str(surgery.q2_taxa_quebra),
        _safe_str(surgery.q3_area),
        _safe_str(surgery.q3_furos),
        _safe_str(surgery.q3_fios),
        _safe_str(surgery.q3_densidade),
        _safe_str(surgery.q3_taxa_quebra),
        _safe_str(surgery.q4_area),
        _safe_str(surgery.q4_furos),
        _safe_str(surgery.q4_fios),
        _safe_str(surgery.q4_densidade),
        _safe_str(surgery.q4_taxa_quebra),
        _safe_str(surgery.densidade_extracao),
        _safe_str(surgery.retoque),
        _safe_str(surgery.tipo_implante),
        _safe_str(surgery.infiltracao),
        _safe_str(surgery.sedacao),
        _safe_str(surgery.sangramento),
        _safe_str(surgery.tadalafila),
        _safe_str(surgery.bloqueio_seringas),
        _safe_str(surgery.fonte_1),
        _safe_str(surgery.fonte_2),
        _safe_str(surgery.fonte_3),
        _safe_str(surgery.fonte_4),
        _safe_str(surgery.fonte_5),
        _safe_str(surgery.pelos_corporais),
        _safe_str(surgery.barba_furos),
        _safe_str(surgery.barba_fios),
        _safe_str(surgery.barba_comentarios),
        _safe_str(surgery.peitoral_furos),
        _safe_str(surgery.peitoral_fios),
        _safe_str(surgery.peitoral_comentarios),
        _safe_str(surgery.abdome_furos),
        _safe_str(surgery.abdome_fios),
        _safe_str(surgery.abdome_comentarios),
        _safe_str(surgery.pernas_furos),
        _safe_str(surgery.pernas_fios),
        _safe_str(surgery.pernas_comentarios),
        _safe_str(surgery.tecnica),
        _safe_str(surgery.solucao_frente),
        _safe_str(surgery.extra_person_1),
        _safe_str(surgery.extra_person_2),
        _safe_str(surgery.extra_person_3),
        _safe_str(surgery.safira),
        _safe_str(surgery.transamin),
        _safe_str(surgery.diprospam),
        _safe_str(surgery.fumante),
        _safe_str(surgery.implante_secundario),
        _safe_str(surgery.created_at),
    ]


def necrose_to_row(necrose):
    return [
        _safe_str(necrose.id),
        _safe_str(necrose.surgery_id),
        _safe_str(necrose.unidade),
        _safe_str(necrose.paciente_nome),
        _safe_str(necrose.data_cirurgia),
        _safe_str(necrose.data_avaliacao),
        _safe_str(necrose.medico_responsavel),
        _safe_str(necrose.tem_necrose),
        _safe_str(necrose.grau_necrose),
        _safe_str(necrose.localizacao),
        _safe_str(necrose.numero_necroses),
        _safe_str(necrose.primeira_faixa),
        _safe_str(necrose.segunda_faixa),
        _safe_str(necrose.terceira_faixa),
        _safe_str(necrose.coroa),
        _safe_str(necrose.tamanho_1_cm),
        _safe_str(necrose.tamanho_2_cm),
        _safe_str(necrose.tamanho_3_cm),
        _safe_str(necrose.tamanho_4_cm),
        _safe_str(necrose.descricao),
        _safe_str(necrose.tratamento_aplicado),
        _safe_str(necrose.observacoes),
        _safe_str(necrose.status),
        _safe_str(necrose.data_resolucao),
        _safe_str(necrose.created_at),
    ]


def _col_letter(n):
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result


def sync_surgery_to_sheets(surgery):
    try:
        spreadsheet_id = _get_or_create_spreadsheet()
        sheets = _get_sheets_service()
        row = surgery_to_row(surgery)
        last_col = _col_letter(len(SURGERY_HEADERS))
        sheets.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"{SHEET_CIRURGIAS}!A:{last_col}",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]}
        ).execute()
        logger.info(f"✅ Cirurgia sincronizada com Google Sheets: {surgery.nome} (ID: {surgery.id})")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao sincronizar cirurgia com Google Sheets: {e}")
        return False


def sync_necrose_to_sheets(necrose):
    try:
        spreadsheet_id = _get_or_create_spreadsheet()
        sheets = _get_sheets_service()
        row = necrose_to_row(necrose)
        last_col = _col_letter(len(NECROSE_HEADERS))
        sheets.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"{SHEET_NECROSES}!A:{last_col}",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]}
        ).execute()
        logger.info(f"✅ Necrose sincronizada com Google Sheets: {necrose.paciente_nome} (ID: {necrose.id})")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao sincronizar necrose com Google Sheets: {e}")
        return False


def sync_all_to_sheets(surgeries, necroses):
    try:
        spreadsheet_id = _find_spreadsheet()
        sheets = _get_sheets_service()

        if spreadsheet_id:
            sheets.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=f"{SHEET_CIRURGIAS}!A:ZZ"
            ).execute()
            sheets.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=f"{SHEET_NECROSES}!A:ZZ"
            ).execute()
        else:
            spreadsheet_id = _create_spreadsheet()

        surgery_last_col = _col_letter(len(SURGERY_HEADERS))
        necrose_last_col = _col_letter(len(NECROSE_HEADERS))

        BATCH_SIZE = 500

        sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{SHEET_CIRURGIAS}!A1:{surgery_last_col}1",
            valueInputOption="USER_ENTERED",
            body={"values": [SURGERY_HEADERS]}
        ).execute()

        for i in range(0, len(surgeries), BATCH_SIZE):
            batch = surgeries[i:i + BATCH_SIZE]
            rows = [surgery_to_row(s) for s in batch]
            sheets.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f"{SHEET_CIRURGIAS}!A:{surgery_last_col}",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": rows}
            ).execute()
            logger.info(f"📊 Cirurgias exportadas: {min(i + BATCH_SIZE, len(surgeries))}/{len(surgeries)}")

        sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{SHEET_NECROSES}!A1:{necrose_last_col}1",
            valueInputOption="USER_ENTERED",
            body={"values": [NECROSE_HEADERS]}
        ).execute()

        if necroses:
            necrose_rows = [necrose_to_row(n) for n in necroses]
            sheets.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f"{SHEET_NECROSES}!A:{necrose_last_col}",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": necrose_rows}
            ).execute()

        _format_header(sheets, spreadsheet_id)

        logger.info(f"✅ Exportação completa: {len(surgeries)} cirurgias, {len(necroses)} necroses")
        return spreadsheet_id
    except Exception as e:
        logger.error(f"❌ Erro na exportação em lote: {e}")
        raise

"""
Script de recuperação completa do banco de dados a partir do Google Sheets.
Uso: python3 recover_from_sheets.py
"""
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SPREADSHEET_ID = "1G6lh3WMfU6p02gKBlavN8MwYAdxmj4QlQxlql1ThdCA"


def _get_sheets_service():
    from google_sheets_sync import _get_access_token
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    token = _get_access_token()
    creds = Credentials(token=token)
    return build("sheets", "v4", credentials=creds)


def fetch_sheet_data(service, sheet_name):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A:ZZ"
    ).execute()
    rows = result.get("values", [])
    if not rows:
        return [], []
    headers = rows[0]
    data = rows[1:]
    return headers, data


def safe_val(row, headers, col_name, default=""):
    try:
        idx = headers.index(col_name)
        val = row[idx] if idx < len(row) else default
        return val if val != "" else default
    except ValueError:
        return default


def safe_int(row, headers, col_name):
    v = safe_val(row, headers, col_name, "0")
    try:
        return int(float(str(v).replace(",", "."))) if v else 0
    except:
        return 0


def safe_float(row, headers, col_name):
    v = safe_val(row, headers, col_name, "0")
    try:
        return float(str(v).replace(",", ".")) if v else 0.0
    except:
        return 0.0


def safe_date(row, headers, col_name):
    v = safe_val(row, headers, col_name, "")
    if not v:
        return None
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"]:
        try:
            return datetime.strptime(str(v).strip(), fmt).date()
        except:
            continue
    return None


def safe_bool(row, headers, col_name):
    v = safe_val(row, headers, col_name, "")
    return v.lower() in ("sim", "true", "1", "yes") if v else False


def restore_surgeries(app, db, Surgery, headers, data):
    logger.info(f"Iniciando restauração de {len(data)} cirurgias...")
    db.session.query(Surgery).delete()
    db.session.commit()

    success = 0
    errors = 0
    for i, row in enumerate(data):
        try:
            s = Surgery(
                data=safe_date(row, headers, "Data"),
                nome=safe_val(row, headers, "Paciente"),
                unidade=safe_val(row, headers, "Unidade"),
                medico=safe_val(row, headers, "Médico"),
                equipe=safe_val(row, headers, "Equipe"),
                hora_cirurgia=safe_val(row, headers, "Hora Cirurgia"),
                tempo_cirurgia=safe_float(row, headers, "Tempo Cirurgia"),
                total_foliculos=safe_int(row, headers, "Total Folículos"),
                frente=safe_int(row, headers, "Frente"),
                densidade_scketh=safe_float(row, headers, "Densidade Sketch"),
                coroa=safe_int(row, headers, "Coroa"),
                scalpe=safe_int(row, headers, "Scalpe"),
                peninsula_direita=safe_int(row, headers, "Península Direita"),
                peninsula_esquerda=safe_int(row, headers, "Península Esquerda"),
                q1_area=safe_val(row, headers, "Q1 Área"),
                q1_furos=safe_int(row, headers, "Q1 Furos"),
                q1_fios=safe_int(row, headers, "Q1 Fios"),
                q1_densidade=safe_float(row, headers, "Q1 Densidade"),
                q1_taxa_quebra=safe_float(row, headers, "Q1 Taxa Quebra"),
                q2_area=safe_val(row, headers, "Q2 Área"),
                q2_furos=safe_int(row, headers, "Q2 Furos"),
                q2_fios=safe_int(row, headers, "Q2 Fios"),
                q2_densidade=safe_float(row, headers, "Q2 Densidade"),
                q2_taxa_quebra=safe_float(row, headers, "Q2 Taxa Quebra"),
                q3_area=safe_val(row, headers, "Q3 Área"),
                q3_furos=safe_int(row, headers, "Q3 Furos"),
                q3_fios=safe_int(row, headers, "Q3 Fios"),
                q3_densidade=safe_float(row, headers, "Q3 Densidade"),
                q3_taxa_quebra=safe_float(row, headers, "Q3 Taxa Quebra"),
                q4_area=safe_val(row, headers, "Q4 Área"),
                q4_furos=safe_int(row, headers, "Q4 Furos"),
                q4_fios=safe_int(row, headers, "Q4 Fios"),
                q4_densidade=safe_float(row, headers, "Q4 Densidade"),
                q4_taxa_quebra=safe_float(row, headers, "Q4 Taxa Quebra"),
                densidade_extracao=safe_float(row, headers, "Densidade Extração"),
                retoque=safe_bool(row, headers, "Retoque"),
                tipo_implante=safe_val(row, headers, "Tipo Implante"),
                infiltracao=safe_val(row, headers, "Infiltração"),
                sedacao=safe_val(row, headers, "Sedação"),
                sangramento=safe_val(row, headers, "Sangramento"),
                tadalafila=safe_bool(row, headers, "Tadalafila"),
                bloqueio_seringas=safe_bool(row, headers, "Bloqueio Seringas"),
                fonte_1=safe_val(row, headers, "Fonte 1"),
                fonte_2=safe_val(row, headers, "Fonte 2"),
                fonte_3=safe_val(row, headers, "Fonte 3"),
                fonte_4=safe_val(row, headers, "Fonte 4"),
                fonte_5=safe_val(row, headers, "Fonte 5"),
                pelos_corporais=safe_val(row, headers, "Pelos Corporais"),
                barba_furos=safe_int(row, headers, "Barba Furos"),
                barba_fios=safe_int(row, headers, "Barba Fios"),
                barba_comentarios=safe_val(row, headers, "Barba Comentários"),
                peitoral_furos=safe_int(row, headers, "Peitoral Furos"),
                peitoral_fios=safe_int(row, headers, "Peitoral Fios"),
                peitoral_comentarios=safe_val(row, headers, "Peitoral Comentários"),
                abdome_furos=safe_int(row, headers, "Abdome Furos"),
                abdome_fios=safe_int(row, headers, "Abdome Fios"),
                abdome_comentarios=safe_val(row, headers, "Abdome Comentários"),
                pernas_furos=safe_int(row, headers, "Pernas Furos"),
                pernas_fios=safe_int(row, headers, "Pernas Fios"),
                pernas_comentarios=safe_val(row, headers, "Pernas Comentários"),
                tecnica=safe_val(row, headers, "Técnica"),
                solucao_frente=safe_val(row, headers, "Solução Frente"),
                extra_person_1=safe_val(row, headers, "Extra Pessoa 1"),
                extra_person_2=safe_val(row, headers, "Extra Pessoa 2"),
                extra_person_3=safe_val(row, headers, "Extra Pessoa 3"),
                safira=safe_bool(row, headers, "Safira"),
                transamin=safe_bool(row, headers, "Transamin"),
                diprospam=safe_bool(row, headers, "Diprospam"),
                fumante=safe_bool(row, headers, "Fumante"),
                implante_secundario=safe_bool(row, headers, "Implante Secundário"),
            )
            db.session.add(s)
            success += 1

            if success % 200 == 0:
                db.session.commit()
                logger.info(f"  Progresso: {success}/{len(data)} cirurgias restauradas")

        except Exception as e:
            errors += 1
            logger.warning(f"  Linha {i+2} ignorada: {e}")

    db.session.commit()
    logger.info(f"✅ Cirurgias: {success} restauradas, {errors} erros")
    return success


def restore_necroses(app, db, Necrose, headers, data):
    logger.info(f"Iniciando restauração de {len(data)} necroses...")
    db.session.query(Necrose).delete()
    db.session.commit()

    success = 0
    errors = 0
    for i, row in enumerate(data):
        try:
            n = Necrose(
                surgery_id=safe_int(row, headers, "ID Cirurgia") or None,
                unidade=safe_val(row, headers, "Unidade"),
                paciente_nome=safe_val(row, headers, "Paciente"),
                data_cirurgia=safe_date(row, headers, "Data Cirurgia"),
                data_avaliacao=safe_date(row, headers, "Data Avaliação"),
                medico_responsavel=safe_val(row, headers, "Médico Responsável"),
                tem_necrose=safe_bool(row, headers, "Tem Necrose"),
                grau_necrose=safe_val(row, headers, "Grau Necrose"),
                localizacao=safe_val(row, headers, "Localização"),
                numero_necroses=safe_int(row, headers, "Nº Necroses"),
                primeira_faixa=safe_bool(row, headers, "1ª Faixa"),
                segunda_faixa=safe_bool(row, headers, "2ª Faixa"),
                terceira_faixa=safe_bool(row, headers, "3ª Faixa"),
                coroa=safe_bool(row, headers, "Coroa"),
                tamanho_1_cm=safe_float(row, headers, "Tamanho 1 (cm)"),
                tamanho_2_cm=safe_float(row, headers, "Tamanho 2 (cm)"),
                tamanho_3_cm=safe_float(row, headers, "Tamanho 3 (cm)"),
                tamanho_4_cm=safe_float(row, headers, "Tamanho 4 (cm)"),
                descricao=safe_val(row, headers, "Descrição"),
                tratamento_aplicado=safe_val(row, headers, "Tratamento"),
                observacoes=safe_val(row, headers, "Observações"),
                status=safe_val(row, headers, "Status"),
                data_resolucao=safe_date(row, headers, "Data Resolução"),
            )
            db.session.add(n)
            success += 1
        except Exception as e:
            errors += 1
            logger.warning(f"  Linha {i+2} ignorada: {e}")

    db.session.commit()
    logger.info(f"✅ Necroses: {success} restauradas, {errors} erros")
    return success


def main():
    logger.info("=" * 60)
    logger.info("RECUPERAÇÃO DO BANCO DE DADOS - ICB")
    logger.info("Fonte: Google Sheets (3.388 cirurgias, 40 necroses)")
    logger.info("=" * 60)

    # 1. Testar conexão com banco
    logger.info("1. Testando conexão com o banco...")
    try:
        import psycopg2
        url = os.environ.get("DATABASE_URL", "postgresql://neondb_owner:npg_BoiquUY6v8CN@ep-flat-salad-a4j7rvot.us-east-1.aws.neon.tech/neondb?sslmode=require")
        conn = psycopg2.connect(url, connect_timeout=10)
        conn.close()
        logger.info("   ✅ Banco de dados acessível!")
    except Exception as e:
        logger.error(f"   ❌ Banco inacessível: {e}")
        logger.error("   ⚠️  Acesse console.neon.tech e reative o endpoint antes de rodar este script.")
        return False

    # 2. Buscar dados do Google Sheets
    logger.info("2. Buscando dados do Google Sheets...")
    try:
        service = _get_sheets_service()
        surgery_headers, surgery_data = fetch_sheet_data(service, "Cirurgias")
        necrose_headers, necrose_data = fetch_sheet_data(service, "Necroses")
        logger.info(f"   ✅ Cirurgias: {len(surgery_data)} registros")
        logger.info(f"   ✅ Necroses: {len(necrose_data)} registros")
    except Exception as e:
        logger.error(f"   ❌ Erro ao buscar Google Sheets: {e}")
        return False

    # 3. Restaurar no banco
    logger.info("3. Restaurando no banco de dados...")
    from app import app, db, Surgery, Necrose
    with app.app_context():
        s_count = restore_surgeries(app, db, Surgery, surgery_headers, surgery_data)
        n_count = restore_necroses(app, db, Necrose, necrose_headers, necrose_data)

    logger.info("=" * 60)
    logger.info(f"✅ RECUPERAÇÃO CONCLUÍDA!")
    logger.info(f"   Cirurgias restauradas: {s_count}")
    logger.info(f"   Necroses restauradas:  {n_count}")
    logger.info("=" * 60)
    return True


if __name__ == "__main__":
    main()

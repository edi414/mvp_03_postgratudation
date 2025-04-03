import pandas as pd
import logging
from datetime import datetime
import shutil
import sys
from scripts.reading_files import ExtratoTransacao
from scripts.transform_files import TransformerTrasacoes
from scripts.connection_db import (
    insert_df_to_db, 
    get_existing_records,
    register_file_processing
)
import psycopg2
from psycopg2 import sql

def prepare_dimension_tables(df_transacoes):
    df_tempo = pd.DataFrame({
        'data': pd.to_datetime(df_transacoes['data_transacao']).dt.date,
        'dia_semana': pd.to_datetime(df_transacoes['data_transacao']).dt.day_name(),
        'mes': pd.to_datetime(df_transacoes['data_transacao']).dt.month,
        'ano': pd.to_datetime(df_transacoes['data_transacao']).dt.year
    }).drop_duplicates()

    df_loja = pd.DataFrame({
        'identificacao_loja': df_transacoes['identificacao_loja'],
        'codigo_ec_venda': df_transacoes['codigo_ec_venda'],
        'codigo_ec_pagamento': df_transacoes['codigo_ec_pagamento'],
        'cnpj_ec_pagamento': df_transacoes['cnpj_ec_pagamento']
    }).drop_duplicates()

    df_produto = pd.DataFrame({
        'codigo_produto': df_transacoes['codigo_produto'],
        'descricao': df_transacoes['codigo_produto']
    }).drop_duplicates()

    df_pagamento = pd.DataFrame({
        'codigo_bandeira': df_transacoes['codigo_bandeira'],
        'tipo_pagamento': df_transacoes['tipo_transacao']
    }).drop_duplicates()

    return df_tempo, df_loja, df_produto, df_pagamento

def prepare_fact_table(df_transacoes):
    df_fact = df_transacoes[[
        'data_transacao', 'horario_transacao', 'tipo_lancamento', 'data_lancamento',
        'valor_bruto_venda', 'valor_liquido_venda', 'valor_desconto', 'tipo_produto',
        'meio_captura', 'tipo_transacao', 'codigo_bandeira', 'codigo_produto',
        'identificacao_loja', 'nsu_host_transacao', 'numero_cartao', 'numero_parcela',
        'numero_total_parcelas', 'nsu_host_parcela', 'valor_bruto_parcela',
        'valor_desconto_parcela', 'valor_liquido_parcela', 'banco', 'agencia',
        'conta', 'codigo_autorizacao', 'valor_tx_interchange_tarifa',
        'valor_tx_administracao', 'valor_tx_interchange_parcela',
        'valor_tx_administracao_parcela', 'valor_redutor_multi_fronteira',
        'valor_tx_antecipacao', 'valor_liquido_antecipado', 'codigo_pedido',
        'sigla_pais', 'data_vencimento_original', 'indicador_deb_balance',
        'indicador_reenvio', 'nsu_origem', 'numero_operacao_recebivel',
        'sequencial_operacao_recebivel', 'tipo_operacao_recebivel',
        'valor_operacao_recebivel'
    ]].copy()
    
    return df_fact

def insert_dimension_if_not_exists(df_dimension, table_name, key_column, connection_params, conn=None):
    """Insere registros na tabela dimensional se não existirem"""
    try:
        if conn is None:
            conn = psycopg2.connect(
                host=connection_params['host'],
                port=connection_params['port'],
                user=connection_params['user'],
                password=connection_params['password'],
                database=connection_params['database']
            )
            conn.autocommit = False
            should_close = True
        else:
            should_close = False

        existing_records = get_existing_records(
            user=connection_params['user'],
            host=connection_params['host'],
            password=connection_params['password'],
            database=connection_params['database'],
            port=connection_params['port'],
            schema='unica_transactions',
            table=table_name,
            key_column=key_column,
            conn=conn
        )
        
        # Filtra apenas registros novos
        new_records = df_dimension[~df_dimension[key_column].isin(existing_records)]
        
        if not new_records.empty:
            insert_df_to_db(
                user=connection_params['user'],
                host=connection_params['host'],
                password=connection_params['password'],
                database=connection_params['database'],
                port=connection_params['port'],
                schema='unica_transactions',
                table=table_name,
                df=new_records,
                conn=conn
            )
            logging.info(f"{len(new_records)} novos registros inseridos na tabela {table_name}.")
        else:
            logging.info(f"Nenhum novo registro para inserir na tabela {table_name}.")

        if should_close:
            conn.close()

    except Exception as e:
        if should_close and conn:
            conn.close()
        raise e

def insert_df_to_db(user, host, password, database, port, schema, table, df, conn=None):
    """Insere DataFrame no banco de dados"""
    try:
        if conn is None:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            conn.autocommit = False
            should_close = True
        else:
            should_close = False

        # Converte DataFrame para lista de tuplas
        records = [tuple(x) for x in df.to_numpy()]
        
        # Obtém nomes das colunas
        columns = ', '.join(df.columns)
        
        # Cria string de placeholders
        placeholders = ', '.join(['%s'] * len(df.columns))
        
        # Query de inserção
        query = f"INSERT INTO {schema}.{table} ({columns}) VALUES ({placeholders})"
        
        # Executa inserção
        with conn.cursor() as cur:
            cur.executemany(query, records)
        
        if should_close:
            conn.close()

    except Exception as e:
        if should_close and conn:
            conn.close()
        raise e

def get_existing_records(user, host, password, database, port, schema, table, key_column, conn=None):
    """Obtém registros existentes da tabela"""
    try:
        if conn is None:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            conn.autocommit = False
            should_close = True
        else:
            should_close = False

        with conn.cursor() as cur:
            cur.execute(f"SELECT {key_column} FROM {schema}.{table}")
            existing_records = [row[0] for row in cur.fetchall()]
        
        if should_close:
            conn.close()

        return existing_records

    except Exception as e:
        if should_close and conn:
            conn.close()
        raise e

def register_file_processing(user, host, password, database, port, file_name, data_geracao, 
                            status, error=None, google_drive_path=None, schema='unica_transactions', conn=None):
    """Registra o processamento de um arquivo"""
    try:
        if conn is None:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            conn.autocommit = False
            should_close = True
        else:
            should_close = False

        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {schema}.controle_arquivos 
                (nome_arquivo, data_geracao, data_processamento, status_processamento, 
                erro_processamento, arquivo_google_drive_path)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (file_name, data_geracao, datetime.now(), status, error, google_drive_path)
            )
            file_id = cur.fetchone()[0]
        
        if should_close:
            conn.close()

        return file_id

    except Exception as e:
        if should_close and conn:
            conn.close()
        raise e

def process_file(file_name, local_file_path, google_drive_path, connection_params, is_tryout=False):
    """Processa um arquivo individual"""
    conn = None
    try:
        # Estabelece conexão com o banco
        conn = psycopg2.connect(
            host=connection_params['host'],
            port=connection_params['port'],
            user=connection_params['user'],
            password=connection_params['password'],
            database=connection_params['database']
        )
        
        conn.autocommit = False
        extrato = ExtratoTransacao(file_path=local_file_path)
        df_header, df_transacoes, df_trailer = extrato.process_file()

        df_header = df_header[['codigo_registro', 'versao_layout', 'data_geracao',
                            'hora_geracao', 'tipo_processamento', 'destinatario']]
        df_summary_processing = pd.concat([df_header, df_trailer[['total_registros']]], axis=1)
        df_summary_processing['file_path'] = google_drive_path
        df_summary_processing['file_name'] = file_name
        df_transacoes['file_name'] = file_name

        if not (
            (df_summary_processing['codigo_registro'] == 'A0').all() and
            (df_summary_processing['versao_layout'] == '002.0a').all() and
            (df_summary_processing['destinatario'] == '000051309').all()
        ):
            error_msg = "Validação falhou: Verifique 'codigo_registro', 'versao_layout' e 'destinatario'."
            register_file_processing(
                **connection_params,
                file_name=file_name,
                data_geracao=pd.to_datetime(df_header['data_geracao'].iloc[0]).date(),
                status='ERRO',
                error=error_msg,
                google_drive_path=google_drive_path,
                conn=conn
            )
            return False

        transacoes_transformer = TransformerTrasacoes(dataframe=df_transacoes)
        df_transacoes_validated = transacoes_transformer.validate_all()
        
        if isinstance(df_transacoes_validated, list):
            error_msg = "\n".join(df_transacoes_validated)
            register_file_processing(
                **connection_params,
                file_name=file_name,
                data_geracao=pd.to_datetime(df_header['data_geracao'].iloc[0]).date(),
                status='ERRO',
                error=error_msg,
                google_drive_path=google_drive_path,
                conn=conn
            )
            return False

        df_tempo, df_loja, df_produto, df_pagamento = prepare_dimension_tables(df_transacoes_validated)
        
        # Inserir dimensões e obter IDs
        insert_dimension_if_not_exists(df_tempo, 'tempo', 'data', connection_params, conn)
        insert_dimension_if_not_exists(df_loja, 'loja', 'identificacao_loja', connection_params, conn)
        insert_dimension_if_not_exists(df_produto, 'produto', 'codigo_produto', connection_params, conn)
        insert_dimension_if_not_exists(df_pagamento, 'pagamento', 'codigo_bandeira', connection_params, conn)
        
        df_fact = prepare_fact_table(df_transacoes_validated)

        # Registrar processamento do arquivo e obter file_id
        file_id = register_file_processing(
            **connection_params,
            file_name=file_name,
            data_geracao=pd.to_datetime(df_header['data_geracao'].iloc[0]).date(),
            status='SUCESSO',
            google_drive_path=google_drive_path,
            conn=conn
        )

        if not file_id:
            raise Exception("Falha ao registrar processamento do arquivo")

        df_fact['file_id'] = file_id

        # Inserir dados na tabela de fatos
        insert_df_to_db(
            **connection_params,
            schema='unica_transactions',
            table='transacoes',
            df=df_fact,
            conn=conn
        )

        # Se chegou até aqui sem erros, commit a transação
        conn.commit()

        if not is_tryout:
            shutil.move(local_file_path, google_drive_path)

        return True

    except Exception as e:
        # Em caso de erro, rollback na transação
        if conn:
            conn.rollback()
            
        error_msg = str(e)
        # Registrar erro usando uma nova conexão
        try:
            register_file_processing(
                **connection_params,
                file_name=file_name,
                data_geracao=datetime.now().date(),  # Data atual como fallback
                status='ERRO',
                error=error_msg,
                google_drive_path=google_drive_path
            )
        except Exception as register_error:
            logging.error(f"Erro ao registrar erro de processamento: {register_error}")
            
        return False
    finally:
        if conn:
            conn.close()

def analyze_files_to_process(sftp_files, google_drive_files, db_status):
    """Analisa quais arquivos precisam ser processados baseado em diferentes cenários"""
    files_to_process = []
    files_to_report = []
    
    # Conjunto de todos os arquivos únicos (SFTP + Google Drive)
    all_files = set(sftp_files + google_drive_files)
    
    for file in all_files:
        if "EXTRATO" not in file:
            continue
            
        # Cenário 1: Arquivo novo no SFTP
        if file in sftp_files and file not in google_drive_files and file not in db_status:
            files_to_process.append(file)
            logging.info(f"Arquivo novo encontrado no SFTP: {file}")
            continue
            
        # Cenário 2: Arquivo existe no Google Drive mas não está registrado no banco
        if file in google_drive_files and file not in db_status:
            files_to_process.append(file)
            logging.info(f"Arquivo encontrado no Google Drive sem registro no banco: {file}")
            continue
            
        # Cenário 3: Arquivo está registrado com erro no banco
        if file in db_status and db_status[file]['status'] == 'ERRO':
            files_to_process.append(file)
            logging.info(f"Arquivo com erro encontrado para reprocessamento: {file}")
            continue
            
        # Cenário 4: Arquivo está registrado como sucesso mas não existe no Google Drive
        if file in db_status and db_status[file]['status'] == 'SUCESSO' and file not in google_drive_files:
            files_to_report.append({
                'file': file,
                'status': 'DESINCRONIZADO',
                'message': 'Arquivo registrado como sucesso mas não existe no Google Drive'
            })
            logging.warning(f"Arquivo desincronizado encontrado: {file}")
            continue
            
        # Cenário 5: Arquivo existe no SFTP mas está com status diferente de SUCESSO no banco
        if file in sftp_files and file in db_status and db_status[file]['status'] != 'SUCESSO':
            files_to_process.append(file)
            logging.info(f"Arquivo encontrado no SFTP com status não sucesso no banco: {file}")
            continue
    
    # Log resumo da análise
    logging.info(f"Total de arquivos analisados: {len(all_files)}")
    logging.info(f"Arquivos a serem processados: {len(files_to_process)}")
    logging.info(f"Arquivos com inconsistências: {len(files_to_report)}")
    
    return files_to_process, files_to_report



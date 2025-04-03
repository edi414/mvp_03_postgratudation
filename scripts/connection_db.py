from psycopg2 import sql
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import logging
from datetime import datetime
import os
from typing import Dict, List, Optional, Union

def get_existing_records(user, host, password, database, port, schema, table, key_column):
    """Retorna lista de registros existentes em uma tabela baseado na coluna chave"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        with conn.cursor() as cur:
            query = sql.SQL("""
                SELECT {} 
                FROM {}.{}
            """).format(
                sql.Identifier(key_column),
                sql.Identifier(schema),
                sql.Identifier(table)
            )
            
            cur.execute(query)
            results = cur.fetchall()
            return [row[0] for row in results]
            
    except Exception as e:
        logging.error(f"Erro ao buscar registros existentes: {e}")
        raise
    finally:
        if conn:
            conn.close()

def insert_df_to_db(user, host, password, database, port, schema, table, df):
    """Insere um DataFrame em uma tabela do banco de dados"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        # Converte o DataFrame para uma lista de tuplas
        records = [tuple(x) for x in df.values]
        
        # Obtém os nomes das colunas
        columns = df.columns.tolist()
        
        # Cria a query de inserção
        query = sql.SQL("""
            INSERT INTO {}.{} ({})
            VALUES ({})
        """).format(
            sql.Identifier(schema),
            sql.Identifier(table),
            sql.SQL(', ').join(map(sql.Identifier, columns)),
            sql.SQL(', ').join(sql.Placeholder() * len(columns))
        )
        
        with conn.cursor() as cur:
            cur.executemany(query, records)
            conn.commit()
            logging.info(f"{len(records)} registros inseridos na tabela {table}")
            
    except Exception as e:
        logging.error(f"Erro ao inserir dados na tabela {table}: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def get_processed_files(user, host, password, database, port, schema='unica_transactions'):
    """Retorna lista de arquivos já processados com sucesso"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        with conn.cursor() as cur:
            query = sql.SQL("""
                SELECT nome_arquivo 
                FROM {}.controle_arquivos 
                WHERE status_processamento = 'SUCESSO'
            """).format(sql.Identifier(schema))
            
            cur.execute(query)
            processed_files = [row[0] for row in cur.fetchall()]
            
            return processed_files
            
    except Exception as e:
        logging.error(f"Erro ao buscar arquivos processados: {e}")
        raise
    finally:
        if conn:
            conn.close()

def register_file_processing(user, host, password, database, port, file_name, data_geracao, 
                           status, error=None, google_drive_path=None, schema='unica_transactions'):
    """Registra o processamento de um arquivo e retorna o ID do registro"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        with conn.cursor() as cur:
            query = sql.SQL("""
                INSERT INTO {}.controle_arquivos 
                (nome_arquivo, data_geracao, data_processamento, status_processamento, 
                erro_processamento, arquivo_google_drive_path)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """).format(sql.Identifier(schema))
            
            cur.execute(query, (
                file_name,
                data_geracao,
                datetime.now(),
                status,
                error,
                google_drive_path
            ))
            
            file_id = cur.fetchone()[0]
            conn.commit()
            logging.info(f"Registro de processamento criado para o arquivo {file_name}")
            return file_id
            
    except Exception as e:
        logging.error(f"Erro ao registrar processamento do arquivo {file_name}: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def get_google_drive_files(directory):
    """Lista arquivos existentes no diretório do Google Drive"""
    try:
        if not os.path.exists(directory):
            logging.warning(f"Diretório do Google Drive não encontrado: {directory}")
            return []
            
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        return files
    except Exception as e:
        logging.error(f"Erro ao listar arquivos do Google Drive: {e}")
        return []

def get_file_processing_status(user, host, password, database, port, schema='unica_transactions'):
    """Retorna o status de processamento de todos os arquivos registrados"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        with conn.cursor() as cur:
            query = sql.SQL("""
                SELECT nome_arquivo, status_processamento, erro_processamento
                FROM {}.controle_arquivos
            """).format(sql.Identifier(schema))
            
            cur.execute(query)
            results = cur.fetchall()
            
            # Converte para um dicionário para fácil acesso
            return {row[0]: {'status': row[1], 'erro': row[2]} for row in results}
            
    except Exception as e:
        logging.error(f"Erro ao buscar status de processamento dos arquivos: {e}")
        raise
    finally:
        if conn:
            conn.close()

def delete_file_data(user: str, host: str, password: str, database: str, 
                    port: str, file_name: str, schema: str = 'unica_transactions') -> bool:
    conn = None
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        conn.autocommit = False
        
        with conn.cursor() as cur:
            cur.execute(sql.SQL("""
                SELECT id FROM {}.controle_arquivos 
                WHERE nome_arquivo = %s
            """).format(sql.Identifier(schema)), (file_name,))
            
            result = cur.fetchone()
            if not result:
                logging.warning(f"Arquivo {file_name} não encontrado no banco de dados")
                return False
                
            file_id = result[0]
            
            cur.execute(sql.SQL("""
                DELETE FROM {}.transacoes 
                WHERE file_id = %s
            """).format(sql.Identifier(schema)), (file_id,))
            
            cur.execute(sql.SQL("""
                DELETE FROM {}.controle_arquivos 
                WHERE id = %s
            """).format(sql.Identifier(schema)), (file_id,))
            
            conn.commit()
            logging.info(f"Dados do arquivo {file_name} deletados com sucesso")
            return True
            
    except Exception as e:
        logging.error(f"Erro ao deletar dados do arquivo {file_name}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

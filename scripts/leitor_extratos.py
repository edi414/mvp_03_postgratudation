import pandas as pd
import logging
from datetime import datetime
import os
import shutil
from ftplib import FTP_TLS
import pandas as pd
from scripts.reading_files import ExtratoTransacao
from scripts.transform_files import TransformerTrasacoes
from scripts.connection_db import insert_df_to_db

host = "sftp1.tribanco.com.br"
user = "ftp_edi_supermercadopopular"
password = "xhAZYpXWMKoYFz0SDvX0*"
local_directory = os.getcwd()
google_drive_directory = 'G:/Meu Drive/Reports/Maquinetas/integration_conciliacao/processed_files'

connection_database = {
    'host': 'monorail.proxy.rlwy.net',
    'user': 'postgres',
    'password': 'G1CG2B*6d6GEDdABGcf--dA5cb*5bEf6',
    'dbname': 'railway',
    'port': '48186'
}

log_directory = os.path.join(local_directory, "log")
os.makedirs(log_directory, exist_ok=True)
log_filename = os.path.join(log_directory, f"log_{datetime.now().strftime('%d%m%y_%H_%M_%S')}.txt")
logging.basicConfig(filename=log_filename, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

try:
    ftps = FTP_TLS(host)
    ftps.login(user=user, passwd=password)
    ftps.prot_p()
    
    logging.info("Conexão FTPS estabelecida com sucesso.")

    ftps.cwd("Saida")
    files = ftps.nlst()

    processed_files = set(os.listdir(google_drive_directory))
    logging.info("Arquivos já processados no Google Drive listados.")

    extrato_files = [file for file in files if "EXTRATO" in file and file not in processed_files]

    logging.info(f"Arquivos a serem processados: {extrato_files}")

    for file_name in extrato_files:
        logging.info(f"Baixando e processando arquivo: {file_name}")

        local_file_path = os.path.join(local_directory, file_name)

        with open(local_file_path, 'wb') as local_file:
            ftps.retrbinary(f"RETR {file_name}", local_file.write)

        logging.info(f"Arquivo {file_name} baixado com sucesso.")

        extrato = ExtratoTransacao(file_path=file_name)
        df_header, df_transacoes, df_trailer = extrato.process_file()

        # Prepara o DataFrame de resumo do processamento
        df_header = df_header[['codigo_registro', 'versao_layout', 'data_geracao',
                            'hora_geracao', 'tipo_processamento', 'destinatario']]
        df_summary_processing = pd.concat([df_header, df_trailer[['total_registros']]], axis=1)
        df_summary_processing['file_path'] = os.path.join(google_drive_directory, file_name)
        df_summary_processing['file_name'] = file_name
        df_transacoes['file_name'] = file_name

        # Validações específicas de df_summary_processing
        if not (
            (df_summary_processing['codigo_registro'] == 'A0').all() and
            (df_summary_processing['versao_layout'] == '002.0a').all() and
            (df_summary_processing['destinatario'] == '000051309').all()
        ):
            logging.error(f"Validação falhou para o arquivo {file_name}. Verifique 'codigo_registro', 'versao_layout' e 'destinatario'.")
            os.remove(local_file_path)
            continue

        # Validação e transformação de df_transacoes
        transacoes_transformer = TransformerTrasacoes(dataframe=df_transacoes)
        df_transacoes_validated = transacoes_transformer.validate_all()
        
        if isinstance(df_transacoes_validated, list):
            logging.error(f"Erro na validação das transações para o arquivo {file_name}:")
            for error in df_transacoes_validated:
                logging.error(error)
            os.remove(local_file_path)
            continue
        
        try:
            insert_df_to_db(
                user= connection_database['user'],
                host= connection_database['host'],
                password= connection_database['password'],
                database= connection_database['dbname'],
                port= connection_database['port'],
                schema= 'public',
                table= 'reg_extrato_unica',
                df= df_transacoes_validated)
            
            logging.info(f"Dados de transações inseridos com sucesso para o arquivo {file_name}.")

            insert_df_to_db(
                user= connection_database['user'],
                host= connection_database['host'],
                password= connection_database['password'],
                database= connection_database['dbname'],
                port= connection_database['port'],
                schema= 'public',
                table= 'processing_files_extratos',
                df= df_summary_processing)
            
            logging.info(f"Dados de resumo inseridos com sucesso para o arquivo {file_name}.")

            shutil.move(local_file_path, os.path.join(google_drive_directory, file_name))
            logging.info(f"Arquivo {file_name} movido para o Google Drive com sucesso.")
                        
        except Exception as e:
            os.remove(local_file_path)
            logging.error(f"Erro ao inserir dados no banco de dados para o arquivo {file_name}: {e}")


    ftps.quit()
    logging.info("Conexão FTPS fechada com sucesso.")

except Exception as e:
    logging.error(f"Erro ao conectar ao FTPS: {e}")
    

# df_EX = ExtratoTransacao(file_path='EXTRATO_UNICA_51309_20241102_00027')
# df_EX_E, DF_g, DF_T = df_EX.process_file()

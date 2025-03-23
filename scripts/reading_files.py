import pandas as pd

class ExtratoTransacao:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None
        self.transacoes = []
    
    def load_file(self):
        with open(self.file_path, 'r', encoding='latin-1') as f:
            self.data = f.readlines()
    
    def parse_header(self):
        header = self.data[0]
        if header.startswith("A0"):
            return {
                'codigo_registro': header[0:2],
                'versao_layout': header[2:8],
                'data_geracao': header[8:16],
                'hora_geracao': header[16:22],
                'id_movimento': header[22:28],
                'nome_admin': header[28:58].strip(),
                'remetente': header[58:62],
                'destinatario': header[62:71],
                'tipo_processamento': header[71:72],
                'nseq_registro': header[72:78]
            }
        else:
            print("Cabeçalho não encontrado ou inválido.")
            return None

    def parse_trailer(self):
        trailer = self.data[-1]
        if trailer.startswith("A9"):
            return {
                'codigo_registro': trailer[0:2],
                'total_registros': trailer[2:8],
                'nseq_registro': trailer[8:14]
            }
        else:
            print("Trailer não encontrado ou inválido.")
            return None

    def parse_transacao(self, transacao):
        def parse_numeric_field(value, decimal_places=2):
            if value.strip().isdigit():
                integer_part = value[:-decimal_places]
                decimal_part = value[-decimal_places:]
                return f"{int(integer_part)}.{decimal_part}"
            return value.strip()
        
        return {
            "codigo_registro": transacao[0:2].strip(),
            "identificacao_loja": transacao[2:17].strip().zfill(15),
            "nsu_host_transacao": transacao[17:29].strip(),
            "data_transacao": transacao[29:37].strip(),
            "horario_transacao": transacao[37:43].strip(),
            "tipo_lancamento": transacao[43:44].strip(),
            "data_lancamento": transacao[44:52].strip(),
            "tipo_produto": transacao[52:53].strip(),
            "meio_captura": transacao[53:54].strip(),
            "valor_bruto_venda": parse_numeric_field(transacao[54:65].strip()),
            "valor_desconto": parse_numeric_field(transacao[65:76].strip()),
            "valor_liquido_venda": parse_numeric_field(transacao[76:87].strip()),
            "numero_cartao": transacao[87:106].strip().zfill(19),
            "numero_parcela": transacao[106:108].strip().zfill(2),
            "numero_total_parcelas": transacao[108:110].strip().zfill(2),
            "nsu_host_parcela": transacao[110:122].strip().zfill(12),
            "valor_bruto_parcela": parse_numeric_field(transacao[122:133].strip()),
            "valor_desconto_parcela": parse_numeric_field(transacao[133:144].strip()),
            "valor_liquido_parcela": parse_numeric_field(transacao[144:155].strip()),
            "banco": transacao[155:158].strip(),
            "agencia": transacao[158:164].strip(),
            "conta": transacao[164:175].strip(),
            "codigo_autorizacao": transacao[175:187].strip().zfill(12),
            "codigo_bandeira": transacao[187:190].strip().zfill(3),
            "codigo_produto": transacao[190:193].strip().zfill(3),
            "valor_tx_interchange_tarifa": parse_numeric_field(transacao[193:204].strip()),
            "valor_tx_administracao": parse_numeric_field(transacao[204:215].strip()),
            "valor_tx_interchange_parcela": parse_numeric_field(transacao[215:226].strip()),
            "valor_tx_administracao_parcela": parse_numeric_field(transacao[226:237].strip()),
            "valor_redutor_multi_fronteira": parse_numeric_field(transacao[237:248].strip()),
            "valor_tx_antecipacao": parse_numeric_field(transacao[248:259].strip()),
            "valor_liquido_antecipado": parse_numeric_field(transacao[259:270].strip()),
            "tipo_transacao": transacao[270:272].strip(),
            "codigo_pedido": transacao[272:302].strip(),
            "sigla_pais": transacao[302:305].strip(),
            "reservado": transacao[305:356].strip(),
            "codigo_ec_venda": transacao[305:314].strip(),
            "codigo_ec_pagamento": transacao[314:323].strip(),
            "cnpj_ec_pagamento": transacao[323:337].strip(),
            "data_vencimento_original": transacao[337:345].strip(),
            "indicador_deb_balance": transacao[345:346].strip(),
            "indicador_reenvio": transacao[346:347].strip(),
            "nsu_origem": transacao[347:353].strip(),
            "reservado_final": transacao[353:356].strip(),
            "numero_operacao_recebivel": transacao[356:376].strip(),
            "sequencial_operacao_recebivel": transacao[376:378].strip(),
            "tipo_operacao_recebivel": transacao[378:379].strip(),
            "valor_operacao_recebivel": parse_numeric_field(transacao[379:390].strip()),
            "nseq": transacao[390:396+1].strip()
        }

    def parse_transacoes(self):
        self.transacoes = []
        for linha in self.data[1:-1]:  # Ignorar header e trailer
            if linha.startswith("CV"):
                transacao_info = self.parse_transacao(linha)
                self.transacoes.append(transacao_info)

    def to_dataframe(self):
        return pd.DataFrame(self.transacoes)

    def to_dataframe_header(self, header_info):
        return pd.DataFrame([header_info]) if header_info else pd.DataFrame()

    def to_dataframe_trailer(self, trailer_info):
        return pd.DataFrame([trailer_info]) if trailer_info else pd.DataFrame()

    def process_file(self):
        self.load_file()
        
        # Process header if it starts with "A0"
        header_info = self.parse_header()
        df_header = self.to_dataframe_header(header_info)
        
        # Process transactions if they start with "CV"
        self.parse_transacoes()
        df_transacoes = self.to_dataframe()
        
        # Process trailer if it starts with "A9"
        trailer_info = self.parse_trailer()
        df_trailer = self.to_dataframe_trailer(trailer_info)
        
        return df_header, df_transacoes, df_trailer




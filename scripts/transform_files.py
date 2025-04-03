import pandas as pd

class TransformerTrasacoes:
    def __init__(self, dataframe):
        self.df = dataframe
        self.errors = []

    def validate_structure(self):
        expected_columns = [
            "codigo_registro", "identificacao_loja", "nsu_host_transacao", "data_transacao", "horario_transacao",
            "tipo_lancamento", "data_lancamento", "tipo_produto", "meio_captura", "valor_bruto_venda",
            "valor_desconto", "valor_liquido_venda", "numero_cartao", "numero_parcela", "numero_total_parcelas",
            "nsu_host_parcela", "valor_bruto_parcela", "valor_desconto_parcela", "valor_liquido_parcela",
            "banco", "agencia", "conta", "codigo_autorizacao", "codigo_bandeira", "codigo_produto",
            "valor_tx_interchange_tarifa", "valor_tx_administracao", "valor_tx_interchange_parcela",
            "valor_tx_administracao_parcela", "valor_redutor_multi_fronteira", "valor_tx_antecipacao",
            "valor_liquido_antecipado", "tipo_transacao", "codigo_pedido", "sigla_pais", "reservado",
            "codigo_ec_venda", "codigo_ec_pagamento", "cnpj_ec_pagamento", "data_vencimento_original",
            "indicador_deb_balance", "indicador_reenvio", "nsu_origem", "reservado_final", "numero_operacao_recebivel",
            "sequencial_operacao_recebivel", "tipo_operacao_recebivel", "valor_operacao_recebivel", "nseq", "file_name"
        ]
        if list(self.df.columns) != expected_columns:
            self.errors.append("Estrutura do DataFrame está incorreta.")
            return False
        return True

    def validate_codigo_registro(self):
        if not self.df['codigo_registro'].apply(lambda x: isinstance(x, str) and len(x) == 2).all():
            self.errors.append("Erro no campo 'codigo_registro': Deve ter 2 caracteres.")

    def validate_identificacao_loja(self):
        if not self.df['identificacao_loja'].apply(lambda x: isinstance(x, str) and len(x) == 15 and x[1:].isdigit()).all():
            self.errors.append("Erro no campo 'identificacao_loja': Deve ter 15 dígitos no total, e os 14 últimos devem ser numéricos.")

    def validate_nsu_host_transacao(self):
        if not self.df['nsu_host_transacao'].apply(lambda x: isinstance(x, str) and len(x) == 12 and x.isdigit()).all():
            self.errors.append("Erro no campo 'nsu_host_transacao': Deve ter 12 dígitos numéricos.")
        else:
            self.df['nsu_host_transacao'] = self.df['nsu_host_transacao'].astype(int)

    def validate_data_transacao(self):
        if not self.df['data_transacao'].apply(lambda x: isinstance(x, str) and len(x) == 8 and x.isdigit()).all():
            self.errors.append("Erro no campo 'data_transacao': Deve estar no formato YYYYMMDD.")
        else:
            self.df['data_transacao'] = pd.to_datetime(self.df['data_transacao'], format='%Y%m%d', errors='coerce')
            if self.df['data_transacao'].isnull().any():
                self.errors.append("Erro na conversão de 'data_transacao': Formato inválido para datas.")

    def validate_horario_transacao(self): ## precisa mudar
        """Valida o campo 'horario_transacao'."""
        if not self.df['horario_transacao'].apply(lambda x: isinstance(x, str) and len(x) == 6 and x.isdigit()).all():
            self.errors.append("Erro no campo 'horario_transacao': Deve estar no formato HHMMSS.")

    def validate_tipo_lancamento(self):
        valid_values = {0: "Previsão", 1: "Liquidação Normal", 2: "Liquidação Antecipada"}
        
        try:
            self.df['tipo_lancamento'] = self.df['tipo_lancamento'].astype(int)
        except ValueError:
            self.errors.append("Erro no campo 'tipo_lancamento': Valores devem ser inteiros 0, 1 ou 2.")
            return

        if not self.df['tipo_lancamento'].apply(lambda x: x in valid_values).all():
            self.errors.append("Erro no campo 'tipo_lancamento': Deve ser 0, 1 ou 2.")
        else:
            self.df['tipo_lancamento'] = self.df['tipo_lancamento'].map(valid_values)
    
    def validate_data_lancamento(self):
        if not self.df['data_lancamento'].apply(lambda x: isinstance(x, str) and len(x) == 8 and x.isdigit()).all():
            self.errors.append("Erro no campo 'data_lancamento': Deve estar no formato YYYYMMDD.")
        else:
            self.df['data_lancamento'] = pd.to_datetime(self.df['data_lancamento'], format='%Y%m%d', errors='coerce')
            if self.df['data_lancamento'].isnull().any():
                self.errors.append("Erro na conversão de 'data_lancamento': Formato inválido para datas.")

    def validate_tipo_produto(self):
        if not self.df['tipo_produto'].apply(lambda x: x in ['C', 'D', 'V']).all():
            self.errors.append("Erro no campo 'tipo_produto': Deve ser 'C', 'D' ou 'V'.")

    def validate_meio_captura(self):
        valid_values = {
            '1': "Manual",
            '2': "Pos",
            '3': "Pdv",
            '4': "Trn Off",
            '5': "Internet",
            '6': "URA",
            '8': "Indefinido",
            '9': "Outros"
        }
        if not self.df['meio_captura'].apply(lambda x: x in valid_values).all():
            self.errors.append("Erro no campo 'meio_captura': Deve ser um dos valores permitidos.")
        else:
            self.df['meio_captura'] = self.df['meio_captura'].map(valid_values)
    
    def validate_valor_bruto_venda(self):
        if not self.df['valor_bruto_venda'].apply(lambda x: isinstance(x, str) and x.replace('.', '', 1).isdigit()).all():
            self.errors.append("Erro no campo 'valor_bruto_venda': Deve estar no formato numérico com ponto decimal.")
        else:
            self.df['valor_bruto_venda'] = self.df['valor_bruto_venda'].astype(float)
    
    def validate_valor_desconto(self):
        if not self.df['valor_desconto'].apply(lambda x: isinstance(x, str) and x.replace('.', '', 1).isdigit()).all():
            self.errors.append("Erro no campo 'valor_desconto': Deve estar no formato numérico com ponto decimal.")
        else:
            self.df['valor_desconto'] = self.df['valor_desconto'].astype(float)

    def validate_valor_liquido_venda(self):
        if not self.df['valor_liquido_venda'].apply(lambda x: isinstance(x, str) and x.replace('.', '', 1).isdigit()).all():
            self.errors.append("Erro no campo 'valor_liquido_venda': Deve estar no formato numérico com ponto decimal.")
        else:
            self.df['valor_liquido_venda'] = self.df['valor_liquido_venda'].astype(float)

    def validate_numero_cartao(self):
        if not self.df['numero_cartao'].apply(lambda x: isinstance(x, str) and len(x) == 19).all():
            self.errors.append("Erro no campo 'numero_cartao': Deve ter exatamente 19 caracteres.")

    def validate_numero_parcela(self):
        if not self.df['numero_parcela'].apply(lambda x: isinstance(x, int) or (isinstance(x, str) and x.isdigit())).all():
            self.errors.append("Erro no campo 'numero_parcela': Deve ser zero ou um número.")
        else:
            self.df['numero_parcela'] = self.df['numero_parcela'].astype(int)

    def validate_numero_total_parcelas(self):
        if not self.df['numero_total_parcelas'].apply(lambda x: isinstance(x, int) or (isinstance(x, str) and x.isdigit())).all():
            self.errors.append("Erro no campo 'numero_total_parcelas': Deve ser zero ou um número.")
        else:
            self.df['numero_total_parcelas'] = self.df['numero_total_parcelas'].astype(int)
    
    def validate_nsu_host_parcela(self):
        if not self.df['nsu_host_parcela'].apply(lambda x: isinstance(x, str) and (x.isdigit() and (len(x) == 0 or len(x) == 12))).all():
            self.errors.append("Erro no campo 'nsu_host_parcela': Deve ter 12 dígitos ou estar vazio.")
        else:
            self.df['nsu_host_parcela'] = self.df['nsu_host_parcela'].apply(lambda x: int(x) if x else 0)
    
    def validate_valor_bruto_parcela(self):
        if not self.df['valor_bruto_parcela'].apply(lambda x: isinstance(x, str) and x.replace('.', '', 1).isdigit()).all():
            self.errors.append("Erro no campo 'valor_bruto_parcela': Deve estar no formato numérico com ponto decimal.")
        else:
            self.df['valor_bruto_parcela'] = self.df['valor_bruto_parcela'].astype(float)

    def validate_valor_desconto_parcela(self):
        if not self.df['valor_desconto_parcela'].apply(lambda x: isinstance(x, str) and x.replace('.', '', 1).isdigit()).all():
            self.errors.append("Erro no campo 'valor_desconto_parcela': Deve estar no formato numérico com ponto decimal.")
        else:
            self.df['valor_desconto_parcela'] = self.df['valor_desconto_parcela'].astype(float)

    def validate_valor_liquido_parcela(self):
        if not self.df['valor_liquido_parcela'].apply(lambda x: isinstance(x, str) and x.replace('.', '', 1).isdigit()).all():
            self.errors.append("Erro no campo 'valor_liquido_parcela': Deve estar no formato numérico com ponto decimal.")
        else:
            self.df['valor_liquido_parcela'] = self.df['valor_liquido_parcela'].astype(float)

    def validate_banco(self):
        if not self.df['banco'].apply(lambda x: isinstance(x, str) and len(x) == 3).all():
            self.errors.append("Erro no campo 'banco': Deve ter exatamente 3 dígitos.")

    def validate_agencia(self):
        if not self.df['agencia'].apply(lambda x: isinstance(x, str) and len(x) == 6).all():
            self.errors.append("Erro no campo 'agencia': Deve ter exatamente 6 dígitos.")

    def validate_conta(self):
        if not self.df['conta'].apply(lambda x: isinstance(x, str) and len(x) == 6).all():
            self.errors.append("Erro no campo 'conta': Deve ter exatamente 6 dígitos.")

    def validate_codigo_autorizacao(self):
        if not self.df['codigo_autorizacao'].apply(lambda x: isinstance(x, str) and len(x) == 12).all():
            self.errors.append("Erro no campo 'codigo_autorizacao': Deve ter exatamente 12 dígitos.")
    
    def validate_codigo_bandeira(self):
        valid_values = {'1': "Master", '2': "Visa", '7': "Elo"}

        self.df['codigo_bandeira'] = self.df['codigo_bandeira'].apply(lambda x: str(int(x)))

        if not self.df['codigo_bandeira'].apply(lambda x: x in valid_values).all():
            self.errors.append("Erro no campo 'codigo_bandeira': Deve ser 1, 2 ou 7.")
        else:
            self.df['codigo_bandeira'] = self.df['codigo_bandeira'].map(valid_values)
    
    def validate_codigo_produto(self):
        valid_values = {
            '1': "Visa Crédito", '2': "Master Crédito", '3': "Visa Débito", 
            '4': "Master Débito", '5': "Elo Crédito", '6': "Elo Débito", '10': 'Outros',
            '12': 'Outros', '8': 'Outros', '9': 'Outros', '7': 'Outros', '11': 'Outros'
        }
        self.df['codigo_produto'] = self.df['codigo_produto'].apply(lambda x: str(int(x)))

        # Filtra linhas com valores inválidos
        invalid_rows = self.df.loc[~self.df['codigo_produto'].apply(lambda x: x in valid_values)]

        if not invalid_rows.empty:
            # Extrai valores inválidos e seus índices
            invalid_values = invalid_rows['codigo_produto'].unique()
            invalid_indexes = invalid_rows.index.tolist()

            self.errors.append(
                f"Erro no campo 'codigo_produto': Valores inválidos encontrados: {invalid_values} "
                f"nas linhas: {invalid_indexes}. "
                f"Deve ser um dos valores permitidos: {list(valid_values.keys())}."
            )
            raise ValueError(self.errors)
        else:
            self.df['codigo_produto'] = self.df['codigo_produto'].map(valid_values)

    def validate_valor_tx_interchange_tarifa(self):
        if not self.df['valor_tx_interchange_tarifa'].apply(lambda x: isinstance(x, str) and x.replace('.', '', 1).isdigit()).all():
            self.errors.append("Erro no campo 'valor_tx_interchange_tarifa': Deve estar no formato numérico com ponto decimal.")
        else:
            self.df['valor_tx_interchange_tarifa'] = self.df['valor_tx_interchange_tarifa'].astype(float)

    def validate_valor_tx_administracao(self):
        if not self.df['valor_tx_administracao'].apply(lambda x: isinstance(x, str) and x.replace('.', '', 1).isdigit()).all():
            self.errors.append("Erro no campo 'valor_tx_administracao': Deve estar no formato numérico com ponto decimal.")
        else:
            self.df['valor_tx_administracao'] = self.df['valor_tx_administracao'].astype(float)

    def validate_valor_tx_interchange_parcela(self):
        if not self.df['valor_tx_interchange_parcela'].apply(lambda x: isinstance(x, str) and x.replace('.', '', 1).isdigit()).all():
            self.errors.append("Erro no campo 'valor_tx_interchange_parcela': Deve estar no formato numérico com ponto decimal.")
        else:
            self.df['valor_tx_interchange_parcela'] = self.df['valor_tx_interchange_parcela'].astype(float)

    def validate_tipo_transacao(self):
        valid_values = {'00': "Normal"}
        invalid_values = ['01', '02', '03', '04']
        
        if not self.df['tipo_transacao'].apply(lambda x: x in valid_values or x in invalid_values).all():
            self.errors.append("Erro no campo 'tipo_transacao': Deve ser '00' para transações válidas.")
        else:
            self.df['tipo_transacao'] = self.df['tipo_transacao'].apply(lambda x: valid_values.get(x, None))
            if self.df['tipo_transacao'].isnull().any():
                self.errors.append("Erro no campo 'tipo_transacao': Contém valores não utilizados.")

    def validate_sigla_pais(self):
        if not self.df['sigla_pais'].apply(lambda x: x == "BRA").all():
            self.errors.append("Erro no campo 'sigla_pais': Deve ser 'BRA'.")

    # def validate_reservado(self):
    #     if not self.df['reservado'].apply(lambda x: isinstance(x, str) and len(x) == 51).all():
    #         self.errors.append("Erro no campo 'reservado': Deve ter 51 caracteres.")

    def validate_codigo_ec_venda(self):
        if not self.df['codigo_ec_venda'].apply(lambda x: isinstance(x, str) and len(x) == 9).all():
            self.errors.append("Erro no campo 'codigo_ec_venda': Deve ter 9 caracteres.")

    def validate_codigo_ec_pagamento(self):
        if not self.df['codigo_ec_pagamento'].apply(lambda x: isinstance(x, str) and len(x) == 9).all():
            self.errors.append("Erro no campo 'codigo_ec_pagamento': Deve ter 9 caracteres.")

    def validate_cnpj_ec_pagamento(self):
        if not self.df['cnpj_ec_pagamento'].apply(lambda x: isinstance(x, str) and len(x) == 14).all():
            self.errors.append("Erro no campo 'cnpj_ec_pagamento': Deve ter 14 caracteres.")

    def validate_data_vencimento_original(self):
        if not self.df['data_vencimento_original'].apply(lambda x: isinstance(x, str) and len(x) == 8 and x.isdigit()).all():
            self.errors.append("Erro no campo 'data_vencimento_original': Deve estar no formato YYYYMMDD.")
        else:
            self.df['data_vencimento_original'] = pd.to_datetime(self.df['data_vencimento_original'], format='%Y%m%d', errors='coerce')
            if self.df['data_vencimento_original'].isnull().any():
                self.errors.append("Erro na conversão de 'data_vencimento_original': Formato inválido para datas.")

    def validate_indicador_deb_balance(self):
        if not self.df['indicador_deb_balance'].apply(lambda x: x in ['D', '']).all():
            self.errors.append("Erro no campo 'indicador_deb_balance': Deve ser 'D' ou estar vazio.")

    def validate_indicador_reenvio(self):
        if not self.df['indicador_reenvio'].apply(lambda x: x in ['R', '']).all():
            self.errors.append("Erro no campo 'indicador_reenvio': Deve ser 'R' ou estar vazio.")

    def validate_nsu_origem(self):
        if not self.df['nsu_origem'].apply(lambda x: isinstance(x, str) and len(x) <= 6 and x.isdigit()).all():
            self.errors.append("Erro no campo 'nsu_origem': Deve ter até 6 dígitos numéricos.")
        else:
            self.df['nsu_origem'] = self.df['nsu_origem'].apply(lambda x: x.zfill(6))

    def validate_numero_operacao_recebivel(self):
        if not self.df['numero_operacao_recebivel'].apply(lambda x: (isinstance(x, str) and (len(x) == 20 or x == ""))).all():
            self.errors.append("Erro no campo 'numero_operacao_recebivel': Deve ter 20 caracteres ou estar vazio.")

    def validate_sequencial_operacao_recebivel(self):
       if not self.df['sequencial_operacao_recebivel'].apply(lambda x: isinstance(x, str) and len(x) == 2).all():
            self.errors.append("Erro no campo 'sequencial_operacao_recebivel': Deve ter 2 caracteres.")

    def validate_tipo_operacao_recebivel(self):
        valid_values = ['C', 'G', 'P', 'R', 'A', 'F', 'E', 'U']
        if not self.df['tipo_operacao_recebivel'].apply(lambda x: x in valid_values or x == "").all():
            self.errors.append("Erro no campo 'tipo_operacao_recebivel': Deve ser um dos valores permitidos ou estar vazio.")

    def validate_nseq(self):
        if not self.df['nseq'].apply(lambda x: isinstance(x, str) and len(x) == 6).all():
            self.errors.append("Erro no campo 'nseq': Deve ter 6 caracteres.")

    def validate_valor_operacao_recebivel(self):
        if not self.df['valor_operacao_recebivel'].apply(lambda x: isinstance(x, str) and x.replace('.', '', 1).isdigit()).all():
            self.errors.append("Erro no campo 'valor_operacao_recebivel': Deve estar no formato numérico com ponto decimal.")
        else:
            self.df['valor_operacao_recebivel'] = self.df['valor_operacao_recebivel'].astype(float)

    def validate_all(self):
        self.validate_structure()

        self.validate_codigo_registro()
        self.validate_identificacao_loja()
        self.validate_nsu_host_transacao()
        self.validate_data_transacao()
        self.validate_horario_transacao()
        self.validate_tipo_lancamento()
        self.validate_data_lancamento()
        self.validate_tipo_produto()
        self.validate_meio_captura()
        self.validate_valor_bruto_venda()
        self.validate_valor_desconto()
        self.validate_valor_liquido_venda()
        self.validate_numero_cartao()
        self.validate_numero_parcela()
        self.validate_numero_total_parcelas()
        self.validate_nsu_host_parcela()
        self.validate_valor_bruto_parcela()
        self.validate_valor_desconto_parcela()
        self.validate_valor_liquido_parcela()
        self.validate_banco()
        self.validate_agencia()
        self.validate_conta()
        self.validate_codigo_autorizacao()
        self.validate_codigo_bandeira()
        self.validate_codigo_produto()
        self.validate_valor_tx_interchange_tarifa()
        self.validate_valor_tx_administracao()
        self.validate_valor_tx_interchange_parcela()
        self.validate_tipo_transacao()
        self.validate_sigla_pais()
        self.validate_codigo_ec_venda()
        self.validate_codigo_ec_pagamento()
        self.validate_cnpj_ec_pagamento()
        self.validate_data_vencimento_original()
        self.validate_indicador_deb_balance()
        self.validate_indicador_reenvio()
        self.validate_nsu_origem()
        self.validate_numero_operacao_recebivel()
        self.validate_sequencial_operacao_recebivel()
        self.validate_tipo_operacao_recebivel()
        self.validate_valor_operacao_recebivel()
        self.validate_nseq()
        
        # Exibe os erros, se houver
        if self.errors:
            print("Validações falharam:")
            return self.errors
        else:
            print("Todas as validações passaram.")
            return self.df




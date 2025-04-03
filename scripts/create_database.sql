CREATE SCHEMA IF NOT EXISTS unica_transactions;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE OR REPLACE FUNCTION unica_transactions.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION unica_transactions.validate_cnpj(cnpj varchar)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN length(cnpj) = 14 AND cnpj ~ '^[0-9]+$';
END;
$$ LANGUAGE plpgsql;

CREATE TABLE unica_transactions.controle_arquivos (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome_arquivo varchar NOT NULL UNIQUE,
    data_geracao date NOT NULL,
    data_processamento timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status_processamento varchar(20) NOT NULL,
    erro_processamento text,
    arquivo_google_drive_path varchar(255),
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_status_valido CHECK (status_processamento IN ('SUCESSO', 'ERRO', 'PROCESSANDO'))
);

CREATE TABLE unica_transactions.tempo (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    data date UNIQUE NOT NULL,
    dia_semana varchar NOT NULL,
    mes int NOT NULL,
    ano int NOT NULL,
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_mes_valido CHECK (mes >= 1 AND mes <= 12),
    CONSTRAINT check_ano_valido CHECK (ano >= 2000)
);

CREATE TABLE unica_transactions.loja (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    identificacao_loja varchar UNIQUE NOT NULL,
    codigo_ec_venda varchar NOT NULL,
    codigo_ec_pagamento varchar NOT NULL,
    cnpj_ec_pagamento varchar NOT NULL,
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_cnpj_length CHECK (length(cnpj_ec_pagamento) = 14),
    CONSTRAINT check_cnpj_valido CHECK (unica_transactions.validate_cnpj(cnpj_ec_pagamento))
);

CREATE TABLE unica_transactions.produto (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo_produto varchar UNIQUE NOT NULL,
    descricao varchar NOT NULL,
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE unica_transactions.pagamento (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo_bandeira varchar UNIQUE NOT NULL,
    tipo_pagamento varchar NOT NULL,
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE unica_transactions.transacoes (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    data_transacao timestamp NOT NULL,
    horario_transacao varchar(6) NOT NULL,
    tipo_lancamento varchar(20) NOT NULL,
    data_lancamento date NOT NULL,
    valor_bruto_venda decimal(15,2) NOT NULL,
    valor_liquido_venda decimal(15,2) NOT NULL,
    valor_desconto decimal(15,2) NOT NULL DEFAULT 0,
    tipo_produto varchar(1) NOT NULL,
    meio_captura varchar(1) NOT NULL,
    tipo_transacao varchar(2) NOT NULL,
    codigo_bandeira varchar(3) NOT NULL,
    codigo_produto varchar(3) NOT NULL,
    identificacao_loja varchar(15) NOT NULL,
    nsu_host_transacao varchar(12) NOT NULL,
    numero_cartao varchar(19) NOT NULL,
    numero_parcela varchar(2) NOT NULL,
    numero_total_parcelas varchar(2) NOT NULL,
    nsu_host_parcela varchar(12) NOT NULL,
    valor_bruto_parcela decimal(15,2) NOT NULL,
    valor_desconto_parcela decimal(15,2) NOT NULL,
    valor_liquido_parcela decimal(15,2) NOT NULL,
    banco varchar(3),
    agencia varchar(6),
    conta varchar(11),
    codigo_autorizacao varchar(12) NOT NULL,
    valor_tx_interchange_tarifa decimal(15,2) NOT NULL,
    valor_tx_administracao decimal(15,2) NOT NULL,
    valor_tx_interchange_parcela decimal(15,2) NOT NULL,
    valor_tx_administracao_parcela decimal(15,2) NOT NULL,
    valor_redutor_multi_fronteira decimal(15,2) NOT NULL,
    valor_tx_antecipacao decimal(15,2) NOT NULL,
    valor_liquido_antecipado decimal(15,2) NOT NULL,
    codigo_pedido varchar(30),
    sigla_pais varchar(3) NOT NULL,
    data_vencimento_original date NOT NULL,
    indicador_deb_balance varchar(1),
    indicador_reenvio varchar(1),
    nsu_origem varchar(6),
    numero_operacao_recebivel varchar(20),
    sequencial_operacao_recebivel varchar(2),
    tipo_operacao_recebivel varchar(1),
    valor_operacao_recebivel decimal(15,2),
    file_id uuid NOT NULL,
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_valor_bruto_positivo CHECK (valor_bruto_venda >= 0),
    CONSTRAINT check_valor_liquido_positivo CHECK (valor_liquido_venda >= 0),
    CONSTRAINT fk_pagamento FOREIGN KEY (codigo_bandeira) REFERENCES unica_transactions.pagamento(codigo_bandeira),
    CONSTRAINT fk_produto FOREIGN KEY (codigo_produto) REFERENCES unica_transactions.produto(codigo_produto),
    CONSTRAINT fk_loja FOREIGN KEY (identificacao_loja) REFERENCES unica_transactions.loja(identificacao_loja),
    CONSTRAINT fk_arquivo FOREIGN KEY (file_id) REFERENCES unica_transactions.controle_arquivos(id)
);

--------------------

CREATE TRIGGER update_controle_arquivos_updated_at
    BEFORE UPDATE ON unica_transactions.controle_arquivos
    FOR EACH ROW
    EXECUTE FUNCTION unica_transactions.update_updated_at_column();

CREATE TRIGGER update_tempo_updated_at
    BEFORE UPDATE ON unica_transactions.tempo
    FOR EACH ROW
    EXECUTE FUNCTION unica_transactions.update_updated_at_column();

CREATE TRIGGER update_loja_updated_at
    BEFORE UPDATE ON unica_transactions.loja
    FOR EACH ROW
    EXECUTE FUNCTION unica_transactions.update_updated_at_column();

CREATE TRIGGER update_produto_updated_at
    BEFORE UPDATE ON unica_transactions.produto
    FOR EACH ROW
    EXECUTE FUNCTION unica_transactions.update_updated_at_column();

CREATE TRIGGER update_pagamento_updated_at
    BEFORE UPDATE ON unica_transactions.pagamento
    FOR EACH ROW
    EXECUTE FUNCTION unica_transactions.update_updated_at_column();

CREATE TRIGGER update_transacoes_updated_at
    BEFORE UPDATE ON unica_transactions.transacoes
    FOR EACH ROW
    EXECUTE FUNCTION unica_transactions.update_updated_at_column();

-------------------- INDICES

CREATE INDEX idx_transacoes_data_loja ON unica_transactions.transacoes(data_transacao, identificacao_loja);
CREATE INDEX idx_transacoes_bandeira ON unica_transactions.transacoes(codigo_bandeira);
CREATE INDEX idx_transacoes_produto ON unica_transactions.transacoes(codigo_produto);
CREATE INDEX idx_transacoes_file ON unica_transactions.transacoes(file_id);

CREATE INDEX idx_tempo_ano_mes ON unica_transactions.tempo(ano, mes);
CREATE INDEX idx_tempo_data ON unica_transactions.tempo(data);

CREATE INDEX idx_loja_identificacao ON unica_transactions.loja(identificacao_loja);
CREATE INDEX idx_loja_cnpj ON unica_transactions.loja(cnpj_ec_pagamento);

CREATE INDEX idx_produto_codigo ON unica_transactions.produto(codigo_produto);
CREATE INDEX idx_pagamento_codigo ON unica_transactions.pagamento(codigo_bandeira);

CREATE INDEX idx_controle_nome_arquivo ON unica_transactions.controle_arquivos(nome_arquivo);
CREATE INDEX idx_controle_data_status ON unica_transactions.controle_arquivos(data_geracao, status_processamento);

-------------------- COMMENTS

COMMENT ON TABLE unica_transactions.transacoes IS 'Tabela fato que armazena todas as transações financeiras';
COMMENT ON TABLE unica_transactions.tempo IS 'Dimensão de tempo para análise temporal';
COMMENT ON TABLE unica_transactions.loja IS 'Dimensão com informações da loja';
COMMENT ON TABLE unica_transactions.produto IS 'Dimensão com informações dos produtos';
COMMENT ON TABLE unica_transactions.pagamento IS 'Dimensão com informações das formas de pagamento';
COMMENT ON TABLE unica_transactions.controle_arquivos IS 'Controle de processamento dos arquivos de transação';

-------------------- DELETE

DELETE FROM unica_transactions.transacoes;
DELETE FROM unica_transactions.tempo;
DELETE FROM unica_transactions.pagamento;
DELETE FROM unica_transactions.produto;
DELETE FROM unica_transactions.loja;
DELETE FROM unica_transactions.controle_arquivos;


--------------------- DROP

drop table unica_transactions.transacoes;
drop table unica_transactions.tempo;
drop table unica_transactions.pagamento;
drop table unica_transactions.produto;
drop table unica_transactions.loja;
drop table unica_transactions.controle_arquivos;














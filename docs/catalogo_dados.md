# Catálogo de Dados - Unica Transactions

## Visão Geral
Este catálogo descreve a estrutura do banco de dados utilizado para armazenar e processar transações financeiras. O banco é organizado em um schema chamado `unica_transactions` e utiliza um modelo dimensional para análise de dados.

## Esquema do Banco

### Tabelas Principais

#### 1. transacoes (Tabela Fato)
Armazena todas as transações financeiras processadas.

**Campos:**
- `id` (uuid): Identificador único da transação
- `data_transacao` (timestamp): Data e hora da transação
- `horario_transacao` (varchar(6)): Horário da transação
- `tipo_lancamento` (varchar(20)): Tipo do lançamento
- `data_lancamento` (date): Data do lançamento
- `valor_bruto_venda` (decimal(15,2)): Valor bruto da venda
- `valor_liquido_venda` (decimal(15,2)): Valor líquido da venda
- `valor_desconto` (decimal(15,2)): Valor do desconto
- `tipo_produto` (varchar(1)): Tipo do produto
- `meio_captura` (varchar(1)): Meio de captura
- `tipo_transacao` (varchar(2)): Tipo da transação
- `codigo_bandeira` (varchar(3)): Código da bandeira
- `codigo_produto` (varchar(3)): Código do produto
- `identificacao_loja` (varchar(15)): Identificação da loja
- `nsu_host_transacao` (varchar(12)): NSU do host da transação
- `numero_cartao` (varchar(19)): Número do cartão
- `numero_parcela` (varchar(2)): Número da parcela
- `numero_total_parcelas` (varchar(2)): Número total de parcelas
- `nsu_host_parcela` (varchar(12)): NSU do host da parcela
- `valor_bruto_parcela` (decimal(15,2)): Valor bruto da parcela
- `valor_desconto_parcela` (decimal(15,2)): Valor do desconto da parcela
- `valor_liquido_parcela` (decimal(15,2)): Valor líquido da parcela
- `banco` (varchar(3)): Código do banco
- `agencia` (varchar(6)): Agência
- `conta` (varchar(11)): Conta
- `codigo_autorizacao` (varchar(12)): Código de autorização
- `valor_tx_interchange_tarifa` (decimal(15,2)): Valor da taxa de interchange
- `valor_tx_administracao` (decimal(15,2)): Valor da taxa de administração
- `valor_tx_interchange_parcela` (decimal(15,2)): Valor da taxa de interchange da parcela
- `valor_tx_administracao_parcela` (decimal(15,2)): Valor da taxa de administração da parcela
- `valor_redutor_multi_fronteira` (decimal(15,2)): Valor do redutor multi-fronteira
- `valor_tx_antecipacao` (decimal(15,2)): Valor da taxa de antecipação
- `valor_liquido_antecipado` (decimal(15,2)): Valor líquido antecipado
- `codigo_pedido` (varchar(30)): Código do pedido
- `sigla_pais` (varchar(3)): Sigla do país
- `data_vencimento_original` (date): Data de vencimento original
- `indicador_deb_balance` (varchar(1)): Indicador de débito balance
- `indicador_reenvio` (varchar(1)): Indicador de reenvio
- `nsu_origem` (varchar(6)): NSU de origem
- `numero_operacao_recebivel` (varchar(20)): Número da operação recebível
- `sequencial_operacao_recebivel` (varchar(2)): Sequencial da operação recebível
- `tipo_operacao_recebivel` (varchar(1)): Tipo da operação recebível
- `valor_operacao_recebivel` (decimal(15,2)): Valor da operação recebível
- `file_id` (uuid): ID do arquivo de origem
- `created_at` (timestamp): Data de criação
- `updated_at` (timestamp): Data de atualização

#### 2. loja (Dimensão)
Armazena informações das lojas.

**Campos:**
- `id` (uuid): Identificador único da loja
- `identificacao_loja` (varchar): Identificação única da loja
- `codigo_ec_venda` (varchar): Código do estabelecimento de venda
- `codigo_ec_pagamento` (varchar): Código do estabelecimento de pagamento
- `cnpj_ec_pagamento` (varchar): CNPJ do estabelecimento de pagamento
- `created_at` (timestamp): Data de criação
- `updated_at` (timestamp): Data de atualização

#### 3. produto (Dimensão)
Armazena informações dos produtos.

**Campos:**
- `id` (uuid): Identificador único do produto
- `codigo_produto` (varchar): Código único do produto
- `descricao` (varchar): Descrição do produto
- `created_at` (timestamp): Data de criação
- `updated_at` (timestamp): Data de atualização

#### 4. pagamento (Dimensão)
Armazena informações das formas de pagamento.

**Campos:**
- `id` (uuid): Identificador único do pagamento
- `codigo_bandeira` (varchar): Código único da bandeira
- `tipo_pagamento` (varchar): Tipo de pagamento
- `created_at` (timestamp): Data de criação
- `updated_at` (timestamp): Data de atualização

#### 5. tempo (Dimensão)
Armazena informações temporais para análise.

**Campos:**
- `id` (uuid): Identificador único do registro temporal
- `data` (date): Data
- `dia_semana` (varchar): Dia da semana
- `mes` (int): Mês
- `ano` (int): Ano
- `created_at` (timestamp): Data de criação
- `updated_at` (timestamp): Data de atualização

#### 6. controle_arquivos
Armazena informações sobre os arquivos processados.

**Campos:**
- `id` (uuid): Identificador único do arquivo
- `nome_arquivo` (varchar): Nome do arquivo
- `data_geracao` (date): Data de geração do arquivo
- `data_processamento` (timestamp): Data de processamento
- `status_processamento` (varchar(20)): Status do processamento
- `erro_processamento` (text): Mensagem de erro (se houver)
- `arquivo_google_drive_path` (varchar(255)): Caminho no Google Drive
- `created_at` (timestamp): Data de criação
- `updated_at` (timestamp): Data de atualização

## Relacionamentos

1. `transacoes` -> `loja` (identificacao_loja)
2. `transacoes` -> `produto` (codigo_produto)
3. `transacoes` -> `pagamento` (codigo_bandeira)
4. `transacoes` -> `controle_arquivos` (file_id)

## Índices

1. `idx_transacoes_data_loja`: Data da transação e identificação da loja
2. `idx_transacoes_bandeira`: Código da bandeira
3. `idx_transacoes_produto`: Código do produto
4. `idx_transacoes_file`: ID do arquivo
5. `idx_tempo_ano_mes`: Ano e mês
6. `idx_tempo_data`: Data
7. `idx_loja_identificacao`: Identificação da loja
8. `idx_loja_cnpj`: CNPJ
9. `idx_produto_codigo`: Código do produto
10. `idx_pagamento_codigo`: Código da bandeira
11. `idx_controle_nome_arquivo`: Nome do arquivo
12. `idx_controle_data_status`: Data de geração e status

## Restrições

1. Validação de CNPJ
2. Valores positivos para campos monetários
3. Status de processamento válido
4. Mês válido (1-12)
5. Ano válido (>= 2000)

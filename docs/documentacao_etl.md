# Documentação do ETL - Unica Transactions

## Visão Geral
Este documento descreve o processo de ETL (Extract, Transform, Load) implementado para processar extratos financeiros da Unica. O sistema é responsável por extrair dados de arquivos de extrato, transformá-los em um formato adequado e carregá-los em um banco de dados dimensional para análise.

## Arquitetura do Sistema

### Componentes Principais
1. **Extrator de Arquivos**
   - Monitora diretório local para novos arquivos
   - Integração com Google Drive para backup
   - Validação de formato e estrutura dos arquivos

2. **Processador de Dados**
   - Leitura e parsing de arquivos de extrato
   - Transformação e validação de dados
   - Preparação de tabelas dimensionais e fatos

3. **Banco de Dados**
   - Schema: `unica_transactions`
   - Modelo dimensional com tabelas de fato e dimensões
   - Controle de processamento de arquivos

### Estrutura de Diretórios
```
├── scripts/
│   ├── leitor_extratos.py      # Processamento principal
│   ├── analysis.py             # Análise e simulação
│   ├── create_database.sql     # Schema do banco
│   └── requirements.txt        # Dependências
├── docs/
│   ├── catalogo_dados.md       # Catálogo de dados
│   ├── modelo_dados.dbml      # Modelo DBML
│   └── documentacao_etl.md     # Esta documentação
└── notebooks/
    └── analise_dados.ipynb     # Análises e visualizações
```

## Fluxo de Processamento

### 1. Extração
- Monitoramento de diretório local para novos arquivos
- Validação inicial do formato do arquivo
- Backup automático para Google Drive
- Registro inicial no controle de arquivos

### 2. Transformação
- Leitura e parsing do arquivo de extrato
- Validação de dados e estrutura
- Preparação de tabelas dimensionais:
  - Loja
  - Produto
  - Pagamento
  - Tempo
- Preparação da tabela de fato (transações)

### 3. Carregamento
- Inserção em lote nas tabelas dimensionais
- Inserção em lote na tabela de fato
- Atualização do status de processamento
- Tratamento de erros e rollback em caso de falha

## Componentes Detalhados

### 1. Leitor de Extratos (leitor_extratos.py)
Responsável pelo processamento principal dos arquivos.

**Funções Principais:**
- `process_file`: Coordena o processamento completo
- `prepare_dimension_tables`: Prepara dados dimensionais
- `prepare_fact_table`: Prepara dados de transações
- `register_file_processing`: Registra status do processamento

### 2. Análise e Simulação (analysis.py)
Ferramentas para análise de dados e simulação de cenários.

**Funções Principais:**
- `calculate_mdr_by_produto`: Cálculo de MDR por produto
- `simulate_mdr_impact`: Simulação de impacto de mudanças de MDR
- `plot_mdr_comparison`: Visualização de comparação de MDR

### 3. Banco de Dados
Modelo dimensional com as seguintes tabelas:

**Tabelas de Dimensão:**
- `loja`: Informações das lojas
- `produto`: Tipos de produtos
- `pagamento`: Formas de pagamento
- `tempo`: Dimensão temporal
- `controle_arquivos`: Controle de processamento

**Tabela de Fato:**
- `transacoes`: Dados detalhados das transações

## Tratamento de Erros

### 1. Validação de Arquivos
- Verificação de formato e estrutura
- Validação de campos obrigatórios
- Verificação de consistência de dados

### 2. Tratamento de Exceções
- Log detalhado de erros
- Rollback de transações em caso de falha
- Registro de erros no controle de arquivos
- Notificação de falhas no processamento

## Monitoramento e Controle

### 1. Controle de Processamento
- Registro de início e fim de processamento
- Status de cada arquivo processado
- Histórico de erros e correções
- Backup automático de arquivos

### 2. Métricas de Performance
- Tempo de processamento por arquivo
- Volume de dados processados
- Taxa de sucesso no processamento
- Tempo médio de processamento

## Próximos Passos e Melhorias

### 1. Melhorias Planejadas
- Implementação de processamento paralelo
- Otimização de consultas e índices
- Expansão das análises disponíveis
- Melhorias na visualização de dados

### 2. Manutenção
- Atualização regular de dependências
- Backup e recuperação de dados
- Monitoramento de performance
- Documentação contínua

## Considerações de Segurança

### 1. Acesso a Dados
- Controle de acesso ao banco de dados
- Criptografia de dados sensíveis
- Logs de acesso e alterações

### 2. Backup e Recuperação
- Backup regular do banco de dados
- Recuperação de arquivos processados
- Plano de contingência para falhas

## Referências
- [Catálogo de Dados](catalogo_dados.md)
- [Modelo de Dados](modelo_dados.dbml)
- [Scripts SQL](create_database.sql)

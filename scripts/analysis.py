import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns
from decimal import Decimal
import matplotlib.dates as mdates

plt.style.use('seaborn-v0_8')
sns.set_palette(['#8B0000', '#A52A2A', '#B22222', '#DC143C'])
plt.rcParams['figure.figsize'] = (15, 7)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12

def plot_mdr_by_produto(df: pd.DataFrame) -> None:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
    
    sns.barplot(data=df, x='descricao', y='mdr_percentual', ax=ax1, color='#8B0000')
    ax1.set_title('MDR Percentual por Tipo de Produto')
    ax1.set_xlabel('Produto')
    ax1.set_ylabel('MDR (%)')
    ax1.tick_params(axis='x', rotation=45)
    
    for p in ax1.patches:
        ax1.annotate(f'{p.get_height():.2f}%', 
                    (p.get_x() + p.get_width()/2., p.get_height()),
                    ha='center', va='bottom', fontsize=10)
    
    sns.barplot(data=df, x='descricao', y='mdr_nominal', ax=ax2, color='#A52A2A')
    ax2.set_title('Volume de MDR por Tipo de Produto')
    ax2.set_xlabel('Produto')
    ax2.set_ylabel('Valor MDR (R$)')
    ax2.tick_params(axis='x', rotation=45)
    
    for p in ax2.patches:
        ax2.annotate(f'R$ {p.get_height():,.2f}', 
                    (p.get_x() + p.get_width()/2., p.get_height()),
                    ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.show()

def calculate_mdr_by_produto(connection_params: Dict, mes: str = None) -> pd.DataFrame:
    query = """
    WITH transacoes_filtradas AS (
        SELECT DISTINCT
            t.nsu_host_transacao,
            t.valor_bruto_venda,
            t.valor_liquido_venda,
            pr.codigo_produto,
            pr.descricao
        FROM unica_transactions.transacoes t
        JOIN unica_transactions.produto pr ON t.codigo_produto = pr.codigo_produto
    """
    
    if mes:
        query += " WHERE DATE_TRUNC('month', t.data_transacao) = %s"
        params = (mes,)
    else:
        params = None
    
    query += """
    )
    SELECT 
        codigo_produto,
        descricao,
        COUNT(*) as total_transacoes,
        SUM(valor_bruto_venda) as valor_total,
        SUM(valor_liquido_venda) as valor_liquido,
        (SUM(valor_bruto_venda) - SUM(valor_liquido_venda)) / SUM(valor_bruto_venda) * 100 as mdr_percentual,
        SUM(valor_bruto_venda - valor_liquido_venda) as mdr_nominal
    FROM transacoes_filtradas
    GROUP BY codigo_produto, descricao
    ORDER BY mdr_nominal DESC
    """
    
    try:
        conn = psycopg2.connect(**connection_params)
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        logging.error(f"Erro ao calcular MDR por produto: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def simulate_mdr_by_product(connection_params, taxas_json):
    try:
        # Validação do formato das taxas
        if not isinstance(taxas_json, dict):
            raise ValueError("taxas_json deve ser um dicionário")
            
        for produto, config in taxas_json.items():
            if not isinstance(config, dict):
                raise ValueError(f"Configuração inválida para o produto {produto}")
            for tipo, taxa in config.items():
                if not isinstance(taxa, dict) or 'mdr_percentual' not in taxa:
                    raise ValueError(f"Taxa inválida para {produto} - {tipo}")
                if not isinstance(taxa['mdr_percentual'], (int, float)):
                    raise ValueError(f"Valor de MDR inválido para {produto} - {tipo}")
        
        conn = psycopg2.connect(**connection_params)
        
        query = """
            WITH transacoes_filtradas AS (
                SELECT distinct
                	t.nsu_host_transacao,
                    t.data_transacao,
                    t.valor_bruto_venda,
                    t.valor_liquido_venda,
                    t.numero_total_parcelas,
                    pr.codigo_produto
                FROM unica_transactions.transacoes t
                JOIN unica_transactions.produto pr ON t.codigo_produto = pr.codigo_produto
                --WHERE t.data_transacao >= CURRENT_DATE - INTERVAL '30 days'
            )
            SELECT 
                DATE_TRUNC('month', data_transacao) as mes,
                codigo_produto,
                CASE 
                    WHEN numero_total_parcelas > '01' THEN 'parcelado'
                    ELSE 'a_vista'
                END as tipo_parcelamento,
                COUNT(*) as total_transacoes,
                SUM(valor_bruto_venda) as volume_total,
                SUM(valor_bruto_venda - valor_liquido_venda) as mdr_atual
            FROM transacoes_filtradas
            GROUP BY 
                DATE_TRUNC('month', data_transacao),
                codigo_produto,
                CASE 
                    WHEN numero_total_parcelas > '01' THEN 'parcelado'
                    ELSE 'a_vista'
                END
            ORDER BY mes
        """
        
        with conn.cursor() as cur:
            cur.execute(query)
            columns = [
                'mes', 'codigo_produto', 'tipo_parcelamento',
                'total_transacoes', 'volume_total', 'mdr_atual'
            ]
            results = cur.fetchall()
            
            if not results:
                return None, None
            
            df = pd.DataFrame(results, columns=columns)
            
            # Converter todos os valores numéricos para Decimal
            df['volume_total'] = df['volume_total'].apply(lambda x: Decimal(str(x)))
            df['mdr_atual'] = df['mdr_atual'].apply(lambda x: Decimal(str(x)))
            
            # Calcular MDR proposto
            def calcular_mdr_proposto(row):
                try:
                    if (row['codigo_produto'] in taxas_json and 
                        row['tipo_parcelamento'] in taxas_json[row['codigo_produto']]):
                        taxa = Decimal(str(taxas_json[row['codigo_produto']][row['tipo_parcelamento']]['mdr_percentual']))
                        return (row['volume_total'] * taxa) / Decimal('100')
                    return row['mdr_atual']
                except Exception as e:
                    logging.error(f"Erro ao calcular MDR proposto para {row['codigo_produto']}: {str(e)}")
                    return row['mdr_atual']
            
            df['mdr_proposto'] = df.apply(calcular_mdr_proposto, axis=1)
            df['diferenca_mdr'] = df['mdr_proposto'] - df['mdr_atual']
            
            df_mensal = df.groupby('mes').agg({
                'volume_total': 'sum',
                'mdr_atual': 'sum',
                'mdr_proposto': 'sum'
            }).reset_index()
            
            # Converter para float apenas para plotagem
            df_mensal['mdr_atual'] = df_mensal['mdr_atual'].apply(float)
            df_mensal['mdr_proposto'] = df_mensal['mdr_proposto'].apply(float)
            
            # Criar gráfico
            plt.figure(figsize=(15, 7))
            plt.plot(df_mensal['mes'], df_mensal['mdr_atual'], 
                    label='MDR Atual', marker='o', linewidth=2, color='#006400')
            plt.plot(df_mensal['mes'], df_mensal['mdr_proposto'], 
                    label='MDR Proposto', marker='o', linewidth=2, color='#A52A2A')
            
            plt.title('Comparação MDR Atual vs Proposto (Agrupado por Mês)', pad=20)
            plt.xlabel('Mês')
            plt.ylabel('Valor MDR (R$)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
            plt.xticks(rotation=45)
            
            for i, row in df_mensal.iterrows():
                plt.annotate(f'R$ {row["mdr_atual"]:,.2f}', 
                           (row['mes'], row['mdr_atual']),
                           textcoords="offset points", xytext=(0,10), ha='center')
                plt.annotate(f'R$ {row["mdr_proposto"]:,.2f}', 
                           (row['mes'], row['mdr_proposto']),
                           textcoords="offset points", xytext=(0,-15), ha='center')
            
            plt.tight_layout()
            plt.show()
            
            impacto_total = float(df['diferenca_mdr'].sum())
            
            return df, impacto_total
            
    except Exception as e:
        logging.error(f"Erro ao simular MDR por produto: {str(e)}")
        raise
    finally:
        if conn:
            conn.close() 
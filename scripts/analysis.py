import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use('seaborn-v0_8')
sns.set_palette(['#8B0000', '#A52A2A', '#B22222', '#DC143C'])
plt.rcParams['figure.figsize'] = (15, 7)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12

def plot_mdr_by_bandeira(df: pd.DataFrame) -> None:
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x='codigo_bandeira', y='mdr_percentual', hue='tipo_pagamento')
    plt.title('MDR por Bandeira e Tipo de Pagamento')
    plt.xlabel('Bandeira')
    plt.ylabel('MDR (%)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def calculate_mdr_by_bandeira(connection_params: Dict) -> pd.DataFrame:
    query = """
    SELECT 
        p.codigo_bandeira,
        p.tipo_pagamento,
        CASE 
            WHEN t.numero_total_parcelas > '01' THEN 'Parcelado'
            ELSE 'À Vista'
        END as tipo_parcelamento,
        COUNT(*) as total_transacoes,
        SUM(t.valor_bruto_venda) as valor_total,
        SUM(t.valor_liquido_venda) as valor_liquido,
        (SUM(t.valor_bruto_venda) - SUM(t.valor_liquido_venda)) / SUM(t.valor_bruto_venda) * 100 as mdr_percentual
    FROM unica_transactions.transacoes t
    JOIN unica_transactions.pagamento p ON t.codigo_bandeira = p.codigo_bandeira
    GROUP BY p.codigo_bandeira, p.tipo_pagamento, 
        CASE 
            WHEN t.numero_total_parcelas > '01' THEN 'Parcelado'
            ELSE 'À Vista'
        END
    ORDER BY mdr_percentual DESC
    """
    
    try:
        conn = psycopg2.connect(**connection_params)
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        logging.error(f"Erro ao calcular MDR por bandeira: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

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
    SELECT 
        pr.codigo_produto,
        pr.descricao,
        COUNT(*) as total_transacoes,
        SUM(t.valor_bruto_venda) as valor_total,
        SUM(t.valor_liquido_venda) as valor_liquido,
        (SUM(t.valor_bruto_venda) - SUM(t.valor_liquido_venda)) / SUM(t.valor_bruto_venda) * 100 as mdr_percentual,
        SUM(t.valor_bruto_venda - t.valor_liquido_venda) as mdr_nominal
    FROM unica_transactions.transacoes t
    JOIN unica_transactions.produto pr ON t.codigo_produto = pr.codigo_produto
    """
    
    if mes:
        query += " WHERE DATE_TRUNC('month', t.data_transacao) = %s"
        params = (mes,)
    else:
        params = None
    
    query += """
    GROUP BY pr.codigo_produto, pr.descricao
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

def simulate_mdr_scenarios(connection_params: Dict, 
                          bandeira: str, 
                          produto: str,
                          tipo_pagamento: str,
                          parcelado: bool,
                          aumento_percentual: float) -> Tuple[pd.DataFrame, float]:
    query = """
    SELECT 
        t.valor_bruto_venda,
        t.valor_liquido_venda,
        p.codigo_bandeira,
        p.tipo_pagamento,
        pr.descricao as produto,
        t.numero_total_parcelas
    FROM unica_transactions.transacoes t
    JOIN unica_transactions.pagamento p ON t.codigo_bandeira = p.codigo_bandeira
    JOIN unica_transactions.produto pr ON t.codigo_produto = pr.codigo_produto
    WHERE p.codigo_bandeira = %s
    AND pr.codigo_produto = %s
    AND p.tipo_pagamento = %s
    AND CASE 
        WHEN %s = true THEN t.numero_total_parcelas > '01'
        ELSE t.numero_total_parcelas = '01'
    END
    """
    
    try:
        conn = psycopg2.connect(**connection_params)
        df = pd.read_sql(query, conn, params=(bandeira, produto, tipo_pagamento, parcelado))
        
        df['mdr_atual'] = (df['valor_bruto_venda'] - df['valor_liquido_venda']) / df['valor_bruto_venda'] * 100
        df['novo_mdr_percentual'] = df['mdr_atual'] * (1 + aumento_percentual/100)
        df['novo_valor_liquido'] = df['valor_bruto_venda'] * (1 - df['novo_mdr_percentual']/100)
        df['impacto'] = df['novo_valor_liquido'] - df['valor_liquido_venda']
        impacto_total = df['impacto'].sum()
        
        return df, impacto_total
        
    except Exception as e:
        logging.error(f"Erro ao simular cenários de MDR: {e}")
        return pd.DataFrame(), 0
    finally:
        if conn:
            conn.close()

def plot_mdr_trends(df: pd.DataFrame) -> None:
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=df, x='data_transacao', y='mdr_percentual', 
                 hue='codigo_bandeira', style='tipo_pagamento')
    plt.title('Evolução do MDR por Bandeira e Tipo de Pagamento')
    plt.xlabel('Data')
    plt.ylabel('MDR (%)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def analyze_mdr_trends(connection_params: Dict, 
                      bandeira: str = None, 
                      periodo_dias: int = 30) -> pd.DataFrame:
    query = """
    SELECT 
        t.data_transacao,
        p.codigo_bandeira,
        p.tipo_pagamento,
        CASE 
            WHEN t.numero_total_parcelas > '01' THEN 'Parcelado'
            ELSE 'À Vista'
        END as tipo_parcelamento,
        COUNT(*) as total_transacoes,
        SUM(t.valor_bruto_venda) as valor_total,
        SUM(t.valor_liquido_venda) as valor_liquido,
        (SUM(t.valor_bruto_venda) - SUM(t.valor_liquido_venda)) / SUM(t.valor_bruto_venda) * 100 as mdr_percentual
    FROM unica_transactions.transacoes t
    JOIN unica_transactions.pagamento p ON t.codigo_bandeira = p.codigo_bandeira
    WHERE t.data_transacao >= CURRENT_DATE - INTERVAL '%s days'
    """
    
    if bandeira:
        query += " AND p.codigo_bandeira = %s"
        params = (periodo_dias, bandeira)
    else:
        params = (periodo_dias,)
    
    query += " GROUP BY t.data_transacao, p.codigo_bandeira, p.tipo_pagamento, "
    query += " CASE WHEN t.numero_total_parcelas > '01' THEN 'Parcelado' ELSE 'À Vista' END "
    query += " ORDER BY t.data_transacao"
    
    try:
        conn = psycopg2.connect(**connection_params)
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        logging.error(f"Erro ao analisar tendências de MDR: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def calculate_mdr_impact_by_store(connection_params: Dict) -> pd.DataFrame:
    query = """
    SELECT 
        l.identificacao_loja,
        COUNT(*) as total_transacoes,
        SUM(t.valor_bruto_venda) as valor_total,
        SUM(t.valor_liquido_venda) as valor_liquido,
        (SUM(t.valor_bruto_venda) - SUM(t.valor_liquido_venda)) / SUM(t.valor_bruto_venda) * 100 as mdr_percentual,
        SUM(t.valor_bruto_venda - t.valor_liquido_venda) as valor_mdr
    FROM unica_transactions.transacoes t
    JOIN unica_transactions.loja l ON t.identificacao_loja = l.identificacao_loja
    GROUP BY l.identificacao_loja
    ORDER BY valor_mdr DESC
    """
    
    try:
        conn = psycopg2.connect(**connection_params)
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        logging.error(f"Erro ao calcular impacto do MDR por loja: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def simulate_mdr_impact(connection_params, bandeira, produto, tipo_pagamento, parcelado, nova_taxa_mdr):
    try:
        conn = psycopg2.connect(**connection_params)
        
        query = """
            WITH transacoes_filtradas AS (
                SELECT 
                    t.data_transacao,
                    t.valor_bruto_venda,
                    t.valor_tx_interchange_tarifa,
                    t.valor_tx_administracao,
                    t.valor_tx_interchange_parcela,
                    t.valor_tx_administracao_parcela,
                    t.numero_total_parcelas,
                    p.codigo_bandeira,
                    pr.codigo_produto,
                    p.tipo_pagamento
                FROM unica_transactions.transacoes t
                JOIN unica_transactions.pagamento p ON t.codigo_bandeira = p.codigo_bandeira
                JOIN unica_transactions.produto pr ON t.codigo_produto = pr.codigo_produto
                WHERE p.codigo_bandeira = %s
                AND pr.codigo_produto = %s
                AND p.tipo_pagamento = %s
                AND CASE 
                    WHEN %s = true THEN t.numero_total_parcelas > '01'
                    ELSE t.numero_total_parcelas = '01'
                END
                AND t.data_transacao >= CURRENT_DATE - INTERVAL '30 days'
            )
            SELECT 
                DATE_TRUNC('week', data_transacao) as semana,
                DATE_TRUNC('month', data_transacao) as mes,
                COUNT(*) as total_transacoes,
                SUM(valor_bruto_venda) as volume_total,
                SUM(
                    CASE 
                        WHEN numero_total_parcelas > '01' THEN 
                            valor_tx_interchange_parcela + valor_tx_administracao_parcela
                        ELSE 
                            valor_tx_interchange_tarifa + valor_tx_administracao
                    END
                ) as mdr_atual,
                SUM(valor_bruto_venda * (%s / 100)) as mdr_proposto
            FROM transacoes_filtradas
            GROUP BY 
                DATE_TRUNC('week', data_transacao),
                DATE_TRUNC('month', data_transacao)
            ORDER BY semana DESC
        """
        
        with conn.cursor() as cur:
            cur.execute(query, (
                bandeira, 
                produto, 
                tipo_pagamento, 
                parcelado,
                nova_taxa_mdr
            ))
            
            columns = [
                'semana', 'mes', 'total_transacoes', 'volume_total',
                'mdr_atual', 'mdr_proposto'
            ]
            results = cur.fetchall()
            
            if not results:
                return None, None, None
            
            df = pd.DataFrame(results, columns=columns)
            
            df['diferenca_mdr'] = df['mdr_proposto'] - df['mdr_atual']
            
            impacto_semanal = df.groupby('semana')['diferenca_mdr'].sum().mean()
            impacto_mensal = df.groupby('mes')['diferenca_mdr'].sum().mean()
            
            df['volume_total'] = df['volume_total'].apply(lambda x: f"R$ {x:,.2f}")
            df['mdr_atual'] = df['mdr_atual'].apply(lambda x: f"R$ {x:,.2f}")
            df['mdr_proposto'] = df['mdr_proposto'].apply(lambda x: f"R$ {x:,.2f}")
            df['diferenca_mdr'] = df['diferenca_mdr'].apply(lambda x: f"R$ {x:,.2f}")
            
            return df, impacto_semanal, impacto_mensal
            
    except Exception as e:
        logging.error(f"Erro ao simular impacto MDR: {e}")
        raise
    finally:
        if conn:
            conn.close()

def simulate_mdr_by_product(connection_params, taxas_json):
    try:
        conn = psycopg2.connect(**connection_params)
        
        query = """
            WITH transacoes_filtradas AS (
                SELECT 
                    t.data_transacao,
                    t.valor_bruto_venda,
                    t.valor_liquido_venda,
                    t.numero_total_parcelas,
                    pr.codigo_produto,
                    p.tipo_pagamento
                FROM unica_transactions.transacoes t
                JOIN unica_transactions.pagamento p ON t.codigo_bandeira = p.codigo_bandeira
                JOIN unica_transactions.produto pr ON t.codigo_produto = pr.codigo_produto
                WHERE t.data_transacao >= CURRENT_DATE - INTERVAL '30 days'
            )
            SELECT 
                DATE_TRUNC('month', data_transacao) as mes,
                codigo_produto,
                tipo_pagamento,
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
                tipo_pagamento,
                CASE 
                    WHEN numero_total_parcelas > '01' THEN 'parcelado'
                    ELSE 'a_vista'
                END
            ORDER BY mes
        """
        
        with conn.cursor() as cur:
            cur.execute(query)
            columns = [
                'mes', 'codigo_produto', 'tipo_pagamento', 'tipo_parcelamento',
                'total_transacoes', 'volume_total', 'mdr_atual'
            ]
            results = cur.fetchall()
            
            if not results:
                return None, None
            
            df = pd.DataFrame(results, columns=columns)
            
            df['volume_total'] = df['volume_total'].astype(float)
            df['mdr_atual'] = df['mdr_atual'].astype(float)
            
            df['mdr_proposto'] = df.apply(
                lambda row: (
                    row['volume_total'] * 
                    (taxas_json.get(row['codigo_produto'], {})
                              .get(row['tipo_parcelamento'], {})
                              .get('mdr_percentual', 0) / 100)
                ) if (
                    row['codigo_produto'] in taxas_json and
                    row['tipo_parcelamento'] in taxas_json[row['codigo_produto']]
                ) else row['mdr_atual'],
                axis=1
            )
            
            df['diferenca_mdr'] = df['mdr_proposto'] - df['mdr_atual']
            
            df_mensal = df.groupby('mes').agg({
                'volume_total': 'sum',
                'mdr_atual': 'sum',
                'mdr_proposto': 'sum'
            }).reset_index()
            
            plt.figure(figsize=(15, 7))
            plt.plot(df_mensal['mes'], df_mensal['mdr_atual'], label='MDR Atual', marker='o', linewidth=2, color='#8B0000')
            plt.plot(df_mensal['mes'], df_mensal['mdr_proposto'], label='MDR Proposto', marker='o', linewidth=2, color='#A52A2A')
            plt.title('Comparação MDR Atual vs Proposto (Agrupado por Mês)', pad=20)
            plt.xlabel('Mês')
            plt.ylabel('Valor MDR (R$)')
            plt.legend()
            plt.grid(True, alpha=0.3)
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
            
            impacto_total = df['diferenca_mdr'].sum()
            
            return df, impacto_total
            
    except Exception as e:
        logging.error(f"Erro ao simular MDR por produto: {e}")
        raise
    finally:
        if conn:
            conn.close() 
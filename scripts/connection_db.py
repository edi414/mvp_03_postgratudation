from psycopg2 import sql
import psycopg2
from psycopg2.extras import execute_values

def insert_df_to_db(host, port, user, password, database, schema, table, df):
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        print("Connection successful!")

        with conn.cursor() as cur:
            # Preparando colunas e placeholders
            cols = df.columns.tolist()
            col_names = sql.SQL(', ').join(map(sql.Identifier, cols))

            # Montando a query de inserção
            query = sql.SQL("""
                INSERT INTO {}.{} ({}) VALUES %s;
            """).format(
                sql.Identifier(schema),
                sql.Identifier(table),
                col_names
            )

            # Convertendo o DataFrame em uma lista de tuplas (rows)
            rows = [tuple(row) for row in df.itertuples(index=False, name=None)]

            # Usando execute_values para inserir todas as linhas de uma vez
            execute_values(cur, query, rows)

            # Commit da transação
            conn.commit()
            print(f"{len(df)} records inserted into table '{table}' in schema '{schema}'.")

    except Exception as error:
        print(f"Error inserting data: {error}")
        if conn:
            conn.rollback()
        raise

    finally:
        if conn:
            conn.close()
            print("Connection closed")

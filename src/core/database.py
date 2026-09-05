import psycopg2
from psycopg2 import sql, pool
from contextlib import contextmanager
import os

class PostgresDB:
    def __init__(self, minconn=1, maxconn=10):
        self.minconn = minconn
        self.maxconn = maxconn
        self.pool = None
        self._init_pool()

    def _init_pool(self):
        try:
            cert_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'certs', 'global-bundle.pem')
            if not os.path.exists(cert_path):
                cert_path = './src/certs/global-bundle.pem'

            conn_kwargs = {
                'host': os.environ.get('dburl'),
                'port': int(os.environ.get('dbport', 5432)),
                'database': os.environ.get('dbname', 'EVENT'),
                'user': os.environ.get('dbuser', 'postgres'),
                'password': os.environ.get('password'),
            }
            if os.path.exists(cert_path):
                conn_kwargs['sslmode'] = 'verify-full'
                conn_kwargs['sslrootcert'] = cert_path

            self.pool = pool.ThreadedConnectionPool(
                self.minconn,
                self.maxconn,
                **conn_kwargs
            )
            print("PostgreSQL ThreadedConnectionPool initialized successfully.")
        except Exception as e:
            print(f"Database connection pool initialization failed: {e}")
            raise e

    @contextmanager
    def get_connection(self):
        """
        Thread-safe context manager to checkout a connection from the pool,
        verify liveness (pre-ping for AWS RDS idle timeout), and return it cleanly.
        """
        if self.pool is None or self.pool.closed:
            self._init_pool()

        conn = None
        try:
            conn = self.pool.getconn()
            if conn.closed:
                self.pool.putconn(conn, close=True)
                conn = self.pool.getconn()
            else:
                try:
                    with conn.cursor() as test_cur:
                        test_cur.execute("SELECT 1;")
                except Exception:
                    self.pool.putconn(conn, close=True)
                    conn = self.pool.getconn()

            yield conn
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise e
        finally:
            if conn and self.pool and not self.pool.closed:
                self.pool.putconn(conn)

    def close(self):
        try:
            if self.pool and not self.pool.closed:
                self.pool.closeall()
                print("All database pool connections closed.")
        except Exception as e:
            print(f"Error closing database pool: {e}")

    def verify_update(self, table, data):
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE event_registrations
                        SET
                            payment_id = %s,
                            signature = %s,
                            status = %s,
                            update_at = NOW()
                        WHERE order_id = %s
                        RETURNING *;
                        """,
                        (
                            data["payment_id"],
                            data["signature"],
                            "paid",
                            data["order_id"],
                        )
                    )
                    row = cur.fetchone()
                conn.commit()
                return row
        except Exception as e:
            print(f"Database update error: {e}")
            raise e

    def get_all(self, table):
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table)))
                    columns = [d.name for d in cur.description]
                    rows = cur.fetchall()
                return columns, rows
        except Exception as e:
            print(f"Database read error: {e}")
            raise e

    def insert(self, table: str, data: dict):
        try:
            with self.get_connection() as conn:
                columns = sql.SQL(", ").join([sql.Identifier(k) for k in data.keys()])
                placeholders = sql.SQL(", ").join([sql.Placeholder() for _ in data])
                query = sql.SQL(
                    "INSERT INTO {} ({}) VALUES ({}) RETURNING *;"
                ).format(sql.Identifier(table), columns, placeholders)

                with conn.cursor() as cur:
                    cur.execute(query, list(data.values()))
                    row = cur.fetchone()
                conn.commit()
                return row
        except Exception as e:
            print(f"Database insert error: {e}")
            raise e

    def get_orgid(self, table, org_code):
        try:
            with self.get_connection() as conn:
                query = sql.SQL("SELECT id FROM {} WHERE org_code = %s;").format(sql.Identifier(table))
                with conn.cursor() as cur:
                    cur.execute(query, (org_code,))
                    user = cur.fetchone()
                return user[0] if user else None
        except Exception as e:
            print(f"Database get_orgid error: {e}")
            raise e

    def update(self, table, data, id):
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = sql.SQL(
                        """
                        UPDATE {table}
                        SET {fields}
                        WHERE id = %s
                        """
                    ).format(
                        table=sql.Identifier(table),
                        fields=sql.SQL(", ").join(
                            sql.SQL("{} = %s").format(sql.Identifier(key))
                            for key in data.keys()
                        )
                    )
                    values = list(data.values()) + [id]
                    cur.execute(query, values)
                    print("Rows updated:", cur.rowcount)
                conn.commit()
        except Exception as e:
            print(f"Database update error: {e}")
            raise e

    def insert_where(
        self,
        table: str,
        key: str,
        values: str,
        where_key: str,
        where_val: str,
        condition: str = "="
    ):
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = sql.SQL(
                        """
                        UPDATE {table}
                        SET {key} = %s
                        WHERE {where_key} {condition} %s
                        RETURNING *;
                        """
                    ).format(
                        table=sql.Identifier(table),
                        key=sql.Identifier(key),
                        where_key=sql.Identifier(where_key),
                        condition=sql.SQL(condition),
                    )
                    cur.execute(query, (values, where_val))
                    affected_rows = cur.rowcount
                conn.commit()
                return affected_rows
        except Exception as e:
            print(f"Database insert_where error: {e}")
            raise e

    def get_where(
        self,
        table: str,
        keys: list[str],
        where_key: str,
        where_val,
        condition: str = "=",
        order_by: str = "created_at",
        order: str = "DESC",
    ):
        try:
            order = order.upper()
            if order not in ("ASC", "DESC"):
                raise ValueError("order must be 'ASC' or 'DESC'")

            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = sql.SQL("""
                        SELECT *
                        FROM {table}
                        WHERE {where_key} {condition} %s
                        ORDER BY {order_by} {order}
                    """).format(
                        table=sql.Identifier(table),
                        where_key=sql.Identifier(where_key),
                        condition=sql.SQL(condition),
                        order_by=sql.Identifier(order_by),
                        order=sql.SQL(order),
                    )
                    cur.execute(query, (where_val,))
                    rows = cur.fetchall()
                return rows
        except Exception as e:
            print(f"Database get_where error: {e}")
            raise e

    def login(self, table, data):
        username = data['login_id']
        org_id = data['organization_id']
        password = data['password']

        try:
            with self.get_connection() as conn:
                query = sql.SQL("""
                    SELECT id, role, organization_id, password_hash
                    FROM {table}
                    WHERE username = %s
                        AND organization_id = %s
                """).format(table=sql.Identifier(table))

                with conn.cursor() as cur:
                    cur.execute(query, (username, org_id))
                    user = cur.fetchone()

            if user is None:
                return {
                    "success": False,
                    "message": "User doesn't exist"
                }

            user_id, role, org_id, password_hash = user

            if password != password_hash:
                return {
                    "success": False,
                    "message": "Invalid password"
                }

            return {
                "success": True,
                "message": "Login successful",
                "user": {
                    "user_id": user_id,
                    "organization_id": org_id,
                    "role": role,
                }
            }
        except Exception as e:
            print(f"Database login error: {e}")
            raise e

    def delete(self, table, key, val):
        try:
            with self.get_connection() as conn:
                query = sql.SQL("""
                    DELETE FROM {table}
                    WHERE {key} = %s;
                """).format(
                    table=sql.Identifier(table),
                    key=sql.Identifier(key)
                )

                with conn.cursor() as cur:
                    cur.execute(query, (val,))
                conn.commit()

            return {
                "success": True,
                "message": "DELETE successful",
            }
        except Exception as e:
            print(f"Database delete error: {e}")
            raise e
            
                
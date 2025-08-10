# pgvector_handler.py

import os
from pgvector.psycopg2 import register_vector
import psycopg2
import numpy as np

class PGVectorHandler:
    """
    A class to handle all interactions with the PostgreSQL database with the pgvector extension.
    It connects to the Aurora database, creates the necessary tables, and provides methods for
    adding documents, adding chunks, and performing similarity searches.
    """

    def __init__(self, db_host, db_user, db_password, db_name="postgres", dimension=1024):
        """
        Initializes the PGVectorHandler and connects to the database.

        Args:
            db_host (str): The database endpoint (Writer endpoint).
            db_user (str): The database username.
            db_password (str): The database password.
            db_name (str): The name of the database.
            dimension (int): The dimension of the vector embeddings. Defaults to 1024 for Mistral.
        """
        self.db_host = db_host
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.dimension = dimension
        self.conn = None

        try:
            self.conn = psycopg2.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                dbname=self.db_name
            )
            self.conn.autocommit = True
            print("Successfully connected to the PostgreSQL database.")
            # Register the vector data type with psycopg2
            register_vector(self.conn)
            self._create_tables()
        except psycopg2.OperationalError as e:
            print(f"Error connecting to database: {e}")
            raise e

    def _create_tables(self):
        """
        Creates the 'documents' and 'chunks' tables if they don't already exist.
        The 'documents' table stores metadata like title, and the 'chunks' table
        stores the original text chunks and their corresponding embeddings.
        """
        create_documents_table_sql = """
                                     CREATE TABLE IF NOT EXISTS documents \
                                     ( \
                                         id \
                                         SERIAL \
                                         PRIMARY \
                                         KEY, \
                                         doc_tag \
                                         VARCHAR \
                                     ( \
                                         255 \
                                     ) UNIQUE NOT NULL,
                                         title VARCHAR \
                                     ( \
                                         255 \
                                     )
                                         ); \
                                     """
        create_chunks_table_sql = f"""
        CREATE TABLE IF NOT EXISTS chunks (
            id SERIAL PRIMARY KEY,
            text TEXT,
            embedding VECTOR({self.dimension}),
            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE
        );
        """
        with self.conn.cursor() as cur:
            cur.execute(create_documents_table_sql)
            cur.execute(create_chunks_table_sql)
            self.conn.commit()
        print("Tables 'documents' and 'chunks' are ready.")

    def add_document_metadata(self, doc_tag, title):
        """
        Adds a new document's metadata to the database and returns its ID.

        Args:
            doc_tag (str): A unique tag for the document (e.g., a UUID).
            title (str): The title of the document.

        Returns:
            int: The ID of the newly created document.
        """
        insert_sql = "INSERT INTO documents (doc_tag, title) VALUES (%s, %s) RETURNING id;"
        with self.conn.cursor() as cur:
            cur.execute(insert_sql, (doc_tag, title))
            doc_id = cur.fetchone()[0]
            self.conn.commit()
        return doc_id

    def add_chunks_with_embeddings(self, chunks, embeddings, document_id):
        """
        Adds a list of text chunks and their corresponding embeddings to the database,
        linking them to a specific document.

        Args:
            chunks (list): A list of text strings.
            embeddings (list): A list of numpy arrays representing the vector embeddings.
            document_id (int): The ID of the document these chunks belong to.
        """
        insert_sql = "INSERT INTO chunks (text, embedding, document_id) VALUES (%s, %s, %s);"
        with self.conn.cursor() as cur:
            for text_chunk, embedding_vector in zip(chunks, embeddings):
                try:
                    # Convert list to numpy array for pgvector
                    cur.execute(insert_sql, (text_chunk, np.array(embedding_vector), document_id))
                except psycopg2.Error as e:
                    print(f"Error inserting data: {e}")
            self.conn.commit()
        print(f"Successfully added {len(chunks)} chunks to the database.")

    def search_similar_chunks(self, query_embedding, doc_id=None, k=5):
        """
        Performs a vector similarity search for the top k most similar chunks.

        Args:
            query_embedding (list): The vector embedding of the user's query.
            doc_id (int): An optional document ID to filter the search by.
            k (int): The number of similar chunks to retrieve.

        Returns:
            list: A list of text chunks similar to the query.
        """
        if doc_id:
            search_sql = "SELECT text FROM chunks WHERE document_id = %s ORDER BY embedding <-> %s LIMIT %s;"
            params = (doc_id, np.array(query_embedding), k)
        else:
            search_sql = "SELECT text FROM chunks ORDER BY embedding <-> %s LIMIT %s;"
            params = (np.array(query_embedding), k)

        results = []
        with self.conn.cursor() as cur:
            cur.execute(search_sql, params)
            results = [row[0] for row in cur.fetchall()]
        return results

    def get_document_id_by_title(self, title):
        """
        Retrieves a document's ID based on its title.

        Args:
            title (str): The title of the document.

        Returns:
            int: The document ID, or None if not found.
        """
        select_sql = "SELECT id FROM documents WHERE title = %s;"
        with self.conn.cursor() as cur:
            cur.execute(select_sql, (title,))
            result = cur.fetchone()
        return result[0] if result else None

    def get_all_document_titles(self):
        """
        Retrieves a list of all unique document titles.

        Returns:
            list: A list of document titles.
        """
        select_sql = "SELECT DISTINCT title FROM documents ORDER BY title;"
        with self.conn.cursor() as cur:
            cur.execute(select_sql)
            titles = [row[0] for row in cur.fetchall()]
        return titles

    def get_all_chunks_for_document(self, doc_id):
        """
        Retrieves all text chunks for a given document.

        Args:
            doc_id (int): The ID of the document.

        Returns:
            list: A list of all text chunks for the document.
        """
        select_sql = "SELECT text FROM chunks WHERE document_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(select_sql, (doc_id,))
            chunks = [row[0] for row in cur.fetchall()]
        return chunks

    def close(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            print("Database connection closed.")
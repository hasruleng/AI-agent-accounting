from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import psycopg2

# Database configuration
DB_USER = "postgres"
DB_PASSWORD = "example"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "ai_gcc"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create the database if it does not exist
def create_database():
    conn = psycopg2.connect(dbname="postgres", user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
    exists = cursor.fetchone()
    if not exists:
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
    cursor.close()
    conn.close()

create_database()

# Create database engine
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class ObjectTable(Base):
        __tablename__ = 'object_table'
        object_id = Column(Integer, primary_key=True, autoincrement=True)
        object_name = Column(String, nullable=False)
        jenis_object = Column(String, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)

        journals = relationship("JurnalUmumTable", back_populates="object")

# Define Kode Akuntansi Table
class KodeAkuntansiTable(Base):
    __tablename__ = 'kode_akuntansi_table'
    kode_id = Column(Integer, primary_key=True, autoincrement=False)
    nama_kode = Column(String, nullable=False)

    journals = relationship("JurnalUmumTable", back_populates="kode_akuntansi_rel", cascade="all, delete-orphan")

# Define Jurnal Umum Table
class JurnalUmumTable(Base):
    __tablename__ = 'jurnal_umum_table'
    id_jurnal = Column(Integer, primary_key=True, autoincrement=True)
    nama_transaksi = Column(String, nullable=False)
    kode_akuntansi = Column(Integer, ForeignKey('kode_akuntansi_table.kode_id', ondelete="CASCADE"), nullable=False)
    object_id = Column(Integer, ForeignKey('object_table.object_id', ondelete="SET NULL"), nullable=True)
    keterangan = Column(String)
    debit = Column(Numeric(12, 2), default=0.00)
    kredit = Column(Numeric(12, 2), default=0.00)
    created_at = Column(DateTime, default=datetime.utcnow)

    object = relationship("ObjectTable", back_populates="journals")
    kode_akuntansi_rel = relationship("KodeAkuntansiTable", back_populates="journals")

if __name__ == '__main__':
    # Create tables
    Base.metadata.create_all(engine)

    print("Database and tables created successfully.")

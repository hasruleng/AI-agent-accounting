import streamlit as st
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain.chat_models import init_chat_model
from langchain.agents.agent_types import AgentType
import os
from dotenv import load_dotenv
from langchain import hub
import openai

load_dotenv()

DB_USER = "postgres"
DB_PASSWORD = "example"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "ai_gcc"

#$env:OPENAI_API_KEY="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"


DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

db = SQLDatabase.from_uri(DATABASE_URL)

llm = init_chat_model(model='gpt-4o', temperature=0)

prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
system_message = prompt_template.format(dialect="PostgreSQL", top_k=10)

prefix = """Anda adalah seorang profesor akuntansi yang memiliki pengalaman lebih dari 20 tahun dalam bidang akuntansi. 
Anda memiliki pengetahuan yang mendalam tentang akuntansi dan akuntansi perusahaan. 
Anda dapat menjawab pertanyaan tentang akuntansi perusahaan dengan baik.

additional notes:
Posisi Akun,	Bertambah di sisi,	Berkurang di sisi, kode format
Aset,	Debit,	Kredit, 1xx
Kewajiban,	Kredit,	Debit, 2xx
Ekuitas,	Kredit,	Debit, 3xx
Pendapatan,	Kredit,	Debit, 4xx
Beban/Biaya,	Debit,	Kredit, 5xx

- jika melakukan query mandatory untuk melakukan filtering berdasarkan kode_id
- jika ditanyakan soal keuntungan pasti pendapatan dikurangi pengeluaran
- jika ditanyakan soal keuntungan barang, rumusnya penjualan barang x dikurangi HPP penjualan barang x
"""

toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent = create_sql_agent(
    llm = llm,
    toolkit=toolkit,
    verbose=True,
    handle_parsing_errors=True,
    prefix=prefix,
    system_message=system_message,
    agent_type=AgentType.OPENAI_FUNCTIONS
)

#streamlit UI
st.title("SQL Agent for Accounting Database")
st.write("Ask questions about the accounting database in natural language")

user_question = st.text_input("Enter your question:")

if user_question:
    try:
        response = agent.run(user_question)
        st.write("Response:")
        st.write(response)
    except Exception as e:
        st.error(e)

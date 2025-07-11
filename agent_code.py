import streamlit as st
from sqlalchemy import create_engine, text
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain.chat_models import init_chat_model
from langchain.agents.agent_types import AgentType
import os
from dotenv import load_dotenv
from langchain import hub
import json
import pandas as pd
from datetime import datetime
from utils_code import generate_laporan_jurnal_umum, generate_laporan_laba_rugi, save_dataframe

load_dotenv()

DB_USER = "postgres"
DB_PASSWORD = "example"
DB_HOST = "localhost"
DB_PORT = "5433"
DB_NAME = "ai_gcc"

def classify_question(question):
    classification_prompt= "please classify this question into 3 types of question " \
    "[laporan laba rugi, laporan jurnal umum, other question], for the laporan laba rugi or laporan jurnal umum " \
    "it's mandatory to contain word laporan in the question please don't add any extra text"

    classification = llm.invoke(f"{classification_prompt}: {question}")
    return classification.content.strip()

def extract_parameters(question):
    extraction_prompt = "please extract this question into these fields\noutput_format:\nstart_date:\nend_date\nplease don't add any extra text only json format on startdate and enddate please follow format yyyy-mm-dd"
    extraction = llm.invoke(f"{extraction_prompt}: {question}")
    extraction = extraction.content.replace('```json', '').replace('```', '').strip()
    return json.loads(extraction)

def generate_laporan_laba_rugi_with_params(start_date, end_date, format: str = 'pdf'):
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

    df = generate_laporan_laba_rugi(start_date=start_date_obj, end_date=end_date_obj)

    filename = f"laba_rugi_report.{format}" if format != "excel" else f"laba_rugi_report.xlsx"

    save_dataframe(df, filename, format, "LAPORAN LABA RUGI", start_date_obj, end_date_obj)

    st.success("Laporan Laba Rugi generated.")

    st.download_button(
        label=f"Download Laporan Laba Rugi ({format.upper()})",
        data=open(filename, "rb").read(),
        file_name=filename,
        mime=f"application/{format}"
    )

def generate_laporan_jurnal_umum_with_params(start_date, end_date, format: str = 'pdf'):
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

    df = generate_laporan_jurnal_umum(start_date=start_date_obj, end_date=end_date_obj)

    filename = f"jurnal_umum_report.{format}" if format != "excel" else f"jurnal_umum_report.xlsx"

    save_dataframe(df, filename, format, "LAPORAN JURNAL UMUM", start_date_obj, end_date_obj)
    st.success("Laporan Jurnal Umum generated.")
    st.download_button(
        label=f"Download Laporan Jurnal Umum ({format.upper()})",
        data=open(filename, "rb").read(),
        file_name=filename,
        mime=f"application/{format}"
    )

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

db = SQLDatabase.from_uri(DATABASE_URL)

llm = init_chat_model(model='gpt-4o', temperature=0) # Low Temperature (Output is more deterministic and focused, less hallucination

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
        classification = classify_question(user_question)
        if classification == "laporan laba rugi":
            params = extract_parameters(user_question)
            generate_laporan_laba_rugi_with_params(
            start_date=params.get('start_date'),
            end_date=params.get('end_date'),
            format=params.get('output_format', 'pdf')
        )
        elif classification == "laporan jurnal umum":
            params = extract_parameters(user_question)
            generate_laporan_jurnal_umum_with_params(
                    start_date=params.get('start_date'),
                    end_date=params.get('end_date'),
                    format=params.get('output_format', 'pdf')
                )
        else:
            response = agent.run(user_question)
            st.write("Response:")
            st.write(response)
    except Exception as e:
        st.error(e)

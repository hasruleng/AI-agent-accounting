import streamlit as st
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain.chat_models import init_chat_model
from langchain.agents.agent_types import AgentType
import os
from dotenv import load_dotenv
from langchain import hub
from utils import generate_laporan_jurnal_umum, generate_laporan_laba_rugi, save_dataframe
from datetime import datetime
import json
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()

# Database configuration
DB_USER = "postgres"
DB_PASSWORD = "example"
DB_HOST = "localhost"
DB_PORT = "5433"
DB_NAME = "ai_gcc"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Initialize the database connection
db = SQLDatabase.from_uri(DATABASE_URL)

# Initialize the LLM
llm = init_chat_model(model="gpt-4o", temperature=0)

prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
system_message = prompt_template.format(dialect="PostgreSQL", top_k=10)
prefix = """Anda adalah seorang profesor akuntansi yang memiliki pengalaman lebih dari 20 tahun dalam bidang akuntansi. 
Anda memiliki pengetahuan yang mendalam tentang akuntansi dan akuntansi perusahaan. 
Anda dapat menjawab pertanyaan tentang akuntansi perusahaan dengan baik.

Berikut adalah struktur database:
"""

rule = """
rule: (if asked about profit and loss statement, use this rule)
- keuntungan = pendapatan akun (401,410) Kredit - beban akun (501-520) Debit
- no akun terdiri dari 3 digit angka
\n
"""

# Create the SQL agent
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    handle_parsing_errors=True,
    prefix=prefix,
    system_message=system_message,
    agent_type=AgentType.OPENAI_FUNCTIONS,
)

# Streamlit UI
st.title("SQL Agent for Accounting Database")
st.write("Ask questions about the accounting database in natural language")

# User input
user_question = st.text_input("Enter your question:")

# Define functions for ChatGPT function calling

def generate_laporan_laba_rugi_with_params(start_date: str = None, end_date: str = None, format: str = "pdf"):
    # Convert date strings to datetime objects
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
    
    # Generate Laporan Laba Rugi
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


def generate_laporan_jurnal_umum_with_params(start_date: str = None, end_date: str = None, format: str = "pdf"):
    # Convert date strings to datetime objects
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
    
    # Generate Laporan Jurnal Umum
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

# Function to classify the question using LLM

def classify_question(question):
    classification_prompt = "please classify this question into 3 types of question [laporan laba rugi, laporan jurnal umum, other question], for the laporan laba rugi or laporan jurnal umum it's mandatory to contain word laporan in the question please don't add any extra text"
    # Call LLM to classify
    classification = llm.invoke(f"{classification_prompt}: {question}")
    return classification.content.strip()

# Function to extract parameters using LLM

def extract_parameters(question):
    extraction_prompt = "please extract this question into these fields\noutput_format:\nstart_date:\nend_date\nplease don't add any extra text only json format"
    # Call LLM to extract parameters
    extraction = llm.invoke(f"{extraction_prompt}: {question}")
    # Handle JSON formatting
    extraction = extraction.content.replace('```json', '').replace('```', '').strip()
    return json.loads(extraction)

# Function to classify if the output is plotable

def classify_output_as_plotable(output):
    plotable_prompt = "please classify this answer into plotable answer or not please only answer with yes or no"
    classification = llm.invoke(f"{plotable_prompt}: {output}")
    return classification.content.strip().lower() == 'yes'

# Function to extract plot parameters

def extract_plot_parameters(output):
    extraction_prompt = "please extract this question into these fields\nplot_type (doughnut, line, or scatter or else):\nlist of the data:\ntitle of the plot\ndata variable name\nplease don't add any extra text only json format"
    extraction = llm.invoke(f"{extraction_prompt}: {output}")
    extraction = extraction.content.replace('```json', '').replace('```', '').strip()
    return json.loads(extraction)

# Function to plot the data using matplotlib

def plot_data(plot_params):
    plot_type = plot_params.get('plot_type')
    data = plot_params.get('list of the data')
    title = plot_params.get('title of the plot')
    data_var_name = plot_params.get('data variable name')
    print(plot_params)
    plt.figure(figsize=(10, 6))
    if plot_type == 'line':
        plt.plot(data, label=data_var_name)
    elif plot_type == 'scatter':
        plt.scatter(range(len(data)), data, label=data_var_name)
    elif plot_type == 'doughnut':
        plt.pie(data, labels=data_var_name, wedgeprops=dict(width=0.3))
    else:
        st.error("Unsupported plot type")
        return

    plt.title(title)
    plt.legend()
    st.pyplot(plt)

# Function to generate matplotlib code

def generate_matplotlib_code(output):
    code_generation_prompt = "please generate matplotlib python code to plot the following data, please save the plot into plot.png file please don't add any extra text only python code"
    code = llm.invoke(f"{code_generation_prompt}: {output}")
    return code.content.replace('```python', '').replace('```', '').strip()

# Function to handle user input using LLM classification and extraction
def handle_user_input_with_llm(question):
    classification = classify_question(question)
    if classification == "laporan laba rugi":
        params = extract_parameters(question)
        generate_laporan_laba_rugi_with_params(
            start_date=params.get('start_date'),
            end_date=params.get('end_date'),
            format=params.get('output_format', 'pdf')
        )
    elif classification == "laporan jurnal umum":
        params = extract_parameters(question)
        generate_laporan_jurnal_umum_with_params(
            start_date=params.get('start_date'),
            end_date=params.get('end_date'),
            format=params.get('output_format', 'pdf')
        )
    else:
        # Handle other questions with SQL agent
        try:
            response = agent.run(question + "\n" + rule)
            st.write("Response:")
            st.write(response)
            # Check if the response is plotable
            if classify_output_as_plotable(response):
                print("Yes")
                # Generate and execute matplotlib code
                matplotlib_code = generate_matplotlib_code(response)
                exec(matplotlib_code)
                st.image("plot.png")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if user_question:
    handle_user_input_with_llm(user_question)

# Add some helpful information about the database schema
st.sidebar.title("Database Schema")
st.sidebar.write("""
The database contains the following tables:
1. object_table
2. kode_akuntansi_table
3. jurnal_umum_table

You can ask questions like:
- What are all the objects in the system?
- Show me the total debit and credit for each account
- List all transactions for a specific object
- What is the balance of a specific account?
""") 
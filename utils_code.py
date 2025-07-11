import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
from typing import Optional
import pdfkit

DB_USER = "postgres"
DB_PASSWORD = "example"
DB_HOST = "localhost"
DB_PORT = "5433"
DB_NAME = "ai_gcc"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def get_db_connection():
    """Create and return a database connection"""
    engine = create_engine(DATABASE_URL)
    return engine.connect()

def generate_laporan_jurnal_umum(start_date, end_date):
    conn = get_db_connection()

    query = """
    SELECT 
        ju.id_jurnal,
        ju.nama_transaksi,
        ju.kode_akuntansi,
        ka.nama_kode AS nama_akun,
        ju.keterangan,
        ju.debit,
        ju.kredit,
        ju.created_at,
        o.object_name
    FROM 
        jurnal_umum_table ju
    JOIN 
        kode_akuntansi_table ka ON ju.kode_akuntansi = ka.kode_id
    LEFT JOIN 
        object_table o ON ju.object_id = o.object_id
    """

    where_clauses = []
    params = {}

    if start_date:
        where_clauses.append("ju.created_at >= :start_date")
        params['start_date'] = start_date
    
    if end_date:
        where_clauses.append("ju.created_at <= :end_date")
        params['end_date'] = end_date

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses) #WHERE ju.created_at >= :start_date AND ju.created_at <= :end_date

    result = conn.execute(text(query), params)

    df = pd.DataFrame(result.fetchall(), columns=result.keys())

    if not df.empty:
        # Format currency columns
        df['debit'] = df['debit'].apply(lambda x: f"Rp {x:,.2f}" if x > 0 else "")
        df['kredit'] = df['kredit'].apply(lambda x: f"Rp {x:,.2f}" if x > 0 else "")
        
        # Format date
        df['created_at'] = df['created_at'].dt.strftime('%d-%m-%Y')
        
        # Reorder columns
        df = df[['created_at', 'kode_akuntansi', 'nama_akun', 'debit', 'kredit']]

    conn.close()
    return df

def generate_laporan_laba_rugi(start_date, end_date):
    conn = get_db_connection()
    date_filter = ""
    params = {}

    if start_date or end_date:
        date_filter = "WHERE "
        
        if start_date:
            date_filter += "ju.created_at >= :start_date"
            params['start_date'] = start_date
            
        if start_date and end_date:
            date_filter += " AND "
            
        if end_date:
            date_filter += "ju.created_at <= :end_date"
            params['end_date'] = end_date
    
    operating_revenue_query = f"""
    SELECT 
        ka.kode_id,
        ka.nama_kode,
        SUM(ju.kredit) - SUM(ju.debit) as total
    FROM 
        jurnal_umum_table ju
    JOIN 
        kode_akuntansi_table ka ON ju.kode_akuntansi = ka.kode_id
    {date_filter}
    AND ka.kode_id = 401
    GROUP BY 
        ka.kode_id, ka.nama_kode
    ORDER BY 
        ka.kode_id
    """

    non_operating_revenue_query = f"""
    SELECT 
        ka.kode_id,
        ka.nama_kode,
        SUM(ju.kredit) - SUM(ju.debit) as total
    FROM 
        jurnal_umum_table ju
    JOIN 
        kode_akuntansi_table ka ON ju.kode_akuntansi = ka.kode_id
    {date_filter}
    AND ka.kode_id = 410
    GROUP BY 
        ka.kode_id, ka.nama_kode
    ORDER BY 
        ka.kode_id
    """

    operating_expense_query = f"""
    SELECT 
        ka.kode_id,
        ka.nama_kode,
        SUM(ju.debit) - SUM(ju.kredit) as total
    FROM 
        jurnal_umum_table ju
    JOIN 
        kode_akuntansi_table ka ON ju.kode_akuntansi = ka.kode_id
    {date_filter}
    AND (ka.kode_id BETWEEN 501 AND 509 OR ka.kode_id BETWEEN 511 AND 520)
    GROUP BY 
        ka.kode_id, ka.nama_kode
    ORDER BY 
        ka.kode_id
    """

    non_operating_expense_query = f"""
    SELECT 
        ka.kode_id,
        ka.nama_kode,
        SUM(ju.debit) - SUM(ju.kredit) as total
    FROM 
        jurnal_umum_table ju
    JOIN 
        kode_akuntansi_table ka ON ju.kode_akuntansi = ka.kode_id
    {date_filter}
    AND ka.kode_id = 510
    GROUP BY 
        ka.kode_id, ka.nama_kode
    ORDER BY 
        ka.kode_id
    """

    operating_revenue_result = conn.execute(text(operating_revenue_query), params)
    non_operating_revenue_result = conn.execute(text(non_operating_revenue_query), params)
    operating_expense_result = conn.execute(text(operating_expense_query), params)
    non_operating_expense_result = conn.execute(text(non_operating_expense_query), params)

    operating_revenue_df = pd.DataFrame(operating_revenue_result.fetchall(), columns=operating_revenue_result.keys())
    non_operating_revenue_df = pd.DataFrame(non_operating_revenue_result.fetchall(), columns=non_operating_revenue_result.keys())
    operating_expense_df = pd.DataFrame(operating_expense_result.fetchall(), columns=operating_expense_result.keys())
    non_operating_expense_df = pd.DataFrame(non_operating_expense_result.fetchall(), columns=non_operating_expense_result.keys())

    report_data = []

    period_text = ""
    if start_date and end_date:
        period_text = f"Periode: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
    elif start_date:
        period_text = f"Periode: Mulai {start_date.strftime('%d/%m/%Y')}"
    elif end_date:
        period_text = f"Periode: Sampai {end_date.strftime('%d/%m/%Y')}"

    total_operating_revenue = operating_revenue_df['total'].sum() if not operating_revenue_df.empty else 0

    report_data.append({"keterangan": "Pendapatan Usaha", "nilai": ""})
    for _, row in operating_revenue_df.iterrows():
        kode_nama = f"{row['kode_id']} - {row['nama_kode']}"
        report_data.append({
            "keterangan": kode_nama, 
            "nilai": f"Rp {row['total']:,.2f}"
        })
    
    total_operating_expense = operating_expense_df['total'].sum() if not operating_expense_df.empty else 0
    
    report_data.append({"keterangan": "Beban Usaha", "nilai": ""})

    for _, row in operating_expense_df.iterrows():
        kode_nama = f"{row['kode_id']} - {row['nama_kode']}"
        report_data.append({
            "keterangan": kode_nama, 
            "nilai": f"Rp {row['total']:,.2f}"
        })

    report_data.append({
        "keterangan": "Jumlah Beban Usaha", 
        "nilai": f"(Rp {total_operating_expense:,.2f})"
    })

    operating_profit = total_operating_revenue - total_operating_expense

    report_data.append({
        "keterangan": "Laba Usaha", 
        "nilai": f"Rp {operating_profit:,.2f}"
    })

    total_non_operating_revenue = non_operating_revenue_df['total'].sum() if not non_operating_revenue_df.empty else 0

    report_data.append({"keterangan": "Pendapatan di Luar Usaha", "nilai": ""})

    for _, row in non_operating_revenue_df.iterrows():
        kode_nama = f"{row['kode_id']} - {row['nama_kode']}"
        report_data.append({
            "keterangan": kode_nama, 
            "nilai": f"Rp {row['total']:,.2f}"
        })

    total_non_operating_expense = non_operating_expense_df['total'].sum() if not non_operating_expense_df.empty else 0
    report_data.append({"keterangan": "Beban di Luar Usaha", "nilai": ""})

    for _, row in non_operating_expense_df.iterrows():
        kode_nama = f"{row['kode_id']} - {row['nama_kode']}"
        report_data.append({
            "keterangan": kode_nama, 
            "nilai": f"Rp {row['total']:,.2f}"
        })

    report_data.append({
        "keterangan": "Jumlah Beban di Luar Usaha", 
        "nilai": f"(Rp {total_non_operating_expense:,.2f})"
    })

    non_operating_profit = total_non_operating_revenue - total_non_operating_expense

    report_data.append({
        "keterangan": "Laba di Luar Usaha", 
        "nilai": f"Rp {non_operating_profit:,.2f}"
    })

    net_profit = operating_profit + non_operating_profit

    report_data.append({
        "keterangan": "Laba Bersih", 
        "nilai": f"Rp {net_profit:,.2f}"
    })

    conn.close()

    result_df = pd.DataFrame(report_data)
    if not result_df.empty:
        # Add period information as metadata
        result_df.attrs['period'] = period_text
        
    return result_df

def dataframe_to_html(df, title, start_date, end_date):
    """
    Convert a DataFrame to an HTML string with a title and date range.

    Args:
        df: DataFrame to convert
        title: Title for the report
        start_date: Optional start date for the report
        end_date: Optional end date for the report

    Returns:
        HTML string
    """
    # Create HTML header
    html = f"<html><head><style>"
    html += "body {font-family: Arial, sans-serif;}"
    html += "table {width: 100%; border-collapse: collapse; margin: 20px 0;}"
    html += "th, td {border: 1px solid black; padding: 8px; text-align: left;}"
    html += "th {background-color: #f2f2f2;}"
    html += "h1, h2, p {text-align: center;}"
    html += "</style></head><body>"

    # Add title and date range
    html += f"<h1>{title}</h1>"
    if start_date and end_date:
        html += f"<p>Periode: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}</p>"
    elif start_date:
        html += f"<p>Periode: Mulai {start_date.strftime('%d/%m/%Y')}</p>"
    elif end_date:
        html += f"<p>Periode: Sampai {end_date.strftime('%d/%m/%Y')}</p>"

    # Convert DataFrame to HTML table
    html += "<table>"
    if title == "LAPORAN LABA RUGI":
        for index, row in df.iterrows():
            if row['keterangan'].startswith('Pendapatan') or row['keterangan'].startswith('Beban'):
                html += f"<tr><th colspan='2'>{row['keterangan']}</th></tr>"
            else:
                html += f"<tr><td>{row['keterangan']}</td><td style='text-align: right;'>{row['nilai']}</td></tr>"
    else:
        html += df.to_html(index=False, border=0)
    html += "</table>"

    # Close HTML
    html += "</body></html>"

    return html

def save_dataframe(df: pd.DataFrame, filename: str, format: str, title: str = "", start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    if format == 'pdf':
        html = dataframe_to_html(df, title, start_date, end_date)
        pdfkit.from_string(html, filename)
    
    elif format == 'excel':
        df.to_excel(filename, index=False)
    
    elif format == 'csv':
        df.to_csv(filename, index=False)
    
    else:
        raise ValueError("Unsupported format. Please choose 'pdf', 'excel', or 'csv'.")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
import re
import requests
from bs4 import BeautifulSoup
from auth import login
from ml_models import modelo_churn, previsao_receita
from simulador import simular_negocio
from insights import gerar_insights
from pdf_report import gerar_pdf
from fpdf import FPDF
from textblob import TextBlob
import urllib3
import base64


# Esta deve ser a PRIMEIRA instrução do Streamlit no código
st.set_page_config(page_title="RevMind", layout="wide")
st.set_page_config(layout="wide")

# =============================
# 🔐 LOGIN
# =============================
if not login():
    st.stop()

st.title(f"🚀 Revenue Intelligence AI | {st.session_state['empresa']}")

# =============================
# 📂 DADOS
# =============================
file = st.file_uploader("Upload de dados (CSV)")

if file:
    df = pd.read_csv(file)
else:
    df = pd.DataFrame({
        'campanha': np.random.choice(['Google','Meta','TikTok'],200),
        'cliques': np.random.randint(100,1000,200),
        'reservas': np.random.randint(10,200,200),
        'valor': np.random.randint(1000,10000,200),
        'custo': np.random.randint(500,5000,200)
    })

# =============================
# 📊 ABAS
# =============================
aba1, aba2, aba3, aba4, aba5, aba6, aba7 = st.tabs([
    "📊 Visão Geral",
    "📈 Marketing",
    "🔻 Funil",
    "🔮 Simulador",
    "👥 CRM",
    "🌐 URL",
    "🤖 IA"
])

# =============================
# 📊 VISÃO GERAL
# =============================
with aba1:
    receita = df['valor'].sum()
    custo = df['custo'].sum()
    reservas = df['reservas'].sum()
    cliques = df['cliques'].sum()

    ticket = receita / reservas if reservas else 0
    roas = receita / custo if custo else 0
    cac = custo / reservas if reservas else 0
    conversao = reservas / cliques if cliques else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Receita", f"R$ {receita:,.0f}")
    col2.metric("📦 Reservas", reservas)
    col3.metric("📈 ROAS", round(roas,2))
    col4.metric("💸 CAC", round(cac,2))

    fig = px.bar(df, x='campanha', y='valor', color='campanha')
    st.plotly_chart(fig, use_container_width=True)

# =============================
# 📈 MARKETING
# =============================
with aba2:
    df_group = df.groupby('campanha').sum().reset_index()
    df_group['ROAS'] = df_group['valor'] / df_group['custo']
    df_group['CAC'] = df_group['custo'] / df_group['reservas']

    st.dataframe(df_group)

    fig = px.bar(df_group, x='campanha', y='ROAS')
    st.plotly_chart(fig, use_container_width=True)

# =============================
# 🔻 FUNIL
# =============================
with aba3:
    funil = pd.DataFrame({
        'Etapa': ['Cliques','Reservas'],
        'Valor': [df['cliques'].sum(), df['reservas'].sum()]
    })

    fig = px.funnel(funil, x='Valor', y='Etapa')
    st.plotly_chart(fig, use_container_width=True)

# =============================
# 🔮 SIMULADOR
# =============================
with aba4:
    investimento = st.number_input("Investimento", value=10000)
    cpc = st.number_input("CPC", value=2.0)
    conv = st.slider("Conversão", 0.0, 0.1, 0.02)
    ticket = st.number_input("Ticket médio", value=1000)
    custo_op = st.number_input("Custo operacional", value=300)

    res = simular_negocio(investimento, cpc, conv, ticket, custo_op)

    col1, col2, col3 = st.columns(3)
    col1.metric("Receita", f"R$ {res['receita']:,.0f}")
    col2.metric("Lucro", f"R$ {res['lucro']:,.0f}")
    col3.metric("ROI", round(res['roi'],2))

# =============================
# 👥 CRM
# =============================
with aba5:
    df = modelo_churn(df)

    fig = px.pie(df, names='churn_pred')
    st.plotly_chart(fig)


# =============================
# 🌐 URL INTELIGENTE ABA 6 PRO
# ============================ 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- FUNÇÃO: GERADOR DE PDF PADRÃO INTERNACIONAL ---
def gerar_pdf_internacional(df, ticket, cpc):
    pdf = FPDF()
    pdf.add_page()
    
    # Header Estilo Consultoria (McKinsey/Gartner)
    pdf.set_fill_color(44, 62, 80) # Azul Escuro Corporate
    pdf.rect(0, 0, 210, 40, 'F')
    
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "STRATEGIC DIGITAL AUDIT REPORT", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 5, "Global Benchmarking & Revenue Intelligence", ln=True, align='C')
    
    pdf.ln(25)
    pdf.set_text_color(0, 0, 0)
    
    # Section 1: Executive Summary
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. EXECUTIVE SUMMARY", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 7, f"This audit evaluates the digital maturity of selected assets. Analyzing a target Ticket of R$ {ticket:,.2f} against a market CPC of R$ {cpc:,.2f}. The Revenue Intelligence Engine calculates the EPC (Earnings Per Click) to determine financial scalability.")
    
    pdf.ln(10)
    
    # Section 2: Data Matrix
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(75, 10, "Target URL", 1, 0, 'C', 1)
    pdf.cell(35, 10, "Speed (LCP)", 1, 0, 'C', 1)
    pdf.cell(40, 10, "EPC (Earnings)", 1, 0, 'C', 1)
    pdf.cell(40, 10, "Conv. Score", 1, 1, 'C', 1)
    
    pdf.set_font("Arial", '', 9)
    for _, row in df.iterrows():
        pdf.cell(75, 10, str(row['URL'][:40]), 1)
        pdf.cell(35, 10, f"{row['Velocidade (s)']}s", 1, 0, 'C')
        pdf.cell(40, 10, f"R$ {row['EPC Estimado (R$)']}", 1, 0, 'C')
        pdf.cell(40, 10, f"{row['Score Conversão']}%", 1, 1, 'C')
        
    pdf.ln(10)
    
    # Section 3: Strategic Insights
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "2. COMPETITIVE INSIGHTS", ln=True)
    pdf.set_font("Arial", '', 11)
    
    melhor_site = df.sort_values("EPC Estimado (R$)", ascending=False).iloc[0]
    insight = f"The asset {melhor_site['URL']} presents the highest yield potential per click. Recommendation: Focus on 'Wedding' and 'VIP' segments to leverage high-ticket conversions and mitigate current churn risks."
    pdf.multi_cell(0, 7, insight)
    
    pdf.set_y(-25)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "Confidential - Revenue Intelligence AI | Global Hotel Standards", 0, 0, 'C')
    
    return pdf.output(dest='S').encode('latin-1', 'ignore')


# =============================
# 🌐 INTERDACE (DEBTRO DO WITCH ABA6)
# ============================ 
with aba6:
    st.title("🚀 Global Revenue Intelligence Hub")
    st.write("Auditoria de Performance, Sentimento e **Potencial de Lucro por Clique (EPC)**.")

    with st.sidebar:
        st.subheader("⚙️ Configurações de ROI")
        ticket_simulacao = st.number_input("Ticket Médio do Pacote (R$):", value=5500, key="ticket_aba6")
        cpc_alvo = st.number_input("Custo por Clique Médio (R$):", value=2.50, key="cpc_aba6")

    urls_input = st.text_area("URLs para Auditoria (uma por linha):", 
                              "https://canabravaresort.com.br\nhttps://costadosauipe.com.br")

    if st.button("📡 Executar Auditoria 360º & Alertas"):
        urls = [u.strip() for u in urls_input.split("\n") if u.strip()]
        resultados = []

        for url in urls:
            with st.spinner(f"Analisando Big Data: {url}..."):
                res = realizar_auditoria_master(url)
                if res: 
                    res["EPC Estimado (R$)"] = estimar_epc(res["Score Conversão"], ticket_simulacao)
                    resultados.append(res)

        if resultados:
            df_final = pd.DataFrame(resultados)

            # --- ALERTAS DE ARBITRAGEM ---
            st.subheader("🚨 Alertas de Arbitragem Financeira")
            for _, row in df_final.iterrows():
                if row['EPC Estimado (R$)'] > cpc_alvo:
                    st.success(f"✅ **Oportunidade em `{row['URL']}`:** EPC (R$ {row['EPC Estimado (R$)']}) > CPC. Altamente Lucrativo.")
                else:
                    st.error(f"⚠️ **Risco em `{row['URL']}`:** EPC (R$ {row['EPC Estimado (R$)']}) < CPC. Operação em Prejuízo.")

            # --- GRÁFICOS DE BI ---
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.bar(df_final, x="URL", y="EPC Estimado (R$)", title="Earnings Per Click (EPC)", color_continuous_scale="Greens"), use_container_width=True)
            with col2:
                st.plotly_chart(px.scatter(df_final, x="Velocidade (s)", y="Sentimento de Marca", size="Score Conversão", color="URL", title="Market Positioning"), use_container_width=True)

            # --- BOTÃO DO PDF EXECUTIVO ---
            st.divider()
            st.subheader("📄 Relatório Executivo Internacional")
            pdf_bytes = gerar_pdf_internacional(df_final, ticket_simulacao, cpc_alvo)
            
            st.download_button(
                label="📥 Download Global Strategic Audit (PDF)",
                data=pdf_bytes,
                file_name="Strategic_Audit_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

            # --- ESPIONAGEM DE ADS ---
            st.divider()
            st.subheader("🕵️ Intelligence: Ads Library")
            for url in urls:
                clean = url.replace("https://","").replace("http://","").replace("www.","").split("/")[0]
                link_ads = f"https://facebook.com{clean}&country=BR"
                st.link_button(f"🔎 Ver Criativos de: {clean}", link_ads)

            st.success("Auditoria internacional concluída com sucesso!")
            
# =============================
# 🤖 IA
# =============================
with aba7:
    df = previsao_receita(df)

    fig = px.line(df, y='forecast')
    st.plotly_chart(fig)

    insights = gerar_insights(df)

    for i in insights:
        st.write("👉", i)

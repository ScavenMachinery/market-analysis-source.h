import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp
import locale
import duckdb
from PIL import Image

img = Image.open('tondino3.png')
image = Image.open('logo.bettershop.png')

st.set_page_config(
        layout="wide",
        page_title='Market Analysis',
        page_icon=img)

st.image(image, width=400)

st.title("ANALISI DI MERCATO 30 GIORNI")
st.markdown("_source.h v.1.0_")

#nascondere dalla pagina la scritta "made with streamlit"
hide_style = """
    <style>
    footer {visibility: hidden;}
    </style>
    """
st.markdown(hide_style, unsafe_allow_html=True)


#upload file
@st.cache_data
def load_data(file):
    data = pd.read_excel(file)
    return data

uploaded_file = st.sidebar.file_uploader("Choose a file")

if uploaded_file is None:
    st.info(" Upload a file through config")
    st.stop()

df = load_data(uploaded_file)

# Rimuovi le colonne specifiche utilizzando Pandas
columns_to_remove = ["Image", "Image URL", "BSR", "Dimensions", "Weight", "Fees €", "Size Tier"]
df_cleaned = df.drop(columns=columns_to_remove, axis=1)

# Rimuovi i duplicati basati sulla colonna "ASIN"
df_cleaned = df_cleaned.drop_duplicates(subset=["ASIN"])

# Elimina le righe con valori "None" nella colonna "Revenue"
df_cleaned = df_cleaned[df_cleaned["Revenue"].notna()]

with st.expander("Data preview"):
    st.dataframe(df_cleaned)


# KPIs

total_Revenue = df["Revenue"].sum()
total_Sales = df["Sales"].sum()

formatted_total_revenues = "{:,.2f}".format(total_Revenue).replace(",", "X").replace(".", ",").replace("X", ".")
formatted_total_units = "{:,.2f}".format(total_Sales).replace(",", "X").replace(".", ",").replace("X", ".")

asp = df["Price €"].mean()

formatted_asp = "{:,.2f}".format(asp).replace(",", "X").replace(".", ",").replace("X", ".")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Total Revenue",
        value=f"{formatted_total_revenues} €")

with col2:
    st.metric(
        label="Total Sales",
        value=f"{formatted_total_units}")
    
with col3:
    st.metric(
        label="Average Selling Price",
        value=f"{formatted_asp} €")



#FULFILLMENT KPIS

fatturato_FBA = df[df['Fulfillment'] == 'FBA']['Revenue'].sum()
fatturato_MFN = df[df['Fulfillment'] == 'MFN']['Revenue'].sum()
fatturato_AMZ = df[df['Fulfillment'] == 'AMZ']['Revenue'].sum()

incidenza_FBA = (fatturato_FBA / total_Revenue) * 100
incidenza_MFN = ( fatturato_MFN / total_Revenue) * 100
incidenza_AMZ = (fatturato_AMZ / total_Revenue) * 100

col4, col5, col6 = st.columns(3)

with col4:
    st.metric(
        label="FBA",
        value="{:.2f} %".format(incidenza_FBA))

with col5:
    st.metric(
        label="MFN/FBM",
        value="{:.2f} %".format(incidenza_MFN))


with col6:
    st.metric(
        label="AMZ",
        value="{:.2f} %".format(incidenza_AMZ))
    

colA, colB= st.columns(2)

# Calcola il conteggio di ASIN e Marca
count_asin = df_cleaned["ASIN"].nunique()
count_brand = df_cleaned["Brand"].nunique()

with colA:
    st.metric("Conteggio ASIN", count_asin, "ASIN")

with colB:
    st.metric("Conteggio BRAND", count_brand, "Brand")


st.subheader("_Visualizzazione TOP BRAND per Revenue e Unita'_", divider ="orange")


col7, col8 = st.columns(2)

    
#GRAFICO 1
df_cleaned = df_cleaned.rename(columns={"Brand": "Brand"})
# Calcola i migliori marchi per fatturato
Brand_revenues = df_cleaned.groupby("Brand").sum().nlargest(10, "Revenue")

fig1 = px.bar(Brand_revenues,
            x=Brand_revenues.index,  # Utilizza l'indice del DataFrame invece del nome della colonna
            y="Revenue",
            title="Top 10 Brands by Revenue")

with col7:
    st.plotly_chart(fig1)

df_cleaned = df_cleaned.rename(columns={"Brand": "Brand"})
# Calcola i migliori marchi per fatturato
Brand_units = df_cleaned.groupby("Brand").sum().nlargest(10, "Sales")

fig2 = px.bar(Brand_units,
            x=Brand_units.index,  # Utilizza l'indice del DataFrame invece del nome della colonna
            y="Sales",
            title="Top 10 Brands by Units")

with col8:
    st.plotly_chart(fig2)

st.subheader("_Visualizzazione Quote di mercato TOP BRAND Revenue e Prezzo medio_", divider ="orange")


col9, col10 = st.columns(2)

# Calcola le quote di mercato percentuali per i primi 10 brand
top_10_brands = df_cleaned.groupby("Brand")["Revenue"].sum().nlargest(10)
brand_market_share_percentage = top_10_brands / top_10_brands.sum() * 100

# Crea un DataFrame con le quote di mercato percentuali
market_share_df = pd.DataFrame({
    "Brand": brand_market_share_percentage.index,
    "Market Share (%)": brand_market_share_percentage.values})

# Crea il grafico a torta per i primi 10 brand
fig_pie = px.pie(market_share_df,
                 names="Brand",
                 values="Market Share (%)",
                 title="Quote di Mercato dei Top 10 Brand")

with col9:
    st.plotly_chart(fig_pie)



# Calcola le quote di mercato percentuali per i primi 10 brand
top_10_brands = df_cleaned.groupby("Brand")["Revenue"].sum().nlargest(10)
brand_market_share_percentage = top_10_brands / top_10_brands.sum() * 100

# Calcola la media dei prezzi per i primi 10 brand
brand_price_mean = df_cleaned[df_cleaned["Brand"].isin(top_10_brands.index)].groupby("Brand")["Price €"].mean()

# Crea un DataFrame con le quote di mercato percentuali e la media dei prezzi
market_share_df = pd.DataFrame({
    "Brand": top_10_brands.index,
    "Market Share (%)": brand_market_share_percentage.values,
    "Price Mean": brand_price_mean.values
})

# Crea il sottografo con due assi y
fig = sp.make_subplots(specs=[[{"secondary_y": True}]])

# Aggiungi il grafico a barre per le quote di mercato sull'asse y sinistra
fig.add_trace(go.Bar(x=market_share_df["Brand"], y=market_share_df["Market Share (%)"], name="Quote di Mercato (%)"))

# Aggiungi il grafico a linee per la media dei prezzi sull'asse y destra
fig.add_trace(go.Scatter(x=market_share_df["Brand"], y=market_share_df["Price Mean"], mode="lines+markers", name="Prezzo Medio"), secondary_y=True)

# Imposta il titolo del grafico
fig.update_layout(title="Quote di Mercato e Prezzo Medio dei Top 10 Brand")

# Imposta le etichette degli assi
fig.update_xaxes(title_text="Brand")
fig.update_yaxes(title_text="Quote di Mercato (%)", secondary_y=False)
fig.update_yaxes(title_text="Prezzo Medio", secondary_y=True)

fig.update_layout(width=900)

with col10:
    st.plotly_chart(fig)



st.subheader("_Analisi per Prodotti, TOP 10 ASIN_", divider ="orange")


# Seleziona il grafico da visualizzare

selected_chart = st.selectbox("Seleziona il grafico da visualizzare", ["ASIN BY REVENUES", "ASIN BY UNITS"])

col11, col12 = st.columns(2)

ASIN_revenues = df_cleaned.groupby("ASIN").sum().nlargest(10, "Revenue")

fig3 = px.bar(ASIN_revenues,
            x=ASIN_revenues.index,  # Utilizza l'indice del DataFrame invece del nome della colonna
            y="Revenue",
            title="Top 10 ASIN by Revenue")

ASIN_units = df_cleaned.groupby("ASIN").sum().nlargest(10, "Sales")

fig4 = px.bar(ASIN_units,
            x=ASIN_units.index,  # Utilizza l'indice del DataFrame invece del nome della colonna
            y="Sales",
            title="Top 10 ASIN by Units")

# Ordina il DataFrame in base al fatturato (in ordine decrescente)
df_sorted_revenues = df_cleaned.sort_values(by="Revenue", ascending=False)
df_sorted_units = df_cleaned.sort_values(by="Sales", ascending=False)


# Seleziona solo le colonne "ASIN" e "Product Details"
preview_table1 = df_sorted_revenues[["ASIN", "Product Details","Price €"]]
preview_table2 = df_sorted_units[["ASIN", "Product Details","Price €"]]


# Visualizza il grafico selezionato
if selected_chart == "ASIN BY REVENUES":
    with col11:
        st.plotly_chart(fig3)
    with col12:
        st.dataframe(preview_table1)
else:
    with col11:
        st.plotly_chart(fig4)
    with col12:
        st.dataframe(preview_table2)


st.subheader("_Distribuzione fatturato per Fulfillment dei TOP BRAND_", divider ="orange")


# Filtra il DataFrame per i Top 10 brand
top_10_brands = df_cleaned.groupby("Brand")["Revenue"].sum().nlargest(10)
filtered_df = df_cleaned[df_cleaned["Brand"].isin(top_10_brands.index)]

# Definisci un set personalizzato di colori per le colonne
color_discrete_map = {
    "FBA": "blue",  # Cambia i colori a tuo piacimento
    "MFN": "green",
    "AMZ": "orange"
}

# Crea un grafico a barre raggruppato con il set di colori personalizzato
fig20 = px.bar(filtered_df, x="Brand", y="Revenue", color="Fulfillment", title="Fatturato per FBA, MFN e AMZ dei Top 10 Brand",
             barmode="group", color_discrete_map=color_discrete_map)

# Visualizza il grafico con larghezza adattabile
st.plotly_chart(fig20, use_container_width=True)




st.subheader("_Analisi Revenue, Reviews e RPR_", divider ="orange")

# Calcola la colonna "RPR" (Revenue per Review)
df_cleaned["RPR"] = df_cleaned["Revenue"] / df_cleaned["Review Count"]

# Seleziona solo le colonne desiderate
table_data = df_cleaned[["ASIN","Product Details","Brand", "Revenue", "Review Count", "RPR"]]

# Aggiungi un filtro per "Brand"
selected_brands = st.multiselect("Seleziona una o più Brands", df_cleaned["Brand"].unique())

# Filtra la tabella con i dati desiderati in base ai Brand selezionati
filtered_table_data = table_data[table_data["Brand"].isin(selected_brands)]

# Crea il grafico combinato
fig_combined = go.Figure()

# Aggiungi le barre per "Revenue" e "Review Count" sull'asse y sinistra
fig_combined.add_trace(go.Bar(x=filtered_table_data["ASIN"], y=filtered_table_data["Revenue"], name="Revenue", yaxis="y", marker_color="blue"))
fig_combined.add_trace(go.Bar(x=filtered_table_data["ASIN"], y=filtered_table_data["Review Count"], name="Review Count", yaxis="y", marker_color="lightblue"))

# Aggiungi il grafico a linea per "RPR" sull'asse y destra
fig_combined.add_trace(go.Scatter(x=filtered_table_data["ASIN"], y=filtered_table_data["RPR"], name="RPR", yaxis="y2", mode="lines+markers", line=dict(color="green")))

# Imposta le etichette degli assi
fig_combined.update_layout(
    xaxis=dict(title="ASIN"),
    yaxis=dict(title="Valore", titlefont=dict(color="blue"), tickfont=dict(color="blue")),
    yaxis2=dict(title="RPR", titlefont=dict(color="green"), tickfont=dict(color="green"), overlaying="y", side="right")
)

# Imposta il titolo del grafico combinato
fig_combined.update_layout(title="Confronto tra Revenue, Review Count e RPR per ASIN")

# Visualizza il grafico combinato
st.plotly_chart(fig_combined, use_container_width=True)

st.dataframe(filtered_table_data, use_container_width=True)

st.subheader("_Presentazione pagina prodotto: media numero immagini, media ratings_", divider ="orange")


colC, colD= st.columns([3,1])
# Calcola la media dei valori di "Images" per "Brand"
brand_images_mean = df_cleaned.groupby("Brand")["Images"].mean()

# Crea un DataFrame con i dati
brand_images_df = pd.DataFrame({
    "Brand": brand_images_mean.index,
    "Media Images": brand_images_mean.values
})

# Ordina il DataFrame in base alla media delle immagini
brand_images_df = brand_images_df.sort_values(by="Media Images", ascending=False)

# Crea il grafico a barre orizzontale
fig_barh = px.bar(brand_images_df, x="Media Images", y="Brand", orientation="h", title="Media # Immagini per Brand")

# Imposta le etichette degli assi
fig_barh.update_xaxes(title_text="Media Images")
fig_barh.update_yaxes(title_text="Brand")

with colC:
    st.plotly_chart(fig_barh, use_container_width=True)

# Calcola la media dei valori di "Ratings" per ogni "Brand"
brand_ratings_mean = df_cleaned.groupby("Brand")["Ratings"].mean().reset_index()

with colD:
    st.dataframe(brand_ratings_mean, height=400)


st.subheader("_Conteggi_", divider ="orange")

colE, colF = st.columns(2)

#GRAFICO CONTEGGIO SELLER COUNTRY
# Calcola il conteggio dei valori nella colonna "Seller Country/Region"
country_counts = df_cleaned["Seller Country/Region"].value_counts(dropna=False)

# Crea il grafico a barre per il conteggio dei valori
fig_country_counts = px.bar(
    x=country_counts.index,  # Valori della colonna "Seller Country/Region"
    y=country_counts.values,  # Conteggio dei valori
    title="Conteggio per Seller Country/Region"
)

# Imposta l'etichetta dell'asse x
fig_country_counts.update_xaxes(title_text="Seller Country/Region")

# Imposta l'etichetta dell'asse y
fig_country_counts.update_yaxes(title_text="Conteggio")

with colE:
    st.plotly_chart(fig_country_counts, use_container_width=True)

# GRAFICO CONTEGGIO CATEGORIA
# Calcola il conteggio dei valori nella colonna "Seller Country/Region"
category_counts = df_cleaned["Category"].value_counts(dropna=False)

# Crea il grafico a barre per il conteggio dei valori
fig_category_counts = px.bar(
    x=category_counts.index,  # Valori della colonna "Seller Country/Region"
    y=category_counts.values,  # Conteggio dei valori
    title="Conteggio Category")

# Imposta l'etichetta dell'asse x
fig_category_counts.update_xaxes(title_text="Category")

# Imposta l'etichetta dell'asse y
fig_category_counts.update_yaxes(title_text="Conteggio")

with colF:
    st.plotly_chart(fig_category_counts, use_container_width=True)


# Calcola il conteggio dei "Brand"
brand_count = df_cleaned["Brand"].value_counts().reset_index()
brand_count.columns = ["Brand", "Count"]

# Crea il grafico a barre
fig_bar = px.bar(brand_count, x="Brand", y="Count", title="Conteggio numero di prodotti per Brand")

# Visualizza il grafico a barre
st.plotly_chart(fig_bar, use_container_width=True)


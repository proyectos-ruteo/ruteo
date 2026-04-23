import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from scipy.spatial.distance import cdist

st.set_page_config(page_title="Optimizador de Rutas GOIN", layout="wide")

st.title("RUTEO")

# Definición de Sucursales GOIN
sucursales_goin = [
    {"Nombre": "GOIN Central San Salvador", "Latitud": 13.694192750356294, "Longitud": -89.20764723605487},
    {"Nombre": "GOIN Lourdes", "Latitud": 13.732142182396014, "Longitud": -89.37272523745887},
    {"Nombre": "GOIN San Miguel", "Latitud": 13.4879882726561, "Longitud": -88.17665577285078},
    {"Nombre": "GOIN Santa Ana", "Latitud": 13.985991202082642, "Longitud": -89.55802693152108}
]
df_sucursales = pd.DataFrame(sucursales_goin)

file = st.file_uploader("1. Sube el archivo de entregas (Excel o CSV)", type=['csv', 'xlsx'])

if file:
    df_input = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
    
    # Estandarizar nombres de columnas por si vienen en inglés
    df_input.rename(columns={'Latitude': 'Latitud', 'Longitude': 'Longitud', 'Nombre': 'Nombre'}, inplace=True)
    
    if all(col in df_input.columns for col in ['Nombre', 'Latitud', 'Longitud']):
        
        st.sidebar.header("Configuración de Ruta")
        
        # --- SELECCIÓN DE ORIGEN ---
        tipo_origen = st.sidebar.radio("Punto de Partida:", ["Sucursal GOIN", "Ubicación del Excel"])
        
        if tipo_origen == "Sucursal GOIN":
            origen_sel = st.sidebar.selectbox("Selecciona la Sucursal:", df_sucursales['Nombre'].tolist())
            punto_inicio = df_sucursales[df_sucursales['Nombre'] == origen_sel].iloc[0]
        else:
            origen_sel = st.sidebar.selectbox("Selecciona ubicación del Excel:", df_input['Nombre'].tolist())
            punto_inicio = df_input[df_input['Nombre'] == origen_sel].iloc[0]

        # --- SELECCIÓN DE DESTINO ---
        # Filtramos para que el destino no sea igual al inicio si están en la misma lista
        opciones_destino = df_input[df_input['Nombre'] != origen_sel]['Nombre'].tolist()
        destino_sel = st.sidebar.selectbox("Selecciona Punto Final (del Excel):", opciones_destino)
        punto_fin = df_input[df_input['Nombre'] == destino_sel].iloc[0]

        def optimizar_logistica(inicio, fin, entregas):
            # Crear lista de puntos intermedios (excluyendo el que se eligió como fin)
            intermedios = entregas[entregas['Nombre'] != fin['Nombre']].copy()
            # Si el inicio vino del Excel, también lo quitamos de los intermedios
            intermedios = intermedios[intermedios['Nombre'] != inicio['Nombre']]
            
            puntos_coord = intermedios[['Latitud', 'Longitud']].values
            ruta = [inicio]
            pendientes = list(range(len(puntos_coord)))
            
            # Algoritmo de cercanía
            pos_actual = [inicio['Latitud'], inicio['Longitud']]
            while pendientes:
                distancias = cdist([pos_actual], puntos_coord[pendientes])[0]
                mas_cercano_idx = pendientes[distancias.argmin()]
                ruta.append(intermedios.iloc[mas_cercano_idx])
                pos_actual = [intermedios.iloc[mas_cercano_idx]['Latitud'], intermedios.iloc[mas_cercano_idx]['Longitud']]
                pendientes.remove(mas_cercano_idx)
            
            ruta.append(fin)
            return pd.DataFrame(ruta)

        df_ruta = optimizar_logistica(punto_inicio, punto_fin, df_input)

        # --- MOSTRAR RESULTADOS ---
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Hoja de Ruta")
            st.dataframe(df_ruta[['Nombre']])
            csv = df_ruta.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar Ruta en CSV", data=csv, file_name="ruta_logistica.csv")

        with col2:
            st.subheader("Mapa del Recorrido")
            m = folium.Map(location=[punto_inicio['Latitud'], punto_inicio['Longitud']], zoom_start=10)
            
            coords_mapa = []
            for i, row in df_ruta.iterrows():
                es_inicio = (i == 0)
                es_fin = (i == len(df_ruta)-1)
                color = 'green' if es_inicio else 'red' if es_fin else 'blue'
                icon = 'play' if es_inicio else 'stop' if es_fin else 'info-sign'
                
                folium.Marker(
                    [row['Latitud'], row['Longitud']],
                    popup=f"Orden: {i+1} - {row['Nombre']}",
                    icon=folium.Icon(color=color, icon=icon)
                ).add_to(m)
                coords_mapa.append([row['Latitud'], row['Longitud']])
            
            folium.PolyLine(coords_mapa, color="blue", weight=3, opacity=0.7).add_to(m)
            st_folium(m, width=800, height=500)
    else:
        st.error("Asegúrate de que el archivo tenga columnas: Nombre, Latitud, Longitud")
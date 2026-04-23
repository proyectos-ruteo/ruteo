import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from scipy.spatial.distance import cdist

st.set_page_config(page_title="Optimizador de Rutas GOIN", layout="wide")

st.title("🚚 Sistema de Optimización de Rutas Logísticas")

# Base de datos de Sucursales GOIN
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
    df_input.rename(columns={'Latitude': 'Latitud', 'Longitude': 'Longitud', 'Name': 'Nombre'}, inplace=True)
    
    if all(col in df_input.columns for col in ['Nombre', 'Latitud', 'Longitud']):
        
        st.sidebar.header("Configuración de la Jornada")
        
        # --- SELECCIÓN DE ORIGEN ---
        st.sidebar.subheader("Punto de Salida")
        tipo_origen = st.sidebar.radio("Iniciar desde:", ["Sucursal GOIN", "Punto en Excel"], key="origen_tipo")
        if tipo_origen == "Sucursal GOIN":
            origen_sel = st.sidebar.selectbox("Sucursal de Salida:", df_sucursales['Nombre'].tolist())
            punto_inicio = df_sucursales[df_sucursales['Nombre'] == origen_sel].iloc[0]
        else:
            origen_sel = st.sidebar.selectbox("Punto de Salida (Excel):", df_input['Nombre'].tolist())
            punto_inicio = df_input[df_input['Nombre'] == origen_sel].iloc[0]

        # --- SELECCIÓN DE RETORNO ---
        st.sidebar.subheader("Punto de Retorno")
        tipo_retorno = st.sidebar.radio("Finalizar en:", ["Misma sucursal de salida", "Otra sucursal GOIN", "Punto en Excel"], key="retorno_tipo")
        
        if tipo_retorno == "Misma sucursal de salida":
            punto_fin = punto_inicio
        elif tipo_retorno == "Otra sucursal GOIN":
            retorno_sel = st.sidebar.selectbox("Sucursal de Retorno:", df_sucursales['Nombre'].tolist())
            punto_fin = df_sucursales[df_sucursales['Nombre'] == retorno_sel].iloc[0]
        else:
            retorno_sel = st.sidebar.selectbox("Punto de Retorno (Excel):", df_input['Nombre'].tolist())
            punto_fin = df_input[df_input['Nombre'] == retorno_sel].iloc[0]

        def optimizar_logistica(inicio, fin, entregas):
            # Filtrar entregas para no duplicar el inicio o el fin si están en el Excel
            puntos_intermedios = entregas.copy()
            puntos_intermedios = puntos_intermedios[puntos_intermedios['Nombre'] != inicio['Nombre']]
            puntos_intermedios = puntos_intermedios[puntos_intermedios['Nombre'] != fin['Nombre']]
            
            puntos_coord = puntos_intermedios[['Latitud', 'Longitud']].values
            ruta = [inicio]
            pendientes = list(range(len(puntos_coord)))
            
            pos_actual = [inicio['Latitud'], inicio['Longitud']]
            
            # Algoritmo de vecino más cercano
            while pendientes:
                distancias = cdist([pos_actual], puntos_coord[pendientes])[0]
                mas_cercano_idx = pendientes[distancias.argmin()]
                punto_sig = puntos_intermedios.iloc[mas_cercano_idx]
                ruta.append(punto_sig)
                pos_actual = [punto_sig['Latitud'], punto_sig['Longitud']]
                pendientes.remove(mas_cercano_idx)
            
            ruta.append(fin)
            return pd.DataFrame(ruta)

        df_ruta = optimizar_logistica(punto_inicio, punto_fin, df_input)

        # --- INTERFAZ DE RESULTADOS ---
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Plan de Ruta")
            st.write(f"**Salida:** {punto_inicio['Nombre']}")
            st.write(f"**Llegada final:** {punto_fin['Nombre']}")
            
            # Mostrar tabla numerada
            df_mostrar = df_ruta[['Nombre']].copy()
            df_mostrar.index = range(1, len(df_mostrar) + 1)
            st.table(df_mostrar)
            
            csv = df_ruta.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Hoja de Ruta", data=csv, file_name="ruta_optimizada_goin.csv")

        with col2:
            st.subheader("Mapa Interactivo")
            m = folium.Map(location=[punto_inicio['Latitud'], punto_inicio['Longitud']], zoom_start=9)
            
            coords_mapa = []
            for i, row in df_ruta.iterrows():
                is_start = (i == 0)
                is_end = (i == len(df_ruta) - 1)
                
                # Definir estilo de marcador
                color = 'green' if is_start else 'red' if is_end else 'blue'
                icon = 'play' if is_start else 'home' if is_end else 'info-sign'
                
                folium.Marker(
                    [row['Latitud'], row['Longitud']],
                    popup=f"Parada {i+1}: {row['Nombre']}",
                    tooltip=f"{i+1}. {row['Nombre']}",
                    icon=folium.Icon(color=color, icon=icon)
                ).add_to(m)
                coords_mapa.append([row['Latitud'], row['Longitud']])
            
            folium.PolyLine(coords_mapa, color="blue", weight=3, opacity=0.7).add_to(m)
            st_folium(m, width=800, height=550)
    else:
        st.error("Error: El archivo debe tener las columnas: Nombre, Latitud, Longitud")
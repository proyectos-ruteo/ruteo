import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from scipy.spatial.distance import cdist

st.set_page_config(page_title="Acceso Privado - GOIN", layout="wide")


CODIGO_CORRECTO = "grupogoin.api2026" # <--- Contraseña

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

def verificar_codigo():
    if st.session_state.codigo_ingresado == CODIGO_CORRECTO:
        st.session_state.autenticado = True
    else:
        st.error("Código incorrecto. Intenta de nuevo.")

if not st.session_state.autenticado:
    st.title("Acceso Restringido")
    st.text_input("Ingresa el código de acceso:", type="password", key="codigo_ingresado", on_change=verificar_codigo)
    st.stop()

st.title("RUTEO ÓPTIMO - GOIN")

sucursales_goin = [
    {"Nombre": "GOIN Central San Salvador", "Latitud": 13.694192750356294, "Longitud": -89.20764723605487},
    {"Nombre": "GOIN Lourdes", "Latitud": 13.732142182396014, "Longitud": -89.37272523745887},
    {"Nombre": "GOIN San Miguel", "Latitud": 13.4879882726561, "Longitud": -88.17665577285078},
    {"Nombre": "GOIN Santa Ana", "Latitud": 13.985991202082642, "Longitud": -89.55802693152108}
]
df_sucursales = pd.DataFrame(sucursales_goin)

file = st.file_uploader("1. Sube el archivo de entregas", type=['csv', 'xlsx'])

if file:
    df_input = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
    df_input.rename(columns={'Latitude': 'Latitud', 'Longitude': 'Longitud', 'Name': 'Nombre', 'Latitude ': 'Latitud', 'Longitude ': 'Longitud'}, inplace=True)
    
    if all(col in df_input.columns for col in ['Nombre', 'Latitud', 'Longitud']):
        st.sidebar.header("Configuración")
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()

        # Origen
        tipo_origen = st.sidebar.radio("Salida:", ["Sucursal GOIN", "Excel"])
        if tipo_origen == "Sucursal GOIN":
            origen_sel = st.sidebar.selectbox("Desde:", df_sucursales['Nombre'].tolist())
            punto_inicio = df_sucursales[df_sucursales['Nombre'] == origen_sel].iloc[0]
        else:
            origen_sel = st.sidebar.selectbox("Desde Excel:", df_input['Nombre'].tolist())
            punto_inicio = df_input[df_input['Nombre'] == origen_sel].iloc[0]

        # Retorno
        tipo_retorno = st.sidebar.radio("Retorno:", ["Misma salida", "Otra sucursal", "Excel"])
        if tipo_retorno == "Misma salida":
            punto_fin = punto_inicio
        elif tipo_retorno == "Otra sucursal":
            retorno_sel = st.sidebar.selectbox("Hacia:", df_sucursales['Nombre'].tolist())
            punto_fin = df_sucursales[df_sucursales['Nombre'] == retorno_sel].iloc[0]
        else:
            retorno_sel = st.sidebar.selectbox("Hacia Excel:", df_input['Nombre'].tolist())
            punto_fin = df_input[df_input['Nombre'] == retorno_sel].iloc[0]

        def optimizar_logistica(inicio, fin, entregas):
            puntos_intermedios = entregas.copy()
            puntos_intermedios = puntos_intermedios[puntos_intermedios['Nombre'] != inicio['Nombre']]
            puntos_intermedios = puntos_intermedios[puntos_intermedios['Nombre'] != fin['Nombre']]
            puntos_coord = puntos_intermedios[['Latitud', 'Longitud']].values
            ruta = [inicio]
            pendientes = list(range(len(puntos_coord)))
            pos_actual = [inicio['Latitud'], inicio['Longitud']]
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
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Hoja de Ruta")
            df_mostrar = df_ruta[['Nombre']].copy()
            df_mostrar.index = range(1, len(df_mostrar) + 1)
            st.table(df_mostrar)
            csv = df_ruta.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar CSV", data=csv, file_name="ruta_goin.csv")
        with col2:
            st.subheader("Mapa")
            m = folium.Map(location=[punto_inicio['Latitud'], punto_inicio['Longitud']], zoom_start=9)
            coords_mapa = []
            for i, row in df_ruta.iterrows():
                if i==0: 
                    color = 'green' 
                elif i == len(df_ruta)-1:
                    color = 'red'
                else:
                    color = 'blue'
                    colorelse 'blue'
                folium.Marker([row['Latitud'], row['Longitud']], popup=row['Nombre'], icon=folium.Icon(color=color)).add_to(m)
                coords_mapa.append([row['Latitud'], row['Longitud']])
            folium.PolyLine(coords_mapa, color="blue", weight=3).add_to(m)
            st_folium(m, width=700, height=500)
    else:
        st.error("Columnas requeridas: Nombre, Latitud, Longitud")

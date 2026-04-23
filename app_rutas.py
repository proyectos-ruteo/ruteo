import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from scipy.spatial.distance import cdist

st.set_page_config(page_title="Optimizador de Rutas", layout="wide")

st.title("Optimizador de Rutas de GOIN - Logística")
st.write("Sube el archivo con Nombre, Latitud y Longitud. Luego selecciona el origen y destino.")

file = st.file_uploader("Sube tu archivo (Excel o CSV)", type=['csv', 'xlsx'])

if file:
    df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
    
    if all(col in df.columns for col in ['Nombre', 'Latitud', 'Longitud']):
        
        # --- Configuración de Origen y Destino ---
        st.sidebar.header("Configuración de la Ruta")
        lista_nombres = df['Nombre'].tolist()
        
        origen_nombre = st.sidebar.selectbox("Selecciona el Punto de Origen", lista_nombres)
        # El destino excluye el origen para evitar errores
        opciones_destino = [n for n in lista_nombres if n != origen_nombre]
        destino_nombre = st.sidebar.selectbox("Selecciona el Punto de Destino", opciones_destino)

        def optimizar_ruta(datos, inicio_n, fin_n):
            # Identificar índices de inicio y fin
            idx_inicio = datos[datos['Nombre'] == inicio_n].index[0]
            idx_fin = datos[datos['Nombre'] == fin_n].index[0]
            
            puntos = datos[['Latitud', 'Longitud']].values
            pendientes = [i for i in range(len(puntos)) if i != idx_inicio and i != idx_fin]
            
            ruta_indices = [idx_inicio]
            
            # Algoritmo de vecino más cercano para los puntos intermedios
            while pendientes:
                ultimo = ruta_indices[-1]
                distancias = cdist([puntos[ultimo]], puntos[pendientes])[0]
                mas_cercano = pendientes[distancias.argmin()]
                ruta_indices.append(mas_cercano)
                pendientes.remove(mas_cercano)
            
            # Finalmente añadimos el destino
            ruta_indices.append(idx_fin)
            return datos.iloc[ruta_indices].reset_index(drop=True)

        df_optimizado = optimizar_ruta(df, origen_nombre, destino_nombre)
        
        # --- Visualización ---
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Hoja de Ruta")
            st.write(f"**De:** {origen_nombre}  \n**A:** {destino_nombre}")
            st.table(df_optimizado[['Nombre']]) # Usamos table para una vista más limpia
            
            csv = df_optimizado.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar CSV de la Ruta", data=csv, file_name="ruta_optimizada.csv")
        
        with col2:
            st.subheader("Mapa de la Trayectoria")
            centro = [df['Latitud'].mean(), df['Longitud'].mean()]
            m = folium.Map(location=centro, zoom_start=12)
            
            puntos_ruta = []
            for i, row in df_optimizado.iterrows():
                # Color especial para inicio y fin
                color_icono = 'green' if i == 0 else 'red' if i == len(df_optimizado)-1 else 'blue'
                
                folium.Marker(
                    [row['Latitud'], row['Longitud']], 
                    popup=f"Parada {i+1}: {row['Nombre']}",
                    tooltip=f"{i+1}. {row['Nombre']}",
                    icon=folium.Icon(color=color_icono, icon='info-sign')
                ).add_to(m)
                puntos_ruta.append([row['Latitud'], row['Longitud']])
            
            folium.PolyLine(puntos_ruta, color="blue", weight=3, opacity=0.7).add_to(m)
            st_folium(m, width=800, height=550)
    else:
        st.error("Error: Asegúrate de que las columnas se llamen exactamente: Nombre, Latitud, Longitud")
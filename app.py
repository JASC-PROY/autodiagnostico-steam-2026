import streamlit as st
import pandas as pd
from google import genai
from PIL import Image
import json

# Configuración de la página
st.set_page_config(page_title="Autodiagnóstico STEAM 2026", page_icon="⚡", layout="wide")

# --- ENCABEZADO ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("https://www.utaltamira.edu.mx/wp-content/uploads/2017/06/LOGO-SIN-FONDO.png", width=300)
    
st.title("⚡ Autodiagnóstico Energético Residencial")
st.markdown("Plataforma de evaluación paramétrica. **Paso 1:** Ingresa tus datos de cobro. **Paso 2:** Detalla tu carga térmica y eléctrica.")

# --- PASO 1: DATOS CFE ---
st.header("1. Historial de CFE (Anexo 1)")
metodo = st.radio(
    "¿Cómo ingresarás la información de tu recibo?", 
    ["✍️ Escribir manualmente", "📸 Tomar foto", "🖼️ Subir imagen"], 
    horizontal=True
)

if 'datos_historial' not in st.session_state:
    st.session_state.datos_historial = pd.DataFrame({
        "Bimestre": ["Ene-Feb", "Mar-Abr", "May-Jun", "Jul-Ago", "Sep-Oct", "Nov-Dic"],
        "Consumo (kWh)": [0, 0, 0, 0, 0, 0],
        "Pago ($ MXN)": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    })

def procesar_imagen_recibo(imagen):
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        instruccion = """
        Analiza esta tabla de historial de consumo de CFE. Extrae los primeros 6 renglones (los más recientes).
        Devuelve ÚNICAMENTE un arreglo JSON válido con esta estructura exacta, sin texto adicional ni bloques markdown:
        [
            {"Bimestre": "MAY 26 - JUL 26", "Consumo (kWh)": 26, "Pago ($ MXN)": 58.0},
            {"Bimestre": "MAR 26 - MAY 26", "Consumo (kWh)": 4, "Pago ($ MXN)": 58.0}
        ]
        Asegúrate de que los kWh sean números enteros y los pagos sean números decimales (sin símbolo de pesos).
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[imagen, instruccion]
        )
        
        texto_limpio = response.text.strip().replace('```json', '').replace('```', '')
        datos_extraidos = json.loads(texto_limpio)
        
        st.session_state.datos_historial = pd.DataFrame(datos_extraidos)
        st.success("¡Datos extraídos correctamente con Inteligencia Artificial!")
        
    except Exception as e:
        st.error(f"Error técnico exacto al procesar la imagen: {e}")

if metodo == "🖼️ Subir imagen":
    archivo = st.file_uploader("Selecciona la foto de tu recibo", type=["png", "jpg", "jpeg"])
    if archivo:
        if st.button("Leer datos con IA 🔍"):
            with st.spinner("Analizando la tabla del recibo... 🧐"):
                imagen_pil = Image.open(archivo)
                procesar_imagen_recibo(imagen_pil)

elif metodo == "📸 Tomar foto":
    foto = st.camera_input("Enfoca la tabla de historial")
    if foto:
        if st.button("Leer datos con IA 🔍"):
            with st.spinner("Analizando la foto... 🧐"):
                imagen_pil = Image.open(foto)
                procesar_imagen_recibo(imagen_pil)

st.caption("Captura o edita los datos en la tabla:")
tabla_cfe = st.data_editor(st.session_state.datos_historial, num_rows="fixed", use_container_width=True)
consumo_total_cfe = tabla_cfe["Consumo (kWh)"].sum()

st.divider()

# --- PASO 2: INVENTARIO DETALLADO ---
st.header("2. Censo de Carga y Observaciones (Anexos 2 y 3)")
tab_refri, tab_climas, tab_luces, tab_otros, tab_inst = st.tabs(["🧊 Refrigeración", "❄️ Climatización", "💡 Iluminación", "💻 Otros", "🔌 Instalación"])

consumo_calculado_mensual = 0

with tab_refri:
    tipo_refri = st.selectbox("Tecnología", ["Convencional", "Inverter"])
    edad_refri = st.selectbox("Antigüedad", ["Menor a 3 años", "De 3 a 8 años", "Mayor a 8 años"])
    watts_refri = 300 if tipo_refri == "Inverter" else 450
    horas_refri = 7 if edad_refri == "Menor a 3 años" else (10 if edad_refri == "De 3 a 8 años" else 14)
    kwh_refri_mensual = (watts_refri * horas_refri * 30) / 1000
    consumo_calculado_mensual += kwh_refri_mensual

with tab_climas:
    num_climas = st.number_input("¿Cuántos equipos de AC tienes?", min_value=0, max_value=10, value=1)
    kwh_climas_mensual = 0
    for i in range(int(num_climas)):
        with st.expander(f"Equipo #{i+1}", expanded=True):
            colA, colB = st.columns(2)
            with colA:
                capacidad = st.selectbox("Capacidad", ["1 Ton (12,000 BTU)", "1.5 Ton (18,000 BTU)", "2 Ton (24,000 BTU)"], key=f"cap_{i}")
                btu = int(capacidad.split("(")[1].split()[0].replace(",", ""))
                horas_ac = st.slider("Horas de uso al día", 1, 24, 8, key=f"hrs_{i}")
            with colB:
                tecnologia_ac = st.selectbox("Tecnología", ["Convencional", "Inverter"], key=f"tec_{i}")
                seer = st.number_input("SEER/EER (Eficiencia)", value=(17.0 if tecnologia_ac == "Inverter" else 10.0), key=f"seer_{i}")
            watts_ac = btu / seer
            kwh_diario_ac = (watts_ac * horas_ac) / 1000
            kwh_climas_mensual += kwh_diario_ac * 15 
    consumo_calculado_mensual += kwh_climas_mensual

with tab_luces:
    zonas = ["Recámaras", "Sala/Comedor", "Cocina/Baños", "Exteriores"]
    kwh_luces_mensual = 0
    for zona in zonas:
        c1, c2, c3 = st.columns(3)
        with c1:
            focos = st.number_input(f"Focos en {zona}", 0, 20, 0)
        with c2:
            tipo_foco = st.selectbox("Tipo", ["LED (10W)", "Ahorrador (20W)", "Incandescente (60W)"], key=f"t_{zona}")
            watts_foco = int(tipo_foco.split("(")[1].replace("W)", ""))
        with c3:
            horas_foco = st.number_input("Horas al día", 0, 24, 0, key=f"h_{zona}")
        kwh_luces_mensual += (focos * watts_foco * horas_foco * 30) / 1000
    consumo_calculado_mensual += kwh_luces_mensual

with tab_otros:
    c1, c2 = st.columns(2)
    hrs_tv = c1.number_input("Horas TV al día", 0, 24, 4)
    hrs_pc = c1.number_input("Horas Computadora al día", 0, 24, 3)
    lavadoras = c2.number_input("Cargas lavadora a la semana", 0, 20, 3)
    kwh_otros = ((hrs_tv * 100 * 30) + (hrs_pc * 150 * 30) + (lavadoras * 4 * 500)) / 1000
    consumo_calculado_mensual += kwh_otros

with tab_inst:
    st.info("Estos datos técnicos ayudarán a la Inteligencia Artificial a detectar fugas o riesgos.")
    tipo_proteccion = st.selectbox("Tipo de protección principal", ["Pastillas termomagnéticas (Moderno)", "Fusibles de cartucho (Antiguo)", "Tapones (Muy antiguo)"])
    edad_cableado = st.selectbox("Antigüedad estimada del cableado", ["Menos de 10 años", "Entre 10 y 20 años", "Más de 20 años"])

st.divider()

# --- PASO 3: DIAGNÓSTICO IA ---
if st.button("Generar Autodiagnóstico con IA 🧠", type="primary"):
    consumo_anual_calculado = consumo_calculado_mensual * 12
    diferencia = consumo_total_cfe - consumo_anual_calculado
    
    st.header("📊 Resultados Matemáticos")
    colA, colB, colC = st.columns(3)
    colA.metric("Consumo Anual CFE", f"{consumo_total_cfe:.1f} kWh")
    colB.metric("Consumo Estimado (Censo)", f"{consumo_anual_calculado:.1f} kWh")
    colC.metric("Desviación", f"{diferencia:.1f} kWh")
    
    st.subheader("🤖 Análisis y Propuesta de IA Experta")
    with st.spinner("La IA está auditando tus datos comparando tu censo con tu recibo..."):
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            
            prompt = f"""
            Actúa como un ingeniero experto en auditoría energética residencial en México.
            Acabo de realizar un autodiagnóstico:
            - Consumo cobrado por CFE en el año: {consumo_total_cfe} kWh.
            - Consumo matemático estimado por mi censo de aparatos: {consumo_anual_calculado} kWh.
            - Desviación entre cobro y aparatos: {diferencia} kWh.
            
            Mis mayores consumos mensuales se dividen así: Climas ({kwh_climas_mensual} kWh), Refri ({kwh_refri_mensual} kWh), Luces ({kwh_luces_mensual} kWh).
            Además, mi instalación eléctrica tiene {tipo_proteccion} y el cableado tiene {edad_cableado}.
            
            Redacta tu auditoría en 3 viñetas claras (sin lenguaje excesivamente técnico). 
            1. Diagnóstico de la desviación (¿Es normal? ¿Indica consumos vampiro o fugas a tierra considerando mi tipo de instalación y cableado?).
            2. Área de mayor oportunidad (¿Dónde estoy gastando más?).
            3. Propuesta de ahorro (Acciones concretas para reducir los kWh).
            """
            
            respuesta_ia = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            st.info(respuesta_ia.text)
            
        except Exception as e:
            st.error(f"Error técnico exacto: {e}")

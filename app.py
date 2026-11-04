import streamlit as st
import pandas as pd
from google import genai
from PIL import Image
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Autodiagnóstico STEAM 2026", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PERSONALIZADOS (UI MODERNA Y LIMPIA) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .section-header {
        color: #1e293b;
        font-weight: 700;
        font-size: 1.25rem;
        margin-top: 10px;
        margin-bottom: 16px;
        border-left: 4px solid #2563eb;
        padding-left: 10px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- ENCABEZADO Y HEADER ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("https://www.utaltamira.edu.mx/wp-content/uploads/2017/06/LOGO-SIN-FONDO.png", width=280)

st.title("⚡ Autodiagnóstico Energético Residencial")
st.markdown("Plataforma de evaluación paramétrica para auditorías de eficiencia energética en el hogar.")
st.divider()

# --- PASO 1: DATOS CFE ---
st.markdown('<div class="section-header">1. Historial de Consumo CFE (Anexo 1)</div>', unsafe_allow_html=True)

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
            model='gemini-1.5-flash',
            contents=[imagen, instruccion]
        )
        
        texto_limpio = response.text.strip().replace('```json', '').replace('```', '')
        datos_extraidos = json.loads(texto_limpio)
        
        st.session_state.datos_historial = pd.DataFrame(datos_extraidos)
        st.success("¡Datos extraídos correctamente con Inteligencia Artificial!")
        st.rerun()
        
    except Exception as e:
        if "503" in str(e):
            st.warning("⏳ Los servidores de IA están ocupados por alta demanda. Por favor, espera unos segundos y vuelve a dar clic.")
        else:
            st.error(f"Error técnico exacto al procesar la imagen: {e}")

if metodo == "🖼️ Subir imagen":
    archivo = st.file_uploader("Selecciona la foto de tu recibo", type=["png", "jpg", "jpeg"])
    if archivo:
        if st.button("Leer datos con IA 🔍"):
            with st.spinner("Analizando la tabla del recibo... 🧐"):
                procesar_imagen_recibo(Image.open(archivo))

elif metodo == "📸 Tomar foto":
    foto = st.camera_input("Enfoca la tabla de historial")
    if foto:
        if st.button("Leer datos con IA 🔍"):
            with st.spinner("Analizando la foto... 🧐"):
                procesar_imagen_recibo(Image.open(foto))

st.caption("Captura o edita los datos en la tabla:")
tabla_cfe = st.data_editor(
    st.session_state.datos_historial, 
    num_rows="fixed", 
    use_container_width=True,
    hide_index=True
)
consumo_total_cfe = tabla_cfe["Consumo (kWh)"].sum()

st.caption(f"**Consumo Anual Facturado Total:** {consumo_total_cfe:,.0f} kWh")
st.divider()

# --- PASO 2: INVENTARIO DETALLADO ---
st.markdown('<div class="section-header">2. Censo de Carga y Observaciones (Anexos 2 y 3)</div>', unsafe_allow_html=True)

tab_refri, tab_climas, tab_luces, tab_otros, tab_inst = st.tabs([
    "🧊 Refrigeración", 
    "❄️ Climatización", 
    "💡 Iluminación", 
    "💻 Otros Equipos", 
    "🔌 Instalación Eléctrica"
])

consumo_calculado_mensual = 0
lista_refris_ia = []
lista_climas_ia = []
lista_focos_ia = []

# --- TAB REFRIGERACIÓN ---
with tab_refri:
    st.markdown("##### Configuración de Refrigeradores")
    num_refris = st.number_input("¿Cuántos refrigeradores o congeladores tienes?", min_value=1, max_value=5, value=1)
    kwh_refri_mensual_total = 0
    
    for i in range(int(num_refris)):
        with st.expander(f"Refrigerador / Congelador #{i+1}", expanded=True):
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                tipo_entrada = st.radio("¿Cómo ingresarás la información de consumo?", ["Especificar Potencia (Watts)", "Consumo Anual de Etiqueta (kWh/año)"], key=f"tipo_in_{i}")
                tipo_refri = st.selectbox("Tecnología del motor", ["Convencional", "Inverter"], key=f"tec_ref_{i}")
                edad_refri = st.selectbox("Antigüedad estimada", ["Menor a 3 años", "De 3 a 8 años", "Mayor a 8 años"], key=f"edad_ref_{i}")

            with col_r2:
                if tipo_entrada == "Especificar Potencia (Watts)":
                    potencia_def = 300 if tipo_refri == "Inverter" else 450
                    potencia_w = st.number_input("Potencia nominal (Watts)", min_value=50, max_value=2000, value=potencia_def, step=10, key=f"watts_ref_{i}")
                    horas_uso = 7 if edad_refri == "Menor a 3 años" else (10 if edad_refri == "De 3 a 8 años" else 14)
                    kwh_diario = (potencia_w * horas_uso) / 1000
                    kwh_mensual = kwh_diario * 30
                else: 
                    kwh_anual_etiq = st.number_input("Consumo anual impreso en la etiqueta CFE/NOM (kWh/año)", min_value=100, max_value=2000, value=450, step=10, key=f"kwh_anual_{i}")
                    kwh_diario = kwh_anual_etiq / 365
                    kwh_mensual = kwh_anual_etiq / 12
                    
                st.metric("Consumo diario estimado", f"{kwh_diario:.2f} kWh/día")
                st.metric("Consumo mensual estimado", f"{kwh_mensual:.1f} kWh/mes")
                kwh_refri_mensual_total += kwh_mensual
                
            lista_refris_ia.append(f"Tecnología: {tipo_refri}, Edad: {edad_refri}")

    consumo_calculado_mensual += kwh_refri_mensual_total

# --- TAB CLIMATIZACIÓN ---
with tab_climas:
    st.markdown("##### Aire Acondicionado")
    num_climas = st.number_input("¿Cuántos equipos de AC tienes?", min_value=0, max_value=10, value=1)
    kwh_climas_mensual = 0
    
    for i in range(int(num_climas)):
        with st.expander(f"Equipo #{i+1}", expanded=True):
            colA, colB = st.columns(2)
            with colA:
                capacidad = st.selectbox("Capacidad", ["1 Ton (12,000 BTU)", "1.5 Ton (18,000 BTU)", "2 Ton (24,000 BTU)"], key=f"cap_{i}")
                btu = int(capacidad.split("(")[1].split()[0].replace(",", ""))
                horas_ac = st.number_input("Horas de uso al día", min_value=0.0, max_value=24.0, value=8.0, step=0.5, key=f"hrs_ac_{i}")
            with colB:
                tecnologia_ac = st.selectbox("Tecnología", ["Convencional", "Inverter"], key=f"tec_{i}")
                edad_ac = st.selectbox("Antigüedad", ["Menos de 2 años", "Más de 2 años"], key=f"edad_ac_{i}")
                seer = st.number_input("SEER/EER (Eficiencia)", value=(17.0 if tecnologia_ac == "Inverter" else 10.0), key=f"seer_{i}")
            
            watts_ac = btu / seer
            kwh_diario_ac = (watts_ac * horas_ac) / 1000
            kwh_climas_mensual += kwh_diario_ac * 15 
            
            lista_climas_ia.append(f"Tecnología: {tecnologia_ac}, Edad: {edad_ac}")
            
    consumo_calculado_mensual += kwh_climas_mensual

# --- TAB ILUMINACIÓN ---
with tab_luces:
    st.markdown("##### Iluminación por Espacios")
    num_zonas = st.number_input("¿Cuántas habitaciones o zonas vas a registrar?", min_value=1, max_value=15, value=3)
    kwh_luces_mensual = 0
    
    for i in range(int(num_zonas)):
        with st.expander(f"Zona / Habitación #{i+1}", expanded=(i==0)):
            nombre_zona = st.text_input("Nombre del espacio (ej. Sala, Recámara Principal)", value=f"Habitación {i+1}", key=f"nombre_z_{i}")
            
            st.markdown("**💡 Dispositivos de Iluminación**")
            num_tipos_luz = st.number_input("¿Cuántos tipos distintos de dispositivos (focos, ventiladores) hay aquí?", min_value=1, max_value=5, value=1, key=f"num_tipos_{i}")
            
            consumo_focos_zona = 0
            for j in range(int(num_tipos_luz)):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    focos = st.number_input("Cantidad", min_value=1, max_value=30, value=1, key=f"focos_{i}_{j}")
                with c2:
                    tipo_foco = st.selectbox(
                        "Tipo", 
                        ["LED", "Ahorrador (LFC)", "Dicroico / Halógeno", "Incandescente", "Tubo Fluorescente", "Ventilador de Techo (con focos)", "Otro"], 
                        key=f"t_foco_{i}_{j}"
                    )
                with c3:
                    def_w = 9 if tipo_foco == "LED" else 23 if tipo_foco == "Ahorrador (LFC)" else 50 if tipo_foco == "Dicroico / Halógeno" else 60 if tipo_foco == "Incandescente" else 32 if tipo_foco == "Tubo Fluorescente" else 100 if tipo_foco == "Ventilador de Techo (con focos)" else 15
                    watts_foco = st.number_input("Watts totales (c/u)", min_value=1, max_value=500, value=def_w, key=f"w_foco_{i}_{j}")
                with c4:
                    horas_foco = st.number_input("Horas/día", min_value=0.0, max_value=24.0, value=4.0, step=0.5, key=f"h_foco_{i}_{j}")
                    
                consumo_focos_zona += (focos * watts_foco * horas_foco * 30) / 1000
                lista_focos_ia.append(tipo_foco)

            st.caption(f"Consumo total estimado en **{nombre_zona}**: **{consumo_focos_zona:.2f} kWh/mes**")
            kwh_luces_mensual += consumo_focos_zona
        
    consumo_calculado_mensual += kwh_luces_mensual

# --- TAB OTROS ---
with tab_otros:
    st.markdown("##### Electrodomésticos Secundarios y Otras Cargas")
    num_otros = st.number_input("¿Cuántos tipos distintos de aparatos vas a registrar?", min_value=1, max_value=20, value=3)
    kwh_otros = 0
    
    for i in range(int(num_otros)):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            cant = st.number_input("Cantidad", min_value=1, max_value=20, value=1, key=f"cant_o_{i}")
        with c2:
            tipo_eq = st.selectbox(
                "Tipo de aparato",
                ["Televisión", "Computadora / Laptop", "Consola de Videojuegos", "Estéreo / Bocinas", "Lavadora", "Secadora de Ropa", "Plancha", "Microondas", "Refrigerador de agua (Dispensador)", "Celular / Tablet", "Otro"],
                key=f"tipo_o_{i}"
            )
        with c3:
            if tipo_eq == "Televisión": def_w = 100
            elif tipo_eq == "Computadora / Laptop": def_w = 150
            elif tipo_eq == "Consola de Videojuegos": def_w = 200
            elif tipo_eq == "Estéreo / Bocinas": def_w = 80
            elif tipo_eq == "Lavadora": def_w = 500
            elif tipo_eq == "Secadora de Ropa": def_w = 3000
            elif tipo_eq == "Plancha": def_w = 1200
            elif tipo_eq == "Microondas": def_w = 1000
            elif tipo_eq == "Refrigerador de agua (Dispensador)": def_w = 150
            elif tipo_eq == "Celular / Tablet": def_w = 15
            else: def_w = 100
            
            watts_eq = st.number_input("Watts (c/u)", min_value=1, max_value=10000, value=def_w, key=f"w_o_{i}")
        with c4:
            hrs_sem = st.number_input("Horas de uso A LA SEMANA", min_value=0.0, max_value=168.0, value=10.0, step=0.5, key=f"h_o_{i}")
            
        consumo_eq_mensual = (cant * watts_eq * (hrs_sem / 7) * 30) / 1000
        kwh_otros += consumo_eq_mensual
        
    consumo_calculado_mensual += kwh_otros
    st.caption(f"**Consumo total estimado en Otros Equipos:** {kwh_otros:.2f} kWh/mes")

# --- TAB INSTALACIÓN ---
with tab_inst:
    st.info("Estos datos técnicos ayudarán a la Inteligencia Artificial a detectar fugas, riesgos y problemas de seguridad eléctrica.")
    
    col_i1, col_i2 = st.columns(2)
    
    with col_i1:
        edad_cableado = st.selectbox("Antigüedad estimada del cableado", ["Menos de 10 años", "Entre 10 y 20 años", "Más de 20 años"])
        interruptor_principal = st.selectbox("Interruptor Principal (junto al medidor)", ["Pastilla (Termomagnético)", "Fusibles (Cartucho)", "Tapones (Muy antiguo)", "No estoy seguro"])
        sistema_tierra = st.radio("¿Cuenta con sistema de tierra física (tercer cable/varilla)?", ["Sí", "No", "No estoy seguro"], horizontal=True)
        
    with col_i2:
        centro_carga = st.radio("¿Cuenta con Centro de Carga al interior de la casa?", ["Sí", "No"], horizontal=True)
        if centro_carga == "Sí":
            num_circuitos = st.number_input("¿Cuántos circuitos derivados (pastillas) tiene?", min_value=1, max_value=30, value=2)
        else:
            num_circuitos = 0
            
    st.markdown("##### ⚠️ Historial de Problemas")
    problemas_recientes = st.radio("¿Ha tenido problemas eléctricos recientemente (cortos circuitos, parpadeos, olor a quemado, se botan las pastillas)?", ["No", "Sí"], horizontal=True)
    
    desc_falla = ""
    if problemas_recientes == "Sí":
        desc_falla = st.text_area("Describa brevemente la falla o problema que ha notado:")

st.divider()

# --- PASO 3: DIAGNÓSTICO IA Y RESULTADOS ---
st.markdown('<div class="section-header">3. Resultados y Auditoría Energética</div>', unsafe_allow_html=True)

# 1. CÁLCULOS MATEMÁTICOS EN TIEMPO REAL
consumo_anual_calculado = consumo_calculado_mensual * 12
diferencia = consumo_total_cfe - consumo_anual_calculado

promedio_diario_cfe = consumo_total_cfe / 365 if consumo_total_cfe > 0 else 0
promedio_diario_calculado = consumo_anual_calculado / 365 if consumo_anual_calculado > 0 else 0

if promedio_diario_calculado > 0:
    grado_certeza = (promedio_diario_cfe / promedio_diario_calculado) * 100
else:
    grado_certeza = 0.0

if consumo_calculado_mensual > 0:
    pct_refri = (kwh_refri_mensual_total / consumo_calculado_mensual) * 100
    pct_climas = (kwh_climas_mensual / consumo_calculado_mensual) * 100
    pct_luces = (kwh_luces_mensual / consumo_calculado_mensual) * 100
    pct_otros = (kwh_otros / consumo_calculado_mensual) * 100
else:
    pct_refri = pct_climas = pct_luces = pct_otros = 0.0

# --- RENDERIZADO DE MÉTRICAS VISUALES ---
st.subheader("📊 Resultados")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Promedio Diario CFE", f"{promedio_diario_cfe:,.2f} kWh/día")
col2.metric("Promedio Diario Calculado", f"{promedio_diario_calculado:,.2f} kWh/día")
col3.metric("Desviación Anual", f"{diferencia:,.1f} kWh", delta=f"{diferencia:,.1f} kWh", delta_color="inverse")

certeza_color = "normal" if 80 <= grado_certeza <= 120 else "inverse"
col4.metric("Grado de Certeza", f"{grado_certeza:,.1f}%", help="Un valor alto indica posibles fugas. Un valor bajo indica aparatos sobreestimados.")

st.markdown("##### 🥧 Distribución del Consumo Calculado")
cC1, cC2, cC3, cC4 = st.columns(4)
cC1.metric("🧊 Refrigeración", f"{pct_refri:.1f}%")
cC2.metric("❄️ Climatización", f"{pct_climas:.1f}%")
cC3.metric("💡 Iluminación", f"{pct_luces:.1f}%")
cC4.metric("💻 Otros Equipos", f"{pct_otros:.1f}%")

st.divider()

# --- PREPARACIÓN DEL PROMPT ---
# Pasamos las listas creadas arriba para que la IA sepa exactamente qué hay y aplique las reglas.
info_refris_str = ", ".join(lista_refris_ia) if lista_refris_ia else "Ninguno"
info_climas_str = ", ".join(lista_climas_ia) if lista_climas_ia else "Ninguno"
info_focos_str = ", ".join(list(set(lista_focos_ia))) if lista_focos_ia else "Ninguno"

prompt_ia = f"""Actúa como un ingeniero experto en auditoría energética residencial en México.
Acabo de realizar un autodiagnóstico:
- Consumo cobrado por CFE en el año: {consumo_total_cfe:,.0f} kWh (Promedio diario: {promedio_diario_cfe:.2f} kWh/día).
- Consumo matemático estimado por mi censo de aparatos: {consumo_anual_calculado:,.0f} kWh (Promedio diario: {promedio_diario_calculado:.2f} kWh/día).
- Grado de certeza (CFE/Censo): {grado_certeza:.1f}%.
- Desviación entre cobro y aparatos: {diferencia:,.0f} kWh anuales.

Mi distribución de consumo según los aparatos es: Refrigeración ({pct_refri:.1f}%), Climatización ({pct_climas:.1f}%), Iluminación ({pct_luces:.1f}%), y Otros ({pct_otros:.1f}%).

Detalle de mis equipos para aplicar reglas de eficiencia:
- Refrigeradores en casa: {info_refris_str}
- Climatización en casa: {info_climas_str}
- Tipos de focos utilizados: {info_focos_str}

Datos de la instalación eléctrica y seguridad:
- Antigüedad del cableado: {edad_cableado}.
- Tipo de interruptor principal: {interruptor_principal}.
- Cuenta con centro de carga interno: {centro_carga} (Número de circuitos/pastillas: {num_circuitos}).
- Cuenta con sistema de tierra física: {sistema_tierra}.
- ¿Ha tenido fallas recientes?: {problemas_recientes}. {f'Descripción de la falla: {desc_falla}' if problemas_recientes == 'Sí' else ''}

Redacta tu auditoría en 3 viñetas claras (sin lenguaje excesivamente técnico). 
1. Diagnóstico de Certeza y Seguridad (Analiza el Grado de Certeza de {grado_certeza:.1f}%. Si es muy alto o bajo, di qué significa. ¿El estado del cableado y las fallas descritas indican fugas a tierra, riesgos de incendio o consumos vampiro severos justificando esa desviación?).
2. Área de mayor oportunidad (¿Dónde estoy gastando más energía basándose en mis porcentajes?).
3. Propuesta de ahorro y remediación (Acciones concretas para reducir los kWh en la categoría más alta y recomendaciones urgentes de mantenimiento eléctrico según los datos proporcionados. Además, incluye obligatoriamente las siguientes recomendaciones preventivas evaluando mis equipos actuales:
   - Sugiere el cambio de aire acondicionado por tecnología Inverter si actualmente es convencional (estándar) y tiene más de 2 años de antigüedad.
   - Sugiere el cambio de refrigerador si la tecnología actual tiene más de 7 años de antigüedad (Marcado como Mayor a 8 años).
   - Recomienda la sustitución inmediata de lámparas LFC (ahorradoras), dicroicos, halógenos o cualquier tecnología que no sea LED por focos LED de alta eficiencia si detectas que los estoy usando).
"""

# --- BOTÓN PARA LLAMAR A LA IA ---
st.subheader("🤖 Análisis y Propuesta de IA Experta")
if st.button("Generar Autodiagnóstico con IA 🧠", type="primary", use_container_width=True):
    with st.spinner("La IA está auditando tus datos, analizando la certeza matemática, los riesgos y tu recibo..."):
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            
            respuesta_ia = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt_ia
            )
            st.info(respuesta_ia.text)
            
        except Exception as e:
            if "503" in str(e):
                st.warning("⏳ Los servidores de IA están ocupados por alta demanda. Por favor, espera unos segundos y vuelve a dar clic.")
            else:
                st.error(f"Error técnico al conectar con IA: {e}")

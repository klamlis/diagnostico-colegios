import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime
import glob

st.set_page_config(
    page_title="Diagnóstico Centros Educativos",
    page_icon="🏫",
    layout="wide"
)

# ── Estilos ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { min-width: 320px; }
.metric-box { background:#f8f9fa; border-radius:10px; padding:16px 20px; text-align:center; border:1px solid #e0e0e0; }
.metric-label { font-size:13px; color:#666; margin-bottom:4px; }
.metric-val { font-size:30px; font-weight:700; }
.blue { color:#185FA5; } .green { color:#2d6a1f; } .amber { color:#7a4f00; } .red { color:#8b1a1a; }
.badge-c { background:#d4edda; color:#155724; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
.badge-i { background:#fff3cd; color:#856404; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
.badge-n { background:#f8d7da; color:#721c24; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
.update-box { background:#e8f4fd; border-left:4px solid #185FA5; padding:10px 16px; border-radius:6px; margin-bottom:20px; font-size:13px; }
table { width:100%; }
</style>
""", unsafe_allow_html=True)

# ── Configuración de instrumentos ─────────────────────────────────────────────
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

INSTRUMENTS = {
    "Ficha CE":             ("Código SIACE del colegio",                                          True),
    "Entrevista":           ("Código SIACE del colegio",                                          False),
    "Clima Capacitación":   ("Preguntas de localización/Selecciona el código del colegio",        False),
    "Clima Docentes":       ("Selecciona el código del colegio",                                  False),
    "Clima Estudiantes":    ("Selecciona el código del colegio",                                  False),
    "Clima Líderes":        ("Selecciona el código del colegio",                                  False),
    "Línea Base Comunidad": ("Selecciona el código del colegio",                                  False),
    "Línea Base Directivo": ("Selecciona el código del colegio",                                  False),
    "Línea Base Docente":   ("Selecciona el código del colegio",                                  False),
    "Lista Chequeo":        ("Selecciona el código del colegio",                                  False),
}

FILE_KEYS = {
    "pulldata":              "PullData.csv",
    "Ficha CE":              "Ficha_CE.csv",
    "Entrevista":            "Entrevista.csv",
    "Clima Capacitación":    "Clima_Capacitacion.csv",
    "Clima Docentes":        "Clima_Docentes.csv",
    "Clima Estudiantes":     "Clima_Estudiantes.csv",
    "Clima Líderes":         "Clima_Lideres.csv",
    "Línea Base Comunidad":  "Linea_Base_Comunidad.csv",
    "Línea Base Directivo":  "Linea_Base_Directivo.csv",
    "Línea Base Docente":    "Linea_Base_Docente.csv",
    "Lista Chequeo":         "Lista_Chequeo.csv",
}

UPLOAD_LABELS = {
    "pulldata":              "📋 PullData (lista de colegios)",
    "Ficha CE":              "1. Ficha de información CE",
    "Entrevista":            "2. Entrevista semiestructurada",
    "Clima Capacitación":    "3. Clima escolar – Capacitación",
    "Clima Docentes":        "4. Clima escolar – Docentes",
    "Clima Estudiantes":     "5. Clima escolar – Estudiantes",
    "Clima Líderes":         "6. Clima escolar – Líderes",
    "Línea Base Comunidad":  "7. Línea base – Comunidad",
    "Línea Base Directivo":  "8. Línea base – Directivo",
    "Línea Base Docente":    "9. Línea base – Docente",
    "Lista Chequeo":         "10. Lista de chequeo físico",
}

META_FILE = os.path.join(DATA_DIR, "ultima_actualizacion.txt")

# ── Helpers ────────────────────────────────────────────────────────────────────
def save_upload_time():
    now = datetime.now().strftime("%d/%m/%Y a las %H:%M")
    with open(META_FILE, "w") as f:
        f.write(now)

def get_last_update():
    if os.path.exists(META_FILE):
        with open(META_FILE) as f:
            return f.read().strip()
    return None

def read_csv_robust(path_or_bytes):
    for sep in [';', ',', '\t']:
        try:
            if isinstance(path_or_bytes, (str, os.PathLike)):
                df = pd.read_csv(path_or_bytes, sep=sep, encoding='utf-8', on_bad_lines='skip')
            else:
                path_or_bytes.seek(0)
                df = pd.read_csv(path_or_bytes, sep=sep, encoding='utf-8', on_bad_lines='skip')
            if len(df.columns) >= 3:
                return df
        except Exception:
            continue
    return None

def safe_to_int(val):
    try:
        return str(int(float(val)))
    except Exception:
        return None

def files_on_disk():
    return {k: os.path.exists(os.path.join(DATA_DIR, v)) for k, v in FILE_KEYS.items()}

def count_files_on_disk():
    status = files_on_disk()
    return sum(1 for k, v in status.items() if v and k != "pulldata")

# ── Sidebar: carga de archivos ─────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.svg/1200px-Camponotus_flavomarginatus_ant.svg.png", width=0)
    st.title("📂 Actualizar archivos")
    st.markdown("Sube los CSV exportados desde KoboToolbox. Los archivos se guardan y el reporte se actualiza automáticamente.")

    uploaded_files = {}
    all_keys = ["pulldata"] + list(INSTRUMENTS.keys())
    for key in all_keys:
        label = UPLOAD_LABELS[key]
        exists = os.path.exists(os.path.join(DATA_DIR, FILE_KEYS[key]))
        indicator = "✅" if exists else "⬜"
        uploaded_files[key] = st.file_uploader(
            f"{indicator} {label}",
            type="csv",
            key=f"upload_{key}"
        )

    if st.button("💾 Guardar y actualizar reporte", type="primary", use_container_width=True):
        saved = []
        for key, file in uploaded_files.items():
            if file is not None:
                dest = os.path.join(DATA_DIR, FILE_KEYS[key])
                with open(dest, "wb") as f:
                    f.write(file.getvalue())
                saved.append(UPLOAD_LABELS[key])
        if saved:
            save_upload_time()
            st.success(f"✅ {len(saved)} archivo(s) guardados.")
            st.rerun()
        else:
            st.warning("No seleccionaste ningún archivo nuevo.")

    st.markdown("---")
    on_disk = files_on_disk()
    loaded_count = sum(1 for k, v in on_disk.items() if v and k != "pulldata")
    st.markdown(f"**Instrumentos disponibles: {loaded_count}/10**")
    st.progress(loaded_count / 10)
    for key in list(INSTRUMENTS.keys()):
        icon = "✅" if on_disk.get(key) else "❌"
        st.markdown(f"{icon} {UPLOAD_LABELS[key]}")

# ── Verificar que haya datos ───────────────────────────────────────────────────
pulldata_path = os.path.join(DATA_DIR, FILE_KEYS["pulldata"])
if not os.path.exists(pulldata_path):
    st.title("🏫 Diagnóstico de Centros Educativos")
    st.info("👈 Para comenzar, sube el archivo **PullData.csv** y los instrumentos en el panel izquierdo, luego haz clic en **Guardar y actualizar reporte**.")
    st.stop()

# ── Cargar PullData ────────────────────────────────────────────────────────────
pulldata = read_csv_robust(pulldata_path)
if pulldata is None or 'codigo' not in pulldata.columns:
    st.error("No se pudo leer el PullData. Verifica que sea el archivo correcto.")
    st.stop()

pulldata['codigo'] = pulldata['codigo'].astype(str)
name_to_code = {row['nombre'].strip().upper(): str(row['codigo']) for _, row in pulldata.iterrows()}

# ── Procesar instrumentos ──────────────────────────────────────────────────────
instrument_data = {}
for instr_name, (code_col, use_name_map) in INSTRUMENTS.items():
    path = os.path.join(DATA_DIR, FILE_KEYS[instr_name])
    if not os.path.exists(path):
        instrument_data[instr_name] = {}
        continue
    df = read_csv_robust(path)
    if df is None or code_col not in df.columns:
        instrument_data[instr_name] = {}
        continue
    if use_name_map:
        df['_code'] = df[code_col].astype(str).str.strip().str.upper().map(name_to_code)
    else:
        df['_code'] = df[code_col].apply(safe_to_int)
    result = {}
    for code, grp in df.dropna(subset=['_code']).groupby('_code'):
        if str(code) in pulldata['codigo'].values:
            fecha = None
            if '_submission_time' in df.columns:
                dates = grp['_submission_time'].dropna()
                if len(dates):
                    try:
                        fecha = sorted(dates.tolist())[-1][:10]
                    except Exception:
                        pass
            result[str(code)] = {'count': len(grp), 'fecha': fecha}
    instrument_data[instr_name] = result

# Director info from Entrevista
ent_path = os.path.join(DATA_DIR, FILE_KEYS["Entrevista"])
ent_info = {}
if os.path.exists(ent_path):
    ent_df = read_csv_robust(ent_path)
    if ent_df is not None and 'Código SIACE del colegio' in ent_df.columns:
        ent_df['_code'] = ent_df['Código SIACE del colegio'].apply(safe_to_int)
        for code, grp in ent_df.dropna(subset=['_code']).groupby('_code'):
            if str(code) in pulldata['codigo'].values:
                grp_s = grp.sort_values('_submission_time', ascending=False) if '_submission_time' in grp.columns else grp
                row = grp_s.iloc[0]
                def cl(v):
                    s = str(v) if pd.notna(v) else ''
                    return '' if s in ['nan', 'NaN', 'None'] else s
                tel = cl(row.get('Número de teléfono del entrevistado/a:', ''))
                if tel.endswith('.0'):
                    tel = tel[:-2]
                ent_info[str(code)] = {
                    'director': cl(row.get('Nombre de la persona que entrega la información - Director(a):', '')),
                    'contacto': tel,
                    'correo':   cl(row.get('Correo electrónico del entrevistado/a:', '')),
                }

# ── Construir tabla de resultados ──────────────────────────────────────────────
instr_names = list(INSTRUMENTS.keys())
rows = []
for _, school in pulldata.iterrows():
    code = str(school['codigo'])
    ei = ent_info.get(code, {})

    instr_status = {}
    missing = []
    fecha_diag = None

    for iname in instr_names:
        data = instrument_data[iname].get(code)
        if data:
            instr_status[iname] = data['count']
            if data['fecha'] and (fecha_diag is None or data['fecha'] > fecha_diag):
                fecha_diag = data['fecha']
        else:
            instr_status[iname] = 0
            missing.append(iname)

    total_done = sum(1 for i in instr_names if instr_status[i] > 0)
    if total_done == len(instr_names):
        estado = 'Diagnóstico completo'
    elif total_done == 0:
        estado = 'Sin realizar'
    else:
        estado = 'Diagnóstico incompleto'

    row = {
        'SIACE':                  code,
        'Nombre CE':              school['nombre'],
        'Regional/Provincia':     school['provincia'],
        'Director/a':             ei.get('director', ''),
        'Teléfono':               ei.get('contacto', ''),
        'Correo':                 ei.get('correo', ''),
        'Fecha último registro':  fecha_diag or '',
        'Estado':                 estado,
        'Completados':            total_done,
        'Falta':                  '; '.join(missing) if missing else '',
    }
    for iname in instr_names:
        row[iname] = instr_status[iname]
    rows.append(row)

df_result = pd.DataFrame(rows)

# ── Header + última actualización ─────────────────────────────────────────────
st.title("🏫 Diagnóstico de Centros Educativos")

last_update = get_last_update()
if last_update:
    st.markdown(f'<div class="update-box">🕐 <strong>Última actualización:</strong> {last_update} &nbsp;|&nbsp; <strong>{count_files_on_disk()}/10</strong> instrumentos cargados</div>', unsafe_allow_html=True)

# ── Métricas ───────────────────────────────────────────────────────────────────
total   = len(df_result)
comp    = (df_result['Estado'] == 'Diagnóstico completo').sum()
inc     = (df_result['Estado'] == 'Diagnóstico incompleto').sum()
sin     = (df_result['Estado'] == 'Sin realizar').sum()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Total CEs</div><div class="metric-val blue">{total}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Diagnóstico completo</div><div class="metric-val green">{comp}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Diagnóstico incompleto</div><div class="metric-val amber">{inc}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Sin realizar</div><div class="metric-val red">{sin}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Filtros ────────────────────────────────────────────────────────────────────
f1, f2, f3 = st.columns([2, 2, 3])
with f1:
    provincias = ["Todas"] + sorted(df_result['Regional/Provincia'].unique().tolist())
    prov_sel = st.selectbox("Provincia", provincias)
with f2:
    estado_sel = st.selectbox("Estado diagnóstico", ["Todos", "Diagnóstico completo", "Diagnóstico incompleto", "Sin realizar"])
with f3:
    buscar = st.text_input("Buscar por nombre o SIACE", placeholder="Ej: ESC. DEBORAH o 314")

df_view = df_result.copy()
if prov_sel != "Todas":
    df_view = df_view[df_view['Regional/Provincia'] == prov_sel]
if estado_sel != "Todos":
    df_view = df_view[df_view['Estado'] == estado_sel]
if buscar:
    q = buscar.strip().lower()
    df_view = df_view[
        df_view['Nombre CE'].str.lower().str.contains(q, na=False) |
        df_view['SIACE'].str.contains(q, na=False)
    ]

st.markdown(f"**{len(df_view)} centros educativos** encontrados")

# ── Tabla ──────────────────────────────────────────────────────────────────────
def badge_html(estado):
    if estado == 'Diagnóstico completo':
        return '✅ Completo'
    elif estado == 'Sin realizar':
        return '❌ Sin realizar'
    return '⚠️ Incompleto'

def progress_str(done):
    filled = '🟢' * done + '⚪' * (10 - done)
    return f"{filled} {done}/10"

display_df = df_view[[
    'SIACE', 'Nombre CE', 'Regional/Provincia',
    'Director/a', 'Teléfono', 'Fecha último registro',
    'Estado', 'Completados', 'Falta'
]].copy()

display_df['Estado'] = display_df['Estado'].apply(badge_html)
display_df['Avance'] = display_df['Completados'].apply(progress_str)
display_df = display_df.drop(columns=['Completados'])

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=520,
    column_config={
        'SIACE':                    st.column_config.TextColumn("SIACE", width=70),
        'Nombre CE':                st.column_config.TextColumn("Centro Educativo", width=220),
        'Regional/Provincia':       st.column_config.TextColumn("Provincia", width=120),
        'Director/a':               st.column_config.TextColumn("Director/a", width=150),
        'Teléfono':                 st.column_config.TextColumn("Teléfono", width=100),
        'Fecha último registro':    st.column_config.TextColumn("Último reg.", width=100),
        'Estado':                   st.column_config.TextColumn("Estado", width=130),
        'Avance':                   st.column_config.TextColumn("Avance", width=180),
        'Falta':                    st.column_config.TextColumn("Falta completar", width=300),
    }
)

# ── Descarga CSV ───────────────────────────────────────────────────────────────
st.markdown("---")
csv_bytes = df_result.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
st.download_button(
    label="⬇️ Descargar reporte completo (CSV)",
    data=csv_bytes,
    file_name=f"reporte_diagnostico_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
    use_container_width=False,
)

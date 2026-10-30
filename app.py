import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import os

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS (CSS)
# ==========================================
st.set_page_config(
    page_title="CETPRO La Arena - Inventario",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .header-container {
        background-color: #006633; /* Verde Institucional */
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }
    .header-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin: 0;
        color: #FFFFFF;
    }
    .header-subtitle {
        font-size: 1.1rem;
        margin-top: 5px;
        font-weight: 400;
        color: #E0E0E0;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BASE DE DATOS LOCAL (SQLite) Y CONFIGURACIÓN
# ==========================================
DB_NAME = "inventario.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabla de inventario
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            codigo TEXT UNIQUE NOT NULL,
            equipo TEXT NOT NULL,
            marca TEXT,
            modelo TEXT,
            serie TEXT,
            estado TEXT,
            ubicacion TEXT,
            responsable TEXT,
            fecha TEXT,
            observaciones TEXT
        )
    ''')
    # Tabla de configuración para la contraseña del admin
    c.execute('''
        CREATE TABLE IF NOT EXISTS config (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )
    ''')
    # Contraseña por defecto si no existe
    c.execute("SELECT valor FROM config WHERE clave = 'password_admin'")
    if not c.fetchone():
        c.execute("INSERT INTO config (clave, valor) VALUES ('password_admin', 'cetpro2026')")
    
    conn.commit()
    conn.close()

init_db()

def obtener_password_admin():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT valor FROM config WHERE clave = 'password_admin'")
    row = c.fetchone()
    conn.close()
    return row[0] if row else "cetpro2026"

def actualizar_password_admin(nueva_pass):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE config SET valor = ? WHERE clave = 'password_admin'", (nueva_pass,))
    conn.commit()
    conn.close()

def guardar_item(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO inventario (categoria, codigo, equipo, marca, modelo, serie, estado, ubicacion, responsable, fecha, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        conn.close()
        return True, "Registro guardado correctamente."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Error: El código ingresado ya existe en la base de datos."

def actualizar_item(item_id, data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        UPDATE inventario 
        SET categoria=?, codigo=?, equipo=?, marca=?, modelo=?, serie=?, estado=?, ubicacion=?, responsable=?, fecha=?, observaciones=?
        WHERE id=?
    ''', (*data, item_id))
    conn.commit()
    conn.close()

def obtener_datos(categoria=None):
    conn = sqlite3.connect(DB_NAME)
    if categoria and categoria != "Todos":
        query = f"SELECT * FROM inventario WHERE categoria = '{categoria}'"
    else:
        query = "SELECT * FROM inventario"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def obtener_registro_por_id(item_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM inventario WHERE id = ?", (item_id,))
    row = c.fetchone()
    conn.close()
    return row

def eliminar_registro(item_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM inventario WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

# ==========================================
# 3. CONTROL DE ACCESO Y CAMBIO DE CONTRASEÑA
# ==========================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

def login():
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔒 Control de Acceso")
    
    password_actual_db = obtener_password_admin()

    if not st.session_state['autenticado']:
        pwd = st.sidebar.text_input("Contraseña de Administrador", type="password")
        if st.sidebar.button("Ingresar"):
            if pwd == password_actual_db:
                st.session_state['autenticado'] = True
                st.sidebar.success("Acceso concedido")
                st.rerun()
            else:
                st.sidebar.error("Contraseña incorrecta")
    else:
        st.sidebar.info("Modo Administrador Activo")
        
        # Opción para cambiar la contraseña dentro del panel de admin
        with st.sidebar.expander("🔑 Cambiar Contraseña"):
            with st.form("form_cambiar_pass"):
                pass_antigua = st.text_input("Contraseña Actual", type="password")
                pass_nueva = st.text_input("Nueva Contraseña", type="password")
                pass_repetir = st.text_input("Confirmar Nueva Contraseña", type="password")
                btn_cambiar = st.form_submit_button("Actualizar Clave")
                
                if btn_cambiar:
                    if pass_antigua != password_actual_db:
                        st.error("La contraseña actual es incorrecta.")
                    elif not pass_nueva:
                        st.error("La nueva contraseña no puede estar vacía.")
                    elif pass_nueva != pass_repetir:
                        st.error("Las nuevas contraseñas no coinciden.")
                    else:
                        actualizar_password_admin(pass_nueva)
                        st.success("¡Contraseña actualizada con éxito!")
                        st.rerun()

        if st.sidebar.button("Cerrar Sesión"):
            st.session_state['autenticado'] = False
            st.rerun()

# ==========================================
# 4. ENCABEZADO CON LOGO Y VERDE INSTITUCIONAL
# ==========================================
if os.path.exists("logo.png"):
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.image("logo.png", width=120)
    with col_titulo:
        st.markdown("""
            <div class="header-container">
                <h1 class="header-title">CETPRO La Arena</h1>
                <div class="header-subtitle">Sistema de Control de Inventario Institucional</div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div class="header-container">
            <h1 class="header-title">CETPRO La Arena</h1>
            <div class="header-subtitle">Sistema de Control de Inventario Institucional</div>
        </div>
    """, unsafe_allow_html=True)

CATEGORIAS = {
    "🌐 Ver Todos los Registros": "Todos",
    "🖱️ Mouse": "Mouse",
    "🖥️ Computadora": "Computadora",
    "💻 Laptop": "Laptop",
    "⌨️ Teclado": "Teclado",
    "🌀 Ventilador": "Ventilador",
    "🔊 Parlantes": "Parlantes",
    "🗄️ Escritorio": "Escritorio",
    "🪑 Sillas": "Sillas",
    "🧍 Unipersonales": "Unipersonales",
    "🟫 Mesas": "Mesas",
    "🔌 Cargador": "Cargador",
    "⚡ Supresor de Picos": "Supresor de Picos"
}

st.sidebar.title("📌 Menú de Equipos")
opcion_menu = st.sidebar.radio("Seleccione Categoría:", list(CATEGORIAS.keys()))
categoria_seleccionada = CATEGORIAS[opcion_menu]

cat_mobile = st.selectbox("📱 Selección rápida de categoría (Celular):", list(CATEGORIAS.keys()), index=list(CATEGORIAS.keys()).index(opcion_menu))
if cat_mobile != opcion_menu:
    categoria_seleccionada = CATEGORIAS[cat_mobile]

login()

# ==========================================
# 5. FORMULARIO DE REGISTRO
# ==========================================
if categoria_seleccionada == "Todos":
    st.header("📋 Inventario General (Todos los Registros)")
else:
    st.header(f"Gestión de Inventario: {categoria_seleccionada}")

    if st.session_state['autenticado']:
        with st.expander(f"➕ Registrar Nuevo Componente en {categoria_seleccionada}", expanded=False):
            with st.form("form_inventario", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    codigo = st.text_input("Código de Inventario *")
                    equipo = st.text_input("Equipo / Nombre *", value=categoria_seleccionada)
                    marca = st.text_input("Marca")
                    modelo = st.text_input("Modelo")
                    serie = st.text_input("Número de Serie")
                
                with col2:
                    estado = st.selectbox("Estado del Equipo", ["Bueno", "Regular", "Malo", "En Mantenimiento", "Inoperativo"])
                    ubicacion = st.text_input("Ubicación / Taller / Aula")
                    responsable = st.text_input("Responsable(s)")
                    fecha = st.date_input("Fecha de Registro", datetime.now()).strftime("%Y-%m-%d")
                    observaciones = st.text_area("Observaciones")

                guardar = st.form_submit_button("Guardar Registro")
                
                if guardar:
                    if not codigo or not equipo:
                        st.warning("Los campos 'Código' y 'Equipo' son obligatorios.")
                    else:
                        datos = (categoria_seleccionada, codigo, equipo, marca, modelo, serie, estado, ubicacion, responsable, fecha, observaciones)
                        exito, msg = guardar_item(datos)
                        if exito:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
    else:
        st.warning("🔒 Inicie sesión como Administrador en la barra lateral para agregar registros.")

# ==========================================
# 6. VISUALIZACIÓN, EDICIÓN Y EXPORTACIÓN CLASIFICADA
# ==========================================
df_datos = obtener_datos(categoria_seleccionada)

if not df_datos.empty:
    st.dataframe(df_datos, use_container_width=True)

    if st.session_state['autenticado']:
        st.markdown("---")
        st.subheader("🛠️ Panel de Gestión de Registros (Admin)")
        
        tab_editar, tab_eliminar = st.tabs(["✏️ Editar Registro", "🗑️ Eliminar Registro"])
        
        df_todos_registros = obtener_datos("Todos")
        
        with tab_editar:
            if not df_todos_registros.empty:
                opciones_registros = [
                    f"Código: {row['codigo']} | Equipo: {row['equipo']} ({row['categoria']})"
                    for _, row in df_todos_registros.iterrows()
                ]
                seleccion_edit = st.selectbox("Seleccione el equipo que desea editar:", opciones_registros, key="sel_edit")
                
                idx_seleccionado = opciones_registros.index(seleccion_edit)
                id_editar = int(df_todos_registros.iloc[idx_seleccionado]['id'])
                
                registro_actual = obtener_registro_por_id(id_editar)
                
                if registro_actual:
                    cat_idx = list(CATEGORIAS.values()).index(registro_actual[1]) if registro_actual[1] in CATEGORIAS.values() else 0
                    estados_lista = ["Bueno", "Regular", "Malo", "En Mantenimiento", "Inoperativo"]
                    est_idx = estados_lista.index(registro_actual[7]) if registro_actual[7] in estados_lista else 0
                    
                    try:
                        fecha_obj = datetime.strptime(registro_actual[10], "%Y-%m-%d").date()
                    except:
                        fecha_obj = datetime.now().date()

                    with st.form("form_edicion"):
                        st.info(f"Editando: **{registro_actual[3]}** (Código: {registro_actual[2]})")
                        col_e1, col_e2 = st.columns(2)
                        
                        with col_e1:
                            nueva_categoria = st.selectbox("Categoría", list(CATEGORIAS.values()), index=cat_idx)
                            nuevo_codigo = st.text_input("Código de Inventario", value=registro_actual[2])
                            nuevo_equipo = st.text_input("Equipo / Nombre", value=registro_actual[3])
                            nueva_marca = st.text_input("Marca", value=str(registro_actual[4] or ""))
                            nuevo_modelo = st.text_input("Modelo", value=str(registro_actual[5] or ""))
                            nueva_serie = st.text_input("Número de Serie", value=str(registro_actual[6] or ""))
                        
                        with col_e2:
                            nuevo_estado = st.selectbox("Estado del Equipo", estados_lista, index=est_idx)
                            nueva_ubicacion = st.text_input("Ubicación / Taller / Aula", value=str(registro_actual[8] or ""))
                            nuevo_responsable = st.text_input("Responsable(s)", value=str(registro_actual[9] or ""))
                            nueva_fecha = st.date_input("Fecha", value=fecha_obj)
                            nuevas_observaciones = st.text_area("Observaciones", value=str(registro_actual[11] or ""))

                        btn_actualizar = st.form_submit_button("Guardar Cambios")
                        
                        if btn_actualizar:
                            datos_actualizados = (
                                nueva_categoria, nuevo_codigo, nuevo_equipo, nueva_marca, 
                                nuevo_modelo, nueva_serie, nuevo_estado, nueva_ubicacion, 
                                nuevo_responsable, nueva_fecha.strftime("%Y-%m-%d"), nuevas_observaciones
                            )
                            actualizar_item(id_editar, datos_actualizados)
                            st.success(f"¡Registro actualizado correctamente!")
                            st.rerun()
            else:
                st.info("No hay registros disponibles para editar.")

        with tab_eliminar:
            if not df_todos_registros.empty:
                opciones_eliminar = [
                    f"Código: {row['codigo']} | Equipo: {row['equipo']} ({row['categoria']})"
                    for _, row in df_todos_registros.iterrows()
                ]
                seleccion_del = st.selectbox("Seleccione el equipo a eliminar completamente:", opciones_eliminar, key="sel_del")
                idx_del = opciones_eliminar.index(seleccion_del)
                id_eliminar = int(df_todos_registros.iloc[idx_del]['id'])
                
                if st.button("Eliminar Registro Definitivamente"):
                    eliminar_registro(id_eliminar)
                    st.success(f"¡El equipo seleccionado ha sido eliminado por completo de la base de datos!")
                    st.rerun()
            else:
                st.info("No hay registros disponibles para eliminar.")

    st.markdown("---")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_completo = obtener_datos("Todos")
        df_completo.to_excel(writer, sheet_name="Inventario General", index=False)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT categoria FROM inventario")
        categorias_existentes = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        for cat in categorias_existentes:
            df_cat = obtener_datos(cat)
            nombre_hoja = cat[:30].replace("/", "-").replace("\\", "-")
            if not df_cat.empty:
                df_cat.to_excel(writer, sheet_name=nombre_hoja, index=False)
    
    st.download_button(
        label="📥 Exportar Inventario Clasificado a Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"Inventario_CETPRO_La_Arena_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("No hay registros guardados en esta categoría.")
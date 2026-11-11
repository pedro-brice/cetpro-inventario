from datetime import datetime
import io
import sqlite3
import pandas as pd
import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Sistema de Inventario - CETPRO La Arena",
    page_icon="📦",
    layout="wide",
)


# --- INICIALIZACIÓN Y CONEXIÓN DE BASE DE DATOS ---
def get_connection():
  conn = sqlite3.connect("inventario.db", check_same_thread=False)
  return conn


def init_db():
  conn = get_connection()
  cursor = conn.cursor()

  # Crear tabla si no existe
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            especialidad TEXT,
            codigo TEXT,
            equipo TEXT,
            marca TEXT,
            modelo TEXT,
            serie TEXT,
            estado TEXT,
            ubicacion TEXT,
            responsables TEXT,
            fecha TEXT,
            observaciones TEXT
        )
    """)

  # Verificar si la tabla tiene la estructura nueva (campo 'codigo')
  cursor.execute("PRAGMA table_info(inventario)")
  columns = [info[1] for info in cursor.fetchall()]

  if "codigo" not in columns:
    # Si tiene la estructura vieja, actualizarla limpiando la tabla una sola vez
    cursor.execute("DROP TABLE inventario")
    cursor.execute("""
            CREATE TABLE inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                especialidad TEXT,
                codigo TEXT,
                equipo TEXT,
                marca TEXT,
                modelo TEXT,
                serie TEXT,
                estado TEXT,
                ubicacion TEXT,
                responsables TEXT,
                fecha TEXT,
                observaciones TEXT
            )
        """)

  conn.commit()
  conn.close()


# Inicializar base de datos
init_db()

# --- ESPECIALIDADES OFICIALES DEL CETPRO ---
ESPECIALIDADES = [
    "Plataformas y servicios de TI",
    "Fabricación de prendas de vestir",
    "Operaciones de Almacenamiento",
    "Peluquería y Barbería",
    "Mecánica de Motos y Vehículos Afines",
    "Servicios Básicos Gastronómicos",
    "Panadería y Pastelería",
]

# --- GESTIÓN DE SESIÓN Y CONTRASEÑA ---
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "admin_password" not in st.session_state:
  st.session_state.admin_password = "admin"

# --- TÍTULO PRINCIPAL ---
st.markdown(
    "<h1 style='text-align: center; color: #1E3A8A;'>CETPRO La Arena</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<h3 style='text-align: center; color: #4B5563;'>Sistema de Control de"
    " Inventario Institucional</h3>",
    unsafe_allow_html=True,
)
st.write("---")

# --- MENÚ LATERAL (SIDEBAR) ---
st.sidebar.title("Navegación")
especialidad_sel = st.sidebar.selectbox(
    "Seleccione Especialidad:", ESPECIALIDADES
)

st.sidebar.write("---")
st.sidebar.subheader("Control de Acceso")

if not st.session_state.logged_in:
  password_input = st.sidebar.text_input(
      "Contraseña de Administrador", type="password"
  )
  if st.sidebar.button("Iniciar Sesión"):
    if password_input == st.session_state.admin_password:
      st.session_state.logged_in = True
      st.sidebar.success("¡Acceso concedido!")
      st.rerun()
    else:
      st.sidebar.error("Contraseña incorrecta")
else:
  st.sidebar.success("Modo Administrador Activo")
  if st.sidebar.button("🔑 Cambiar Contraseña"):
    st.session_state.changing_password = True
  if st.sidebar.button("Cerrar Sesión"):
    st.session_state.logged_in = False
    st.rerun()

# Modal para cambiar contraseña
if (
    st.session_state.get("logged_in", False)
    and st.session_state.get("changing_password", False)
):
  with st.sidebar.form("form_cambiar_pass"):
    st.write("Cambiar Contraseña")
    nueva_pass = st.text_input("Nueva Contraseña", type="password")
    confirmar_pass = st.text_input("Confirmar Contraseña", type="password")
    btn_guardar_pass = st.form_submit_button("Actualizar")

    if btn_guardar_pass:
      if nueva_pass == confirmar_pass and nueva_pass != "":
        st.session_state.admin_password = nueva_pass
        st.session_state.changing_password = False
        st.success("¡Contraseña actualizada con éxito!")
        st.rerun()
      else:
        st.error("Las contraseñas no coinciden o están vacías.")


# --- FUNCIONES DE MANEJO DE DATOS ---
def obtener_inventario(especialidad):
  conn = get_connection()
  try:
    df = pd.read_sql_query(
        "SELECT id, codigo, equipo, marca, modelo, serie, estado, ubicacion,"
        " responsables, fecha, observaciones FROM inventario WHERE especialidad"
        " = ?",
        conn,
        params=(especialidad,),
    )
  except Exception:
    df = pd.DataFrame()
  finally:
    conn.close()
  return df


def obtener_todo_inventario():
  conn = get_connection()
  try:
    df = pd.read_sql_query(
        "SELECT especialidad, codigo, equipo, marca, modelo, serie, estado,"
        " ubicacion, responsables, fecha, observaciones FROM inventario",
        conn,
    )
  except Exception:
    df = pd.DataFrame()
  finally:
    conn.close()
  return df


# --- CUERPO PRINCIPAL ---
st.subheader(f"Gestión de Inventario: {especialidad_sel}")

# Registrar nuevo componente (Solo Administrador)
if st.session_state.logged_in:
  with st.expander(f"➕ Registrar Nuevo Equipo en {especialidad_sel}"):
    with st.form("form_registrar", clear_on_submit=True):
      col1, col2, col3 = st.columns(3)

      with col1:
        codigo = st.text_input("Código Patrimonial / Interno")
        modelo = st.text_input("Modelo")
        ubicacion = st.text_input("Ubicación / Taller")

      with col2:
        equipo = st.text_input("Equipo / Bien")
        serie = st.text_input("N° de Serie")
        responsables = st.text_input("Responsable(s)")
        
      with col3:
        marca = st.text_input("Marca")
        estado = st.selectbox(
            "Estado", ["Bueno", "Regular", "Malo", "En Mantenimiento"]
        )
         fecha = st.date_input(
            "Fecha de Registro", value=datetime.now()
        ).strftime("%Y-%m-%d")

      observaciones = st.text_area("Observaciones")
      btn_submit = st.form_submit_button("Guardar Registro")

      if btn_submit:
        if equipo.strip() != "":
          conn = get_connection()
          cursor = conn.cursor()
          cursor.execute(
              """
                        INSERT INTO inventario (especialidad, codigo, equipo, marca, modelo, serie, estado, ubicacion, responsables, fecha, observaciones)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
              (
                  especialidad_sel,
                  codigo,
                  equipo,
                  marca,
                  modelo,
                  serie,
                  estado,
                  ubicacion,
                  responsables,
                  fecha,
                  observaciones,
              ),
          )
          conn.commit()
          conn.close()
          st.success("¡Equipo guardado exitosamente!")
          st.rerun()
        else:
          st.warning("El nombre del equipo es obligatorio.")

# Mostrar registros de la especialidad
df_actual = obtener_inventario(especialidad_sel)

if not df_actual.empty:
  st.dataframe(df_actual, use_container_width=True)

  if st.session_state.logged_in:
    st.write("---")
    st.subheader("Eliminar Registro")
    ids_disponibles = (
        df_actual["id"].tolist() if "id" in df_actual.columns else []
    )
    if ids_disponibles:
      id_a_borrar = st.selectbox(
          "Seleccione el ID del registro a eliminar", ids_disponibles
      )
      if st.button("Eliminar Registro Seleccionado"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventario WHERE id = ?", (id_a_borrar,))
        conn.commit()
        conn.close()
        st.success("Registro eliminado correctamente.")
        st.rerun()
else:
  st.info("No hay equipos registrados en esta especialidad.")

# --- BOTÓN DE EXPORTACIÓN A EXCEL ---
st.write("---")
df_total = obtener_todo_inventario()

if not df_total.empty:
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="openpyxl") as writer:
    for esp in ESPECIALIDADES:
      df_esp = df_total[df_total["especialidad"] == esp]
      nombre_hoja = esp[:31]
      df_esp.to_excel(writer, sheet_name=nombre_hoja, index=False)
  output.seek(0)

  st.download_button(
      label="📊 Exportar Todo el Inventario Clasificado a Excel (.xlsx)",
      data=output,
      file_name=(
          f"Inventario_CETPRO_La_Arena_{datetime.now().strftime('%Y%m%d')}.xlsx"
      ),
      mime=(
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      ),
  )

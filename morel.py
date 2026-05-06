import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os


#----------------login con base de datos---------------------------
st.set_page_config(page_title="mi registro de productos", page_icon="🔐")

#AQUI SE INICIA EL BENDITO ST.SESSION STATE
if "login" not in st.session_state:
    st.session_state.login = False

conn = sqlite3.connect("colmado.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
               CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE,
                    password TEXT)
                    """)

cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros (id INTEGER PRIMARY KEY AUTOINCREMENT,
               usuario TEXT,
               nombre TEXT,
               precio REAL,
               cantidad INTEGER,
               total REAL
            )
            """)

conn.commit()

#---------------FUNCIONES-----------------

def encriptar(clave):
    return hashlib.sha256(clave.encode()).hexdigest()

#-----------la sesion-----------
if not st.session_state.login:

#---------Su sesion----------
    tab1, tab2 = st.tabs(["🔐 Iniciar sesión", "📝 Registrarse"])

#---------el Login----------------

    with tab1:
        st.subheader("Entrar")

        user = st.text_input("Usuario", key="login_user").strip()
        password = st.text_input("Contraseña",type="password", key="login_pass").strip()

        if st.button("Entrar"):
            clave_hash = encriptar(password)

            cursor.execute(
                "SELECT * FROM usuarios WHERE usuario=? AND password=?",
                (user,clave_hash) 
            )

            usuario = cursor.fetchone()

            if usuario:
                st.session_state.login = True
                st.session_state.usuario = user
                st.success("Bienvenido")
                st.rerun()
            else:
                st.error("Datos incorrectos")

#------- REGISTRO ----------
    with tab2:
        st.title("📝 Crear Cuenta")

        nuevo_user = st.text_input("Nuevo usuario", key="reg_user")
        clave_hash = st.text_input("Nueva contraseña", type="password", key="reg_pass")

        if st.button("Registrarse"):
            try:
                clave_hash = encriptar(clave_hash)

                cursor.execute(
                    "INSERT INTO usuarios (usuario, password) VALUES (?, ?)",
                    (nuevo_user, clave_hash)
                )
                conn.commit()

                st.success("Cuenta creada correctamente")      
        
            except:
                st.error("Ese usario ya existe")
#-------------------BLOQUEAR APP-----------------
    if not st.session_state.login:
        st.stop()                          


#TITULOOO-------------------------------------
st.title("🛒 Sistema de Registro de Productos")
st.write(f"Bienvenido, {st.session_state.usuario}")


#-------------------------- OCULTAR BOTONES DE LA MISMA WEB-----------------------------------
st.markdown("""
<style>

/* Ocultar footer normal */
footer {visibility: hidden;}
header {visibility: hidden;}
#MainMenu {visibility: hidden;}

/* Ocultar elementos flotantes móviles comunes */
[data-testid="stToolbar"] {
    display: none;
}

[data-testid="stDecoration"] {
    display: none;
}

/* Botones flotantes abajo */
button[kind="header"] {
    display:none;
}

/* Solo móvil */
@media (max-width: 768px) {
    footer, header {
        display:none !important;
    }
}

</style>
""", unsafe_allow_html=True)
#-----------AQUI ACABA EL QUITAR BOTONES DE LA WEB--------------



# Formulario
with st.form("formulario"):
    nombre = st.text_input("Nombre del producto")
    precio = st.number_input("precio unitario", min_value=0.0, format="%.2f")
    cantidad = st.number_input("cantidad", min_value=1, step=1)

    guardar = st.form_submit_button("Registrar producto")

    if guardar:
        total = precio * cantidad

        cursor.execute("""
        INSERT INTO registros (usuario,nombre, precio, cantidad, total)
        VALUES (?, ?, ?, ?, ?)
        """, (st.session_state.usuario,nombre, precio, cantidad, total)) 

        conn.commit()

        st.success("Producto guardado correctamente")


#-------------Editar productos--------
st.subheader("✏️ Editar producto")

#esto leera los productos
df = pd.read_sql_query("SELECT * FROM registros WHERE usuario=?", conn,
            params=(st.session_state.usuario,))

if not df.empty:
    seleccion = st.selectbox(
        "Seleccionar productos POR SU ID",
        df["id"].astype(str) + " - " + df["nombre"]
    )

    producto_id = int(seleccion.split(" - ")[0])

    fila_filtrada = df[df["id"] == producto_id]
    if not fila_filtrada.empty:
        fila = fila_filtrada.iloc[0]

    else:
        st.warning("Producto no encontrado")
        st.rerun()    

    nuevo_nombre = st.text_input("Nombre", value=fila["nombre"])
    
    nuevo_precio = st.number_input("Precio", min_value=0.0, value=float(fila["precio"]), format="%.2f")

    nueva_cantidad = st.number_input("Cantidad", min_value=1, value=int(fila["cantidad"]), step=1)

    if st.button("💾 Guardar cambios"):

        nuevo_total = nuevo_precio * nueva_cantidad

        cursor.execute("""
        UPDATE registros
        SET nombre = ?,
            precio = ?,           
            cantidad = ?,
            total = ?
        WHERE id = ?
        """,(
            nuevo_nombre,
            nuevo_precio,
            nueva_cantidad,
            nuevo_total,
            producto_id
        ))

        conn.commit()

        st.success("Producto actualizado")

        st.rerun()  
    if st.button("🗑️ Eliminar producto"):    
        cursor.execute(
        "DELETE FROM registros WHERE id = ? AND usuario = ?"
            , (producto_id, st.session_state.usuario))
       
        conn.commit()

        st.success("Producto eliminado")

        st.rerun()                                
                       
#Mostrar la tabla--------
df = pd.read_sql_query("SELECT * FROM registros WHERE usuario=?",
            conn,
            params=(st.session_state.usuario,))

if not df.empty:
    st.subheader("📦 Productos registrados")
    st.dataframe(df, use_container_width=True)

suma_total = df["total"].sum()

st.metric("💰 Total General", f"${suma_total:.2f}")

if st.button("🗑️ Limpiar todo"):
   cursor.execute("DELETE FROM registros")
   conn.commit()
   st.rerun()  
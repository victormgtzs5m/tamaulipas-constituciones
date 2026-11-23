archivo_excel = r"C:\Users\VMGS\OneDrive - CONSORCIO PETROLERO 5M DEL GOLFO\Documentos\GitHub\tamaulipas-constituciones\Base.xlsx"      # cambia por el nombre de tu archivo
archivo_db = r"C:\Users\VMGS\OneDrive - CONSORCIO PETROLERO 5M DEL GOLFO\Documentos\GitHub\tamaulipas-constituciones\prodcoord.db"

# Leer hojas
prod = pd.read_excel(archivo_excel, sheet_name="TMPL-CONST")
listado = pd.read_excel(archivo_excel, sheet_name="Listado")
coord = pd.read_excel(archivo_excel, sheet_name="Coord")
contorno = pd.read_excel(archivo_excel, sheet_name="Contorno")
asignacion = pd.read_excel(archivo_excel, sheet_name="Asignacion")
termpozos = pd.read_excel(archivo_excel, sheet_name="TERM")
rmapozos = pd.read_excel(archivo_excel, sheet_name="RMA")
estadopozo = pd.read_excel(archivo_excel, sheet_name="Estado")
presionespozo = pd.read_excel(archivo_excel, sheet_name="Presiones")
operacioncampo = pd.read_excel(archivo_excel, sheet_name="Operacion")
inyectorescampo = pd.read_excel(archivo_excel, sheet_name="Inyectores")
localizacionespozos = pd.read_excel(archivo_excel, sheet_name="Localizaciones")
instalaciones = pd.read_excel(archivo_excel, sheet_name="Instalaciones")
reservas = pd.read_excel(archivo_excel, sheet_name="Reservas")
evaluaciones = pd.read_excel(archivo_excel, sheet_name="Evaluaciones")

# Limpiar nombres de columnas
prod.columns = prod.columns.str.strip()
listado.columns = listado.columns.str.strip()
coord.columns = coord.columns.str.strip()
contorno.columns = contorno.columns.str.strip()
asignacion.columns = asignacion.columns.str.strip()
termpozos.columns = termpozos.columns.str.strip()
rmapozos.columns = rmapozos.columns.str.strip()
estadopozo.columns = estadopozo.columns.str.strip()
presionespozo.columns = presionespozo.columns.str.strip()
operacioncampo.columns = operacioncampo.columns.str.strip()
inyectorescampo.columns = inyectorescampo.columns.str.strip()
localizacionespozos.columns = localizacionespozos.columns.str.strip()
instalaciones.columns = instalaciones.columns.str.strip()
reservas.columns = reservas.columns.str.strip()
evaluaciones.columns = evaluaciones.columns.str.strip()

# Conectar / crear base SQLite
conn = sqlite3.connect(archivo_db)

# Guardar en .db
prod.to_sql("Produccion", conn, if_exists="replace", index=False)
listado.to_sql("Listado", conn, if_exists="replace", index=False)
coord.to_sql("Coord", conn, if_exists="replace", index=False)
contorno.to_sql("Contorno", conn, if_exists="replace", index=False)
asignacion.to_sql("Asignacion", conn, if_exists="replace", index=False)
termpozos.to_sql("TERM", conn, if_exists="replace", index=False)
rmapozos.to_sql("RMA", conn, if_exists="replace", index=False)
estadopozo.to_sql("Estado", conn, if_exists="replace", index=False)
presionespozo.to_sql("Presiones", conn, if_exists="replace", index=False)
operacioncampo.to_sql("Operacion", conn, if_exists="replace", index=False)
inyectorescampo.to_sql("Inyectores", conn, if_exists="replace", index=False)
localizacionespozos.to_sql("Localizaciones", conn, if_exists="replace", index=False)
instalaciones.to_sql("Instalaciones", conn, if_exists="replace", index=False)
reservas.to_sql("Reservas", conn, if_exists="replace", index=False)
evaluaciones.to_sql("Evaluaciones", conn, if_exists="replace", index=False)

conn.close()


################################################################

  # Trayectoria superficie-fondo
    for _, row in mapa.iterrows():
        if pd.notna(row["SUP X UTM"]) and pd.notna(row["SUP Y UTM"]) and pd.notna(row["FONDO X UTM"]) and pd.notna(row["FONDO Y UTM"]):
            fig.add_trace(go.Scatter(
                x=[row["SUP X UTM"], row["FONDO X UTM"]],
                y=[row["SUP Y UTM"], row["FONDO Y UTM"]],
                mode="lines",
                line=dict(width=1.5, color="gray"),
                hoverinfo="skip",
                showlegend=False
            ))

            # Punto de superficie
            fig.add_trace(go.Scatter(
                x=[row["SUP X UTM"]],
                y=[row["SUP Y UTM"]],
                mode="markers",
                marker=dict(size=4, color="black"),
                hovertemplate=f"<b>{row[COL_POZO]}</b><br>Superficie<extra></extra>",
                showlegend=False
            ))

            # Punto de fondo
            fig.add_trace(go.Scatter(
                x=[row["FONDO X UTM"]],
                y=[row["FONDO Y UTM"]],
                mode="markers",
                marker=dict(size=4, color="gray"),
                hovertemplate=f"<b>{row[COL_POZO]}</b><br>Fondo<extra></extra>",
                showlegend=False
            ))


########################################
TABLA 

st.markdown("<div class='section-title'>Datos filtrados del pozo</div>", unsafe_allow_html=True)

    show_cols = [
        COL_POZO, COL_FECHA, COL_YAC, COL_CONTA, COL_DIAS,
        COL_ACEITE, COL_AGUA, COL_GAS,
        COL_ACEITE_BBL, COL_AGUA_BBL, COL_GAS_PC,
        COL_QO, COL_QW, COL_QG,
        COL_NP, COL_WP, COL_GP,
        COL_WC, COL_RGA
    ]

    st.dataframe(
        dfp[show_cols],
        use_container_width=True,
        hide_index=True
    )

    csv = dfp[show_cols].to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "Descargar datos filtrados en CSV",
        data=csv,
        file_name=f"produccion_{pozo_sel}.csv",
        mime="text/csv"
    )


import pandas as pd
import os
import zipfile
from datetime import datetime

def procesoInventarios(inventario_path, tabla_upc, output_folder):
    """
    Procesa el archivo de inventarios y genera archivos ZIP con las propuestas.
    :param inventario_path: Ruta del archivo de inventarios
    :param tabla_upc: DataFrame de la tabla UPC
    :param output_folder: Ruta de la carpeta de salida
    :return: Rutas de los archivos ZIP generados
    """

    hoy = datetime.now()
    fecha = hoy.strftime("%d-%m-%Y")

    # Cargar el archivo de inventarios
    inventario = pd.read_excel(inventario_path)
    inventario["UPC"] = inventario["UPC"].astype(str)
    inventario["UPC"] = inventario["UPC"].str.replace(".0", "", regex=False)
    inventario = inventario.rename(columns={"STYLE": "STYLE_INV"})

    # Hacer merge con la tabla UPC
    inventarioFinal = pd.merge(inventario, tabla_upc[["UPC", "Brand", "STYLE", "Color Name"]], on="UPC", how="left")

    # Filtrar marcas no necesarias
    inventarioFinal = inventarioFinal[~inventarioFinal["Brand"].isin(["CALZANETTO", "SMJ", "SMA"])]

    # Crear la columna BARCODE
    inventarioFinal["BARCODE"] = inventarioFinal["STYLE_INV"].astype(str) + "-" + inventarioFinal["COLOR_CODE"].astype(str)

    # Obtener el 25% superior del inventario
    percent = 0.25
    num_registros = int(len(inventarioFinal) * percent)
    muestra = inventarioFinal.head(num_registros)

    # Archivos ZIP de salida
    zip_propuesta_path = os.path.join(output_folder, f"Propuestas_Tienda_{fecha}.zip")
    zip_upc_path = os.path.join(output_folder, f"UPCs_Cantidades_{fecha}.zip")

    # Crear archivo ZIP para la propuesta por tienda
    with zipfile.ZipFile(zip_propuesta_path, 'w') as zipf:
        for tienda in muestra["STORE_NAME"].unique():
            df_tienda = muestra[muestra["STORE_NAME"] == tienda]
            df_propuesta = df_tienda.pivot_table(
                index=["STORE_NAME", "BARCODE", "STYLE", "Color Name", "Brand"],
                columns=["SIZE_DESC"],
                values=["STORE_ON_HAND"],
                fill_value=0
            ).reset_index()

            # Aplanar el MultiIndex de las columnas
            df_propuesta.columns = [f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col for col in df_propuesta.columns]

            # Crear el archivo Excel por tienda y agregarlo al ZIP
            propuesta_filename = f"Propuesta_{tienda}.xlsx"
            propuesta_path = os.path.join(output_folder, propuesta_filename)
            df_propuesta.to_excel(propuesta_path, index=False)

            # Agregar archivo Excel al ZIP
            zipf.write(propuesta_path, arcname=propuesta_filename)

    # Crear archivo ZIP para UPCs y cantidades
    with zipfile.ZipFile(zip_upc_path, 'w') as zipf:
        for tienda in muestra["STORE_NAME"].unique():
            df_tienda = muestra[muestra["STORE_NAME"] == tienda]
            upc_tienda = df_tienda.groupby("UPC", as_index=False)["AVAILABLE"].sum()

            # Crear el archivo Excel por tienda con UPCs y cantidades
            upc_filename = f"UPCs_{tienda}.xlsx"
            upc_path = os.path.join(output_folder, upc_filename)
            upc_tienda.to_excel(upc_path, index=False)

            # Agregar archivo Excel al ZIP
            zipf.write(upc_path, arcname=upc_filename)

    # Devolver las rutas de los archivos ZIP generados
    return zip_propuesta_path, zip_upc_path

from flask import Flask, request, render_template, send_from_directory
import pandas as pd
import os
from generaArchivos import procesoInventarios  # Importar la función de generación de archivos

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Cargar la tabla de UPC al inicio de la aplicación
upc_path = "./TABLA UPC.xlsx"  # Ruta del archivo de TABLA UPC
tabla_upc = pd.read_excel(upc_path)
tabla_upc['UPC'] = tabla_upc['UPC'].astype(str)
tabla_upc['UPC'] = tabla_upc['UPC'].str.replace(".0", "", regex=False)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "inventario_file" not in request.files:
            return "No se cargó ningún archivo", 400

        file = request.files["inventario_file"]
        if file.filename == "":
            return "Nombre de archivo inválido", 400

        # Guardar el archivo cargado
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        try:
            # Procesamos el archivo cargado y obtenemos los archivos generados
            resultados = procesoInventarios(file_path, tabla_upc, app.config['OUTPUT_FOLDER'])
            
            # Asegurarse de que los resultados contengan solo los nombres de los archivos
            zip_propuesta = os.path.basename(resultados[0])  # Extraemos solo el nombre del archivo
            zip_upc = os.path.basename(resultados[1])  # Extraemos solo el nombre del archivo
            
            # Devolver los archivos generados para descargar
            return render_template("resultados.html", zip_propuesta=zip_propuesta, zip_upc=zip_upc)

        except Exception as e:
            return f"Error al procesar el archivo: {str(e)}", 500
    
    return render_template("index.html")


@app.route("/download/<filename>")
def descargar_zip(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)


# Asegurarse que las carpetas existen y correr la app
if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['OUTPUT_FOLDER']):
        os.makedirs(app.config['OUTPUT_FOLDER'])
    
    app.run(host="0.0.0.0", port=5000, debug=True)

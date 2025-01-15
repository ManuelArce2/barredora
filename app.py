from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import matplotlib
matplotlib.use('Agg')  # Usar backend no interactivo
import matplotlib.pyplot as plt
import os
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

detener_flag = False  # Bandera para detener el procesamiento

# Ruta para la página principal
@app.route('/')
def index():
    filepath = 'mapeo.png'
    mapa_disponible = os.path.exists(filepath)
    return render_template('index_realtime.html', mapa_disponible=mapa_disponible, now=datetime.now())

# Ruta para recibir datos
@app.route('/recibir_datos', methods=['POST'])
def recibir_datos():
    global detener_flag
    if detener_flag:
        return jsonify({'status': 'stopped', 'message': 'El procesamiento está detenido.'}), 200

    try:
        datos = request.json  # Recibir datos en formato JSON
        if 'data' in datos:
            mensaje = datos['data']
            print(f'Datos recibidos:\n{mensaje}')
            procesar_mapa_radar(mensaje)  # Generar el mapa tipo radar
            # Emitir evento para actualizar clientes conectados
            socketio.emit('actualizar_mapa', {'status': 'updated'})
            return jsonify({'status': 'success', 'message': 'Datos procesados correctamente.'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Formato de datos incorrecto.'}), 400
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Ruta para detener el procesamiento
@app.route('/detener', methods=['POST'])
def detener():
    global detener_flag
    detener_flag = True
    print("Procesamiento detenido.")
    socketio.emit('detener_procesamiento', {'status': 'stopped'})
    return jsonify({'status': 'success', 'message': 'Procesamiento detenido.'}), 200

# Ruta para reiniciar el procesamiento
@app.route('/reiniciar', methods=['POST'])
def reiniciar():
    global detener_flag
    detener_flag = False
    print("Procesamiento reiniciado.")
    socketio.emit('reiniciar_procesamiento', {'status': 'resumed'})
    return jsonify({'status': 'success', 'message': 'Procesamiento reiniciado.'}), 200

# Ruta para servir el mapa generado
@app.route('/mapeo')
def ver_mapeo():
    filepath = 'mapeo.png'
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='image/png')
    else:
        return 'No se ha generado ningún mapa aún.', 404

# Procesar los datos y generar el mapa tipo radar
def procesar_mapa_radar(datos):
    datos_procesados = []
    for linea in datos.split('\n'):
        if 'Angulo:' in linea and 'Distancia:' in linea:
            partes = linea.split(',')
            angulo = int(partes[0].split(':')[1].strip())
            distancia = int(partes[1].split(':')[1].strip().replace('mm', ''))
            datos_procesados.append((angulo, distancia))

    # Generar gráfico tipo radar
    angulos = [dato[0] for dato in datos_procesados]
    distancias = [dato[1] for dato in datos_procesados]

    # Asegurar que el gráfico es cerrado
    angulos.append(angulos[0])
    distancias.append(distancias[0])

    plt.figure()
    ax = plt.subplot(111, polar=True)
    ax.fill([a * (3.14159 / 180) for a in angulos], distancias, alpha=0.4)
    ax.plot([a * (3.14159 / 180) for a in angulos], distancias, marker='o')
    ax.set_title('Mapa tipo Radar')
    plt.savefig('mapeo.png')
    plt.close()

    if os.path.exists('mapeo.png'):
        print("Mapa generado correctamente.")
    else:
        print("Error: No se pudo generar el archivo mapeo.png.")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

import json
import random
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Cargar los datos de personajes desde el archivo JSON
with open('amongus_data.json', encoding='utf-8') as f:
    amongus_data = json.load(f)

def seleccionar_asesino(excluir):
    sospechosos = [char for char in amongus_data['characters'] if char['name'] != excluir]
    return random.choice(sospechosos)

def generar_pistas(asesino):
    pistas_iniciales = random.sample(asesino['evidence'], 1)
    otras_pistas = [evidencia for char in amongus_data['characters'] if char['name'] != asesino['name'] for evidencia in char['evidence']]
    pistas_iniciales += random.sample(otras_pistas, 1)
    session['pistas_adicionales'] = list(set(asesino['evidence']) - set(pistas_iniciales))
    return pistas_iniciales

def agregar_pista():
    if session['pistas_adicionales']:
        nueva_pista = random.choice(session['pistas_adicionales'])
        session['pistas'].append(nueva_pista)
        session['pistas_adicionales'].remove(nueva_pista)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/seleccionar_personaje', methods=['GET', 'POST'])
def seleccionar_personaje():
    if request.method == 'POST':
        asesinado = request.form['asesinado']
        session['asesinado'] = asesinado
        return redirect(url_for('nueva_partida'))
    
    personajes = [char['name'] for char in amongus_data['characters']]
    return render_template('seleccionar_personaje.html', personajes=personajes)

@app.route('/nueva_partida', methods=['GET', 'POST'])
def nueva_partida():
    if request.method == 'POST':
        session.clear()
        asesinado = request.form['personaje']
        session['asesinado'] = asesinado
        asesino = seleccionar_asesino(asesinado)
        pistas = generar_pistas(asesino)
        
        # Inicializa variables de sesión
        session['asesino'] = asesino['name']
        session['pistas'] = pistas
        session['sospechosos_restantes'] = [char['name'] for char in amongus_data['characters'] if char['name'] != asesinado]
        session['intentos'] = 0
        
        return redirect(url_for('adivinar'))
    
    return render_template('seleccionar_personaje.html', personajes=[char['name'] for char in amongus_data['characters']])

@app.route('/adivinar')
def adivinar():
    asesinado = session.get('asesinado')
    personajes = session.get('sospechosos_restantes', [])
    return render_template('adivinar.html', personajes=personajes, pistas=session['pistas'], asesinado=asesinado)

@app.route('/verificar', methods=['POST'])
def verificar():
    sospechoso = request.form['sospechoso']
    asesino = session['asesino']
    
    session['intentos'] += 1  # Incrementar el contador de intentos

    if sospechoso != asesino:
        # Si se alcanza el límite de intentos, termina el juego
        if session['intentos'] >= 3:
            resultado = "Has agotado tus intentos. ¡Perdiste!"
            return render_template('resultado.html', resultado=resultado, asesino=None)
        
        # Eliminar al sospechoso incorrecto
        if sospechoso in session['sospechosos_restantes']:
            session['sospechosos_restantes'].remove(sospechoso)
        
        agregar_pista()  # Añadir una nueva pista
        return redirect(url_for('adivinar', intento_fallido=1))
    else:
        # Si acierta, muestra el resultado
        resultado = "¡Correcto! Has descubierto al asesino."
        return render_template('resultado.html', resultado=resultado, asesino=asesino)

if __name__ == '__main__':
    app.run(debug=True)

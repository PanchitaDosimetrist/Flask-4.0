import threading
from flask import Flask, redirect, render_template, request, jsonify, url_for
import requests
from uuid import uuid4
from urllib.parse import urlparse
from hashlib import sha256
import datetime
import time
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Simulación de la blockchain y sus métodos

class Block:
    def __init__(self, previous_hash_block, data):
        self.previous_hash_block = previous_hash_block
        self.data = data
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.nonce = 0

    def hash(self):
        info = "#".join(str(item) for item in self.data) + self.previous_hash_block + str(self.nonce) + str(self.timestamp)
        return sha256(info.encode()).hexdigest()

    def to_dict(self):
        return {
            "previous_hash": self.previous_hash_block,
            "data": self.data,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "hash": self.hash()
        }

class Blockchain:
    def __init__(self):
        self.transactions = []
        self.chain = []
        genesis_block = Block("0", ["Genesis Block"])
        self.mine(genesis_block)

    def get_previous_block(self):
        if self.chain:
            return self.chain[-1]
        return None

    def mine(self, block):
        while block.hash()[:3] != "000":
            block.nonce += 1
        self.chain.append(block)

    def add_transaction(self, paciente, vacuna, dosis):
        self.transactions.append({'paciente': paciente, 'vacuna': vacuna, 'dosis': dosis})

    def print_chain(self):
        return [block.to_dict() for block in self.chain]

blockchain = Blockchain()

# Rutas de la aplicación
@app.route('/')
def menu():
    return '''
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; background-color: #f4f4f9; height: 100vh; font-family: Arial, sans-serif;">
        <div style="max-width: 500px; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: #fff; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); text-align: center;">
            <h1 style="color: #333;">Sistema de Minado de Vacunas</h1>
            <p style="color: #666; font-size: 16px;">Seleccione una opción para continuar:</p>
            <form method="POST" action="/opcion">
                <div style="margin-bottom: 20px;">
                    <select name="opcion" style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 16px;">
                        <option value="1">Minar un nuevo bloque</option>
                        <option value="2">Registrar una nueva vacuna</option>
                        <option value="3">Ver la blockchain completa</option>
                        <option value="4">Salir</option>
                    </select>
                </div>
                <button type="submit" style="background-color: #007BFF; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">Enviar</button>
            </form>
        </div>
    </div>
    '''

@app.route('/opcion', methods=['POST'])
def manejar_opcion():
    opcion = request.form.get('opcion')
    mensaje = ""

    if opcion == "1":
        previous_block = blockchain.get_previous_block()
        previous_hash = previous_block.hash() if previous_block else "0"
        new_block = Block(previous_hash, blockchain.transactions)
        blockchain.mine(new_block)
        blockchain.transactions = []
        mensaje = "Nuevo bloque minado."
    elif opcion == "2":
        paciente = request.form.get('paciente')
        vacuna = request.form.get('vacuna')
        try:
            dosis = float(request.form.get('dosis'))
            blockchain.add_transaction(paciente, vacuna, dosis)
            mensaje = "Vacuna agregada."
        except ValueError:
            mensaje = "La dosis debe ser un número."
    elif opcion == "3":
        cadena = blockchain.print_chain()
        mensaje = f"Blockchain: {jsonify(cadena).get_data(as_text=True)}"
    elif opcion == "4":
        return redirect(url_for('Saliendo'))
    else:
        mensaje = "Opción inválida, intente de nuevo."

    return render_template('Formulario.html', mensaje=mensaje)

@app.route('/Saliendo', methods=['POST', 'GET'])
def Saliendo():
    # Crear el grafo
    G = nx.DiGraph()

    # Agregar nodos y conexiones
    for i, block in enumerate(blockchain.chain):
        G.add_node(f"Bloque {i}", timestamp=block.timestamp)
        if block.previous_hash_block != "0":
            prev_index = next((j for j, b in enumerate(blockchain.chain) if b.hash() == block.previous_hash_block), None)
            if prev_index is not None:
                G.add_edge(f"Bloque {prev_index}", f"Bloque {i}")

    # Dibujar el grafo
    pos = nx.spring_layout(G)
    plt.figure(figsize=(10, 8))
    nx.draw(G, pos, with_labels=True, node_color="skyblue", node_size=2000, font_size=10, font_weight="bold", arrows=True)
    labels = nx.get_node_attributes(G, 'timestamp')
    nx.draw_networkx_labels(G, pos, labels={node: f"{node}\n{data}" for node, data in labels.items()}, font_size=8)

    # Guardar el grafo en memoria y codificarlo en base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    # Retornar el grafo como HTML
    return f'''
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; border: 1px solid #ccc; border-radius: 10px; background-color: #f9f9f9; max-width: 600px; margin: 20px auto; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <h2 style="text-align: center; color: #333; font-family: Arial, sans-serif;">¡Gracias por utilizar el sistema de minado para vacunas!</h2>
        <p style="text-align: center; color: #666; font-size: 16px;">A continuación puede ver el grafo de conectividad:</p>
        <div style="margin-top: 20px;">
            <img src="data:image/png;base64,{graph_url}" alt="Blockchain Graph" style="max-width: 100%; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);">
        </div>
    </div>
    '''
if __name__ == '__main__':
    app.run(debug=True)

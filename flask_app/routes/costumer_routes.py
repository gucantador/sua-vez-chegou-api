from flask_app import  db, sock #, jwt__
from flask import jsonify, request
from flask_app.models import Costumer
import threading
import time
import json
from simple_websocket import ConnectionClosed, ConnectionError
#from flask_app.utils.utils import check_and_update, check_username, load_roles, jwt_handling, create_token_and_send_email, can_donate
#from flask_app.constants import errors, messages
#from flask_jwt_extended import jwt_required, get_jwt_identity, create_refresh_token, create_access_token, get_jwt
from . import BaseResponse
#from flask_app.constants import errors, messages
import base64
#from flask_jwt_extended import jwt_required


def get_app():
    """
    Returns the Flask application object.
    This function imports the Flask application object from the `flask_app` module and returns it.
    This must be done so there is no circular import problem.
    """
    from flask_app import app
    return app

app = get_app()
sera = False
new = False

active_connections = []
monitor_thread_started = False
monitor_thread_started2 = False

# Mensagens e erros
messages = {
    "LIST_COSTUMERS": "Costumer list updated",
    "CREATE_COSTUMER": "Costumer created",
    "GET_COSTUMER": "Costumer found",
    "UPDATE_COSTUMER": "Costumer updated",
    "DELETE_COSTUMER": "Cliente deletado com sucesso.",
    "NEXT_COSTUMER_UPDATED": "Position updated",
    "NO_NEXT_COSTUMER": "There is only one costumer on the line",
    "NO_CURRENT_COSTUMER": "There are no costumers on the line"
}

errors = {
    "NOT_FOUND": "Costumer was not found",
    "INTERNAL_ERROR": "Internal server error",
    "INVALID_DATA": "Invalid data"
}

# 1. GET - Listar todos os Costumers
@app.route('/costumers', methods=['GET'])
def get_costumers():
    try:
        costumers = Costumer.query.all()
        response = BaseResponse(data=[costumer.to_dict() for costumer in costumers], errors=None, message=messages["LIST_COSTUMERS"])
        return response.response(), 200
    except Exception as e:
        print(e)
        response = BaseResponse(data=None, errors=errors["INTERNAL_ERROR"], message=errors["INTERNAL_ERROR"])
        return response.response(), 500


# 2. POST - Criar um novo Costumer
@app.route('/costumers', methods=['POST'])  # make possible to save costumer without phone
def create_costumer():
    try:
        data = request.get_json()
        phone = data.get('phone')

        if not phone:
            response = BaseResponse(data=None, errors=errors["INVALID_DATA"], message=errors["INVALID_DATA"])
            return jsonify(response.response()), 400

        last_costumer = Costumer.query.order_by(Costumer.id.desc()).first()


        if last_costumer:
            position_in_line = last_costumer.position_in_line + 1
        else:
            position_in_line = 1

        costumers = Costumer.query.all()

        if costumers:
            is_turn = False
        if not costumers:
            is_turn = True

        new_costumer = Costumer(phone=phone, position_in_line=position_in_line, is_turn=is_turn)
        db.session.add(new_costumer)
        db.session.commit()

        global new
        new = not new

        response = BaseResponse(data=new_costumer.to_dict(), errors=None, message=messages["CREATE_COSTUMER"])
        return response.response(), 201
    except Exception as e:
        print(e)
        response = BaseResponse(data=None, errors=errors["INTERNAL_ERROR"], message=errors["INTERNAL_ERROR"])
        return new_costumer.to_dict(), 500

# 3. GET - Obter um único Costumer
@app.route('/costumers/<int:id>', methods=['GET'])
def get_costumer(id):
    try:
        costumer = Costumer.query.get(id)
        if not costumer:
            response = BaseResponse(data=None, errors=errors["NOT_FOUND"], message=errors["NOT_FOUND"])
            return jsonify(response.response()), 404

        response = BaseResponse(data=costumer.to_dict(), errors=None, message=messages["GET_COSTUMER"])
        return jsonify(response.response()), 200
    except Exception as e:
        print(e)
        response = BaseResponse(data=None, errors=errors["INTERNAL_ERROR"], message=errors["INTERNAL_ERROR"])
        return jsonify(response.response()), 500

# 4. PUT - Atualizar um Costumer
@app.route('/costumers/<int:id>', methods=['PUT'])
def update_costumer(id):
    try:
        costumer = Costumer.query.get(id)
        if not costumer:
            response = BaseResponse(data=None, errors=errors["NOT_FOUND"], message=errors["NOT_FOUND"])
            return jsonify(response.response()), 404

        data = request.get_json()
        costumer.phone = data.get('phone', costumer.phone)
        costumer.position_in_line = data.get('position_in_line', costumer.position_in_line)

        db.session.commit()

        response = BaseResponse(data=costumer.to_dict(), errors=None, message=messages["UPDATE_COSTUMER"])
        return jsonify(response.response()), 200
    except Exception as e:
        print(e)
        response = BaseResponse(data=None, errors=errors["INTERNAL_ERROR"], message=errors["INTERNAL_ERROR"])
        return jsonify(response.response()), 500


# 5. DELETE - Deletar um Costumer
@app.route('/costumers/<int:id>', methods=['DELETE'])
def delete_costumer(id):
    try:
        costumer = Costumer.query.get(id)
        if costumer.is_turn:
            update_current_costumer()

        if not costumer:
            response = BaseResponse(data=None, errors=errors["NOT_FOUND"], message=errors["NOT_FOUND"])
            return response.response(), 404

        db.session.delete(costumer)
        db.session.commit()

        response = BaseResponse(data=None, errors=None, message=messages["DELETE_COSTUMER"])
        return response.response(), 200
    except Exception as e:
        print(e)
        response = BaseResponse(data=None, errors=errors["INTERNAL_ERROR"], message=errors["INTERNAL_ERROR"])
        return response.response(), 500


@app.route('/update_current_costumer', methods=['PUT'])
def update_current_costumer():
    try:
        # Buscar o cliente atual com is_turn=True
        current_costumer = Costumer.query.filter_by(is_turn=True).first()

        if not current_costumer:
            response = BaseResponse(
                data=None,
                errors=None,
                message=messages["NO_CURRENT_COSTUMER"]
            )
            return jsonify(response.response()), 404

        # Atualizar o cliente atual para is_turn=False

        db.session.commit()

        # Buscar o próximo cliente na fila (com base na posição)

        next_costumer = Costumer.query.filter(Costumer.position_in_line > current_costumer.position_in_line).order_by(Costumer.position_in_line).first()
        db.session.delete(current_costumer)
        db.session.commit()

        if next_costumer:
            # Atualizar o próximo cliente para is_turn=True
            print("Passou aqui")
            next_costumer.is_turn = True
            db.session.commit()

            response = BaseResponse(
                data=next_costumer.to_dict(),
                errors=None,
                message=messages["NEXT_COSTUMER_UPDATED"]
            )


            global sera
            sera = not sera
            return response.response(), 200
        else:
            response = BaseResponse(
                data=None,
                errors=None,
                message=messages["NO_NEXT_COSTUMER"]
            )
            return response.response(), 404

    except Exception as e:
        print(e)
        db.session.rollback()  # Desfaz qualquer alteração em caso de erro
        response = BaseResponse(
            data=None,
            errors=errors["INTERNAL_ERROR"],
            message=errors["INTERNAL_ERROR"]
        )
        return response.response(), 500


def monitor():
    global sera
    global active_connections
    previous_value = sera
    print("Thread started")

    with app.app_context():
        current_costumer = Costumer.query.filter_by(is_turn=True).first()
        costumers = len(Costumer.query.all())
    position = current_costumer.to_dict()
    position["costumers_in_line"] = costumers
    for i in range(len(active_connections)):
        try:
            active_connections[i].send(json.dumps(position))
        except ConnectionClosed:
            print("Connection closed")

    while True:
        time.sleep(1)  # Checagem a cada 1 segundo
        if sera != previous_value:
            previous_value = sera
            with app.app_context():
                current_costumer = Costumer.query.filter_by(is_turn=True).first()
                costumers = len(Costumer.query.all())
            position = current_costumer.to_dict()
            position["costumers_in_line"]=costumers
            for i in range(len(active_connections)):
                try:
                    active_connections[i].send(json.dumps(position))
                except ConnectionClosed:
                    print("Connection closed")
                    return


def monitor_line(sock):
    global new
    #global sera

    previous_value = new
    #previous_value_sera = sera
    print("Thread started")

    with app.app_context():
        costumers = len(Costumer.query.all())
    try:
        sock.send(json.dumps(dict(costumers=costumers)))
    except ConnectionClosed:
        print("Connection closed")

    while True:
        time.sleep(1)  # Checagem a cada 1 segundo

        if new != previous_value:
            previous_value = new
            print("Entrou aqui")

            with app.app_context():
                costumers = len(Costumer.query.all())
            try:
                sock.send(json.dumps(dict(costumers=costumers)))
            except ConnectionClosed:
                print("Connection closed")
                return


@sock.route('/current_costumer_socket')
def current_costumer_to_show(sock):

    global active_connections
    global monitor_thread_started
    active_connections.append(sock)


    if not monitor_thread_started:

        monitor_thread_started = True
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.daemon = True
        monitor_thread.start()



    # Mantenha o WebSocket ativo enquanto o monitor está rodando
    try:
        while True:
            sock.receive()
                # Recebe dados para manter a conexão aberta
    except ConnectionClosed:
        print("Conexão WebSocket fechada")
        active_connections.remove(sock)



@sock.route('/how_many_in_line_socket')
def how_many_in_line_socket(sock):

    global monitor_thread_started2

    if not monitor_thread_started2:

        monitor_thread_started2 = True
        monitor_thread = threading.Thread(target=monitor_line, args=[sock,])
        monitor_thread.daemon = True
        monitor_thread.start()

    # Mantenha o WebSocket ativo enquanto o monitor está rodando
    try:
        while True:
            sock.receive()
                # Recebe dados para manter a conexão aberta
    except ConnectionClosed:
        print("Conexão WebSocket fechada")

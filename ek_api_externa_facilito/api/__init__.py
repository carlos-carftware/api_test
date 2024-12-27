import sys
from flask import Flask,jsonify, json,request, make_response,current_app
import os
from mako.template import Template as MakoTemplate
from .api import OdooApi
from .message_catalog import MessageCataloglist
import jwt
import datetime
from functools import wraps


app = Flask(__name__)
app.config['SECRET_KEY'] = 'Eku@s0ft'

dir_json = os.path.dirname(os.path.realpath(__file__))
filname = os.path.join(dir_json, 'config.json')
with open(filname) as config_file:
    conn_config = json.load(config_file)


# #TODO LOGUIN ODOO
srv_app = conn_config['ODOO_SERVER']
db_app = conn_config['ODOO_DATABASE']
usr_app = conn_config['ODOO_USER']
apikey_app = conn_config['ODOO_APIKEY']
API = OdooApi(srv_app,db_app,usr_app,apikey_app)



@app.route('/contract/contract_jwt/', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("user")
    password = data.get("password")
    time = data.get("time")

    if not username:
        return jsonify({
            "codigoRespuesta": "JT001",
            "descripcionRespuesta": MessageCataloglist.MessageCatalog['JT001']
            }), 400

    if not password:
        return jsonify({
            "codigoRespuesta": "JT002",
            "descripcionRespuesta": MessageCataloglist.MessageCatalog['JT002']
            }), 400

    if not time:
        return jsonify({
            "codigoRespuesta": "JT003",
            "descripcionRespuesta": MessageCataloglist.MessageCatalog['JT003']
            }), 400
    

    value = API.get_search_user_token(username,password)
    if not value:
        return jsonify({
            "codigoRespuesta": "JT004",
            "descripcionRespuesta": MessageCataloglist.MessageCatalog['JT004']
        }), 400

    if value[0].get('user_name') == username and value[0].get('password') == password:

        expiration_time =  datetime.datetime.utcnow()  + datetime.timedelta(seconds=time)
        token = jwt.encode({
            "username": username,
            "exp": expiration_time,
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify(
                        [
                {
                    "jwt_token": token,
                    "codigoRespuesta": "JT006",
                    "descripcionRespuesta": MessageCataloglist.MessageCatalog['JT006']
                }
                    ]
            )


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token es requerido'}), 401

        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            request.username = data['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token ha expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token no válido'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/contract/search', methods=['POST', 'GET'])
@jwt_required
def get_data_debit():
    try:
        data = request.get_json()
        valor_busqueda = data.get('valor_busqueda')
        # id_sub_empresa = data.get('idSubempresa')
        # if not id_sub_empresa:
        #    return jsonify({
        #        "codigoRespuesta": "C001",
        #       "descripcionRespuesta": MessageCataloglist.MessageCatalog['C001']
        #  }), 400


        resultado = API.get_debt_payment(valor_busqueda)

        return jsonify(resultado)

    except Exception as e:
        return jsonify({
            "codigoRespuesta": "500",
            "descripcionRespuesta": f"Error interno del servidor: {str(e)}",
        }), 500



@app.route('/contract/payment', methods=['POST', 'GET'])
@jwt_required
def set_data_payment():
    try:
        data = request.get_json()
        id_sub_empresa = data.get('idSubempresa')
        id_recaudadora =    data.get('idRecaudadora')
        id_deuda =    data.get('idDeuda')
        valorDeuda =    data.get('valorDeuda')
        fechaTransaccion =    data.get('fechaTransaccion')
        idPagoIr =    data.get('idPagoIr')

        if not idPagoIr:
            return jsonify({
                "codigoRespuesta": "P010",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['P010']
            }), 400

        if valorDeuda <= 0:
            return jsonify({
                "codigoRespuesta": "P009",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['P009']
            }), 400
        if not valorDeuda:
            return jsonify({
                "codigoRespuesta": "P008",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['P008']
            })
        if not fechaTransaccion:
            return jsonify({
                "codigoRespuesta": "P006",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['P006']
            }), 400
        username = request.username
        resultado = API.set_debt_payment(id_sub_empresa,id_recaudadora,
                                         id_deuda,valorDeuda,fechaTransaccion,idPagoIr,username)

        return jsonify(resultado)

    except Exception as e:
        return jsonify({
            "codigoRespuesta": "500",
            "descripcionRespuesta": f"Error interno del servidor: {str(e)}",
        }), 500




@app.route('/contract/reverse', methods=['POST', 'GET'])
@jwt_required
def set_data_payment_reverse():
    try:
        data = request.get_json()
        id_sub_empresa = data.get('idSubempresa')
        id_recaudadora =    data.get('idRecaudadora')
        valorDeuda =    data.get('valorDeuda')
        idPagoIr =    data.get('idPagoIr')
        fechaTransaccion =    data.get('fechaTransaccion')
        id_deuda =    data.get('idDeuda')


        if not id_sub_empresa or not id_recaudadora or not id_deuda or not valorDeuda or not fechaTransaccion or not idPagoIr:
            return jsonify({
                "codigoRespuesta": "R001",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['R001']
            }), 400
        username = request.username
        resultado = API.reverse_debt_payment(id_sub_empresa,
                                             id_recaudadora,
                                             idPagoIr,
                                            valorDeuda,
                                            fechaTransaccion,
                                            id_deuda,
                                            username
                                         )

        return jsonify(resultado)

    except Exception as e:
        return jsonify({
            "codigoRespuesta": "500",
            "descripcionRespuesta": f"Error interno del servidor: {str(e)}",
            "idSubempresa": id_sub_empresa,
            "idPagoIr": idPagoIr
        }), 500
    



@app.route('/contract/search_payment', methods=['POST', 'GET'])
@jwt_required
def get_data_payment():
    try:
        data = request.get_json()
        id_recaudadora =    data.get('idRecaudadora')
        id_sub_empresa = data.get('idSubempresa')
        fecha_proceso_ir =    data.get('fechaProcesoIr')
        if not fecha_proceso_ir:
            return jsonify({
                "codigoRespuesta": "PS003",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['PS003']
            }), 400
        if not id_recaudadora:
            return jsonify({
                "codigoRespuesta": "PS004",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['PS004']
            }), 400
        if not id_sub_empresa:
            return jsonify({
                "codigoRespuesta": "PS005",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['PS005']
            }), 400

        resultado = API.get_data_payment_search(id_recaudadora,
                                                id_sub_empresa,
                                                fecha_proceso_ir,
                                                )

        return jsonify(resultado)

    except Exception as e:
        return jsonify({
            "codigoRespuesta": "500",
            "descripcionRespuesta": f"Error interno del servidor: {str(e)}",
        }), 500

    
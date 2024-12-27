

class MessageCataloglist():
    MessageCatalog = {
                    #Mensajes para el servicio web de Buasqueda de deudas por cedula

                    'C001' : 'Falta código del Subempresa.',
                    'C002' : 'Código Subempresa no configurado.',
                    'C003' : 'Cliente Correcto.',
                    'C004' :'No existe parametro para procesar busqueda.',

                    #Mensajes para pagos

                    'P001' : 'Pago Exitoso.',
                    'P002' : 'Deuda no existe',
                    'P003' : 'Pago No procesado - Valor Deuda no coincide.',
                    'P004' : 'Pago No procesado - Cliente no tiene Deudas.',
                    'P006' :'Pago No procesado - Falta paramerto de Fecha Transaccion.',
                    'P008' :'Ingresar parametro de valor de la Deuda.',
                    'P009' :'El Parametro de valor de la Deuda no puede ser 0.',
                    'P010' :'Pago No procesado - Falta paramerto de Id de Pago.',
                    'P011' :'Pago No procesado.',

                    # Mensajes para reverso

                    'R001':'No existe parametro para procesar el reverso.',
                    'R002':'No existe codigo de pago para el reverso.',
                    'R003':'Reverso No procesado - Valor Deuda no coincide.',
                    'R004' :'Reverso Procesado correctamente.',

                    # Mensajes para genarar jwt

                    'JT001' :'Ingresar Usuario para generar el JWT',
                    'JT002' :'Ingresar Password para generar el JWT',
                    'JT003' :'Ingresar Time de Validez del JWT',
                    'JT004' :'Usuario Incorrecto',
                    'JT005' :'Password Incorrecto',
                    'JT006' :'JWT Generado',


                    #Mensajes para Listar pagos realizados en una Fecha

                    'PS001' :'No existen transacciones con el parametro enviado.',
                    'PS002' :'Transaccion generada correctamente.',
                    'PS003' :'Ingresar fecha de Proceso.',
                    'PS004' :'Ingresar Codigo entidad recaudadora.',
                    'PS005' :'Ingresar Codigo Subempresa.'

    }
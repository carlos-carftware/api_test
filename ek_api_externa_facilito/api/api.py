import xmlrpc.client
from datetime import datetime, timedelta
from .message_catalog import MessageCataloglist



class OdooApi:

    def __init__(self, server, db, user, key):
        self.server = server
        self.db = db
        self.user = user
        self.key = key
        self.uid = 0
        self.common = False

    def connect(self):
        if not self.common:
            common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.server))
            uid = common.authenticate(self.db, self.user, self.key, {})

            self.uid = uid
            self.common = common

        return self.common
    
    def get_search_user_token(self, username,password):
        self.connect()
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.server))

        domain = [
            ['password', '=', password],
            ['user_name', '=', username],
            ['state', '=', 'active'],

            ]
        user_jwt = models.execute_kw(
            self.db,
            self.uid,
            self.key,
            'ek.collection.ext.user.jwt',
            'search_read',
            [domain],
            {'fields': ['password', 'user_name']})
        return user_jwt
    
    def get_search_sub_company(self,models):
        company = models.execute_kw(
            self.db,
            self.uid,
            self.key,
            'ek.collection.ext.config',
            'search_read',
            [[['type', '=','facilito']]],
            {'fields': ['id', 'name', 'login','codigopago','id_subcompany',
                        'company_id','bank_id','journal_id','payment_method_line_id']})
        return company
    
    def get_sale_subscription(self, models, valor_busqueda):
        ids = []
        domain = [
            '|', 
            ['partner_id.vat', '=', valor_busqueda],
            ['code', '=', valor_busqueda],
            ]
        saleSubscriptions = models.execute_kw(
            self.db,
            self.uid,
            self.key,
            'sale.subscription',
            'search_read',
            [domain],
            {'fields': ['id', 'name', 'code','company_id','partner_id']})


        for rec in saleSubscriptions:
            ids.append(rec.get('id', 0))
        return (saleSubscriptions, ids)

    def get_debt_payment(self, valor_busqueda):
        self.connect()
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.server))
        (subscription, ids) = self.get_sale_subscription(models, valor_busqueda)

        if not ids:
            return {
                "codigoRespuesta": "C004",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['C004']
            }
        
        id_sub_company = self.get_search_sub_company(models)

        if not id_sub_company:
             return {
                "codigoRespuesta": "C002",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['C002']
            }


        sales = models.execute_kw(
            self.db,
            self.uid,
            self.key,
            'sale.order',
            'search_read',
            [[
                ['amount_residual', '>', 0],
                ['order_line.subscription_id', 'in', ids],
            ]],
            {'fields': ['id', 'name', 'partner_id', 'promotion_templ_id', 'ek_subscription_id', 'amount_residual','company_id',
                        'date_order','amount_tax','validity_date','city_id'],
             'order': "date_order asc"})
        if not sales:
            return {
                "codigoRespuesta": "P002 ",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['P002']
            }
        partner = False
        deudas = []
        cliente = {}
        secuencial = 0
        for sale in sales:
            date_str_to = datetime.strptime(sale.get('date_order'), '%Y-%m-%d %H:%M:%S')
            amount = round(sale.get('amount_residual', 0.0), 2)
            formatted_amount = f"{amount:.2f}"
            if not partner:
                partner = subscription[0].get('partner_id', ["", False])

                vat = self.get_partner_vat(models,subscription[0].get('partner_id', ["", False])[0])
                cliente = {
                    "nombre": partner[1],  
                    "identificacion": vat[0].get('vat', ''),
                }
            if sale.get("ek_subscription_id", False):
                contrato =  sale.get("ek_subscription_id", False)[1].split(" - ")[0]
            if sale.get("company_id", False):
                id_company = sale.get("company_id", False)[0]
                id_sub_empresa = False
                for company in id_sub_company:
                    if company.get("company_id", False)[0] == id_company:
                        id_sub_empresa = company.get("id_subcompany", False)
                if not id_sub_empresa:
                    return {
                        "codigoRespuesta": "C002",
                        "descripcionRespuesta": MessageCataloglist.MessageCatalog['C002']
                    }

            deudas.append({
                "secuencial": secuencial,
                "idDeuda": sale.get('name', ''),
                "fechaEmision": date_str_to.strftime("%Y-%m-%d"),
                "fechaVencimiento": sale.get('validity_date', ''), 
                "nombreDeuda": (sale.get('name', '') or '')+" "+ contrato + " " + (' ' or sale.get('city_id', [None, ""])[1] ),
                "valorDeuda": formatted_amount,
                "idSubempresa": id_sub_empresa
            })
            secuencial += 1


        value = {
            "deudas": deudas,
            "cliente": cliente,
            "codigoRespuesta": "C003",
            "descripcionRespuesta": MessageCataloglist.MessageCatalog['C003'],

        }


        return value

    def get_partner_vat(self, models,partner_id):
        partner = models.execute_kw(
            self.db,
            self.uid,
            self.key,
            'res.partner',
            'search_read',
            [[
                ['id', '=', partner_id],
            ]],
            {'fields': ['id', 'vat']})
        return partner

    def get_sale_order_with_amount_residual(self, models, id_deuda,company_id):
        sales = models.execute_kw(
            self.db,
            self.uid,
            self.key,
            'sale.order',
            'search_read',
            [[
                ['name', '=', id_deuda],
                ['amount_residual', '>=', 0],
                ['company_id.id', '=', company_id],
            ]],
            {'fields': ['id', 'partner_id', 'amount_residual']})
        return sales

    def set_debt_payment(self, id_sub_empresa,id_recaudadora,
                            id_deuda,valorDeuda,fechaTransaccion,idPagoIr,username):
        self.connect()
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.server), allow_none=True)
        duals = models.execute_kw(self.db,
                                self.uid,
                                self.key, 'account.payment', 'search', [[
                ['ref_card', '=', idPagoIr],
                ['state', 'in', ['posted','draft']],        

            ]])
       
        if len(duals) >= 1:
            return {
                "codigoRespuesta": "P011",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['P011']
            }



        id_sub_company = self.get_search_sub_company(models)
        company_id = False
        for company in id_sub_company:
            if company.get("id_subcompany", False) == id_sub_empresa and company.get("codigopago", False) == id_recaudadora:
                company_id = company
        if not company_id:
            return {
                "codigoRespuesta": "C002",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['C002']
            }
        
        partner_id_for_sale = self.get_sale_order_with_amount_residual(models, id_deuda,company_id.get('company_id', [None, ""])[0])

        if  partner_id_for_sale[0].get('amount_residual', 0) <= 0:
            return {
                "codigoRespuesta": "P004",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['P004']
        }

        data = {
            
            "type_Payment": "payment",
            "ref": idPagoIr,
            "ref_ext": id_deuda,
            "ref_card": idPagoIr,
            "date": fechaTransaccion,
            "collector_ext": id_recaudadora,
            "sale_id": partner_id_for_sale[0].get('id', 0),
            "partner_id": partner_id_for_sale[0].get('partner_id', [None, ""])[0],
            "amount": valorDeuda,
            "payment_method_line_id": company_id.get('payment_method_line_id', [None, ""])[0],
            "company_id": company_id.get('company_id', [None, ""])[0],
            "journal_id": company_id.get('journal_id', [None, ""])[0],

            #login

            "login": company_id.get('login', ''),
            "name_collector": company_id.get('name', ''),
            "codigopago": company_id.get('codigopago', ''),
            "bank_id": company_id.get('bank_id', ''),
            "id_subcompany": company_id.get('id_subcompany', ''),
            "username": username

        }


        try:
                    models.execute_kw(
                        self.db,
                        self.uid,
                        self.key,
                        'ek.collection.ext.config',
                        'payment_ext_action_done',
                       
                        [[]],
                        data
                    )                   
        except Exception as ex:
            if "Fault 2" not in ex.__str__():
                res_partner = partner_id_for_sale[0].get('partner_id', [None, ""])
                vat = self.get_partner_vat(models,res_partner[0])
                return [
                    {
                        "idSubempresa": id_sub_empresa,
                        "cedulaCliente": vat[0].get('vat'),
                        "nameCliente": res_partner[1],
                        "descripcionRespuesta": MessageCataloglist.MessageCatalog['P001'],
                        "codigoRespuesta": "P001",
                        "idPagoIr": idPagoIr
                    }
                ]
            raise ex
            





    def reverse_debt_payment(self, id_subempresa, id_recaudadora,idPagoIr,valor_deuda,fecha_transaccion,id_deuda,username):
        self.connect()
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.server), allow_none=True)
        
        id_sub_company = self.get_search_sub_company(models)
        company_id = False
        for company in id_sub_company:
            if company.get("id_subcompany", False) == id_subempresa:
                company_id = company
        if not company_id:
            return {
                "codigoRespuesta": "C002",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['C002']
            }

        
        payment = models.execute_kw(self.db,
                                self.uid,
                                self.key, 'account.payment', 'search_read', [[
                ['ref_card', '=', idPagoIr],
                ['collector_ext', '=', id_recaudadora],
                ['state', '=', 'posted'],
                ['ref_ext', '=', id_deuda],
                ['date', '=', fecha_transaccion],
                ['company_id.id', '=', company_id.get('company_id', [None, ""])[0]],


            ]],
            {'fields': ['id', 'name',
                        'ref', 'ref_ext','ref_card','date','collector_ext','sale_id','partner_id',
                        'amount','payment_method_line_id','company_id','journal_id'
                         ]})
        if not payment:
             return {
                "codigoRespuesta": "R002",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['R002']
            }

        if payment[0].get('amount', 0) != valor_deuda:
            return {
                "codigoRespuesta": "R003",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['R003']
            }
        data = {
            "type_Payment": "reverse",
            "id" : payment[0].get('id', 0),
            "ref": idPagoIr,
            "ref_ext": id_deuda,
            "ref_card": idPagoIr,
            "date": payment[0].get('date', ''),
            "collector_ext": id_recaudadora,
            "sale_id":  payment[0].get('sale_id', 0),
            "partner_id": payment[0].get('partner_id', [None, ""])[0],
            "amount":  payment[0].get('amount', 0),
            "payment_method_line_id":  payment[0].get('payment_method_line_id', [None, ""])[0],
            "company_id":  payment[0].get('company_id', [None, ""])[0],
            "journal_id":  payment[0].get('journal_id', [None, ""])[0],

            #login

            "login": company_id.get('login', ''),
            "name_collector": company_id.get('name', ''),
            "codigopago": company_id.get('codigopago', ''),
            "bank_id": company_id.get('bank_id', ''),
            "id_subcompany": company_id.get('id_subcompany', ''),
            "username": username

        }
        

        try:
             models.execute_kw(
                        self.db,
                        self.uid,
                        self.key,
                        'ek.collection.ext.config',
                        'reverse_payment_ext_action',
                       
                        [[]],
                        data
                    )       
        except Exception as ex:
                res_partner = payment[0].get('partner_id', [None, ""])
                vat = self.get_partner_vat(models,res_partner[0])
                return [
                    {
                        "idSubempresa": id_subempresa,
                        "cedulaCliente": vat[0].get('vat'),
                        "nameCliente": res_partner[1],
                        "idPagoIr": idPagoIr,
                        "descripcionRespuesta": MessageCataloglist.MessageCatalog['R004'],
                        "codigoRespuesta": "R004",
                        
                    }
                ]
                raise ex
            



 
    def get_data_payment_search(self,id_recaudadora,id_sub_empresa,fecha_proceso_ir):
        self.connect()
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.server), allow_none=True)
        id_sub_company = self.get_search_sub_company(models)
        company_id = False
        for company in id_sub_company:
            if company.get("id_subcompany", False) == id_sub_empresa:
                company_id = company
        if not company_id:
            return {
                "codigoRespuesta": "C002",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['C002']
            }
        
        payment_ids = models.execute_kw(self.db,
                                self.uid,
                                self.key, 'account.payment', 'search_read', [[
                ['collector_ext', '=', id_recaudadora],
                ['state', '=', 'posted'],
                ['company_id.id', '=',company_id.get('company_id', [None, ""])[0],],
                ['date', '=', fecha_proceso_ir],


            ]],
            {'fields': ['id', 'name', 'date','ref_ext','ref_card','collector_ext','amount','partner_id',
                        'company_id'],
                        'order': "date asc"})
        if not payment_ids:
            return {
                "codigoRespuesta": "PS001",
                "descripcionRespuesta": MessageCataloglist.MessageCatalog['PS001']
            }

        datas = self.group_get_data_payment_search(models,payment_ids,id_sub_empresa)

        return datas


    def group_get_data_payment_search(self,models,data = [],id_sub_empresa = False):
        grouped_data = {}
        for entry in data:
            ref_card = entry.get('ref_card')
            amount = entry.get('amount')

            if ref_card in grouped_data:
                grouped_data[ref_card]["valorDeuda"] += amount
            else:

                res_partner = entry.get('partner_id', [None, ""])
                vat = self.get_partner_vat(models,res_partner[0])
                grouped_data[ref_card] = {
                    "idDeuda": entry.get('ref_ext'),
                    "idPagoIr": ref_card,
                    "idSubempresa": id_sub_empresa,
                    "nombreCliente": res_partner[1],
                    "nameSubempresa": entry.get('company_id')[1],
                    "cedulaCliente": vat[0].get('vat'),
                    "valorDeuda": round(amount, 2),
                }

        result = list(grouped_data.values())  
        for item in result:
            item["valorDeuda"] = format(item["valorDeuda"], '.2f')
        pagos = [{
        "pagos": result,
        "descripcionRespuesta": MessageCataloglist.MessageCatalog['PS002'], 
        "codigoRespuesta": 'PS002' 
        }]
        return pagos








    def _normalize_total(self, amount):
        total = str("%.2f" % amount)
        _normalize = total.replace(".", "").replace(",", "")
        return int(_normalize[0]) == 0 and _normalize[1:] or _normalize

    def _desnormalize_total(self, amount):
        str_amount = str(amount)
        if amount:
            if len(str_amount) >= 3:
                return float("%s.%s" % (str_amount[:-2], str_amount[-2:]))
            else:
                return float("0.%s" % str_amount)

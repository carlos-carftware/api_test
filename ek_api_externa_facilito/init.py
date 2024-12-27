from api import app
from api import OdooApi
if __name__ == '__main__':
    app.run(port=9002, host="0.0.0.0",  debug=True)
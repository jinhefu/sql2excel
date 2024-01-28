from flask import Flask, request, render_template, send_file
from gevent import pywsgi
import psycopg2
import pandas as pd
import configparser
import datetime
import base64
import os

config = configparser.RawConfigParser()
config.read('./custom_config.ini', 'utf-8')


def getDatabaseData(sql):
    try:
        connection = psycopg2.connect(
            host=config.get('db.properties', 'ip'),
            port=config.get('db.properties', 'port'),
            user=config.get('db.properties', 'username'),
            password=config.get('db.properties', 'password'),
            database=config.get('db.properties', 'name'),
        )
        cursor = connection.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        result = cursor.fetchall()
        return pd.DataFrame(result, columns=columns)
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")


app = Flask(__name__,
            template_folder='./templates',
            static_folder='./world-peace')


@app.route('/world-peace/index', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/world-peace/exportExcel', methods=['POST'])
def exportExcel():
    try:
        dataId = request.get_json().get('dataId')
        sql = config.get('data.sql', dataId)
        df = getDatabaseData(sql)
        currentDir = os.path.dirname(os.path.abspath(__file__)) 
        # 将DataFrame对象导出为Excel文件
        fileName = dataId + datetime.datetime.now().strftime(
            '%Y%m%d-%H%M%S') + '.xlsx'
        filePath = os.path.join(currentDir, fileName)
        df.to_excel(filePath, index=False, engine='openpyxl')
        return send_file(filePath, as_attachment=True)
    except (Exception) as error:
        print("Error while exporting", error)


@app.route('/world-peace/getDataIdList', methods=['GET'])
def queryDataIdList():
    try:
        return config.options('data.sql')
    except (Exception) as error:
        print("Error while querying", error)


@app.route('/world-peace/addDataItem', methods=['POST'])
def addDataItem():
    try:
        dataItem = request.get_json()
        dataSql = base64.b64decode(dataItem.get('dataSql')).decode()
        if dataSql.find('select') < 0:
            return 'failed', 500
        config.set('data.sql', dataItem.get('dataId'), dataSql)
        with open('custom_config.ini', 'w', encoding='utf-8') as file:
            config.write(file)
            return 'success'
    except (Exception) as error:
        print("Error while querying", error)


@app.route('/world-peace/delDataItem', methods=['POST'])
def delDataItem():
    try:
        dataItem = request.get_json()
        config.remove_option('data.sql', dataItem.get('dataId'))
        with open('custom_config.ini', 'w', encoding='utf-8') as file:
            config.write(file)
            return 'success'
    except (Exception) as error:
        print("Error while querying", error)


@app.route('/world-peace/getDatabaseInfo', methods=['POST'])
def getDatabaseInfo():
    try:
        return {
            "ip": config.get('db.properties', 'ip'),
            "port": config.get('db.properties', 'port'),
            "username": config.get('db.properties', 'username'),
            "password": config.get('db.properties', 'password'),
            "name": config.get('db.properties', 'name')
        }
    except (Exception) as error:
        print("Error while querying", error)


@app.route('/world-peace/saveDatabaseInfo', methods=['POST'])
def saveDatabaseInfo():
    try:
        dbInfo = request.get_json()
        config.set('db.properties', 'ip', dbInfo.get('ip')),
        config.set('db.properties', 'port', dbInfo.get('port')),
        config.set('db.properties', 'username', dbInfo.get('username')),
        config.set('db.properties', 'password', dbInfo.get('password')),
        config.set('db.properties', 'name', dbInfo.get('name')),
        with open('custom_config.ini', 'w', encoding='utf-8') as file:
            config.write(file)
            return 'success'
    except (Exception) as error:
        print("Error while querying", error)


if __name__ == '__main__':
    serverPort = config.get('server.info', 'server.port')
    server = pywsgi.WSGIServer(('0.0.0.0', int(serverPort)), app)
    server.serve_forever()
    # app.run(port=serverPort)

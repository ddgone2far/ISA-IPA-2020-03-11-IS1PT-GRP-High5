from flask import Flask, Response, request, jsonify, g
import json
import datetime
import sqlite3
from uuid import uuid4

# Use Google Cloud API
import io

app = Flask(__name__)


def va_didi_text_detection(image, API_type='text_detection', maxResults=20):
    """Detects text in the file."""
    from google.cloud import vision

    client = vision.ImageAnnotatorClient.from_service_account_json(
        "D:/GoogleCloud/ipadaiyirui001-9cad5c929128.json")

    with io.open(image, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    image_analysis_reply = ""

    for text in texts:
        image_analysis_reply += text.description

    resp = {
        "fulfillment_text": image_analysis_reply
    }

    return resp


def get_covid_status_in_country(host, country, date):
    country = country
    status = "Severe"
    date = date
    host = host

    # TO-DO: Tagui to store Covid-19 data Image at: folder "static" with name "Overall.PNG"
    overall = "Overall.PNG"
    new = "New.PNG"
    death = "Death.PNG"

    resp = {
        "fulfillment_messages": [
            {
                "platform": "SLACK",
                "card": {
                    "title": f"Overall Covid-19 Status of {country}",
                    "image_uri": f"https://{host}/static/{overall}"
                }
            },
            {
                "platform": "SLACK",
                "quick_replies": {
                    "title": "Any specific data you are interested in?",
                    "quick_replies": [
                        f"Daily New Cases in {country}", f"Total Death Cases in {country}"
                    ]
                }
            }
        ]
    }

    return resp


def get_covid_new_cases_in_country(host, country):
    country = country
    host = host

    # TO-DO: Tagui to store Covid-19 data Image at: folder "static" with name "New.PNG"
    new = "New.PNG"

    resp = {
        "fulfillment_messages": [
            {
                "platform": "SLACK",
                "card": {
                    "title": f"Daily New Covid-19 Cases of {country}",
                    "image_uri": f"https://{host}/static/{new}"
                }
            }
        ]
    }

    return resp


def get_covid_total_death_cases_in_country(host, country):
    country = country
    host = host

    # TO-DO: Tagui to store Covid-19 data Image at: folder "static" with name "Death.PNG"
    death = "Death.PNG"

    resp = {
        "fulfillment_messages": [
            {
                "platform": "SLACK",
                "card": {
                    "title": f"Total Covid-19 Death Cases of {country}",
                    "image_uri": f"https://{host}/static/{death}"
                }
            }
        ]
    }

    return resp


def upload_temperature_to_website(host, temp):
    temperature = temp

    # TO-DO: Tagui to store Temperature Image at: folder "static" with name "temperature.jpg"
    resp_text = f"Your tempurature {temperature} is successfully uploaded."
    image_name = "temperature.jpg"

    resp = {
        "fulfillment_messages": [
            {
                "platform": "SLACK",
                "card": {
                    "title": resp_text,
                    "image_uri": f"https://{host}/static/{image_name}"
                }
            }
        ]
    }
    return resp


def redirect_to_website(host):
    host = host

    resp = {
        "fulfillment_messages": [
            {
                "platform": "SLACK",
                "card": {
                    "title": "MOH's News Available at:",
                    "image_uri": f"https://{host}/static/moh.PNG",
                    "buttons": [
                        {
                            "text": "Singapore MOH Website",
                            "postback": "https://www.moh.gov.sg/covid-19"
                        }
                    ]
                }
            },
            {
                "platform": "SLACK",
                "card": {
                    "title": "WHO's News Available at:",
                    "image_uri": f"https://{host}/static/who.PNG",
                    "buttons": [
                        {
                            "text": "WHO Website",
                            "postback": "https://www.who.int/emergencies/diseases/novel-coronavirus-2019/situation-reports"
                        }
                    ]
                }
            }
        ]
    }
    return resp


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def query_db(query, args=()):
    cur = get_db().cursor()
    cur.execute(query, args)

    rv = cur.fetchall()  # Retrive all rows
    cur.close()
    return rv
    # return (rv[0] if rv else None) if one else rv


def update_db(query, args=(), one=False):
    conn = get_db()
    conn.execute(query, args)
    conn.commit()
    conn.close()
    return "DB updated"


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route("/")  # take note of this decorator syntax, it's a common pattern
def home():
    return "API is up and running..."


@app.route('/update_case', methods=['GET', 'POST'])
def raise_case():
    country = request.args.get('country')
    confirmed_no = request.args.get('confirmed_no')
    icu_no = request.args.get('icu_no')
    death_no = request.args.get('death_no')

    time_stamp = str(datetime.datetime.now())
    # case_id = int(time.mktime(rpt_time.timetuple()))

    tmp_list = [country, confirmed_no, icu_no, death_no, time_stamp]

    update_db("INSERT INTO TB_CASE (COUNTRY, CONFIRMED_NO, ICU_NO, DEATH_NO, TIME_STAMP) VALUES (?,?,?,?,?);",
              tmp_list)

    return "Cases updated with time stamp as " + time_stamp


@app.route('/query_case', methods=['GET', 'POST'])
def search_case():
    search_country = request.args.get('country')

    tmp_list = [search_country]

    rows = query_db("SELECT * from TB_CASE WHERE COUNTRY = ?", tmp_list)

    return jsonify(rows)


@app.route('/init', methods=['POST'])
def init_db():
    sql_create_table = """ CREATE TABLE IF NOT EXISTS TB_CASE (
                                          COUNTRY text NOT NULL,
                                          CONFIRMED_NO integer NOT NULL,
                                          ICU_NO integer NOT NULL,
                                          DEATH_NO integer NOT NULL,
                                          TIME_STAMP text NOT NULL
                                      ); """

    update_db(sql_create_table)
    return "DB created!"


@app.route("/main", methods=["POST"])
def main():
    req = request.get_json(silent=True, force=True)
    host = request.host
    intent_name = req["queryResult"]["intent"]["displayName"]
    print(req)

    if intent_name == "CheckCovidStatus":
        country = req["queryResult"]["parameters"]["country"]
        date = req["queryResult"]["parameters"]["date"]
        resp = get_covid_status_in_country(host, country, date)
    elif intent_name == "UploadTemperature":
        temp = req["queryResult"]["parameters"]["temp"]
        resp = upload_temperature_to_website(host, temp)
    elif intent_name == "RedirectToLink":
        resp = redirect_to_website(host)
    elif intent_name == "DailyNewCases":
        country = req["queryResult"]["parameters"]["country"]
        resp = get_covid_new_cases_in_country(host, country)
    elif intent_name == "TotalDeathCases":
        country = req["queryResult"]["parameters"]["country"]
        resp = get_covid_total_death_cases_in_country(host, country)
    elif intent_name == "ReadTempFromImage":
        image = "static/575890997.jpg"
        resp = va_didi_text_detection(image)
    else:
        resp = {
            "fulfillment_text": "Unable to find a matching intent. Try again."
        }

    return Response(json.dumps(resp), status=200, content_type="application/json")


if __name__ == '__main__':
    DATABASE = "./db/demo.db"

    # Generate a globally unique address for this node
    node_identifier = str(uuid4()).replace('-', '')

    print(node_identifier)
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5001, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port, debug=True)

import os
import hashlib
import json
import dataset
import tabulate
from flask import Flask, request, Response


app = Flask(__name__)
db = dataset.connect("sqlite:///db.sqlite3")


@app.route("/v2/domains/<domain>/records", methods=["GET"])
def domains_get_records(domain):
    print('GET RECORD "%s"' % (domain))
    return json.dumps(
        {
            "records": [
                {
                    "id": rec["uid"],
                    "name": rec["name"],
                    "type": rec["type"],
                    "value": rec["value"],
                }
                for rec in db["records"].find()
            ]
        }
    )


@app.route("/v2/domains/<domain>/records", methods=["POST"])
def domains_create_record(domain):
    print(
        'CREATE RECORD "%s" type="%s" name="%s" value="%s"'
        % (domain, request.json["type"], request.json["name"], request.json["value"])
    )
    uid = "rec_" + hashlib.sha256(request.data).hexdigest()[:16]

    record = {}
    record.update({"uid": uid, "domain": domain})
    record.update(request.json)
    db["records"].insert(record)

    return json.dumps({"uid": uid})


@app.route("/v2/domains/<domain>/records/<record_id>", methods=["DELETE"])
def domains_delete_record(domain, record_id):
    db["records"].delete(domain=domain, uid=record_id)
    print('DELETE RECORD "%s" (domain="%s")' % (record_id, domain))
    return json.dumps({})


@app.route("/v4/domains/buy", methods=["POST"])
def domains_buy():
    print(
        'BUY DOMAIN domain="%s" expected_price=%s'
        % (request.json["name"], request.json["expectedPrice"])
    )

    if request.json["name"] == "google.com":
        return json.dumps(
            {"error": {"code": "not_available", "message": "Domain is not available"}}
        )

    record = {}
    record.update(
        {
            "domain": request.json["name"],
            "expected_price": request.json["expectedPrice"],
        }
    )

    db["domains"].insert(record)

    return json.dumps({})


@app.route("/v4/domains/<domain>", methods=["DELETE"])
def delete_domain(domain):
    print('DELETE DOMAIN domain="%s"' % domain)

    db["domains"].delete(domain=domain)

    return json.dumps({})


@app.route("/v4/domains/price", methods=["GET"])
def domains_price():
    PRICE = 10
    PERIOD = 1

    print(
        'DOMAIN PRICE domain="%s" (price=%s period=%s)'
        % (request.args["name"], PRICE, PERIOD)
    )

    return json.dumps({"price": PRICE, "period": PERIOD})


@app.route("/", methods=["GET"])
def index():
    response = []
    response.append(
    """
Domains
=======
"""
    )

    response.append(
        tabulate.tabulate(
            [(row["domain"], row["expected_price"]) for row in db["domains"].find()],
            headers=["domain", "expected_price"],
        )
    )


    response.append(
    """
DNS Records
===========
"""
    )

    response.append(
        tabulate.tabulate(
            [
                (row["domain"], row["type"], row["name"], row["value"])
                for row in db["records"].find()
            ],
            headers=["domain", "type", "name", "value"],
        )
    )
    return Response("\n".join(response), mimetype='text/plain')




if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0", port="80", threaded=False, processes=1)

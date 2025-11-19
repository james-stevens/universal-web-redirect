#! /usr/bin/python3
# (c) Copyright 2023-2023, James Stevens ... see LICENSE for details
# Alternative license arrangements possible, contact me for more information

import os
import random
import flask
from dns import rdatatype

import resolver

RR_URI = rdatatype.from_text("URI")
RR_TXT = rdatatype.from_text("TXT")


def abort(err_no, message):
    return flask.make_response(message + "\n", err_no)


application = flask.Flask("Universal Web Redirect")
qry = resolver.Resolver(os.environ["PYTHON_NAME_SERVERS"].split(" ") if
                        "PYTHON_NAME_SERVERS" in os.environ else ["127.0.0.1"])


def strip_uri(uri):
    pos = uri.find('"')
    out_uri = uri[pos + 1:].strip('"') if pos >= 0 else uri.strip('"')
    if out_uri[:7].lower() != "http://" and out_uri[:8].lower() != "https://":
        return "http://" + out_uri
    return out_uri


def get_uris(msg):
    return [
        uri for rr in msg.answer for i in rr
        if (uri := strip_uri(i.to_text())) is not None
    ]


def get_ttl(msg):
    return max([rr.ttl for rr in msg.answer])


def get_domain(msg):
    for rr in msg.authority:
        for i in rr:
            if rr.rdtype == rdatatype.SOA:
                return rr.name.to_text()
    return None


def has_rr_type(msg_section, rdtype):
    return any(rr.rdtype == rdtype for rr in msg_section for i in rr)


def get_uri_records(host):
    msg = qry.resolv(host, RR_URI)

    if msg.rcode() == 3:
        msg = qry.resolv("_http._tcp." + host, RR_URI)

    if msg.rcode() == 3:
        if (domain := get_domain(msg)) is None:
            return None, None
        msg = qry.resolv("_http._tcp._any" + domain, RR_URI)

    if msg.rcode() != 0:
        return None, None

    if has_rr_type(msg.answer, RR_URI):
        return get_ttl(msg), get_uris(msg)

    msg = qry.resolv(host, RR_TXT)
    if msg.rcode() == 3:
        msg = qry.resolv("_http._tcp." + host, RR_TXT)

    if msg.rcode() == 0 and has_rr_type(msg.answer, RR_TXT):
        return get_ttl(msg), get_uris(msg)

    return None, None


def redirect_user(request, text):
    host = None
    if "Host" not in request.headers:
        return abort(499, "No host name header record found")

    host = request.headers["Host"]
    if host.find(":") > 0:
        host = host.split(":")[0]

    ttl, uris = get_uri_records(host)
    if uris is None or len(uris) <= 0:
        return abort(
            490,
            ("<html><body><h1>Universal Web Forwarding Error</h1>" +
             f"No URI or TXT record found for host '{host}'</body></html>"))

    redirect_code = 301
    if len(uris) > 1:
        redirect_code = 302
        random.shuffle(uris)

    send_them_to = uris[0]

    if send_them_to[-3:] == "/$$":
        send_them_to = send_them_to[:-2] + text
        if len(request.query_string) > 0:
            send_them_to = send_them_to + "?" + request.query_string.decode(
                "utf-8")

    response = flask.redirect(send_them_to, code=redirect_code)
    response.headers['Cache-Control'] = f"max-age={ttl}"
    return response


@application.route('/<path:text>', methods=['GET', 'POST'])
def redirect_text(text):
    return redirect_user(flask.request, text)


@application.route('/', methods=['GET', 'POST'])
def redirect_none():
    return redirect_user(flask.request, "")


if __name__ == "__main__":
    application.run()

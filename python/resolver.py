#! /usr/bin/python3
# (c) Copyright 2019-2022, James Stevens ... see LICENSE for details
# Alternative license arrangements possible, contact me for more information
""" module to resolve DNS queries into DoH JSON objects """

from syslog import syslog
import socket
import select
import argparse
import dns
import dns.message
import dns.rdatatype
import random

import validation

DNS_MAX_RESP = 4096
MAX_TRIES = 10


class ResolverError(Exception):
    """ custom error """


class Resolver:
    """ build a DNS query & resolve it """

    def __init__(self, servers):
        self.next_id_item = 0

        self.id_list = [(int(x / 255), x % 255) for x in range(1, 65535)]
        random.shuffle(self.id_list)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.sock is None:
            raise ResolverError("Failed to open UDP client socket")

        for each_svr in servers:
            if not validation.is_valid_ipv4(each_svr):
                raise ResolverError("Invalid IP v4 Address for a Server")
        self.servers = servers

    def resolv(self, name, rdtype):
        self.qry_id = None
        self.expiry = 1
        self.tries = 0

        if isinstance(rdtype, str):
            try:
                rdtype = dns.rdatatype.from_text(rdtype)
            except dns.rdatatype.UnknownRdatatype:
                return False

        msg = dns.message.make_query(name, rdtype)
        self.question = bytearray(msg.to_wire())

        return self.run_resolver()

    def send_all(self):
        """ send the query to all servers """
        ret = False
        self.drain()
        for each_svr in self.servers:
            try:
                sent_len = self.sock.sendto(self.question, (each_svr, 53))
                ret = ret or (sent_len == len(self.question))
            except Exception as err:
                syslog(str(err))

        return ret  # True if at least one worked

    def send(self):
        """ send the DNS query out """
        if self.question is None:
            return None

        self.qry_id = self.id_list[self.next_id_item]
        self.next_id_item = self.next_id_item + 1
        if self.next_id_item >= len(self.id_list):
            self.next_id_item = 0

        self.question[0] = self.qry_id[0]
        self.question[1] = self.qry_id[1]

        return self.send_all()

    def match_id(self, reply):
        """ check the DNS quiery Id field matches what we asked """
        return (self.qry_id is not None and reply[0] == self.qry_id[0]
                and reply[1] == self.qry_id[1])

    def run_resolver(self):
        """ look for dns UDP response and read it """

        while self.tries < MAX_TRIES:
            if not self.send():
                return None

            while True:
                rlist, _, _ = select.select([self.sock], [], [], self.expiry)
                if len(rlist) <= 0:
                    break

                reply, (addr, _) = self.sock.recvfrom(DNS_MAX_RESP)
                if self.match_id(reply):
                    return dns.message.from_wire(reply)

            self.expiry += int(self.expiry / 2) if self.expiry > 2 else 1
            self.tries += 1

        return None

    def drain(self):
        while True:
            rlist, _, _ = select.select([self.sock], [], [], 0)
            if len(rlist) <= 0:
                return
            _, (_, _) = self.sock.recvfrom(DNS_MAX_RESP)

    def close(self):
        self.drain()
        self.sock.close()


def main():
    """ main """
    parser = argparse.ArgumentParser(
        description='This is a wrapper to test the resolver code')
    parser.add_argument("-s",
                        "--servers",
                        default="8.8.8.8 1.1.1.1",
                        help="Resolvers to query")
    parser.add_argument("-n",
                        "--name",
                        default="jrcs.net",
                        help="Name to query for")
    parser.add_argument("-t",
                        "--rdtype",
                        default="soa",
                        help="RR Type to query for")
    args = parser.parse_args()

    qry = Resolver(args.servers.split(" "))
    msg = qry.resolv(args.name, args.rdtype)
    print("RC:", msg.rcode(), msg.flags)
    print("QR:", msg.question)
    print("AN:", msg.answer)
    for rr in msg.answer:
        for i in rr:
            print(f"    >{i.to_text()}<")
    print("AT:", msg.authority)

    qry.close()


if __name__ == "__main__":
    main()

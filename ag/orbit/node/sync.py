# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from .db import SyncDB, TokenDB
from .. import API

from bitcoinrpc.authproxy import AuthServiceProxy


class Process():

    BCH_TO_SAT_MULTIPLIER = 100000000

    def __init__(self, host='localhost', port=8332, user=None, password=None):
        url = 'http://'
        if user is not None:
            url += user
            if password is not None:
                url += ':' + password
            url += '@'
        url += '{}:{}'.format(host, port)

        self.api = API()
        if self.api.version.major != 0:
            raise ValueError('this version of the ORBIT API is not supported: {}'.format(self.orbit.version))

        self.rpc = AuthServiceProxy(url)
        self.sync = SyncDB()
        self.tokens = TokenDB()

        self.info = None
        self.refresh()

    def close(self):
        self.tokens.close()
        self.sync.close()
        #self.rpc.close()

    def refresh(self):
        prev = None
        if self.info is not None:
            prev = self.info['blocks']

        self.info = self.rpc.getblockchaininfo()
        print('last BCH block sync: {}'.format(self.info['blocks']))

        self.last = self.sync.get_last_block()
        print('last ORBIT block sync: {}'.format(self.last))

        if self.info['blocks'] == prev:
            return False
        else:
            return True

    def next(self):
        if self.last is None:
            cur = self.api.genesis
        else:
            cur = self.last + 1

        if cur > self.info['blocks']:
            print('No more blocks')
            return None

        print('processing block number {}'.format(cur))

        # FIXME check confirmations

        blockhash = self.rpc.getblockhash(cur)
        block = self.rpc.getblock(blockhash)

        if self.info['pruned']:
            # requires a recent Bitcoin-ABC node that includes the patch for lookups by txhash and blockhash
            txs = self.rpc.batch_([ [ "getrawtransaction", txhash, True, block['hash'] ] for txhash in block['tx'] ])
        else:
            txs = self.rpc.batch_([ [ "getrawtransaction", txhash, True ] for txhash in block['tx'] ])

        blockrow = None

        for tx in txs:
            txrow = None

            for vout in tx['vout']:
                asmhex = vout['scriptPubKey']['hex']

                if asmhex.startswith('6a'): # OP_RETURN
                    try:
                        orbit = self.api.parse(bytearray.fromhex(asmhex[4:])) # we skip the next byte too
                        
                        if orbit is not None:
                            print("    ORBIT {}: {}".format(tx['txid'], orbit))

                            if blockrow is None:
                                blockrow = self.sync.save_block(blockhash, cur)

                            if txrow is None:
                                txrow = self.sync.save_tx(tx['txid'], blockrow, tx['confirmations'])

                                for txin in tx['vin']:
                                    self.sync.save_txin(txin['txid'], txrow, txin['scriptSig']['asm'])

                                for txout in tx['vout']:
                                    script = txout['scriptPubKey']
                                    try:
                                        addresses = ','.join(script['addresses'])
                                    except KeyError:
                                        addresses = None

                                    self.sync.save_txout(txrow, int(txout['value'] * self.BCH_TO_SAT_MULTIPLIER),
                                            script['type'], addresses, script['asm'])

                    except ValueError as e:
                        print("    VOID {}: {}".format(tx['txid'], e))

        self.sync.set_last_block(cur)
        self.sync.commit()
        self.last = cur

        return cur


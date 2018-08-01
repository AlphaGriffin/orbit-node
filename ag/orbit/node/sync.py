# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from .. import API
from ..ops import *
from . import TokenError
from .db import TokenDB

from bitcoinrpc.authproxy import AuthServiceProxy


class Process():

    BCH_TO_SAT_MULTIPLIER = 100000000

    def __init__(self, url='http://localhost:8332'): # host='localhost', port=8332, user=None, password=None):
        #url = 'http://'
        #if user is not None:
        #    url += user
        #    if password is not None:
        #        url += ':' + password
        #    url += '@'
        #url += '{}:{}'.format(host, port)

        self.api = API()
        if self.api.version.major != 0:
            raise ValueError('this version of the ORBIT API is not supported: {}'.format(self.orbit.version))

        self.rpc = AuthServiceProxy(url, timeout=120)
        self.tokens = TokenDB()

        self.info = None
        self.refresh()

    def close(self):
        self.tokens.close()
        #self.rpc.close()

    def refresh(self):
        prev = None
        if self.info is not None:
            prev = self.info['blocks']

        self.info = self.rpc.getblockchaininfo()
        print('last BCH block sync: {}'.format(self.info['blocks']))

        self.last = self.tokens.get_last_block()
        print('last ORBIT block sync: {}'.format(self.last))

        last = self.last if self.last else self.api.genesis - 1
        print('blocks to sync: {}'.format(self.info['blocks'] - last))

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

        # FIXME check confirmations?

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
                        # FIXME: proper pushdata op check (future-proofing)
                        orbit = self.api.parse(bytearray.fromhex(asmhex[4:])) # we skip the next byte too (pushdata)

                    except ValueError as e:
                        print("    VOID {}: {}".format(tx['txid'], e))

                    if orbit is not None:
                        print("    ORBIT @ {}".format(tx['txid']))
                        print("        Token Address: {}".format(orbit[0]))
                        print("        {}".format(orbit[1]))

                        if blockrow is None:
                            blockrow = self.tokens.save_block(blockhash, cur)

                        if txrow is None:
                            txrow = self.tokens.save_tx(tx['txid'], blockrow, tx['confirmations'])

                            for txin in tx['vin']:
                                self.tokens.save_txin(txin['txid'], txrow, txin['scriptSig']['hex'])

                            for txout in tx['vout']:
                                script = txout['scriptPubKey']
                                try:
                                    addresses = ','.join(script['addresses'])
                                except KeyError:
                                    addresses = None

                                self.tokens.save_txout(txrow, int(txout['value'] * self.BCH_TO_SAT_MULTIPLIER),
                                        script['type'], addresses, script['hex'])

                        try:
                            self.op(orbit[0], orbit[1], txrow, blockrow)

                        except TokenError as e:
                            # note that we don't rollback the sql transaction; we might want to re-evaluate the data later
                            print("     !--VOIDED: {}".format(e))

        self.tokens.set_last_block(cur)
        self.tokens.commit()
        self.last = cur

        return cur

    def op(self, address, op, txrow, blockrow):
        signer_address = self.tokens.get_signer_address(txrow)

        if not signer_address:
            raise ValueError("Unable to determine signer's address from transaction inputs")

        if op.admin() == True:
            if signer_address != address:
                raise TokenError("Operation requires admin but no proof of ownership for token address in transaction")

        elif op.admin() == False:
            if signer_address == address:
                raise TokenError("Operation may not be used by admin but transaction indicates proof of ownership for token address")

        if isinstance(op, create.Create):
            self.tokens.token_create(address, txrow, blockrow,
                    op.supply, op.decimals, op.symbol, op.name, op.main_uri, op.image_uri)

        elif isinstance(op, transfer.Transfer):
            self.tokens.token_transfer(address, txrow, blockrow,
                    signer_address, op.to, op.units)

        else:
            raise ValueError("Unsupported token operation: {}".format(type(op)))


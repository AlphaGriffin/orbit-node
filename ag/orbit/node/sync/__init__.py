# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ... import API
from ...ops import Abstract, allocation, advertisement
from .. import TokenError
from ..db import TokenDB

from bitcoinrpc.authproxy import AuthServiceProxy

from sys import stdout


class Process():

    BCH_TO_SAT_MULTIPLIER = 100000000

    def __init__(self, url='http://localhost:8332', out=stdout): # host='localhost', port=8332, user=None, password=None):
        #url = 'http://'
        #if user is not None:
        #    url += user
        #    if password is not None:
        #        url += ':' + password
        #    url += '@'
        #url += '{}:{}'.format(host, port)

        self.out = out

        self.api = API()
        if self.api.version.major != 0:
            raise ValueError('this version of the ORBIT API is not supported: {}'.format(self.orbit.version))

        self.rpc = AuthServiceProxy(url, timeout=480)
        self.tokens = TokenDB(auto_commit=False)

        self.info = None

    def close(self):
        self.tokens.close()
        #self.rpc.close()

    def refresh(self):
        prev = None
        if self.info is not None:
            prev = self.info['blocks']

        self.info = self.rpc.getblockchaininfo()
        if self.out: print('last BCH block sync: {}'.format(self.info['blocks']), file=self.out)

        self.last = self.tokens.get_last_block()
        if self.out: print('last ORBIT block sync: {}'.format(self.last), file=self.out)

        last = self.last if self.last else self.api.launched - 1
        if self.out: print('blocks to sync: {}'.format(self.info['blocks'] - last), file=self.out)

        if self.info['blocks'] == prev:
            return False
        else:
            return True

    def get_info(self):
        if self.out: print("Collecting node information...", file=self.out)

        if self.out: print(file=self.out)
        if self.out: print("    ORBIT launch block: {}".format(self.api.launched), file=self.out)

        if self.out: print(file=self.out)
        if self.out: print('BCH node', file=self.out)
        info = self.rpc.getblockchaininfo()

        known = info['headers']
        if self.out: print("    Last known block: {}".format(known), file=self.out)

        completed = info['blocks']
        if self.out: print("    Last completed block: {}".format(completed), file=self.out)

        diff = known - completed
        if self.out: print("    Blocks to complete: {}".format(diff), file=self.out)

        pruned = info['pruned']
        if self.out: print("    Pruned? {}".format(pruned), file=self.out)

        if pruned:
            prune = info['pruneheight']
            if self.out: print("    Pruned at block: {}".format(prune), file=self.out)

        if self.out: print(file=self.out)
        if self.out: print('ORBIT node database', file=self.out)

        last = self.tokens.get_last_block()
        if self.out: print('    Last block sync: {}'.format(last), file=self.out)

        if not last:
            last = self.api.launched - 1

        diff = completed - last
        if self.out: print('    Blocks to sync: {}'.format(diff), file=self.out)

    def _chunks(self, data, size):
        for i in range(0, len(data), size):
            yield data[i:i+size]

    def next(self):
        if not self.info:
            self.refresh()

        if self.last is None:
            cur = self.api.launched
        else:
            cur = self.last + 1

        if cur > self.info['blocks']:
            if self.out: print('No more blocks', file=self.out)
            return None

        if self.out: print('processing block number {}'.format(cur), file=self.out)

        # FIXME check confirmations?

        blockhash = self.rpc.getblockhash(cur)
        block = self.rpc.getblock(blockhash)

        txcount = len(block['tx'])
        if self.out: print('    {} transaction{}...'.format(txcount, '' if txcount == 1 else 's'), end='', flush=True, file=self.out)

        # break into batches of 1,000
        txs = []
        txcount = 0
        txhashes = self._chunks(block['tx'], 1000)

        for txbatch in txhashes:
            if self.info['pruned']:
                # requires a recent Bitcoin-ABC node that includes the patch for lookups by txhash and blockhash
                txs.extend(self.rpc.batch_([ [ "getrawtransaction", txhash, True, block['hash'] ] for txhash in txbatch ]))
            else:
                txs.extend(self.rpc.batch_([ [ "getrawtransaction", txhash, True ] for txhash in txbatch ]))

            txcount += len(txbatch)
            if self.out: print('{}...'.format(txcount), end='', flush=True, file=self.out)

        if self.out: print('validating...', file=self.out)
        blockrow = self.tokens.save_block(blockhash, cur)

        registrations = self.tokens.get_active_registrations_map(blockrow)

        for tx in txs:
            #if i % 5000 == 0:
            #    if self.out: print('{}...'.format(i), end='', flush=True, file=self.out)

            txrow = None
            payments = []

            for vout in tx['vout']:
                value = vout['value']
                asmhex = vout['scriptPubKey']['hex']

                if asmhex.startswith('6a'): # OP_RETURN
                    try:
                        # FIXME: proper pushdata op and length check
                        orbit = self.api.parse(bytearray.fromhex(asmhex[4:])) # we skip the next byte too (pushdata)

                    except ValueError as e:
                        if self.out: print("        VOID {}: {}".format(tx['txid'], e), file=self.out)

                    if orbit is not None:
                        if self.out: print("        ORBIT @ {}".format(tx['txid']), file=self.out)
                        if self.out: print("            Token Address: {}".format(orbit[0]), file=self.out)
                        if self.out: print("            {}".format(orbit[1]), file=self.out)

                        if txrow is None:
                            txrow = self.save_tx_row(tx, blockrow)

                        try:
                            self.op(orbit[0], orbit[1], txrow, blockrow, registrations)

                        except TokenError as e:
                            # note that we don't rollback the sql transaction; we might want to re-evaluate the data later
                            if self.out: print("         !--VOIDED: {}".format(e), file=self.out)

                elif value:
                    addresses = vout['scriptPubKey']['addresses']

                    # because payments occur before OP_RETURN, we hold them to process after the vout loop
                    payments.append([addresses, value])

            for payment in payments:
                addresses = payment[0]
                value = payment[1]

                for address in addresses:
                    if address in registrations:
                        if len(addresses) > 1:
                            raise ValueError('Not expecting multiple addresses for a transaction with value')

                        if txrow is None:
                            txrow = self.save_tx_row(tx, blockrow)

                        regs_for_token = registrations[address]
                        from_address = self.tokens.get_signer_address(txrow)
                        reg_rowid = regs_for_token[from_address]

                        self.tokens.registration_payment(txrow, blockrow, reg_rowid, value)

        self.tokens.process_advertisements(blockrow)

        orbit = self.tokens.hash(blockrow)
        if self.out: print('    -> {}'.format(orbit), file=self.out)

        self.tokens.set_last_block(cur)
        self.tokens.commit()
        self.last = cur

        return cur

    def save_tx_row(self, tx, blockrow):
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

        return txrow

    def op(self, address, op, txrow, blockrow, registrations):
        signer_address = self.tokens.get_signer_address(txrow)

        if not signer_address:
            raise ValueError("Unable to determine signer's address from transaction inputs")

        if op.admin() == True:
            if signer_address != address:
                raise TokenError("Operation requires admin but no proof of ownership for token address in transaction")

        elif op.admin() == False:
            if signer_address == address:
                raise TokenError("Operation may not be used by admin but transaction indicates proof of ownership for token address")

        if isinstance(op, allocation.Create):
            self.tokens.token_create(address, txrow, blockrow,
                    op.supply, op.decimals, op.symbol, op.name, op.main_uri, op.image_uri)

        elif isinstance(op, allocation.Transfer):
            self.tokens.token_transfer(address, txrow, blockrow,
                    signer_address, op.to, op.units)

        elif isinstance(op, advertisement.Advertise):
            self.tokens.token_advertise(address, txrow, blockrow,
                    op.exchange_rate, op.units_avail, op.units_min, op.units_max, op.block_begin, op.block_end,
                    op.block_deliver, op.preregister)

        elif isinstance(op, advertisement.Cancel):
            raise NotImplementedError()

        elif isinstance(op, advertisement.Register):
            rowid = self.tokens.token_register(address, txrow, blockrow, signer_address, op.units_max)

            if address in registrations:
                token_regs = registrations[address]
            else:
                token_regs = {}
                registrations[address] = token_regs

            if signer_address in token_regs:
                raise ValueError("Already have an active registration for this user and token")

            token_regs[signer_address] = rowid

        elif isinstance(op, advertisement.Unregister):
            rowid = self.tokens.token_unregister(address, txrow, blockrow, signer_address)

        else:
            raise ValueError("API version mismatch? Unsupported token operation: {}".format(type(op)))


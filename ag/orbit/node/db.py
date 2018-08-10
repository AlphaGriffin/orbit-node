# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from . import config, TokenError

from bitcash.format import public_key_to_address

from os import path
import sqlite3
from hashlib import sha256


class TokenDB:

    def __init__(self, auto_commit=True):
        isolation = 'EXCLUSIVE' if not auto_commit else None
        conn = sqlite3.connect(path.join(config.dir, 'tokens.db'), isolation_level=isolation)

        conn.execute('''CREATE TABLE IF NOT EXISTS status (
                            key TEXT NOT NULL PRIMARY KEY,
                            value TEXT
                        )''')

        #
        # Block and tx data
        #

        conn.execute('''CREATE TABLE IF NOT EXISTS block (
                            hash TEXT NOT NULL PRIMARY KEY,
                            height INTEGER NOT NULL,
                            orbit BLOB
                        )''')
        conn.execute('''CREATE INDEX IF NOT EXISTS idx_block_height ON block (height)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS tx (
                            hash TEXT NOT NULL PRIMARY KEY,
                            block INTEGER NOT NULL,
                            confirmations INTEGER NOT NULL
                        )''')
        conn.execute('''CREATE INDEX IF NOT EXISTS idx_tx_block ON tx (block)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS txin (
                            hash TEXT NOT NULL PRIMARY KEY,
                            tx INTEGER NOT NULL,
                            asmhex TEXT NOT NULL
                        )''')
        conn.execute('''CREATE INDEX IF NOT EXISTS idx_txin_tx ON txin (tx)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS txout (
                            tx INTEGER NOT NULL,
                            value INTEGER NOT NULL,
                            type TEXT NOT NULL,
                            addresses TEXT,
                            asmhex TEXT NOT NULL
                        )''')
        conn.execute('''CREATE INDEX IF NOT EXISTS idx_txout_tx ON txout (tx)''')

        #
        # Tokens and balances
        #

        conn.execute('''CREATE TABLE IF NOT EXISTS token (
                            address TEXT NOT NULL PRIMARY KEY,
                            tx INTEGER NOT NULL,
                            created INTEGER NOT NULL,
                            updated INTEGER NOT NULL,
                            supply INTEGER NOT NULL,
                            decimals INTEGER NOT NULL,
                            symbol TEXT NOT NULL,
                            name TEXT,
                            main_uri TEXT,
                            image_uri TEXT
                        )''')
        conn.execute('''CREATE INDEX IF NOT EXISTS idx_token_symbol ON token (symbol)''')
        conn.execute('''CREATE INDEX IF NOT EXISTS idx_token_updated ON token (updated)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS balance (
                            address TEXT NOT NULL,
                            token INTEGER NOT NULL,
                            updated INTEGER NOT NULL,
                            units INTEGER NOT NULL,
                            available INTEGER NOT NULL,
                            PRIMARY KEY (address, token)
                        )''')
        conn.execute('''CREATE INDEX IF NOT EXISTS idx_balance_updated ON balance (updated)''')

        #
        # Events
        # TODO: will need to remove primary key from tx if we ever support multiple operations in one transaction
        #

        conn.execute('''CREATE TABLE IF NOT EXISTS transfer (
                            tx INTEGER NOT NULL PRIMARY KEY,
                            created INTEGER NOT NULL,
                            addr_from TEXT NOT NULL,
                            addr_to TEXT NOT NULL,
                            units INTEGER
                        )''')
        conn.execute('''CREATE INDEX IF NOT EXISTS idx_transfer_created ON transfer (created)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS advertisement (
                            tx INTEGER NOT NULL PRIMARY KEY,
                            token INTEGER NOT NULL,
                            created INTEGER NOT NULL,
                            updated INTEGER NOT NULL,
                            finished INTEGER,
                            begins INTEGER NOT NULL,
                            ends INTEGER,
                            delivers INTEGER NOT NULL,
                            available INTEGER NOT NULL,
                            claimed INTEGER NOT NULL,
                            rate INTEGER,
                            minimum INTEGER NOT NULL,
                            maximum INTEGER NOT NULL,
                            preregister TEXT NULL
                        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS registration (
                            tx INTEGER NOT NULL PRIMARY KEY,
                            address TEXT NOT NULL,
                            advertisement INTEGER NOT NULL,
                            created INTEGER NOT NULL,
                            updated INTEGER NOT NULL,
                            finished INTEGER,
                            maximum INTEGER NOT NULL,
                            payments INTEGER NOT NULL,
                            claimed INTEGER NOT NULL
                        )''')

        keys = conn.execute('''SELECT key FROM status''').fetchall()
        self._init_status(conn, keys, 'height')

        conn.commit()
        self.conn = conn

    @classmethod
    def _init_status(self, conn, keys, key):
        for k in keys:
            if k[0] == key:
                return

        conn.execute('''INSERT INTO status (key) VALUES (?)''', (key,))

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def _set_status(self, key, value):
        self.conn.execute('''UPDATE status SET value = ? WHERE key = ?''', (value, key))

    def _get_status(self, key):
        return self.conn.execute('''SELECT value FROM status WHERE key = ?''', (key,)).fetchone()[0]

    def get_last_block(self):
        height = self._get_status('height')
        if height is None:
            return None

        return int(height)

    def set_last_block(self, height):
        self._set_status('height', height)

    def save_block(self, blockhash, height):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO block
                          (hash, height)
                          VALUES (?, ?)''',
                          (blockhash, height))
        return cursor.lastrowid

    def save_tx(self, txhash, block, confirmations):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO tx
                          (hash, block, confirmations)
                          VALUES (?, ?, ?)''',
                          (txhash, block, confirmations))
        return cursor.lastrowid

    def save_txin(self, txhash, tx, asmhex):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO txin
                          (hash, tx, asmhex)
                          VALUES (?, ?, ?)''',
                          (txhash, tx, asmhex))
        return cursor.lastrowid

    def save_txout(self, tx, value, stype, addresses, asmhex):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO txout
                          (tx, value, type, addresses, asmhex)
                          VALUES (?, ?, ?, ?, ?)''',
                          (tx, value, stype, addresses, asmhex))
        return cursor.lastrowid

    def get_signer_address(self, txrow):
        txins = self.conn.execute('''SELECT asmhex FROM txin WHERE tx = ?''', (txrow,)).fetchall()
        address = None

        for txin in txins:
            asmhex = txin[0]
            asm = bytes.fromhex(asmhex)

            sig_size = int.from_bytes(asm[0:1], 'little')
            pubkey_size = int.from_bytes(asm[sig_size+1:sig_size+2], 'little')
            pubkey = asm[sig_size + 2 : sig_size + pubkey_size + 2]
            pubkey_address = public_key_to_address(pubkey)

            if not address:
                address = pubkey_address

            elif address != pubkey_address:
                raise ValueError("Multiple signer keys are present in the transaction inputs")

        return address

    def token_create(self, address, tx, block, supply, decimals, symbol, name=None, main_uri=None, image_uri=None):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''INSERT INTO token
                              (address, tx, created, updated, supply, decimals, symbol, name, main_uri, image_uri)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (address, tx, block, block, supply, decimals, symbol, name, main_uri, image_uri))
            tokenrow = cursor.lastrowid

        except sqlite3.IntegrityError as e:
            raise TokenError("A token is already defined at this address: {}".format(e))

        # no try/except here... it's a critical error to be able to insert a token yet already have a blance for it
        cursor.execute('''INSERT INTO balance
                          (address, token, updated, units, available)
                          VALUES (?, ?, ?, ?, ?)''',
                          (address, tokenrow, block, supply, supply))

        return tokenrow

    def _get_tokenrow(self, cursor, address):
        token = cursor.execute('''SELECT rowid FROM token WHERE address = ?''', (address,)).fetchone()

        if token is None:
            raise TokenError("No token defined at the specified address")

        return token[0]

    def _get_balance(self, cursor, tokenrow, address, total=False):
        balance = cursor.execute('''SELECT units, available FROM balance
                                    WHERE token = ? AND address = ?''',
                                    (tokenrow, address)).fetchone()

        if not balance:
            return None

        return balance[0] if total else balance[1]

    def token_transfer(self, address, txrow, blockrow, from_address, to_address, units):
        cursor = self.conn.cursor()

        if from_address == to_address:
            raise TokenError("Transfer to address must be different than transfer from address")

        tokenrow = self._get_tokenrow(cursor, address)

        # validate source balance
        balance = self._get_balance(cursor, tokenrow, from_address)

        if balance is None:
            raise TokenError("No balance for this token")

        if balance < units:
            raise TokenError("Insufficient available balance for this transfer")

        # update source balance
        cursor.execute('''UPDATE balance
                          SET updated = ?, units = units - ?, available = available - ?
                          WHERE token = ? AND address = ?''',
                          (blockrow, units, units, tokenrow, from_address))


        # update destination balance
        balance = self._get_balance(cursor, tokenrow, to_address)

        if balance is None:
            cursor.execute('''INSERT INTO balance
                              (address, token, updated, units, available)
                              VALUES (?, ?, ?, ?, ?)''',
                              (to_address, tokenrow, blockrow, units, units))

        else:
            cursor.execute('''UPDATE balance
                              SET updated = ?, units = units + ?, available = available + ?
                              WHERE token = ? AND address = ?''',
                              (blockrow, units, units, tokenrow, to_address))
 
        # save transfer event
        cursor.execute('''INSERT INTO transfer
                          (tx, created, addr_from, addr_to, units)
                          VALUES (?, ?, ?, ?, ?)''',
                          (txrow, blockrow, from_address, to_address, units))

        return cursor.lastrowid

    def token_advertise(self, address, txrow, blockrow, exchange_rate=None, units_avail=None, units_min=None, units_max=None,
            block_begin=None, block_end=None, block_deliver=None, preregister=False):

        cursor = self.conn.cursor()

        tokenrow = self._get_tokenrow(cursor, address)
        height = cursor.execute('''SELECT height FROM block WHERE rowid = ?''', (blockrow,)).fetchone()[0]

        # block validation

        if block_begin:
            if block_begin <= height:
                raise TokenError("Beginning block must occur after the advertisement block")
        else:
            block_begin = height + 1

        if block_end:
            if block_end < block_begin:
                raise TokenError("Ending block must be on or after the beginning block")

        if block_deliver:
            if block_deliver < block_begin:
                raise TokenError("Delivery block must be on or after the beginning block")
        else:
            block_deliver = block_begin

        # existing advertisement checks

        advertisement = cursor.execute('''SELECT 1 FROM advertisement
                                           WHERE token = ? AND finished IS NULL AND begins <= ?
                                               AND (ends IS NULL OR ends >= ?)
                                           LIMIT 1''',
                                               (tokenrow, block_begin, block_begin)).fetchone()

        if advertisement:
            raise TokenError("An existing advertisement is currently open")

        advertisement = cursor.execute('''SELECT begins FROM advertisement
                                           WHERE token = ? AND finished IS NULL AND begins > ?
                                           ORDER BY begins LIMIT 1''',
                                           (tokenrow, block_begins)).fetchone()

        if advertisement:
            if block_end:
                if block_end >= advertisement[0]:
                    raise TokenError("An existing advertisement exists that begins before this one ends")
            else:
                raise TokenError("An existing advertisement begins in the future but this one has no ending block")

        advertisement = cursor.execute("""SELECT 1 FROM advertisement
                                           WHERE token = ? AND finished IS NULL AND begins > ? AND preregister = 'Y'""",
                                           (tokenrow, block_begins)).fetchone()

        if advertisement:
            raise TokenError("An existing future advertisement allows preregistration")

        # available balance validation and update

        balance = self._get_balance(cursor, address)

        if units_avail:
            if balance < units_avail:
                raise TokenError("Insufficient available balance to make available")
        else:
            units_avail = balance

        if units_min:
            if units_min > units_avail:
                raise TokenError("Insufficient available balance for the specified minimum units")
        else:
            units_min = 1

        if units_max:
            # note that it's not an error if units_max > units_avail... this allows a per-user maximum to be
            #   set when units_avail might not be specified
            pass
        else:
            units_max = units_avail

        cursor.execute('''UPDATE balance
                          SET updated = ?, available = available - ?
                          WHERE token = ? AND address = ?''',
                          (blockrow, units_avail, tokenrow, address))

        # save advertise event
 
        cursor.execute('''INSERT INTO advertisement
                          (tx, token, created, updated, begins, ends, delivers, available, dispensed,
                              rate, minimum, maximum, preregister)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (txrow, tokenrow, blockrow, blockrow, block_begin, block_end, block_deliver,
                              units_avail, 0, units_min, units_max,
                              'Y' if preregister else None))

        return cursor.lastrowid

    def token_advertise_cancel(self, address, txrow, blockrow, txhash):
        cursor = self.conn.cursor()

        tokenrow = self._get_tokenrow(cursor, address)

        # validate advertisement

        advertisement = cursor.execute('''SELECT a.rowid, a.token, a.finished, a.available, a.claimed
                                          FROM tx
                                          LEFT JOIN advertisement a ON a.tx = tx.rowid
                                          WHERE tx.hash = ?''',
                                          (txhash,)).fetchone()

        if not advertisement:
            raise TokenError("No advertisement exists for the given tx hash")

        if tokenrow != advertisement[1]:
            raise TokenError("Advertisement at the specified tx hash does not match the token indicated")

        if advertisement[2] is not None:
            raise TokenError("The advertisement has already finished")

        # validate registrations

        registrations = cursor.execute('''SELECT 1 FROM registration
                                          WHERE advertisement = ?
                                          LIMIT 1''',
                                          (advertisement[0],))

        if registrations:
            #FIXME: just check that 'claimed' == 0 instead?
            raise TokenError("There have already been registrations for this advertisement; it cannot be cancelled")

        if advertisement[4] != 0:
            raise ValueError("This advertisement indicates claims but no registrations were found")

        # close advertisement and make balance available again

        cursor.execute('''UPDATE advertisement
                          SET updated = ?, finished = ?
                          WHERE rowid = ?''',
                          (blockrow, blockrow, advertisement[0]))

        cursor.execute('''UPDATE balance
                          SET updated = ?, available = available + ?
                          WHERE token = ? AND address = ?''',
                          (blockrow, advertisement[3], tokenrow, address))

        return advertisement[0]

    def get_eligible_advertisement_row(self, cursor, tokenrow, height):
        advertisement = None

        advertisements = cursor.execute('''SELECT rowid FROM advertisement
                                           WHERE token = ? AND finished IS NULL AND begins <= ?
                                               AND (ends IS NULL OR ends >= ?)''',
                                               (tokenrow, height, height)).fetchall()

        if advertisements:
            if len(advertisements) > 1:
                raise ValueError("There are multiple active advertisements")

            advertisement = advertisements[0]

        advertisements = cursor.execute("""SELECT rowid FROM advertisement
                                           WHERE token = ? AND finished IS NULL AND begins > ? AND preregister = 'Y'""",
                                           (tokenrow, height)).fetchall()

        if advertisements:
            if advertisement:
                raise ValueError("There is an active advertisement but also a future advertisement allowing preregistration")

            if len(advertisements) > 1:
                raise ValueError("There are multiple future advertisements allowing preregistration")

            advertisement = advertisements[0]

        if not advertisement:
            raise TokenError("There is no active advertisement or future advertisement allowing preregistration")

        return advertisement[0]

    def token_register(self, address, txrow, blockrow, user_address, units_max=None):
        cursor = self.conn.cursor()

        tokenrow = self._get_tokenrow(cursor, address)
        height = cursor.execute('''SELECT height FROM block WHERE rowid = ?''', (blockrow,)).fetchone()[0]
        advertisement = self.get_eligible_advertisement_row(cursor, tokenrow, height)

        advertisement = cursor.execute('''SELECT rowid, minimum, maximum, rate, available, claimed, delivers
                                          FROM advertisement
                                          WHERE rowid = ?''',
                                          (advertisement,)).fetchone()

        if units_max < advertisement[1]:
            raise TokenError('Specified maximum is less than the advertisement user-minimum required')

        registrations = cursor.execute('''SELECT SUM(maximum)
                                          FROM registration
                                          WHERE address = ? and advertisement = ?''',
                                          (user_address, advertisement[0])).fetchone()

        max_remains = advertisement[2]
        if registrations:
            max_remains -= registrations[0]

            if max_remains < 1:
                raise TokenError('Maximum per-user units has already been registered')

        unclaimed = advertisement[4] - advertisement[5]
        if unclaimed < max_remains:
            max_remains = unclaimed

        if units_max > max_remains:
            units_max = max_remains

        if not advertisement[3]: # free faucet
            units = units_max
            available = (height > advertisement[6])
            # note that if height == delivers then process_advertisements() will make the units available

            # update source balance
            cursor.execute('''UPDATE balance
                              SET updated = ?, units = units - ?
                              WHERE token = ? AND address = ?''',
                              (blockrow, units, tokenrow, address))

            # update destination balance
            balance = self._get_balance(cursor, tokenrow, user_address)

            if balance is None:
                cursor.execute('''INSERT INTO balance
                                  (address, token, updated, units, available)
                                  VALUES (?, ?, ?, ?, ?)''',
                                  (user_address, tokenrow, blockrow, units, units if available else 0))

            else:
                cursor.execute('''UPDATE balance
                                  SET updated = ?, units = units + ?, available = available + ?
                                  WHERE token = ? AND address = ?''',
                                  (blockrow, units, units if available else 0, tokenrow, user_address))

            cursor.execute('''UPDATE advertisement
                              SET updated = ?, claimed = claimed + ?
                              WHERE rowid = ?''',
                              (blockrow, units, advertisement[0]))
 
            # save transfer event
            cursor.execute('''INSERT INTO transfer
                              (tx, created, addr_from, addr_to, units)
                              VALUES (?, ?, ?, ?, ?)''',
                              (txrow, blockrow, address, user_address, units))

        else:
            units = 0

        cursor.execute('''INSERT INTO registration
                          (tx, address, advertisement, created, updated, finished, maximum, payments, claimed)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (txrow, user_address, advertisement[0], blockrow, blockrow,
                              blockrow if advertisement[3] else None, units_max, 0, units))

        return cursor.lastrowid

    def token_unregister(self, address, txrow, blockrow, user_address):
        cursor = self.conn.cursor()

        tokenrow = self._get_tokenrow(cursor, address)
        height = cursor.execute('''SELECT height FROM block WHERE rowid = ?''', (blockrow,)).fetchone()[0]
        advertisement = self.get_eligible_advertisement_row(cursor, tokenrow, height)

        registrations = cursor.execute('''SELECT rowid, token FROM registration
                                          WHERE address = ? AND advertisement = ? AND finished IS NULL''',
                                          (user_address, advertisement)).fetchall()

        if not registrations:
            raise TokenError("No active registration was found")

        if len(registrations) > 1:
            raise ValueError("Multiple active registrations found")

        registration = registrations[0]

        if registration[1] != tokenrow:
            raise ValueError("This registration token does not match the advertisement token")

        cursor.execute('''UPDATE registration
                          SET updated = ?, finished = ?
                          WHERE rowid = ?''',
                          (blockrow, blockrow, registration[0]))

        return registration[0]

    def get_active_registrations_map(self, blockrow):
        cursor = self.conn.cursor()

        height = cursor.execute('''SELECT height FROM block WHERE rowid = ?''', (blockrow,)).fetchone()[0]

        registrations = cursor.execute('''SELECT t.address, r.address, r.rowid
                                          FROM registration r
                                          LEFT JOIN advertisement a ON a.rowid = r.advertisement
                                          LEFT JOIN token t ON t.rowid = a.token
                                          WHERE r.finished IS NULL AND a.finished IS NULL AND a.begins <= ?''',
                                          (height,)).fetchall()

        reg_map = {}

        if registrations:
            for registration in registrations:
                try:
                    records = reg_map[registration[0]]
                except AttributeError:
                    records = {}
                    reg_map[registration[0]] = records

                try:
                    rowid = records[registration[1]]
                    raise ValueError('Already have an active registration for this user and token')
                except AttributeError:
                    records[registration[1]] = registration[2]

        return reg_map

    def registration_payment(self, txrow, blockrow, rowid, value):
        cursor = self.conn.cursor()

        height = cursor.execute('''SELECT height FROM block WHERE rowid = ?''', (blockrow,)).fetchone()[0]

        details = cursor.execute('''SELECT r.address, r.maximum, r.payments, r.claimed,
                                        a.rowid, a.delivers, a.available, a.claimed, a.rate, a.minimum, a.maximum,
                                        t.rowid, t.address
                                    FROM registration r
                                    LEFT JOIN advertisement a ON a.rowid = r.advertisement
                                    LEFT JOIN token t ON t.rowid = a.token
                                    WHERE r.rowid = ?''',
                                    (rowid,)).fetchone()

        claimed = cursor.execute('''SELECT SUM(claimed)
                                    FROM registration
                                    WHERE address = ? AND advertisement = ? AND rowid <> ?''',
                                    (details[0], details[4], rowid)).fetchone()[0]

        ad_remaining = details[6] - details[7]
        user_remaining = details[10] - claimed - details[3]

        if ad_remaining < user_remaining:
            user_remaining = ad_remaining

        if details[1] < user_remaining:
            user_remaining = details[1]

        payments = details[2] + value
        rate = details[8]

        if rate:
            if rate < 0:
                units = payments // (-1 * rate)
            else:
                units = payments * rate

            if units < details[9]:
                units = 0
            else:
                units -= details[3]

            if units > user_remaining:
                units = user_remaining

        else:
            units = user_remaining

        if units > 0:
            available = (height > details[5])
            # note that if height == delivers then process_advertisements() will make the units available

            # update source balance
            cursor.execute('''UPDATE balance
                              SET updated = ?, units = units - ?
                              WHERE token = ? AND address = ?''',
                              (blockrow, units, details[11], details[12]))

            # update destination balance
            balance = self._get_balance(cursor, details[11], details[0])

            if balance is None:
                cursor.execute('''INSERT INTO balance
                                  (address, token, updated, units, available)
                                  VALUES (?, ?, ?, ?, ?)''',
                                  (details[0], details[11], blockrow, units, units if available else 0))

            else:
                cursor.execute('''UPDATE balance
                                  SET updated = ?, units = units + ?, available = available + ?
                                  WHERE token = ? AND address = ?''',
                                  (blockrow, units, units if available else 0, details[11], details[0]))
 
            # save transfer event
            cursor.execute('''INSERT INTO transfer
                              (tx, created, addr_from, addr_to, units)
                              VALUES (?, ?, ?, ?, ?)''',
                              (txrow, blockrow, details[12], details[0], units))

            finished = (units == (details[1] - details[3]))

            cursor.execute('''UPDATE registration
                              SET updated = ?, finished = ?, payments = ?, claimed = claimed + ?
                              WHERE rowid = ?''',
                              (blockrow, blockrow if finished else None, payments, units, rowid))

            cursor.execute('''UPDATE advertisement
                              SET updated = ?, claimed = claimed + ?
                              WHERE rowid = ?''',
                              (blockrow, units, details[4]))

    def process_advertisements(self, blockrow):
        cursor = self.conn.cursor()

        height = cursor.execute('''SELECT height FROM block WHERE rowid = ?''', (blockrow,)).fetchone()[0]

        deliveries = cursor.execute('''SELECT rowid, token
                                       FROM advertisement
                                       WHERE delivers = ?''',
                                       (blockrow,)).fetchall()

        if deliveries:
            for delivery in deliveries:
                registrations = cursor.execute('''SELECT rowid, address, claimed
                                                  FROM registration
                                                  WHERE advertisement = ?
                                                  ORDER BY address''',
                                                  (delivery[0],)).fetchall()

                if registrations:
                    last_address = None
                    user_claimed = 0

                    for registration in registrations:
                        if last_address is None:
                            last_address = registration[1]

                        if last_address == registration[1]:
                            user_claimed += registration[2]
                        else:
                            cursor.execute('''UPDATE balance
                                              SET updated = ?, available = available + ?
                                              WHERE token = ? AND address = ?''',
                                              (blockrow, user_claimed, delivery[1], last_address))

                            last_address = registration[1]
                            user_claimed = registration[2]

                    cursor.execute('''UPDATE balance
                                      SET updated = ?, available = available + ?
                                      WHERE token = ? AND address = ?''',
                                      (blockrow, user_claimed, delivery[1], last_address))

        ads_to_close = cursor.execute('''SELECT a.rowid, a.available - a.claimed,
                                             t.rowid, t.address
                                         FROM advertisement a
                                         LEFT JOIN token t ON t.rowid = a.token
                                         WHERE a.finished IS NULL AND a.claimed = a.available OR a.ends = ?''',
                                         (height,)).fetchall()

        if ads_to_close:
            for advertisement in ads_to_close:
                cursor.execute('''UPDATE registration
                                  SET updated = ?, finished = ?
                                  WHERE advertisement = ? AND finished IS NULL''',
                                  (blockrow, blockrow, advertisement[0]))

                cursor.execute('''UPDATE advertisement
                                  SET updated = ?, finished = ?
                                  WHERE rowid = ?''',
                                  (blockrow, blockrow, advertisement[0]))

                make_available = advertisement[1]
                if make_available:
                    cursor.execute('''UPDATE balance
                                      SET updated = ?, available = available + ?
                                      WHERE token = ? AND address = ?''',
                                      (blockrow, make_available, advertisement[2], advertisement[3]))

    def get_user_tokens(self, address):
        return [{
            "address": row[0],
            "symbol": row[1],
            "decimals": row[2],
            "name": row[3],
            "units": row[4],
            "available": row[5]
            } for row in self.conn.execute('''
                SELECT t.address, t.symbol, t.decimals, t.name, b.units, b.available
                FROM balance b
                LEFT JOIN token t ON t.rowid = b.token
                WHERE b.address = ?''',
                (address,)).fetchall()]

    def hash(self, blockrow):
        cursor = self.conn.cursor()

        blocks = cursor.execute('''SELECT height, rowid, hash FROM block
                                   WHERE orbit IS NULL
                                   ORDER BY height''').fetchall()

        if not blocks:
            return None

        if len(blocks) > 1:
            raise ValueError('Multiple unhashed orbits detected... hash() must be called concurrently as blocks are inserted')

        block = blocks[0]
        height = block[0]
        blockrow = block[1]

        block_prev = cursor.execute('''SELECT orbit FROM block
                                       WHERE height = ?''',
                                       (height - 1,)).fetchone()

        # hash the block and append to previous block hash

        if block_prev:
            data = block_prev[0]

        else:
            not_launch = cursor.execute('''SELECT 1 FROM block
                                            WHERE height < ? LIMIT 1''',
                                            (height,)).fetchone()

            if not_launch:
                raise ValueError('Missing block: {}'.format(height - 1))

            data = b'\x42\x81' # special sequence to indicate launch

        data += self._hash_cols(block)

        # tokens and balances

        data += self._hash_rows(cursor.execute('''SELECT * FROM token
                                                  WHERE updated = ?
                                                  ORDER BY rowid''',
                                                  (blockrow,)))

        data += self._hash_rows(cursor.execute('''SELECT * FROM balance
                                                  WHERE updated = ?
                                                  ORDER BY rowid''',
                                                  (blockrow,)))

        # events

        data += self._hash_rows(cursor.execute('''SELECT * FROM transfer
                                                  WHERE created = ?
                                                  ORDER BY rowid''',
                                                  (blockrow,)))

        data += self._hash_rows(cursor.execute('''SELECT * FROM advertisement
                                                  WHERE updated = ?
                                                  ORDER BY rowid''',
                                                  (blockrow,)))

        data += self._hash_rows(cursor.execute('''SELECT * FROM registration
                                                  WHERE updated = ?
                                                  ORDER BY rowid''',
                                                  (blockrow,)))

        # final hash and save

        orbit = self._hash(data)

        cursor.execute('''UPDATE block
                          SET orbit = ?
                          WHERE rowid = ?''',
                          (sqlite3.Binary(orbit), blockrow))

        return orbit

    def _hash_rows(self, rows):
        if not rows:
            return b'\x00'

        data = b'\x01'

        for row in rows:
            data += self._hash_cols(row)

        data += b'\xFF'

        return self._hash(data)

    def _hash_cols(self, cols):
        data = '['

        for col in cols:
            if col:
                data += '{}'.format(col)
            data += '|'

        data += ']'

        return self._hash(data.encode('utf-8'))

    def _hash(self, data):
        return sha256(sha256(data).digest()).digest()


# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from . import config, TokenError

from bitcash.format import public_key_to_address

from os import path
import sqlite3


class TokenDB:

    def __init__(self):
        conn = sqlite3.connect(path.join(config.dir, 'tokens.db'), isolation_level='EXCLUSIVE')

        conn.execute('''CREATE TABLE IF NOT EXISTS status (
                            key TEXT NOT NULL PRIMARY KEY,
                            value TEXT
                        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS block (
                            hash TEXT NOT NULL PRIMARY KEY,
                            height INTEGER NOT NULL
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

        conn.execute('''CREATE TABLE IF NOT EXISTS status (
                            key TEXT NOT NULL PRIMARY KEY,
                            value TEXT
                        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS token (
                            address TEXT NOT NULL PRIMARY KEY,
                            tx INTEGER NOT NULL,
                            created INTEGER NOT NULL,
                            updated INTEGER,
                            supply INTEGER NOT NULL,
                            decimals INTEGER NOT NULL,
                            symbol TEXT NOT NULL,
                            name TEXT,
                            main_uri TEXT,
                            image_uri TEXT
                        )''')

        conn.execute('''CREATE INDEX IF NOT EXISTS idx_token_symbol ON token (symbol)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS balance (
                            address TEXT NOT NULL,
                            token INTEGER NOT NULL,
                            updated INTEGER NOT NULL,
                            amount INTEGER NOT NULL,
                            PRIMARY KEY (address, token)
                        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS transfer (
                            tx INTEGER NOT NULL,
                            addr_from TEXT NOT NULL,
                            addr_to TEXT NOT NULL,
                            amount INTEGER
                        )''')

        self.conn = conn
        keys = conn.execute('''SELECT key FROM status''').fetchall()
        self._init_status(keys, 'height')

        conn.commit()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def _init_status(self, keys, key):
        for k in keys:
            if k[0] == key:
                return

        self.conn.execute('''INSERT INTO status (key) VALUES (?)''', (key,))

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

    def has_key_for(self, txrow, address):
        txins = self.conn.execute('''SELECT asmhex FROM txin WHERE tx = ?''', (txrow,)).fetchall()

        for txin in txins:
            asmhex = txin[0]
            asm = bytes.fromhex(asmhex)

            sig_size = int.from_bytes(asm[0:1], 'little')
            pubkey_size = int.from_bytes(asm[sig_size+1:sig_size+2], 'little')
            pubkey = asm[sig_size + 2 : sig_size + pubkey_size + 2]
            pubkey_address = public_key_to_address(pubkey)

            if pubkey_address == address:
                # note that we only check for a single match... should we check them all instead?
                return True

        return False

    def token_create(self, address, tx, block, supply, decimals, symbol, name=None, main_uri=None, image_uri=None):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''INSERT INTO token
                              (address, tx, created, supply, decimals, symbol, name, main_uri, image_uri)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (address, tx, block, supply, decimals, symbol, name, main_uri, image_uri))
            tokenrow = cursor.lastrowid

        except sqlite3.IntegrityError as e:
            raise TokenError("A token is already defined at this address: {}".format(e))

        # no try/except here... it's a critical error to be able to insert a token yet already have a blance for it
        cursor.execute('''INSERT INTO balance
                          (address, token, updated, amount)
                          VALUES (?, ?, ?, ?)''',
                          (address, tokenrow, block, supply))

        return tokenrow


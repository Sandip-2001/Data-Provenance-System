from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from datetime import datetime, timezone
import os, json, hashlib
from flask_cors import CORS
from web3 import Web3

def iso_utc(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    # mark UTC (or convert to UTC) and serialize with trailing Z
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")

# Connect to local Ethereum node (Hardhat or Ganache)
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Address of your deployed contract
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

# Your ABI (from artifacts/contracts/Provenance.sol/Provenance.json)
import json
with open("blockchain/artifacts/contracts/Provenance.sol/Provenance.json") as f:
    contract_json = json.load(f)
    abi = contract_json["abi"]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
w3.eth.default_account = w3.eth.accounts[0]

# Load environment variables
load_dotenv()

app = Flask(__name__)

CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'options': '-c timezone=utc'}
}   
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -------------------------------
# Database Model
# -------------------------------
class Record(db.Model):
    __tablename__ = 'record'      # match the table you already created
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(255), nullable=False)
    modified_by = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ProvenanceLog(db.Model):
    __tablename__ = 'provenance_log'
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    table_name = db.Column(db.String(128), nullable=False)
    record_pk = db.Column(db.String(256), nullable=False)   # store as string for safety
    operation = db.Column(db.String(1), nullable=False)     # 'I','U','D'
    record_hash = db.Column(db.String(128), nullable=False)
    payload = db.Column(db.JSON, nullable=True)             # snapshot or diff
    user_id = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    blockchain_tx = db.Column(db.String(256), nullable=True)  # will store Ethereum tx later
    verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime(timezone=True), nullable=True)

# Create tables if not existing
with app.app_context():
    db.create_all()

# -------------------------------
# Utility: canonical hash
# -------------------------------

def canonical_hash(obj):
    # Sort keys & remove whitespace to make it deterministic
    encoded = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(encoded.encode()).hexdigest()

# -------------------------------
# Routes
# -------------------------------
@app.route('/')
def home():
    return "✅ CRUD API for Records is active!"


# -------------------------------
# CRUD endpoints (create / update / delete)
# Each will write a provenance_log row with record_hash (no blockchain yet)
# -------------------------------

# Create
@app.route('/add', methods=['POST'])
def add_record():
    data = request.json.get('data')
    user = request.json.get('user')
    if not data:
        return jsonify({'error':'data required'}), 400
    if not user:
        return jsonify({'error':'user is required in request body'}), 400

    # create record
    new_record = Record(data=data, modified_by=user)
    db.session.add(new_record)
    db.session.flush()  # get new_record.id

    # provenance payload and hash
    payload = {"new": {"id": new_record.id, "data": new_record.data}}
    
    timestamp_now = datetime.now(timezone.utc)

    prov_obj = {
        "table_name": "record",
        "record_pk": str(new_record.id),
        "operation": "I",
        "payload": payload,
        "user_id": user,
        "timestamp": iso_utc(timestamp_now)  # <-- Use the variable
    }

    # 5. Calculate the hash
    rhash = canonical_hash(prov_obj)
    
    print("Original obj = ")
    print(prov_obj)
    print("Original Hash = "+rhash)

    # store provenance row (blockchain_tx left NULL for now)
    prov = ProvenanceLog(
        table_name="record",
        record_pk=str(new_record.id),
        operation="I",
        record_hash=rhash,         # <-- Pass in the hash
        payload=payload,
        user_id=user,
        created_at=timestamp_now   # <-- Pass in the same timestamp
    )
    
    # 7. Add the complete object. The flush for the blockchain
    #    step (or the final commit) will now succeed.
    db.session.add(prov)

    # Send hash to blockchain using record ID as key
    try:
        db.session.flush()
        tx_hash = contract.functions.logAction(
            new_record.id,   # <-- use the record's ID as key
            "INSERT",
            rhash
        ).transact()
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        prov.blockchain_tx = receipt.transactionHash.hex()
    except Exception as e:
        print(f"⚠️ Blockchain logging failed: {e}")
        prov.blockchain_tx = None

    # Commit everything
    db.session.commit()

    return jsonify({
        'message': 'Record added',
        'id': new_record.id,
        'prov_log_id': prov.log_id,
        'blockchain_tx': prov.blockchain_tx
    }), 201


# Read
@app.route('/records', methods=['GET'])
def get_records():
    records = Record.query.all()
    output = [
        {
            'id': r.id,
            'data': r.data,
            'modified_by': r.modified_by,
            'timestamp': iso_utc(r.timestamp)
        }
        for r in records
    ]
    return jsonify(output)


# Update
@app.route('/update/<int:id>', methods=['PUT'])
def update_record(id):
    rec = Record.query.get(id)
    if not rec:
        return jsonify({'error':'Record not found'}), 404

    user = request.json.get('user')
    if not user:
        return jsonify({'error':'user is required in request body'}), 400
    
    new_data = request.json.get('data', rec.data)

    old_snapshot = {"id": rec.id, "data": rec.data}
    rec.data = new_data
    rec.modified_by = user
    rec.timestamp = datetime.now(timezone.utc)
    db.session.flush()

    payload = {"old": old_snapshot, "new": {"id": rec.id, "data": rec.data}}
    timestamp_now = datetime.now(timezone.utc)
    prov_obj = {
        "table_name": "record",
        "record_pk": str(rec.id),
        "operation": "U",
        "payload": payload,
        "user_id": user,
        "timestamp": iso_utc(timestamp_now) # <-- Use the variable
    }
    rhash = canonical_hash(prov_obj)

    prov = ProvenanceLog(
        table_name="record",
        record_pk=str(rec.id),
        operation="U",
        record_hash=rhash,
        payload=payload,
        user_id=user,
        created_at=timestamp_now   # <-- Pass in the same timestamp
    )
    db.session.add(prov)

    # Send hash to blockchain using record ID as key
    try:
        db.session.flush() 
        tx_hash = contract.functions.logAction(
            rec.id,   # <-- use the record's ID as key
            "UPDATE",
            rhash
        ).transact()
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        prov.blockchain_tx = receipt.transactionHash.hex()
    except Exception as e:
        print(f"⚠️ Blockchain logging failed: {e}")
        prov.blockchain_tx = None

    db.session.commit()
    return jsonify({
        'message':'Record updated',
        'id': rec.id, 
        'prov_log_id': prov.log_id, 
        'blockchain_tx': prov.blockchain_tx
    })


# Delete
@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_record(id):
    rec = Record.query.get(id)
    if not rec:
        return jsonify({'error':'not found'}), 404

    user = request.json.get('user')
    if not user:
        return jsonify({'error':'user is required in request body'}), 400
    payload = {"deleted": {"id": rec.id, "data": rec.data}}
    timestamp_now = datetime.now(timezone.utc)
    prov_obj = {
        "table_name": "record",
        "record_pk": str(rec.id),
        "operation": "D",
        "payload": payload,
        "user_id": user,
        "timestamp": iso_utc(timestamp_now)
    }
    rhash = canonical_hash(prov_obj)

    prov = ProvenanceLog(
        table_name="record",
        record_pk=str(rec.id),
        operation="D",
        record_hash=rhash,
        payload=payload,
        user_id=user,
        created_at=timestamp_now
    )
    db.session.add(prov)


    # Send hash to blockchain using record ID as key
    try:
        db.session.flush()  # get prov.log_id
        tx_hash = contract.functions.logAction(
            rec.id,   # <-- use the record's ID as key
            "DELETE",
            rhash
        ).transact()
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        prov.blockchain_tx = receipt.transactionHash.hex()
    except Exception as e:
        print(f"⚠️ Blockchain logging failed: {e}")
        prov.blockchain_tx = None

    # remove the record after logging snapshot
    db.session.delete(rec)
    db.session.commit()
    return jsonify({
        'message':'Record deleted', 
        'id': id, 
        'prov_log_id': prov.log_id,
        'blockchain_tx': prov.blockchain_tx    
    })


@app.route('/verify/<int:record_id>', methods=['GET'])
def verify_record(record_id):
    # 1) get latest provenance entry for the record
    prov = ProvenanceLog.query.filter_by(record_pk=str(record_id)).order_by(ProvenanceLog.log_id.desc()).first()
    if not prov and record:
        return jsonify({
            "status": "error",
            "record_id": record_id,
            "message": "🚨 Record exists but has no provenance log. Possible unlogged insertion or tampering."
        }), 400

    # 4️⃣ Case: no record AND no provenance — it was purged completely
    if not prov and not record:
        return jsonify({
            "status": "error",
            "record_id": record_id,
            "message": "❌ Record and provenance log both missing. Data loss or external tampering."
        }), 404


    # 2) recompute provenance-hash (the one originally stored on-chain)
    prov_obj = {
        "table_name": prov.table_name,
        "record_pk": prov.record_pk,
        "operation": prov.operation,
        "payload": prov.payload,
        "user_id": prov.user_id,
        # use the exact DB timestamp that was used when prov was created
        "timestamp": iso_utc(prov.created_at)
    }
    prov_hash_recomputed = canonical_hash(prov_obj)

    # 3) recompute hash from current record table state (if record exists)
    record = Record.query.get(int(prov.record_pk))
    record_hash_recomputed = None
    if record:
        # Build payload in the same shape as you used when creating provenance (new snapshot)
        if prov.operation == "I":
            payload_current = {"new": {"id": record.id, "data": record.data}}
        elif prov.operation == "U":
            payload_current = {
                "old": prov.payload.get("old", {}),
                "new": {"id": record.id, "data": record.data}
            }
        elif prov.operation == "D":
            payload_current = {"deleted": {"id": record.id, "data": record.data}}
        else:
            payload_current = {"new": {"id": record.id, "data": record.data}}

        record_obj = {
            "table_name": prov.table_name,
            "record_pk": prov.record_pk,
            "operation": prov.operation,
            "payload": payload_current,
            "user_id": prov.user_id,
            "timestamp": iso_utc(prov.created_at)
        }
        record_hash_recomputed = canonical_hash(record_obj)

    # 4) get on-chain hash
    # onchain_hash = None
    try:
        onchain_hash = contract.functions.getRecordHash(int(prov.record_pk)).call()
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Could not call getRecordHash()',
            'exception': str(e)
        }), 500

    # 5) final verification logic:
    # - If record exists: require onchain_hash == prov_hash_recomputed == record_hash_recomputed
    # - If record was deleted (no record row), require onchain_hash == prov_hash_recomputed
    verified = False
    reason = ""
    if onchain_hash:
        if record:
            if onchain_hash == prov_hash_recomputed == record_hash_recomputed:
                verified = True
                reason = "✅ On-chain, provenance log, and DB record all match."
            elif onchain_hash == prov_hash_recomputed:
                # chain equals original provenance snapshot, but current record differs → tampered after logging
                verified = False
                reason = "⚠️ On-chain matches provenance log, but DB record has been tampered."
            else:
                verified = False
                reason = "❌ On-chain hash does not match provenance log."
        else:
            # record missing: we must ensure this deletion was legitimate
            # i.e., the last provenance operation for this record should be a "D" (DELETE)
            if prov.operation == "D":
                # ok, it was logged as deleted
                if onchain_hash == prov_hash_recomputed:
                    verified = True
                    reason = "✅ Record deleted legitimately — provenance and blockchain match."
                else:
                    verified = False
                    reason = "❌ Record marked deleted, but blockchain mismatch."
            else:
                # record is missing but provenance doesn’t say it was deleted — suspicious
                verified = False
                reason = "🚨 Integrity violation: Record missing from DB without a DELETE provenance entry. Possible tampering."
    else:
        verified = False
        reason = "❌ No on-chain hash found."

    # 6) persist verification result, can remove this section from here and place it to upper if else block as it becomes not verified if the data is tampered even if it is verified previously, it s a choice.
    prov.verified = verified
    prov.verified_at = datetime.now(timezone.utc)
    db.session.commit()

    # 7) return detailed result
    return jsonify({
        "record_id": record_id,
        "verified": verified,
        "reason": reason,
        "onchain_hash": onchain_hash,
        "recomputed": {
            "provenance_log_hash": prov_hash_recomputed,
            "record_table_hash": record_hash_recomputed
        },
        "blockchain_tx": prov.blockchain_tx
    }), 200



@app.route('/history/<int:record_id>', methods=['GET'])
def get_history(record_id):
    """
    Fetch complete provenance history for a record ID.
    If provenance logs exist locally, return them.
    If logs are missing, fall back to blockchain events.
    """

    history = []
    source = None

    # 1️⃣ Try to fetch provenance logs from DB
    prov_logs = ProvenanceLog.query.filter_by(record_pk=str(record_id)).order_by(ProvenanceLog.created_at.asc()).all()

    if prov_logs and len(prov_logs) > 0:
        source = "database"
        for p in prov_logs:
            history.append({
                "log_id": p.log_id,
                "operation": p.operation,
                "record_hash": p.record_hash,
                "payload": p.payload,
                "user_id": p.user_id,
                "timestamp": iso_utc(p.created_at),   # ✅ consistent key
                "blockchain_tx": p.blockchain_tx,
                "verified": p.verified
            })
    else:
        # 2️⃣ Fallback: Fetch directly from blockchain events
        source = "blockchain"
        try:
            # filter events by indexed recordId
            event_filter = contract.events.RecordLogged.create_filter(
                fromBlock=0,
                toBlock="latest",
                argument_filters={"recordId": record_id}
            )
            logs = event_filter.get_all_entries()

            for log in logs:
                args = log["args"]
                blk_ts = w3.eth.get_block(log["blockNumber"])["timestamp"]
                history.append({
                    "recordId": args["recordId"],
                    "operation": args["operation"],
                    "record_hash": args["recordHash"],
                    "blockNumber": log["blockNumber"],
                    "txHash": log["transactionHash"].hex(),
                    "timestamp": iso_utc(datetime.fromtimestamp(blk_ts, tz=timezone.utc))
                })

        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"⚠️ Unable to fetch blockchain logs: {str(e)}"
            }), 500

    if not history:
        return jsonify({
            "status": "error",
            "message": f"No provenance or blockchain history found for record {record_id}."
        }), 404

    return jsonify({
        "record_id": record_id,
        "source": source,
        "count": len(history),
        "history": history
    }), 200
    

"""development only ⚠️ (never use in production): the next functions"""

@app.route('/reset_db', methods=['DELETE'])
def reset_database():
    try:
        db.session.query(ProvenanceLog).delete()
        db.session.query(Record).delete()
        db.session.commit()
        return jsonify({'message': '✅ All records and provenance logs deleted from DB.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@app.route('/tamper/<int:record_id>', methods=['PUT'])
def tamper_record(record_id):
    """Simulate data tampering for verification test."""
    try:
        record = Record.query.get(record_id)
        if not record:
            return jsonify({'error': 'Record not found'}), 404

        # Modify the data directly (bypassing provenance + blockchain)
        old_data = record.data
        record.data = record.data + " (TAMPERED)"
        db.session.commit()

        return jsonify({
            'message': 'Record tampered successfully',
            'record_id': record_id,
            'old_data': old_data,
            'new_data': record.data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# -------------------------------
if __name__ == '__main__':
    app.run(debug=True)

""" 
debug = {
        "prov_hash_recomputed": prov_hash_recomputed,
        "record_hash_recomputed": record_hash_recomputed,
        "tried": []
    }
    try:
        # preferred: if contract has getRecordHash(recordId)
        debug['tried'].append('getRecordHash')
        onchain_hash = contract.functions.getRecordHash(int(prov.record_pk)).call()
        debug['method'] = 'getRecordHash'
    except Exception as e:
        debug['getRecordHash_error'] = str(e)
        # fallback to reading event from tx (if tx present)
        if prov.blockchain_tx:
            try:
                debug['tried'].append('tx_receipt_event')
                receipt = w3.eth.get_transaction_receipt(prov.blockchain_tx)
                events = contract.events.RecordLogged().process_receipt(receipt)
                if events and len(events) > 0:
                    # event signature: RecordLogged(string operation, string recordHash, address indexed user)
                    onchain_hash = events[0]['args'].get('recordHash')
                    debug['method'] = 'event_from_tx'
                    debug['event_count'] = len(events)
                else:
                    debug['tx_event_count'] = 0
            except Exception as ex:
                debug['tx_receipt_error'] = str(ex)

        # last fallback: try array accessor by log index (best-effort)
        if onchain_hash is None:
            try:
                debug['tried'].append('getRecord_array_by_log_index')
                # prov.log_id-1 is the array index if you originally appended in order
                arr = contract.functions.getRecord(max(0, prov.log_id - 1)).call()
                # heuristic: second item commonly holds the stored hash
                if isinstance(arr, (list, tuple)) and len(arr) >= 2:
                    onchain_hash = arr[1]
                    debug['method'] = 'getRecord_by_log_index'
                    debug['getRecord_value'] = str(arr)
            except Exception as ex2:
                debug['getRecord_error'] = str(ex2)

    debug['onchain_hash'] = onchain_hash

"""



# -------------------------------
# Endpoint to return latest provenance row for a record (no blockchain check yet)
# -------------------------------
# @app.route('/prov/verify/<int:record_id>', methods=['GET'])
# def prov_verify(record_id):
#     prov = ProvenanceLog.query.filter_by(record_pk=str(record_id)).order_by(ProvenanceLog.log_id.desc()).first()
#     if not prov:
#         return jsonify({'status':'error', 'message':'no provenance found for record', 'record_id': record_id}), 404

#     # return provenance info (later we'll also check Ethereum and set verified)
#     resp = {
#         'record_id': record_id,
#         'provenance': {
#             'log_id': prov.log_id,
#             'operation': prov.operation,
#             'record_hash': prov.record_hash,
#             'payload': prov.payload,
#             'user_id': prov.user_id,
#             'created_at': prov.created_at.isoformat(),
#             'blockchain_tx': prov.blockchain_tx,
#             'verified': prov.verified
#         }
#     }
#     return jsonify(resp), 200


"""@app.route('/verify/<int:record_id>', methods=['GET'])
def verify_record(record_id):
    prov = ProvenanceLog.query.filter_by(record_pk=str(record_id)).order_by(ProvenanceLog.log_id.desc()).first()
    if not prov:
        return jsonify({'status': 'error', 'message': 'No provenance record found'}), 404

    # recompute local hash
    prov_obj = {
        "table_name": prov.table_name,
        "record_pk": prov.record_pk,
        "operation": prov.operation,
        "payload": prov.payload,
        "user_id": prov.user_id,
        "timestamp": prov.created_at.isoformat() 
    }
    print("Recomputed obj = ")
    print(prov_obj)
    recomputed_hash = canonical_hash(prov_obj)
    print("recomputed Hash = "+recomputed_hash)
    try:
        # Directly fetch from blockchain mapping by recordId
        onchain_hash = contract.functions.getRecordHash(int(prov.record_pk)).call()

        verified = (onchain_hash == recomputed_hash)
        prov.verified = verified
        prov.verified_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'record_id': record_id,
            'verified': verified,
            'recomputed_hash': recomputed_hash,
            'onchain_hash': onchain_hash,
            'blockchain_tx': prov.blockchain_tx,
            'message': '✅ Record verified' if verified else '❌ Data mismatch or not found on chain'
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
"""  
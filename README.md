📜 Blockchain-Based Data Provenance Verification System

Tamper-proof, blockchain-integrated system for tracking and verifying the complete provenance history of data records.
Built with Flask + PostgreSQL + React + Solidity (Hardhat) + Web3.py.

⸻

🚀 Features

🔐 Blockchain-Backed Integrity
• Every CRUD operation creates a cryptographically hashed provenance log.
• Hashes are stored immutably on the Ethereum blockchain.
• Detects unauthorized updates, missing provenance logs, or data tampering.

🧾 Complete Provenance History
• View full history of any record.
• Recover deleted logs using blockchain events.
• Forensic detection of:
• Unlogged inserts
• Malicious deletes
• Tampered database records

🖥️ Modern UI (React)
• CRUD operations
• One-click verification
• Right-side history panel
• Manual search for deleted records
• Scrollable tables

🗄️ Backend (Flask + PostgreSQL)
• Secure deterministic hashing (SHA-256)
• UTC-normalized timestamps
• Verification engine ensures:
(Blockchain hash) == (Provenance Log hash) == (Record Table Hash)

🏗️ Tech Stack

Layer Technology

Frontend React.js, Fetch API, HTML/CSS
Backend Flask, SQLAlchemy, Web3.py
Database PostgreSQL
Blockchain Solidity, Hardhat, Ethereum Local Node
Hashing Canonical SHA-256
Tools Python3, Node.js, VS Code

🛠️ Setup Instructions

1️⃣ Clone the repository
git clone https://github.com/your-username/data-provenance-system.git
cd data-provenance-system

2️⃣ Backend Setup (Flask)
python3 -m venv venv
source venv/bin/activate # on macOS/Linux
pip install -r requirements.txt

Create .env:
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=provenance_db

Run Flask:
python app.py

3️⃣ Blockchain Setup (Hardhat)

Inside blockchain/:
npm install
npx hardhat node
npx hardhat run scripts/deploy.js --network localhost

Copy deployed contract address into CONTRACT_ADDRESS inside app.py.

4️⃣ Frontend Setup (React)

cd provenance-frontend
npm install
npm start

🔍 Verify Example Output

Tamper detection example:

❌ On-chain matches provenance log, but DB record has been tampered.

Successful verification:

✅ On-chain, provenance log, and DB record all match.

###See commands.txt file For step by step guidance to run this app

✨ Author

Sandip Ghosh
Full-Stack Developer • Blockchain Enthusiast

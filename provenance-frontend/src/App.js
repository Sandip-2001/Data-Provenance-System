// import React, { useState, useEffect } from "react";

// function App() {
//   const [records, setRecords] = useState([]);
//   const [newData, setNewData] = useState("");
//   const [user, setUser] = useState("");
//   const [selectedRecord, setSelectedRecord] = useState(null); //added this line new
//   const [history, setHistory] = useState([]); //added this line new

//   // Fetch all records
//   const fetchRecords = async () => {
//     const res = await fetch("http://127.0.0.1:5000/records");
//     const data = await res.json();
//     setRecords(data);
//   };

//   useEffect(() => {
//     fetchRecords();
//   }, []);

//   // Add record
//   const addRecord = async () => {
//     let ed_user = user.trim();
//     let ed_newData = newData.trim();
//     if (!ed_user || !ed_newData) {
//       alert("Username or data is missing.");
//       return;
//     }
//     await fetch("http://127.0.0.1:5000/add", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ data: newData, user }),
//     });
//     setNewData("");
//     setUser("");
//     fetchRecords();
//   };

//   // Delete record
//   const deleteRecord = async (id) => {
//     const confirmDelete = window.confirm(
//       `Are you sure you want to delete record #${id}?`
//     );
//     if (!confirmDelete) return;

//     const user = window.prompt("Enter your username to delete:");
//     if (!user.trim()) {
//       alert("Username is required to delete a record.");
//       return;
//     }

//     await fetch(`http://127.0.0.1:5000/delete/${id}`, {
//       method: "DELETE",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ user: user }),
//     });
//     fetchRecords();
//   };

//   // Update record
//   const updateRecord = async (id, currentValue) => {
//     const newData = window.prompt(
//       `Enter new data for record #${id}:`,
//       currentValue
//     );
//     if (!newData) return;
//     if (!newData.trim()) {
//       alert("Update cancelled or no data entered.");
//       return;
//     }

//     const user = window.prompt("Enter your username for this update:");
//     if (!user.trim()) {
//       alert("Username is required to update a record.");
//       return;
//     }

//     await fetch(`http://127.0.0.1:5000/update/${id}`, {
//       method: "PUT",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ data: newData, user }),
//     });

//     fetchRecords();
//   };

//   const verifyRecord = async (id) => {
//     const res = await fetch(`http://127.0.0.1:5000/verify/${id}`);
//     const data = await res.json(); // convert response to JSON
//     alert(JSON.stringify(data, null, 2));
//   };

//   const fetchHistory = async (recordId) => {
//     const res = await fetch(`http://127.0.0.1:5000/history/${recordId}`);
//     const data = await res.json();
//     if (data.history) {
//       setHistory(data.history);
//     } else {
//       setHistory([]);
//     }
//   };

//   return (
//     <div style={{ padding: "20px", fontFamily: "Arial" }}>
//       <h2>📜 Data Provenance Records</h2>

//       <div style={{ marginBottom: "15px" }}>
//         <input
//           type="text"
//           placeholder="Data..."
//           value={newData}
//           onChange={(e) => setNewData(e.target.value)}
//           style={{ marginRight: "10px" }}
//         />
//         <input
//           type="text"
//           placeholder="User..."
//           value={user}
//           onChange={(e) => setUser(e.target.value)}
//           style={{ marginRight: "10px" }}
//         />
//         <button onClick={addRecord}>Add Record</button>
//       </div>
//       <div style={{ display: "flex", gap: "20px" }}>
//         <div style={{ flex: 2 }}>
//           <table border="1" cellPadding="8">
//             <thead>
//               <tr>
//                 <th>ID</th>
//                 <th>Data</th>
//                 <th>Modified By</th>
//                 <th>Timestamp</th>
//                 <th>Action</th>
//               </tr>
//             </thead>
//             <tbody>
//               {records.map((r) => (
//                 <tr
//                   key={r.id}
//                   style={{
//                     cursor: "pointer",
//                     backgroundColor:
//                       selectedRecord?.id === r.id ? "#f0f8ff" : "white",
//                   }}
//                 >
//                   <td
//                     onClick={() => {
//                       setSelectedRecord(r);
//                       fetchHistory(r.id);
//                     }}
//                   >
//                     {r.id}
//                   </td>
//                   <td>{r.data}</td>
//                   <td>{r.modified_by}</td>
//                   <td>{new Date(r.timestamp).toLocaleString()}</td>
//                   <td>
//                     <button onClick={() => updateRecord(r.id, r.data)}>
//                       Update
//                     </button>
//                     <button onClick={() => deleteRecord(r.id, r.data)}>
//                       Delete
//                     </button>
//                     <button onClick={() => verifyRecord(r.id)}>Verify</button>
//                   </td>
//                 </tr>
//               ))}
//             </tbody>
//           </table>
//         </div>

//         {selectedRecord && (
//           <div style={{ flex: 1 }}>
//             <h3>🧾 History for Record #{selectedRecord.id}</h3>

//             {history.length === 0 ? (
//               <p>No history found.</p>
//             ) : (
//               <ul style={{ listStyle: "none", padding: 0 }}>
//                 {history.map((h) => (
//                   <li
//                     key={h.log_id}
//                     style={{
//                       marginBottom: "10px",
//                       padding: "10px",
//                       border: "1px solid #ddd",
//                       borderRadius: "5px",
//                       backgroundColor: "#fff",
//                     }}
//                   >
//                     <p>
//                       <b>Operation:</b> {h.operation}
//                     </p>
//                     <p>
//                       <b>User:</b> {h.user_id}
//                     </p>
//                     <p>
//                       <b>Timestamp:</b> {new Date(h.timestamp).toLocaleString()}
//                     </p>
//                     <p>
//                       <b>Blockchain Tx:</b>{" "}
//                       {h.blockchain_tx
//                         ? `${h.blockchain_tx.slice(0, 10)}...`
//                         : "Not on chain"}
//                     </p>
//                     <p>
//                       <b>Status:</b>{" "}
//                       <span
//                         style={{
//                           color: h.verified ? "green" : "red",
//                           fontWeight: "bold",
//                         }}
//                       >
//                         {h.verified ? "Verified" : "Not Verified"}
//                       </span>
//                     </p>
//                   </li>
//                 ))}
//               </ul>
//             )}
//           </div>
//         )}
//       </div>
//     </div>
//   );
// }

// export default App;

import React, { useState, useEffect } from "react";

function App() {
  const [records, setRecords] = useState([]);
  const [newData, setNewData] = useState("");
  const [user, setUser] = useState("");
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [history, setHistory] = useState([]);
  const [searchId, setSearchId] = useState("");

  const formatTimestamp = (ts) => {
    if (!ts && ts !== 0) return "N/A";

    // If ts is a number — it may be seconds or milliseconds
    if (typeof ts === "number") {
      // treat values smaller than 1e12 as seconds (typical)
      const millis = ts < 1e12 ? ts * 1000 : ts;
      const d = new Date(millis);
      return isNaN(d.getTime()) ? "N/A" : d.toLocaleString();
    }

    // If it's a string — try to parse as ISO or numeric string
    if (typeof ts === "string") {
      // if string looks like digits only, convert to number
      if (/^\d+$/.test(ts)) {
        const n = Number(ts);
        const millis = n < 1e12 ? n * 1000 : n;
        const d = new Date(millis);
        return isNaN(d.getTime()) ? "N/A" : d.toLocaleString();
      }

      // else try Date parse (ISO)
      const d = new Date(ts);
      return isNaN(d.getTime()) ? "N/A" : d.toLocaleString();
    }

    return "N/A";
  };

  // Fetch all records
  const fetchRecords = async () => {
    const res = await fetch("http://127.0.0.1:5000/records");
    const data = await res.json();
    setRecords(data);
  };

  useEffect(() => {
    fetchRecords();
  }, []);

  // Add record
  const addRecord = async () => {
    let ed_user = user.trim();
    let ed_newData = newData.trim();
    if (!ed_user || !ed_newData) {
      alert("Username or data is missing.");
      return;
    }
    await fetch("http://127.0.0.1:5000/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data: newData, user }),
    });
    setNewData("");
    setUser("");
    fetchRecords();
  };

  // Delete record
  const deleteRecord = async (id) => {
    const confirmDelete = window.confirm(
      `Are you sure you want to delete record #${id}?`
    );
    if (!confirmDelete) return;

    const user = window.prompt("Enter your username to delete:");
    if (!user.trim()) {
      alert("Username is required to delete a record.");
      return;
    }

    await fetch(`http://127.0.0.1:5000/delete/${id}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user: user }),
    });
    fetchRecords();
  };

  // Update record
  const updateRecord = async (id, currentValue) => {
    const newData = window.prompt(
      `Enter new data for record #${id}:`,
      currentValue
    );
    if (!newData || !newData.trim()) {
      alert("Update cancelled or no data entered.");
      return;
    }

    const user = window.prompt("Enter your username for this update:");
    if (!user.trim()) {
      alert("Username is required to update a record.");
      return;
    }

    await fetch(`http://127.0.0.1:5000/update/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data: newData, user }),
    });

    fetchRecords();
  };

  const verifyRecord = async (id) => {
    const res = await fetch(`http://127.0.0.1:5000/verify/${id}`);
    const data = await res.json();
    alert(JSON.stringify(data, null, 2));
  };

  const fetchHistory = async (recordId) => {
    const res = await fetch(`http://127.0.0.1:5000/history/${recordId}`);
    const data = await res.json();
    if (data.history) {
      setHistory(data.history);
    } else {
      setHistory([]);
    }
  };

  // Manual search for deleted record
  const handleManualSearch = async () => {
    if (!searchId.trim()) {
      alert("Enter record ID to search history");
      return;
    }
    setSelectedRecord({ id: searchId });
    fetchHistory(searchId);
  };

  return (
    <div
      style={{
        padding: "20px",
        fontFamily: "Arial, sans-serif",
        backgroundColor: "#f9fafc",
        height: "100vh",
        overflow: "hidden",
      }}
    >
      <h2 style={{ textAlign: "center" }}>📜 Data Provenance System</h2>

      {/* Top Controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: "20px",
          alignItems: "center",
        }}
      >
        {/* Add Record Section */}
        <div>
          <input
            type="text"
            placeholder="Enter Data..."
            value={newData}
            onChange={(e) => setNewData(e.target.value)}
            style={{
              marginRight: "10px",
              padding: "8px",
              borderRadius: "5px",
              border: "1px solid #ccc",
            }}
          />
          <input
            type="text"
            placeholder="Enter User..."
            value={user}
            onChange={(e) => setUser(e.target.value)}
            style={{
              marginRight: "10px",
              padding: "8px",
              borderRadius: "5px",
              border: "1px solid #ccc",
            }}
          />
          <button
            onClick={addRecord}
            style={{
              padding: "8px 12px",
              backgroundColor: "#0078d4",
              color: "#fff",
              border: "none",
              borderRadius: "5px",
              cursor: "pointer",
            }}
          >
            ➕ Add Record
          </button>
        </div>

        {/* Manual Search Section */}
        <div>
          <input
            type="number"
            placeholder="Search Deleted Record ID"
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
            style={{
              marginRight: "10px",
              padding: "8px",
              borderRadius: "5px",
              border: "1px solid #ccc",
            }}
          />
          <button
            onClick={handleManualSearch}
            style={{
              padding: "8px 12px",
              backgroundColor: "#28a745",
              color: "#fff",
              border: "none",
              borderRadius: "5px",
              cursor: "pointer",
            }}
          >
            🔍 Search History
          </button>
        </div>
      </div>

      {/* Tables Section */}
      <div style={{ display: "flex", gap: "20px", height: "80%" }}>
        {/* Left - Records Table */}
        <div
          style={{
            flex: 2,
            overflowY: "scroll",
            border: "1px solid #ccc",
            borderRadius: "8px",
            background: "#fff",
          }}
        >
          <table
            border="1"
            cellPadding="8"
            style={{
              width: "100%",
              borderCollapse: "collapse",
            }}
          >
            <thead style={{ backgroundColor: "#f1f1f1" }}>
              <tr>
                <th>ID</th>
                <th>Data</th>
                <th>Modified By</th>
                <th>Timestamp</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr
                  key={r.id}
                  style={{
                    cursor: "pointer",
                    backgroundColor:
                      selectedRecord?.id === r.id ? "#e6f7ff" : "white",
                  }}
                >
                  <td
                    onClick={() => {
                      setSelectedRecord(r);
                      fetchHistory(r.id);
                    }}
                  >
                    {r.id}
                  </td>
                  <td>{r.data}</td>
                  <td>{r.modified_by}</td>
                  <td>{formatTimestamp(r.timestamp)}</td>
                  <td>
                    <button
                      onClick={() => updateRecord(r.id, r.data)}
                      style={{
                        marginRight: "5px",
                        backgroundColor: "#ffc107",
                        border: "none",
                        padding: "5px 8px",
                        borderRadius: "5px",
                        cursor: "pointer",
                      }}
                    >
                      Update
                    </button>
                    <button
                      onClick={() => deleteRecord(r.id)}
                      style={{
                        marginRight: "5px",
                        backgroundColor: "#dc3545",
                        border: "none",
                        padding: "5px 8px",
                        borderRadius: "5px",
                        cursor: "pointer",
                        color: "white",
                      }}
                    >
                      Delete
                    </button>
                    <button
                      onClick={() => verifyRecord(r.id)}
                      style={{
                        backgroundColor: "#007bff",
                        border: "none",
                        padding: "5px 8px",
                        borderRadius: "5px",
                        cursor: "pointer",
                        color: "white",
                      }}
                    >
                      Verify
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Right - History Table */}
        <div
          style={{
            flex: 1,
            overflowY: "scroll",
            border: "1px solid #ccc",
            borderRadius: "8px",
            background: "#fff",
            padding: "10px",
          }}
        >
          {selectedRecord ? (
            <>
              <h3 style={{ textAlign: "center" }}>
                🧾 History for Record #{selectedRecord.id}
              </h3>
              {history.length === 0 ? (
                <p style={{ textAlign: "center" }}>No history found.</p>
              ) : (
                <ul style={{ listStyle: "none", padding: 0 }}>
                  {history.map((h) => (
                    <li
                      key={h.log_id}
                      style={{
                        marginBottom: "10px",
                        padding: "10px",
                        border: "1px solid #ddd",
                        borderRadius: "5px",
                        backgroundColor: "#fdfdfd",
                      }}
                    >
                      <p>
                        <b>Operation:</b> {h.operation}
                      </p>
                      <p>
                        <b>User:</b> {h.user_id}
                      </p>
                      <p>
                        <b>Timestamp:</b> {formatTimestamp(h.timestamp)}
                      </p>
                      <p>
                        <b>Blockchain Tx:</b>{" "}
                        {h.blockchain_tx
                          ? `${h.blockchain_tx.slice(0, 10)}...`
                          : "Not on chain"}
                      </p>
                      <p>
                        <b>Status:</b>{" "}
                        <span
                          style={{
                            color: h.verified ? "green" : "red",
                            fontWeight: "bold",
                          }}
                        >
                          {h.verified ? "Verified" : "Not Verified"}
                        </span>
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </>
          ) : (
            <p style={{ textAlign: "center" }}>
              Select a record or search history to view details.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;

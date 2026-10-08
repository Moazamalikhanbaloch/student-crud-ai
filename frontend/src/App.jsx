import React, { useState, useEffect } from "react";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";

function App() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [students, setStudents] = useState([]);

  const fetchStudents = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/students`);
      const data = await res.json();
      setStudents(data.data || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query) return;

    setMessages((prev) => [...prev, { sender: "user", text: query }]);
    const currentQuery = query;
    setQuery("");

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: currentQuery }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { sender: "bot", text: data.response }]);
      fetchStudents(); // Refresh table if changes were made
    } catch (err) {
      setMessages((prev) => [...prev, { sender: "bot", text: "Error connecting to server." }]);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: "20px auto", fontFamily: "sans-serif" }}>
      <h2>AI Student Management (CRUD)</h2>
      
      {/* Table of Records */}
      <h3>Student Records</h3>
      <table border="1" cellPadding="8" style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th>Roll No</th>
            <th>Name</th>
            <th>Tech Info</th>
          </tr>
        </thead>
        <tbody>
          {students.map((s) => (
            <tr key={s.id}>
              <td>{s.roll_number}</td>
              <td>{s.name}</td>
              <td>{s.tech_info}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Chat / Command Box */}
      <h3>Prompt / Natural Language Action</h3>
      <form onSubmit={handleSubmit} style={{ display: "flex", gap: "10px" }}>
        <input
          style={{ flex: 1, padding: "8px" }}
          placeholder="e.g. Add Ali roll 101 with Web dev OR Delete roll 101"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit">Submit</button>
      </form>

      <div style={{ marginTop: 20 }}>
        <h4>Log / Responses:</h4>
        {messages.map((m, idx) => (
          <div key={idx} style={{ color: m.sender === "user" ? "blue" : "green", marginBottom: 6 }}>
            <b>{m.sender}:</b> {m.text}
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
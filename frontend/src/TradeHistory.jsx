import React, { useState, useEffect } from "react";
import axios from "axios";

const api = axios.create({ baseURL: "/api" });

export default function TradeHistory({ reload }) {
  const [trades, setTrades] = useState([]);

  useEffect(() => {
  api.get("/history").then(res => {
    console.log("API /api/history response:", res.data);
    setTrades(res.data);
  });
}, [reload]);

  return (
    <div>
      <h2>Trade History</h2>
      <table border="1" cellPadding="5" cellSpacing="0" width="100%">
        <thead>
          <tr>
            <th>ID</th>
            <th>Symbol</th>
            <th>Side</th>
            <th>Quantity</th>
            <th>Price</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {trades.map(trade => (
            <tr key={trade.id}>
              <td>{trade.id}</td>
              <td>{trade.symbol}</td>
              <td>{trade.side}</td>
              <td>{trade.quantity}</td>
              <td>{trade.price}</td>
              <td>{new Date(trade.timestamp).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
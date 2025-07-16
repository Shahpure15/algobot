import React, { useState } from "react";
import axios from "axios";

const api = axios.create({ baseURL: "/api" });

export default function TradeForm({ onTrade }) {
  const [symbol, setSymbol] = useState("");
  const [side, setSide] = useState("buy");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [status, setStatus] = useState("");

  const handleSubmit = async e => {
    e.preventDefault();
    setStatus("Submitting...");
    try {
      await api.post("/trade", { symbol, side, quantity, price });
      setStatus("Trade placed!");
      setSymbol(""); setQuantity(""); setPrice("");
      onTrade && onTrade();
    } catch (err) {
      setStatus("Error placing trade");
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{marginBottom: 32}}>
      <input placeholder="Symbol" value={symbol} onChange={e => setSymbol(e.target.value)} required maxLength={10} />
      <select value={side} onChange={e => setSide(e.target.value)}>
        <option value="buy">Buy</option>
        <option value="sell">Sell</option>
      </select>
      <input type="number" min="0" step="any" placeholder="Quantity" value={quantity} onChange={e => setQuantity(e.target.value)} required />
      <input type="number" min="0" step="any" placeholder="Price" value={price} onChange={e => setPrice(e.target.value)} required />
      <button type="submit">Trade</button>
      <span style={{marginLeft: 16}}>{status}</span>
    </form>
  );
}
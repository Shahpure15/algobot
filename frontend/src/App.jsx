import React, { useState, useEffect } from "react";
import TradeForm from "./TradeForm.jsx";
import TradeHistory from "./TradeHistory.jsx";

function App() {
  const [reload, setReload] = useState(false);

  return (
    <div style={{maxWidth: 600, margin: "auto", padding: 16}}>
      <h1>Trading Dashboard</h1>
      <TradeForm onTrade={() => setReload(r => !r)} />
      <TradeHistory reload={reload} />
    </div>
  );
}

export default App;
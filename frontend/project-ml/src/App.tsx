import { useState } from "react";
import LoginPage from "./components/LoginPage";
import DatasetPage from "./components/DatasetPage";

function App() {
  const [token, setToken] = useState<string | null>(
    () => sessionStorage.getItem("ml_token") // persist across refreshes
  );

  function handleLogin(newToken: string) {
    sessionStorage.setItem("ml_token", newToken);
    setToken(newToken);
  }

  function handleLogout() {
    sessionStorage.removeItem("ml_token");
    setToken(null);
  }

  if (!token) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return <DatasetPage token={token} onLogout={handleLogout} />;
}

export default App;

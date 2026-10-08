import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./auth";
import { PageResultsProvider } from "./pageResults";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <PageResultsProvider>
          <App />
        </PageResultsProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);

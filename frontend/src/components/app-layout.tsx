import { Outlet } from "react-router-dom";
import AppHeader from "./app-header";

export default function AppLayout() {
  return (
    <>
      <AppHeader />
      <main>
        <div className="pt-15 mx-auto px-4 container">
          <Outlet />
        </div>
      </main>
    </>
  );
}

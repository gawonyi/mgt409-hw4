import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

const mainLinks = [
  { to: "/", label: "Home" },
  { to: "/products", label: "Products" },
  { to: "/about", label: "About Us" },
];

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="nav">
      <NavLink to="/" className="brand">
        Campus Customs
      </NavLink>
      <nav>
        {mainLinks.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.to === "/"} className="nav-link">
            {l.label}
          </NavLink>
        ))}
        {user ? (
          <>
            <span className="nav-user">Hi, {user.first_name}</span>
            <button
              className="nav-link nav-button"
              onClick={() => {
                logout();
                navigate("/");
              }}
            >
              Log out
            </button>
          </>
        ) : (
          <>
            <NavLink to="/login" className="nav-link">Log in</NavLink>
            <NavLink to="/create-account" className="nav-link">Create account</NavLink>
          </>
        )}
      </nav>
    </header>
  );
}

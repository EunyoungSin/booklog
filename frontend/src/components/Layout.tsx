import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  const authControls = user ? (
    <>
      <span className="muted">{user.name}님</span>
      <button className="btn" onClick={handleLogout}>
        로그아웃
      </button>
    </>
  ) : (
    <>
      <Link to="/login" className="btn">
        로그인
      </Link>
      <Link to="/register" className="btn btn-primary">
        회원가입
      </Link>
    </>
  );

  return (
    <div className="app-shell">
      <nav className="sidebar" aria-label="주요 메뉴">
        <div className="sidebar-header">
          <Link to="/" className="sidebar-brand">
            📚 BookLog
          </Link>
          <div className="mobile-auth">{authControls}</div>
        </div>
        <div className="spines">
          <Link to="/feed" className="spine">
            피드
          </Link>
          <Link to="/search" className="spine spine-burgundy">
            검색
          </Link>
          <Link to="/books/search" className="spine">
            도서 등록
          </Link>
          <Link to="/library" className="spine spine-burgundy">
            내 서재
          </Link>
          <Link to="/stats" className="spine">
            통계
          </Link>
        </div>
      </nav>
      <main className="app-main grain">
        <div className="topbar">{authControls}</div>
        <div className="container">{children}</div>
      </main>
    </div>
  );
}

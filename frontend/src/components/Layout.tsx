import type { ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const WIDE_PAGES = ["/search", "/books/search", "/stats"];

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isWidePage = WIDE_PAGES.includes(location.pathname);

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <nav className="sidebar" aria-label="주요 메뉴">
        <Link to="/" className="sidebar-brand">
          📚 BookLog
        </Link>
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
          {user && (
            <>
              <Link to="/library" className="spine spine-burgundy">
                내 서재
              </Link>
              <Link to="/stats" className="spine">
                통계
              </Link>
            </>
          )}
        </div>

        <div className="sidebar-foot">
          {user ? (
            <>
              <p className="muted">{user.name}님</p>
              <button className="btn" onClick={handleLogout}>
                로그아웃
              </button>
            </>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <Link to="/login" className="spine">
                로그인
              </Link>
              <Link to="/register" className="spine spine-burgundy">
                회원가입
              </Link>
            </div>
          )}
        </div>
      </nav>
      <main className="app-main grain">
        <div className={isWidePage ? "container container-wide" : "container"}>{children}</div>
      </main>
    </div>
  );
}

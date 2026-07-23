import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { BookDetailPage } from "./pages/BookDetailPage";
import { BookSearchPage } from "./pages/BookSearchPage";
import { FeedPage } from "./pages/FeedPage";
import { LoginPage } from "./pages/LoginPage";
import { MyLibraryPage } from "./pages/MyLibraryPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { RegisterPage } from "./pages/RegisterPage";
import { SearchPage } from "./pages/SearchPage";
import { StatsPage } from "./pages/StatsPage";

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<Navigate to="/feed" replace />} />
        <Route path="/books/search" element={<BookSearchPage />} />
        <Route path="/books/:bookId" element={<BookDetailPage />} />
        <Route path="/feed" element={<FeedPage />} />
        <Route path="/library" element={<MyLibraryPage />} />
        <Route path="/stats" element={<StatsPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Layout>
  );
}

export default App;

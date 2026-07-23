import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div>
      <h1>페이지를 찾을 수 없습니다</h1>
      <p className="page-status">요청하신 페이지가 존재하지 않거나 이동되었습니다.</p>
      <Link to="/feed" className="btn btn-primary">
        피드로 돌아가기
      </Link>
    </div>
  );
}

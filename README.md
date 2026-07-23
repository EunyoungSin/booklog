# BookLog

AI 기반 독서 기록 플랫폼.<br>
React + TypeScript(Vite) 프론트엔드와 Python(FastAPI) + MongoDB(motor) 백엔드로 구성됩니다.<br>
회원가입시 JWT토큰, SMTP 이메일 인증 프로토콜 기술이 사용되었습니다.

## 폴더 구조

```
book/
├── backend/   # Python(FastAPI) + MongoDB
└── frontend/  # React + TypeScript (Vite)
```

## 백엔드 실행

```bash
cd backend
cp .env.example .env   # MONGODB_URI, JWT_SECRET_KEY, ALADIN_TTB_KEY, GEMINI_API_KEY 등을 실제 값으로 채우기
uv sync
uv run uvicorn app.main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health
- `MONGODB_URI`는 MongoDB Atlas M0 클러스터의 연결 문자열을 사용하세요 (로컬 MongoDB도 가능).

### 인증이 필요한 API 테스트 방법 (Swagger)

1. `/api/auth/register` 또는 `/api/auth/login` 호출 후 응답의 `access_token` 복사
2. Swagger UI 우측 상단 **Authorize** 버튼 클릭 → `Bearer <access_token>` 형식으로 입력 (또는 토큰 값만 입력, 스킴에 따라 다름)
3. 이후 보호된 엔드포인트 호출 시 자동으로 헤더에 포함됨

## 프론트엔드 실행

```bash
cd frontend
cp .env.example .env   # VITE_API_BASE_URL (기본 http://localhost:8000)
npm install
npm run dev
```

- http://localhost:5173 에서 확인 (백엔드가 http://localhost:8000 에서 함께 실행 중이어야 함)
- 회원가입/로그인 후 상단 네비게이션에 사용자 이름과 로그아웃 버튼이 표시되면 정상 동작
- `npm run build`로 타입체크 + 프로덕션 빌드 확인 가능

## 페이지 목록

| 경로 | 설명 |
| --- | --- |
| `/login`, `/register` | 로그인 / 회원가입 |
| `/` | 홈 |
| `/feed` | 전체 공개 독후감 피드 (태그 필터) |
| `/search` | 도서/독후감/인용문 통합 검색 |
| `/books/search` | 알라딘 도서 검색 및 서재 등록 |
| `/books/:bookId` | 책 상세 — 내 독후감·공개 독후감·인용문·댓글 |
| `/library` | 내 서재 |
| `/stats` | 월별 독서 통계 |

## 배포 참고

- 프론트엔드: Vercel (빌드 명령 `npm run build`, 출력 디렉터리 `dist`, 환경변수 `VITE_API_BASE_URL`을 배포된 백엔드 주소로 설정)
- 백엔드: Render 무료 웹 서비스 (시작 명령 `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`, `.env.example`의 환경변수를 Render 대시보드에 등록)
- DB: MongoDB Atlas M0 (전문 검색 품질을 높이려면 Atlas 콘솔에서 `default`라는 이름의 Search 인덱스를 books/reviews/quotes 컬렉션에 생성 — 없어도 정규식 폴백으로 동작함)

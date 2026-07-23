import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { checkEmailAvailable, confirmVerificationCode, sendVerificationCode } from "../api/auth";
import { extractErrorMessage } from "../api/errors";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
// matches EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES on the backend
const CODE_EXPIRY_SECONDS = 10 * 60;
type EmailStatus = "idle" | "checking" | "available" | "taken";
type VerificationStatus = "unsent" | "sending" | "sent" | "confirming" | "verified";

function formatRemainingTime(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [emailStatus, setEmailStatus] = useState<EmailStatus>("idle");

  const [verification, setVerification] = useState<VerificationStatus>("unsent");
  const [code, setCode] = useState("");
  const [sendError, setSendError] = useState<string | null>(null);
  const [codeError, setCodeError] = useState<string | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState<number | null>(null);
  const isCountingDown = remainingSeconds !== null;

  useEffect(() => {
    if (!isCountingDown) return;
    const timer = setInterval(() => {
      setRemainingSeconds((prev) => (prev !== null && prev > 0 ? prev - 1 : prev));
    }, 1000);
    return () => clearInterval(timer);
  }, [isCountingDown]);

  useEffect(() => {
    if (!EMAIL_PATTERN.test(email)) {
      setEmailStatus("idle");
      return;
    }
    let cancelled = false;
    setEmailStatus("checking");
    const timer = setTimeout(() => {
      checkEmailAvailable(email)
        .then((available) => {
          if (!cancelled) setEmailStatus(available ? "available" : "taken");
        })
        .catch(() => {
          if (!cancelled) setEmailStatus("idle");
        });
    }, 400);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [email]);

  function handleChangeEmail() {
    setVerification("unsent");
    setCode("");
    setSendError(null);
    setCodeError(null);
    setRemainingSeconds(null);
  }

  async function handleSendCode() {
    setSendError(null);
    setVerification("sending");
    try {
      await sendVerificationCode(email);
      setVerification("sent");
      setRemainingSeconds(CODE_EXPIRY_SECONDS);
    } catch (err) {
      setVerification("unsent");
      setSendError(extractErrorMessage(err, "인증코드를 보내지 못했습니다."));
    }
  }

  async function handleConfirmCode() {
    setCodeError(null);
    setVerification("confirming");
    try {
      await confirmVerificationCode(email, code);
      setVerification("verified");
      setRemainingSeconds(null);
    } catch (err) {
      setVerification("sent");
      setCodeError(extractErrorMessage(err, "인증코드가 올바르지 않습니다."));
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (verification !== "verified") {
      setError("이메일 인증을 먼저 완료해주세요.");
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await register(email, password, name);
      navigate("/");
    } catch (err) {
      setError(extractErrorMessage(err, "회원가입에 실패했습니다."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div>
      <h1>회원가입</h1>
      <form className="form" onSubmit={handleSubmit}>
        <label>
          이름
          <input required value={name} onChange={(e) => setName(e.target.value)} />
        </label>

        <label>
          비밀번호 (8자 이상)
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        <label>
          이메일
          <input
            type="email"
            required
            value={email}
            disabled={verification !== "unsent"}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        {emailStatus === "checking" && (
          <p className="muted" style={{ fontSize: 12, margin: 0 }}>
            중복 확인 중...
          </p>
        )}
        {emailStatus === "available" && verification === "unsent" && (
          <p style={{ fontSize: 12, margin: 0, color: "var(--brass-strong)" }}>
            사용 가능한 이메일입니다.
          </p>
        )}
        {emailStatus === "taken" && (
          <p className="error-text" style={{ fontSize: 12, margin: 0 }}>
            이미 사용 중인 이메일입니다.
          </p>
        )}

        {verification === "unsent" && (
          <button
            type="button"
            className="btn"
            onClick={handleSendCode}
            disabled={!EMAIL_PATTERN.test(email) || emailStatus === "taken"}
          >
            인증코드 발송
          </button>
        )}
        {verification === "sending" && (
          <p className="page-status" style={{ padding: 0 }}>
            인증코드 발송 중...
          </p>
        )}
        {sendError && <p className="error-text">{sendError}</p>}

        {verification !== "unsent" && verification !== "sending" && (
          <>
            <label>
              인증코드
              <input
                required
                inputMode="numeric"
                maxLength={6}
                value={code}
                disabled={verification === "verified"}
                onChange={(e) => setCode(e.target.value)}
              />
            </label>
            {verification !== "verified" && remainingSeconds !== null && (
              <p
                className={remainingSeconds > 0 ? "muted" : "error-text"}
                style={{ fontSize: 12, margin: 0 }}
              >
                {remainingSeconds > 0
                  ? `남은 시간 ${formatRemainingTime(remainingSeconds)}`
                  : "인증코드가 만료되었습니다. 재전송해주세요."}
              </p>
            )}
            {codeError && <p className="error-text">{codeError}</p>}
            {verification === "verified" ? (
              <p style={{ fontSize: 13, margin: 0, color: "var(--brass-strong)" }}>
                이메일 인증이 완료되었습니다.
              </p>
            ) : (
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleConfirmCode}
                  disabled={
                    verification === "confirming" ||
                    code.length !== 6 ||
                    remainingSeconds === 0
                  }
                >
                  {verification === "confirming" ? "확인 중..." : "인증코드 확인"}
                </button>
                <button type="button" className="btn" onClick={handleSendCode}>
                  재전송
                </button>
                <button type="button" className="btn" onClick={handleChangeEmail}>
                  이메일 변경
                </button>
              </div>
            )}
          </>
        )}

        {error && <p className="error-text">{error}</p>}
        <button
          className="btn btn-primary"
          type="submit"
          disabled={isSubmitting || verification !== "verified"}
        >
          {isSubmitting
            ? "가입 중..."
            : verification !== "verified"
              ? "이메일 인증 후 가입 가능"
              : "회원가입"}
        </button>
      </form>
      <p className="muted" style={{ marginTop: 16 }}>
        이미 계정이 있으신가요? <Link to="/login">로그인</Link>
      </p>
    </div>
  );
}

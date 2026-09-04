# 프론트엔드 테스트 엔지니어링 가이드

이 문서는 `src/frontend`의 테스트 아키텍처와 실행 규칙을 정의합니다.

## 0) 범위와 우선순위

- 범위: `src/frontend/src/tests` 및 `src/frontend/tests` 하위 전체
- 프론트엔드 테스트 작업 전 읽기 순서:

1. 루트 `AGENTS.md`
2. `src/frontend/FRONTEND.md`
3. 이 문서 (`src/frontend/TEST.md`)

## 1) 테스트 피라미드 (De Facto)

1. Unit: 순수 유틸 및 작은 로직 분기
2. Component: 페이지/컴포넌트 사용자 상호작용 및 렌더링 동작
3. Integration: MSW 기반 API 레이어 + 훅 동작
4. E2E: Playwright 기반 브라우저 라우트 스모크 및 핵심 사용자 여정

## 1.1) 백엔드 시나리오 정합 규칙

프론트 시나리오 테스트는 아래 백엔드 `full-system` 시퀀스를 추적해야 합니다.

1. `src/backend/TEST.md` (`## 8.1) Seeded Full-System Scenario Sequence`)

정합 정책:

1. 주체/자격증명/API 키 이름은 공통 시나리오 fixture(`src/tests/fixtures/fullSystemScenarioData.ts`)에 유지
2. 프론트 UX에서 도달 가능한 백엔드 계약 분기를 커버
3. 프론트 UI에 노출되지 않는 백엔드 전용 플로우(예: `/auth/me`의 `X-API-Key` 인증)는 out-of-scope로 문서화하고 백엔드 테스트에서 검증 유지

## 2) 현재 테스트 레이아웃

```text
src/frontend/
  src/
    tests/
      unit/
        hooks/
          serverConnectivity.test.ts
        utils/
          apiBase.test.ts
          desktopRuntime.test.ts
          validation.test.ts
      component/
        App.test.tsx
        components/
          layout/
            AppNavbar.test.tsx
            DesktopTitleBar.test.tsx
        pages/
          cabin/
            CabinInitPage.test.tsx
          login/
            LoginPage.test.tsx
          settings/
            SettingsPage.test.tsx
      integration/
        api/
          configApi.test.ts
          systemApi.test.ts
        hooks/
          useAuth.test.tsx
          useFeatures.test.tsx
          useServerConnectivity.test.tsx
      fixtures/
        fullSystemScenarioData.ts
      setup.ts
      mocks/
        handlers.ts
        server.ts
      utils/
        renderWithRouter.tsx
  tests/
    e2e/
      auth-smoke.spec.ts
  playwright.config.ts
```

## 3) 툴링

1. Unit/Component/Integration: `Vitest + Testing Library + MSW`
2. E2E: `Playwright`

## 4) 마커 없는 실행 명령

Vitest 스위트 전체 실행:

```bash
cd src/frontend
npm run test
```

Unit 테스트만 실행:

```bash
cd src/frontend
npm run test:unit
```

Component 테스트만 실행:

```bash
cd src/frontend
npm run test:component
```

Integration 테스트만 실행:

```bash
cd src/frontend
npm run test:integration
```

전체 테스트 매트릭스 순차 실행 (unit -> component -> integration -> e2e):

```bash
cd src/frontend
npm run test:all
```

Vitest watch 모드 실행:

```bash
cd src/frontend
npm run test:watch
```

E2E 라우트 스모크 실행:

```bash
cd src/frontend
npm run test:e2e
```

E2E UI 모드 실행:

```bash
cd src/frontend
npm run test:e2e:ui
```

## 5) MSW 규칙

1. 기본 API mock은 `src/tests/mocks/handlers.ts`에 중앙화
2. 분기별 payload가 필요한 테스트는 `server.use(...)`로 handler override
3. 미처리 요청은 실패로 간주 (`onUnhandledRequest: "error"`)

## 6) 테스트 작성 형식

각 테스트는 Given/When/Then 주석으로 시나리오 의도를 명확히 유지합니다.

템플릿:

```ts
it("<behavior>", async () => {
    // Given: ...
    // When: ...
    // Then: ...
});
```

## 7) 도메인 온보딩 규칙

새 프론트엔드 도메인을 추가할 때:

1. 공통 도메인 유틸이 있으면 unit 테스트 추가
2. 핵심 상호작용/검증 플로우에 대한 component/page 테스트 추가
3. API 모듈의 에러/성공 분기에 대한 integration 테스트를 MSW로 추가
4. 핵심 라우트라면 Playwright 라우트 스모크 최소 1개 추가

## 8) 현재 시나리오 인벤토리

1. `src/tests/unit/utils/apiBase.test.ts`
    - 인증 쿠키의 same-site 유지를 위한 로컬 루프백 호스트 정렬
2. `src/tests/unit/utils/desktopRuntime.test.ts`
    - 브라우저/Tauri 런타임 구분과 데스크톱 플랫폼 감지
3. `src/tests/unit/utils/cabinEntryRedirect.test.ts`, `src/tests/unit/utils/cabinEntryReveal.test.ts`
    - OAuth callback bootstrap 치환과 1회성 cabin reveal 저장 처리
4. `src/tests/unit/utils/validation.test.ts`
    - 이메일/비밀번호 검증의 성공/실패 분기
5. `src/tests/component/components/layout/DesktopTitleBar.test.tsx`
    - 브라우저 숨김, macOS 네이티브 컨트롤, Windows 창 액션, standalone 연결 상태 배치
6. `src/tests/integration/api/configApi.test.ts`
    - `/config` 성공/실패 API 응답 처리
7. `src/tests/component/pages/login/LoginPage.test.tsx`
    - 잘못된 이메일의 클라이언트 검증 분기
    - 로그인 성공 submit + 내비게이션 분기
    - `INVALID_CREDENTIALS` 남은 시도 횟수 분기
    - `EMAIL_NOT_VERIFIED` + 인증 메일 재전송 분기
8. `src/tests/component/pages/cabin/CabinInitPage.test.tsx`
    - Playable init 화면이 backend game state를 불러옴
    - 소포/설정 버튼이 `/cabin`을 벗어나지 않고 modal overlay를 엶
    - Login success entry state가 cabin reveal class를 적용함
9. `src/tests/component/pages/settings/SettingsPage.test.tsx`
    - 역할 배지 표시 분기:
      admin은 배지 표시, user는 배지 숨김
    - 백엔드 정합 API 키 라이프사이클:
      create -> reveal -> list-visible -> disable -> enable -> delete
    - 백엔드 정합 에러 분기:
      duplicate-name (`API_KEY_NAME_ALREADY_EXISTS`), delete not-found (`API_KEY_NOT_FOUND`)
10. `src/tests/integration/hooks/useAuth.test.tsx`
    - refresh bootstrap 성공 분기 (토큰 없음 -> refresh -> me)
    - 저장된 토큰 + `/me` 성공 분기 (refresh skip)
    - `/me` 실패 + refresh 실패 분기 (토큰 삭제 및 로그아웃 상태)
    - logout API 실패 시에도 `finally`에서 클라이언트 세션 정리 분기
11. `tests/e2e/auth-smoke.spec.ts`
    - 브라우저 레벨 `/login` 라우트 렌더 스모크
12. `src/tests/unit/hooks/serverConnectivity.test.ts`
    - 지수 재연결 지연, 최대 지연 및 jitter 경계
13. `src/tests/integration/api/systemApi.test.ts`
    - `/health/ready`의 ready/degraded 응답 처리
14. `src/tests/integration/hooks/useServerConnectivity.test.tsx`
    - 브라우저 polling 제외 및 Tauri offline-to-online 복구
15. `src/tests/component/App.test.tsx`
    - `/config`를 사용할 수 없을 때 보호 라우팅의 fail-closed 처리, 공용 public Nav 구조, 지연된 재시도 로딩 상태
16. `src/tests/integration/hooks/useFeatures.test.tsx`
    - 설정 실패와 명시적 로그인 비활성화 구분 및 재시도 복구
17. `src/tests/component/components/layout/AppNavbar.test.tsx`
    - 프로필 컨트롤 옆 compact 데스크톱 연결 상태 배치, 안정적인 재시도 문구, 오프라인 로그아웃 차단
18. `src/tests/component/pages/main/LandingPage.test.tsx`
    - 공용 public Nav 구조와 랜딩 탐색 동작

## 8.1) 백엔드 Full-System 매핑 (프론트 도달 가능 부분집합)

매핑된 Auth 분기:

1. 로그인 성공
2. 남은 시도 횟수를 포함한 잘못된 자격증명 로그인
3. 이메일 미인증 + 인증 메일 재전송 액션
4. 잘못된 이메일 형식의 클라이언트 검증
5. access token 누락 시 refresh 기반 세션 bootstrap
6. `/me`와 refresh 모두 실패할 때 세션 정리 경로
7. logout API 실패 시에도 logout `finally` 정리 경로

매핑된 API key 분기:

1. API 키 생성 성공
2. API 키 이름 중복 충돌
3. 생성 후 목록 반영
4. 키 비활성화 상태 업데이트
5. 키 활성화 상태 업데이트
6. 키 삭제 성공
7. 키 삭제 not-found 분기

백엔드 전용(프론트 도달 불가) 분기는 백엔드 소유로 유지:

1. API-key 기반 `/auth/me` 인증 성공/거부 (`X-API-Key`)

## 9) 검증 체크리스트

커밋 전:

```bash
cd src/frontend
npm run format
npm run format:check
npm run test
npm run build
```

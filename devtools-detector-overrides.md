# devtoolsDetector Overrides 적용 방법

본인 코드 디버깅 또는 허가된 테스트 환경에서만 사용하세요.

## 목적

페이지마다 `devtoolsDetector.addListener(...)` 또는 `devtoolsDetector.launch()` 코드를 하나씩 수정하지 않고, `devtools-detector.min.js` 라이브러리 자체를 빈 동작으로 덮어씁니다.

## Overrides용 코드

Chrome DevTools의 Overrides에서 `devtools-detector.min.js` 파일 내용을 전부 지우고 아래 코드만 넣습니다.

```js
window.devtoolsDetector = {
  addListener: function () {},
  removeListener: function () {},
  launch: function () {},
  stop: function () {},
  isLaunch: function () {
    return false;
  }
};
```

## 적용 순서

1. Chrome에서 새 탭을 엽니다.
2. `F12`를 눌러 개발자 도구를 엽니다.
3. `Sources` 탭으로 이동합니다.
4. 왼쪽 패널에서 `Overrides` 탭을 엽니다.
5. `Select folder for overrides`를 누르고 빈 폴더를 선택합니다.
6. 브라우저가 권한을 물으면 `허용`을 누릅니다.
7. 예약 페이지에 접속합니다.
8. `Sources` 탭에서 `Ctrl + Shift + F`를 누릅니다.
9. 아래 키워드 중 하나로 검색합니다.

```text
devtools-detector.min.js
devtoolsDetector
```

10. `https://cdnjs.cloudflare.com/ajax/libs/devtools-detector/2.0.22/devtools-detector.min.js` 파일을 찾습니다.
11. 해당 파일 내용을 전부 삭제하고 위 Overrides용 코드를 붙여넣습니다.
12. `Ctrl + S`로 저장합니다.
13. 파일명 옆에 보라색 점이 생기면 Overrides 적용 성공입니다.
14. 페이지를 `F5`로 새로고침합니다.

## 확인 방법

페이지 코드에 아래와 같은 호출이 남아 있어도 실제로는 아무 동작을 하지 않습니다.

```js
devtoolsDetector.addListener(function (isOpen) {
  if (isOpen) {
    blockDevTools();
  }
});

devtoolsDetector.launch();
```

## 참고

Network Request Blocking으로 `devtools-detector.min.js` 요청을 차단할 수도 있지만, 페이지 코드가 `devtoolsDetector.launch()`를 호출하면 `devtoolsDetector is not defined` 에러가 발생할 수 있습니다.

그래서 요청 차단보다 위처럼 `window.devtoolsDetector`를 빈 객체로 대체하는 방식이 더 안정적입니다.

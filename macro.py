"""
키이스케이프 방탈출 예약 매크로
================================
실행하면 지점/테마/날짜/시간을 직접 선택!
reCAPTCHA 클릭 + 예약 버튼만 직접 누르면 끝!

사용법:
    pip3 install playwright requests && python3 -m playwright install chromium
    python3 macro.py


  지점 선택:
    1) 강남점
    2) 홍대점
    3) 부산점
    4) 전주점
    5) 강남 더오름
    6) 에버랜드
    7) 후즈데어
    8) STATION
    9) LOG_IN 1
    10) LOG_IN 2
    11) 메모리컴퍼니
    12) 우주라이크

  번호 선택 (1-12): 1
  → 강남점
  [18:24:37.988] 테마 목록 조회 중...

  테마 선택:
    1) 그카지말라캤자나
    2) 살랑살랑연구소
    3) 월야애담-영문병행표기

  번호 선택 (1-3): 1
  → 그카지말라캤자나 (info=7, theme=7)

  예약 날짜 (YYYY-MM-DD): 2026-03-22
  [18:24:44.797] 시간표 조회 중...

  (매진: 15:20)

  시간 선택:
    1) 10:10  
    2) 11:25  
    3) 12:45  
    4) 14:05  
    5) 16:35  
    6) 17:50  
    7) 19:05  
    8) 20:25  
    9) 21:45  

  번호 선택 (1-9): 6
  → 17:50

  이름: 신진서
  전화번호 (-없이, 예: 01012345678): 01034474783
  인원수: 2

"""

import time
import sys
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

BRANCH_LIST = [
    ("강남점", "3"), ("홍대점", "10"), ("부산점", "9"), ("전주점", "7"),
    ("강남 더오름", "14"), ("에버랜드", "26"), ("후즈데어", "23"),
    ("STATION", "22"), ("LOG_IN 1", "19"), ("LOG_IN 2", "20"),
    ("메모리컴퍼니", "18"), ("우주라이크", "16"),
]

BASE_URL = "https://www.keyescape.com"
PROC_URL = f"{BASE_URL}/controller/run_proc.php"


def log(msg):
    now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"  [{now}] {msg}")


def wait_until_open(open_time_str):
    today = datetime.now().strftime("%Y-%m-%d")
    open_dt = datetime.strptime(f"{today} {open_time_str}", "%Y-%m-%d %H:%M:%S")
    while True:
        remaining = (open_dt - datetime.now()).total_seconds()
        if remaining <= 0: 
            break
        if remaining > 10:
            log(f"오픈까지 {remaining:.0f}초...")
            time.sleep(min(remaining - 3, 5))
        elif remaining > 0.05:
            time.sleep(0.01)


def api_post(data):
    """run_proc.php에 POST 요청"""
    r = requests.post(PROC_URL, data=data, headers={"X-Requested-With": "XMLHttpRequest"}, timeout=5)
    return r.json()


def pick(prompt, options, key_fn, label_fn):
    """목록에서 하나를 선택"""
    print(f"\n  {prompt}")
    for i, opt in enumerate(options):
        print(f"    {i + 1}) {label_fn(opt)}")
    while True:
        try:
            idx = int(input(f"\n  번호 선택 (1-{len(options)}): ").strip()) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except (ValueError, IndexError):
            pass
        print("  잘못된 입력!")


def setup_interactive():
    """지점 → 테마 → 날짜 → 시간 → 개인정보 순서로 선택"""
    print("""
  ╔═══════════════════════════════════════════╗
  ║     키이스케이프 예약 매크로               ║
  ╚═══════════════════════════════════════════╝
""")

    # 1) 지점 선택
    branch = pick("지점 선택:", BRANCH_LIST,
                   lambda x: x[1], lambda x: x[0])
    zizum_num = branch[1]
    print(f"  → {branch[0]}")

    # 2) 테마 선택 (API 조회)
    log("테마 목록 조회 중...")
    theme_res = api_post({"t": "get_theme_info_list", "zizum_num": zizum_num})
    themes = theme_res.get("data", [])

    if not themes:
        print("  테마가 없습니다!")
        sys.exit(1)

    theme = pick("테마 선택:", themes,
                  lambda x: x.get("info_num"),
                  lambda x: x.get("info_name", "이름없음"))
    theme_info_num = str(theme.get("info_num", ""))
    theme_num = str(theme.get("theme_num", ""))
    print(f"  → {theme.get('info_name')} (info={theme_info_num}, theme={theme_num})")

    # 3) 날짜 입력
    date = input("\n  예약 날짜 (예: 2026-03-22): ").strip()

    # 4) 시간 조회 + 선택
    log("시간표 조회 중...")
    time_res = api_post({
        "t": "get_theme_time",
        "date": date,
        "zizumNum": zizum_num,
        "themeNum": theme_num,
        "endDay": "",
    })
    time_list = time_res.get("data", [])

    if not time_list:
        print("  해당 날짜에 시간이 없습니다!")
        sys.exit(1)

    # hh:mm 조합
    for t in time_list:
        t["timeStr"] = f"{t.get('hh', '??')}:{t.get('mm', '??')}"

    available = [t for t in time_list if t.get("enable") != "N"]
    sold_out = [t for t in time_list if t.get("enable") == "N"]

    if sold_out:
        print(f"\n  (매진: {', '.join(t['timeStr'] for t in sold_out)})")

    if not available:
        print("  모든 시간이 매진입니다!")
        sys.exit(1)

    chosen_time = pick("시간 선택:", available,
                        lambda x: x.get("num"),
                        lambda x: f"{x['timeStr']}  {'(매진)' if x.get('enable') == 'N' else ''}")
    print(f"  → {chosen_time['timeStr']}")

    # 5) 개인정보
    name = input("\n  이름 (예: 홍길동): ").strip()
    phone = input("  전화번호 (예: 01012345678): ").strip()
    people = input("  인원수 (예: 2): ").strip()

    # 6) 오픈 대기 여부
    wait = input("\n  오픈 시간 대기? (바로 실행: n / 대기: 14:00:00): ").strip()
    wait_for_open = wait.lower() != "n" and wait != ""
    open_time = wait if wait_for_open else "00:00:00"

    cfg = {
        "zizum_num": zizum_num,
        "theme_num": theme_num,
        "theme_info_num": theme_info_num,
        "date": date,
        "chosen_time": chosen_time,  # 이미 선택된 시간 객체
        "name": name,
        "phone": phone,
        "people": people,
        "wait_for_open": wait_for_open,
        "open_time": open_time,
    }

    branch_name = branch[0]
    print(f"""
  ══════════════════════════════════════════
  지점: {branch_name}
  테마: {theme.get('info_name')}
  날짜: {date}
  시간: {chosen_time['timeStr']}
  이름: {name}
  전화: {phone}
  오픈대기: {'예 (' + open_time + ')' if wait_for_open else '아니오'}
  ══════════════════════════════════════════
""")

    if input("  이대로 진행? (y/n): ").strip().lower() != "y":
        return None
    return cfg


def run():
    cfg = setup_interactive()
    if not cfg:
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
        )

        # ── devtools-detector 우회 ──
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false, configurable: true });
            Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight, configurable: true });
            Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth, configurable: true });
            Object.defineProperty(window, 'devtoolsDetector', {
                value: { launch:()=>{}, stop:()=>{}, isLaunch:()=>false, addListener:()=>{}, removeListener:()=>{} },
                writable: false, configurable: false
            });
        """)

        def block_detector(route):
            route.abort()
        context.route("**/devtools-detector*", block_detector)
        context.route("**/devtools_detector*", block_detector)
        context.route("**/disable-devtool*", block_detector)
        context.route("**/DisableDevtool*", block_detector)

        page = context.new_page()

        # ── 아무 페이지나 접속 (쿠키/세션 확보용) ──
        log("사이트 접속 중...")
        page.goto(f"{BASE_URL}/reservation.php", wait_until="domcontentloaded")
        log("사이트 로드 완료")

        # ── 오픈 시간 대기 ──
        if cfg["wait_for_open"]:
            log(f"오픈 시간 대기: {cfg['open_time']}")
            wait_until_open(cfg["open_time"])
            log("오픈!")

        chosen = cfg["chosen_time"]
        log(f"선택된 시간: {chosen['timeStr']} (num={chosen['num']})")

        input("\n  >>> Enter 누르면 매크로 발사!\n")

        t0 = time.time()
        log("매크로 발사!")

        # ══════════════════════════════════════════
        # STEP 1: 폼 생성 → POST 제출 (API 조회 없이 바로!)
        # ══════════════════════════════════════════
        result = page.evaluate(f"""
        () => {{
            const form = document.createElement("form");
            form.method = "POST";
            form.action = "/reservation2.php";
            form.style.display = "none";

            const fields = {{
                zizumNum: "{cfg['zizum_num']}",
                themeNum: "{cfg['theme_num']}",
                themeInfoNum: "{cfg['theme_info_num']}",
                revDays: "{cfg['date']}",
                themeTimeNum: "{chosen['num']}",
                revTimes: "{chosen['timeStr']}",
                themeName: ""
            }};

            for (const [key, val] of Object.entries(fields)) {{
                const input = document.createElement("input");
                input.type = "hidden";
                input.name = key;
                input.value = val;
                form.appendChild(input);
            }}

            document.body.appendChild(form);
            form.submit();

            return {{ ok: true }};
        }}
        """)

        ms1 = f"{(time.time() - t0) * 1000:.0f}ms"
        log(f"STEP 1 완료: 폼 제출 ({ms1})")

        # ── reservation2.php 로딩 대기 ──
        page.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(1)

        ms2 = f"{(time.time() - t0) * 1000:.0f}ms"
        log(f"STEP 2 페이지 도착 ({ms2})")

        # ══════════════════════════════════════════
        # STEP 2: 이름/전화(3칸)/인원/동의 자동 입력
        # ══════════════════════════════════════════

        # 전화번호 3칸 분리
        phone = cfg["phone"].replace("-", "")
        p1 = phone[:3]                    # 010
        p2 = phone[3:7]                   # 1234
        p3 = phone[7:]                    # 5678

        # ── 디버깅: 모든 input/select 필드 이름 출력 ──
        field_info = page.evaluate("""
        () => {
            const els = document.querySelectorAll("input, select, textarea");
            return Array.from(els).map(el => ({
                tag: el.tagName,
                type: el.type || "",
                name: el.name || "",
                id: el.id || "",
                placeholder: el.placeholder || "",
                visible: el.offsetParent !== null,
                value: el.type === "checkbox" ? el.checked : (el.value || ""),
            }));
        }
        """)
        log("reservation2.php 필드 목록:")
        for f in field_info:
            if f["name"] or f["id"]:
                vis = "✓" if f["visible"] else "✗"
                print(f"    [{vis}] <{f['tag']}> name={f['name']!r} id={f['id']!r} type={f['type']!r} placeholder={f['placeholder']!r} val={f['value']!r}")

        # ── 자동 입력 (readonly 필드 대응) ──

        # 이름
        page.fill("input#name_input", cfg["name"])
        log(f"이름 입력: {cfg['name']}")

        # 전화번호 3칸 (mobile1은 readonly라 JS로 입력)
        page.evaluate(f"""
        () => {{
            const set = (name, val) => {{
                const el = document.querySelector("input[name='" + name + "']");
                if (!el) return;
                el.removeAttribute("readonly");
                const nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeSetter.call(el, val);
                el.dispatchEvent(new Event("input", {{ bubbles: true }}));
                el.dispatchEvent(new Event("change", {{ bubbles: true }}));
            }};
            set("mobile1", "{p1}");
            set("mobile2", "{p2}");
            set("mobile3", "{p3}");
        }}
        """)
        log(f"전화번호 입력: {p1}-{p2}-{p3}")

        # 인원수
        page.select_option("select#person", cfg["people"])
        log(f"인원수 선택: {cfg['people']}")

        # 체크박스 모두 체크 (reCAPTCHA 제외)
        page.evaluate("""
        () => {
            document.querySelectorAll("input[type='checkbox']").forEach(cb => {
                if (!cb.checked && !cb.closest(".g-recaptcha") &&
                    !cb.closest("#rc-anchor-container") && cb.id !== "recaptcha") {
                    cb.click();
                }
            });
        }
        """)

        total = f"{(time.time() - t0) * 1000:.0f}ms"
        log(f"STEP 2 완료: 자동입력 끝 ({total})")

        # ── 디버깅: 입력 후 상태 확인 ──
        after = page.evaluate("""
        () => {
            const g = (s) => { const el = document.querySelector(s); return el ? el.value : "NOT FOUND"; };
            return {
                name: g("input#name_input"),
                mobile1: g("input[name='mobile1']"),
                mobile2: g("input[name='mobile2']"),
                mobile3: g("input[name='mobile3']"),
            };
        }
        """)
        log(f"입력 후 확인: 이름={after['name']!r}, 전화={after['mobile1']}-{after['mobile2']}-{after['mobile3']}")

        print(f"""
  ══════════════════════════════════════════
  자동 처리 완료! (총 {total})

  지금 브라우저에서:
    1. reCAPTCHA "로봇이 아닙니다" 체크
    2. 예약하기 버튼 클릭
  ══════════════════════════════════════════
""")

        input("  >>> 예약 완료 후 Enter로 브라우저 닫기...")
        browser.close()


if __name__ == "__main__":
    run()

"""부모님 기기 도움말 — API 없는 선택형 안내. streamlit run app.py"""
import streamlit as st
import requests
import hashlib
import hmac
import secrets
import time
import re
from urllib.parse import quote

st.set_page_config(page_title="차근차근 기기 도우미",page_icon="🤝",layout="centered")
VERSION="선택형 도움말 5.2"
DEVICES=["갤럭시·안드로이드","아이폰·아이패드","윈도우 컴퓨터","맥 컴퓨터","잘 모르겠어요"]
# 노드는 설명과 사용자가 실제 확인한 응답을 연결합니다. AI 추측 없음.
FLOWS={
"복사한 글이 안 보여요":{
"start":("글을 넣으려는 앱에서 입력칸이 보이나요?","메시지나 문서를 쓰는 칸이에요. 복사한 글은 자동으로 나타나지 않아요.",[("네, 보여요","field"),("어떤 칸인지 모르겠어요","help")]),
"field":("그 입력칸을 한 번 눌러주세요.","커서가 나타나거나 키보드가 열리는지 확인해요.",[("글을 입력할 수 있어요","menu"),("입력할 수 없어요","help")]),
"menu":("입력칸의 편집 메뉴를 열어주세요.","휴대폰은 입력칸을 길게, 컴퓨터는 입력칸에서 오른쪽 마우스 버튼을 눌러보세요.",[("붙여넣기가 보여요","paste"),("메뉴가 안 떠요","help"),("붙여넣기가 없어요","recopy")]),
"paste":("붙여넣기를 한 번 눌러주세요.","아직 보내기 버튼은 누르지 마세요. 비밀번호나 인증번호를 붙이지 마세요.",[("글이 나타났어요","verify"),("안 나타났어요","help")]),
"verify":("나타난 글이 복사하려던 내용과 같은가요?","내용을 확인한 뒤에만 직접 전송해주세요.",[("네, 맞아요","done"),("다른 내용이에요","recopy")]),
"recopy":("원래 복사하려던 글이 있는 화면을 열어주세요.","새로 복사하면 이전 복사 내용은 바뀔 수 있어요.",[("원래 글이 보여요","copy"),("찾지 못했어요","help")]),
"copy":("원래 글의 선택 메뉴에서 복사를 눌러주세요.","휴대폰 메시지는 길게 누르면 메뉴가 나올 수 있어요. 메뉴가 다르면 멈춰주세요.",[("복사했어요","retry"),("복사가 없어요","help")]),
"retry":("글을 넣을 앱의 입력칸으로 돌아가주세요.","이제 편집 메뉴에서 다시 확인할 수 있어요.",[("돌아왔어요","menu"),("어려워요","help")])},
"소리가 안 나요":{
"start":("어떤 소리가 안 들리나요?","통화·알림·영상 소리는 따로 조절될 수 있어요.",[("영상·음악 소리","play"),("전화 통화 소리","call"),("전화벨·알림","ring"),("잘 모르겠어요","help")]),
"play":("평소 이용하던 영상이나 음악을 재생해주세요.","낯선 링크는 열지 마세요. 데이터 요금이 걱정되면 여기서 멈춰도 돼요.",[("재생 중이에요","volume"),("재생 자체가 안 돼요","help")]),
"volume":("재생 중 소리 키우기 버튼을 한 번 눌러주세요.","휴대폰은 옆면, 컴퓨터는 스피커 표시가 있는 키일 수 있어요. 키를 모르면 누르지 마세요.",[("들려요","done"),("안 들려요","ear"),("버튼을 모르겠어요","help")]),
"ear":("이어폰이나 외부 스피커를 사용 중인가요?","소리가 휴대폰이나 컴퓨터가 아닌 연결 기기로 나갈 수 있어요.",[("네, 사용해요","disconnect"),("아니요","help"),("모르겠어요","help")]),
"disconnect":("무선 이어폰은 충전함에 넣거나 유선 이어폰을 빼주세요.","기기 등록 삭제나 블루투스 초기화는 하지 않아요.",[("이제 들려요","done"),("여전히 안 들려요","help")]),
"call":("현재 실제로 통화 중인가요?","휴대폰 기본 통화용 안내예요. 컴퓨터 회의 앱은 설정이 달라요.",[("휴대폰 통화 중이에요","callvol"),("통화 중이 아니에요","help"),("컴퓨터 통화예요","help")]),
"callvol":("통화 중 옆면의 소리 키우기 버튼을 한 번 눌러주세요.","볼륨을 갑자기 크게 올리지 마세요.",[("들려요","done"),("안 들려요","help")]),
"ring":("방해 금지 또는 집중 모드 표시가 있는지 확인해주세요.","이름과 위치가 기기마다 달라요. 모르면 설정을 바꾸지 마세요.",[("켜져 있어요","ringhelp"),("꺼져 있어요","help"),("찾지 못했어요","help")]),
"ringhelp":("집중 모드를 켜둔 이유를 가족과 확인해주세요.","끄면 잠자거나 회의 중에도 알림이 울릴 수 있어요. 이 도움말은 임의로 해제하지 않아요.",[("가족에게 확인할게요","help")])},
"글씨를 크게 하고 싶어요":{
"start":("설정을 열어주세요.","톱니바퀴 모양이에요. 아래 안내는 선택한 기기에 맞춰 표시해요.",[("열었어요","search"),("못 찾겠어요","help")]),
"search":("설정에서 글자 크기 관련 항목을 찾아주세요.","기기에 맞는 검색어를 아래에 표시해요. 메뉴 이름은 버전마다 달라요.",[("크기 조절 항목이 보여요","adjust"),("찾지 못했어요","help")]),
"adjust":("크기 조절 막대를 조금만 큰 쪽으로 움직여주세요.","해상도나 화면 전체 배율이 아니라 글자 크기 항목인지 확인해주세요.",[("읽기 편해졌어요","apply"),("화면이 달라요","help")]),
"apply":("적용 버튼이 따로 보이나요?","일부 기기는 바로 반영되고, 일부는 적용 버튼을 눌러야 해요.",[("보여요","applytap"),("없고 글씨가 커졌어요","done"),("없고 바뀌지도 않았어요","help")]),
"applytap":("적용 버튼을 한 번 눌러주세요.","지원되는 앱에만 반영될 수 있어요.",[("이제 편해요","done"),("바뀌지 않았어요","help")])},
"인터넷이 안 돼요":{
"start":("평소 이용하던 다른 사이트 하나도 안 열리나요?","사이트 한 곳만의 장애인지 먼저 구분해요.",[("다른 사이트는 열려요","single"),("다른 사이트도 안 열려요","connection"),("확인이 어려워요","help")]),
"single":("문제가 있는 서비스의 공식 장애 안내를 확인해주세요.","다른 사이트가 된다고 해당 서비스가 안전하다는 뜻은 아니에요. 보안 경고를 무시하지 마세요.",[("나중에 다시 확인할게요","help")]),
"connection":("어떤 연결을 사용하나요?","요금이 발생할 수 있으니 모바일 데이터를 임의로 켜지 마세요.",[("와이파이","wifi"),("컴퓨터 인터넷 선","cable"),("모바일 데이터","data"),("모르겠어요","help")]),
"wifi":("설정의 Wi-Fi에서 평소 네트워크 이름을 확인해주세요.","모르는 무료 네트워크에 연결하지 마세요. 암호를 이 앱에 입력하지 마세요.",[("평소 이름에 연결돼 있어요","other"),("연결이 안 됐어요","wifisupport"),("이름을 모르겠어요","help")]),
"wifisupport":("가족에게 올바른 네트워크 이름을 확인해주세요.","확인되지 않은 네트워크로 바꾸거나 저장된 암호를 삭제하지 마세요.",[("가족에게 요청할게요","help")]),
"cable":("컴퓨터의 인터넷 선이 빠져 보이는지 눈으로 확인해주세요.","선 종류를 모르면 뽑거나 억지로 꽂지 마세요.",[("연결되어 보여요","other"),("잘 모르겠어요","help")]),
"other":("같은 네트워크의 다른 기기는 인터넷이 되나요?","다른 기기가 없으면 확인하지 않아도 괜찮아요.",[("다른 기기는 돼요","help"),("다른 기기도 안 돼요","provider"),("확인할 기기가 없어요","help")]),
"provider":("통신사 공식 고객센터에 연결 장애를 문의해주세요.","공유기 초기화 버튼을 누르거나 보안 설정을 끄지 마세요.",[("도움을 요청할게요","help")]),
"data":("통신사 공식 앱이나 공식 고객센터에서 회선 상태를 확인해주세요.","신호·요금제·사용량 문제는 원인이 달라요. 추가 요금제 가입부터 하지 마세요.",[("공식 지원을 이용할게요","help")])},
"카카오톡으로 사진 보내기":{
"start":("휴대폰 카카오톡에서 받을 사람의 채팅방을 열어주세요.","컴퓨터 카카오톡은 구성이 달라 이 경로에서 안내하지 않아요.",[("휴대폰 채팅방을 열었어요","recipient"),("컴퓨터예요","help"),("어려워요","help")]),
"recipient":("받을 사람의 이름과 프로필이 맞는지 확인해주세요.","동명이인이나 사칭 계정일 수 있어요. 확신이 없으면 보내지 마세요.",[("확인했어요","plus"),("확신이 없어요","help")]),
"plus":("입력칸 옆의 더하기 버튼을 눌러주세요.","버튼이 보이지 않으면 다른 버튼을 추측해서 누르지 마세요.",[("앨범이나 사진이 보여요","album"),("화면이 달라요","help")]),
"album":("앨범 또는 사진을 선택해주세요.","권한을 요청하면 필요한 사진만 허용하는 선택을 고려하세요.",[("사진 목록이 나와요","select"),("권한이나 화면이 어려워요","help")]),
"select":("보낼 사진 한 장을 선택해주세요.","선택만 하는 단계예요. 민감한 사진은 보내지 마세요.",[("선택했어요","review"),("찾지 못했어요","help")]),
"review":("사진에 개인정보가 없는지 확인해주세요.","이 앱은 사진을 보거나 개인정보를 가리지 못해요. 잘못 보낸 사진은 완전히 회수되지 않을 수 있어요.",[("전송해도 괜찮아요","send"),("보내지 않을게요","help")]),
"send":("받는 사람이 맞다면 보내기를 한 번 눌러주세요.","이미 전송된 것 같으면 반복해서 누르지 마세요.",[("사진이 채팅방에 보여요","done"),("전송이 안 돼요","help")])},
"앱이 열리지 않아요":{
"start":("다른 앱은 열리나요?","기기 전체 문제인지 앱 하나의 문제인지 구분해요.",[("다른 앱은 열려요","unsaved"),("다른 앱도 안 돼요","help")]),
"unsaved":("문제가 있는 앱에 저장하지 않은 내용이 있나요?","작성 중인 글이나 진행 중인 결제가 있으면 함부로 종료하지 마세요.",[("없어요","home"),("있거나 모르겠어요","help")]),
"home":("홈 화면으로 나와주세요.","강제 종료·앱 삭제·데이터 지우기는 하지 않아요.",[("나왔어요","reopen"),("못 나가겠어요","help")]),
"reopen":("해당 앱을 다시 열어주세요.","반복해서 여러 번 누르지 마세요.",[("이제 열려요","done"),("여전히 안 열려요","official")]),
"official":("앱의 공식 장애 또는 업데이트 안내를 확인해주세요.","재설치하면 자료가 없어질 수 있어요. 가족이나 공식 지원과 백업을 먼저 확인해주세요.",[("공식 지원을 이용할게요","help")])},
"의심스러운 문자·전화":{
"start":("이미 링크를 누르거나 정보를 전달했나요?","메시지 내용만으로 안전하다고 판단하지 않아요.",[("아직 아무것도 안 했어요","stop"),("링크만 열었어요","clicked"),("돈·정보·인증번호를 전달했어요","urgent"),("원격 제어를 허용했어요","urgent")]),
"stop":("링크 클릭이나 송금을 하지 말아주세요.","가족·택배·기관을 사칭할 수 있어요.",[("멈췄어요","confirm")]),
"confirm":("별도로 확인한 공식 앱이나 평소 저장한 번호로 확인해주세요.","문자에 적힌 전화번호나 링크를 이용하지 마세요.",[("확인할 도움을 요청할게요","help")]),
"clicked":("열린 페이지에 정보를 입력하거나 앱을 설치하지 마세요.","이미 내려받은 파일을 실행하지 마세요. 이 앱은 감염 여부를 진단하지 못해요.",[("멈췄어요","confirm"),("설치·입력도 했어요","urgent")]),
"urgent":("다른 안전한 전화로 금융회사 또는 경찰에 즉시 도움을 요청해주세요.","한국에서는 범죄 신고 112를 이용할 수 있어요. 추가 송금·인증 승인·원격 제어 요청에 응하지 마세요. 이 앱은 신고를 대신하지 못해요.",[("도움을 요청할게요","help")])},
"충전·과열·배터리":{
"start":("물기·부풀음·심한 열·타는 냄새가 있나요?","연기나 불꽃이 있으면 가까이 가지 말고 안전한 곳으로 이동해 긴급 도움을 요청하세요.",[("있어요","hazard"),("없어요","charger"),("판단하기 어려워요","hazard")]),
"hazard":("충전과 기기 사용을 멈춰주세요.","안전하게 접근할 수 없다면 만지지 마세요. 분해·누르기·열풍 건조를 하지 마세요.",[("공식 수리 도움을 받을게요","help")]),
"charger":("정상적인 호환 충전기를 연결해주세요.","규격을 모르거나 선이 손상되었으면 연결하지 마세요.",[("연결했어요","indicator"),("충전기 상태를 모르겠어요","help")]),
"indicator":("충전 표시가 나타나나요?","단자에 금속 도구를 넣지 마세요. 표시가 늦게 나타날 수 있어요.",[("나타나요","done"),("안 나타나요","help"),("물기·온도 경고가 떠요","hazard")])}
}
TERMINALS={"done","help"}
TEXT_HINTS={
"갤럭시·안드로이드":"설정 검색: 글자 크기. 제조사에 따라 글자 크기와 스타일 같은 이름이에요.",
"아이폰·아이패드":"설정 → 디스플레이 및 밝기 → 텍스트 크기. 메뉴가 다르면 설정에서 텍스트 크기를 검색하세요.",
"윈도우 컴퓨터":"설정에서 텍스트 크기를 검색하세요. 화면 해상도 항목과 혼동하지 마세요.",
"맥 컴퓨터":"시스템 설정에서 텍스트 크기를 검색하세요. 버전에 따라 지원하지 않을 수 있어요.",
"잘 모르겠어요":"기기를 확인하기 전 크기 설정을 바꾸지 말고 가족에게 도움을 요청해주세요."}
def config(name):
    try:return str(st.secrets.get(name,""))
    except Exception:return ""

def inbox_ready():
    return bool(config("SUPABASE_URL").startswith("https://") and config("SUPABASE_SERVICE_ROLE_KEY"))

def db_request(method,**kwargs):
    url=config("SUPABASE_URL").rstrip("/")+"/rest/v1/help_messages"
    key=config("SUPABASE_SERVICE_ROLE_KEY")
    headers={"apikey":key,"Authorization":"Bearer "+key,"Content-Type":"application/json"}
    headers.update(kwargs.pop("headers",{}))
    response=requests.request(method,url,headers=headers,timeout=20,**kwargs)
    response.raise_for_status()
    return response

def admin_page():
    st.title("개발자 메시지함")
    expected=config("ADMIN_PASSWORD_SHA256")
    if len(expected)!=64 or not inbox_ready():
        st.write("관리자 설정이 완료되지 않았어요.");st.stop()
    if time.time()>st.session_state.get("admin_until",0):
        if time.time()<st.session_state.get("login_lock",0):
            st.write("잠시 뒤 다시 로그인해주세요.");st.stop()
        with st.form("admin_login"):
            password=st.text_input("관리자 비밀번호",type="password")
            login=st.form_submit_button("로그인")
        if login:
            digest=hashlib.sha256(password.encode()).hexdigest()
            if hmac.compare_digest(digest,expected):
                st.session_state.admin_until=time.time()+1800
                st.session_state.login_fail=0;st.rerun()
            else:
                st.session_state.login_fail=st.session_state.get("login_fail",0)+1
                if st.session_state.login_fail>=5:st.session_state.login_lock=time.time()+300
                st.write("로그인 정보를 확인해주세요.")
        st.stop()
    if st.button("로그아웃"):
        st.session_state.admin_until=0;st.rerun()
    st.caption("30분 뒤 다시 로그인해야 해요. 최신 100건을 표시해요. 오래된 건은 날짜 조건을 바꿔 조회해주세요.")
    before=st.text_input("이 날짜 이전 조회 (선택, 예: 2026-12-31)")
    try:
        params={"select":"id,created_at,message,context","order":"created_at.desc","limit":"100"}
        if before:
            import datetime
            datetime.date.fromisoformat(before);params["created_at"]="lt."+before
        rows=db_request("GET",params=params).json()
        if not rows:st.write("접수된 메시지가 없어요.")
        for row in rows:
            with st.expander(str(row["created_at"])+" · "+row["id"]):
                st.text(row["message"])
                if row.get("context"):st.text(row["context"])
                ok=st.checkbox("이 메시지를 영구 삭제할게요",key="delok_"+row["id"])
                if st.button("삭제",key="delete_"+row["id"],disabled=not ok):
                    db_request("DELETE",params={"id":"eq."+row["id"]});st.rerun()
    except Exception:st.write("목록을 불러오지 못했어요. 날짜 또는 저장소 연결을 확인해주세요.")
    st.stop()

if st.query_params.get("view")=="admin":
    admin_page()

s=st.session_state
if s.get("build") not in {VERSION,"선택형 도움말 3.0","선택형 도움말 3.1"}:
    s.clear();s.update(build=VERSION,topic=None,device=None,node="start",trail=[],family=False,rev=0,miss=0,confirm_done=False,entered=False)
s.build=VERSION
def move(target,label):
    old=s.node
    s.trail.append({"node":old,"answer":label})
    s.node=target;s.rev+=1;s.miss=0;s.confirm_done=False
    st.rerun()
def restart():
    size=s.get("font_size",24);s.clear();s.font_size=size;st.rerun()
def summary():
    flow=FLOWS.get(s.topic,{})
    lines=["기기 사용 도움을 부탁드려요.",f"기기: {s.device or '아직 모름'}",f"문제: {s.topic or '미선택'}"]
    for item in s.trail:
        text=flow.get(item['node'],('확인',))[0]
        lines.append(f"- {text} / 선택: {item['answer']}")
    lines.append("현재 상태: "+("해결 확인됨" if s.node=="done" else "도움 필요" if s.node=="help" else "확인 중"))
    return "\n".join(lines)

# 운영체제 테마 자동 감지 및 사용자 선택
size=s.get("font_size",24)
theme=s.get("appearance","자동 (기기 설정)")
dark="--page:#151c28;--text:#f4f7fc;--muted:#c4d5e8;--line:#6da9df;"
light="--page:#ffffff;--text:#111827;--muted:#465c75;--line:#1673b8;"
variables=dark if theme=="다크" else light
css="""
:root { VARS color-scheme:light; }
.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"] {background:var(--page)!important;color:var(--text)!important;}
.stApp p,.stApp label,.stApp li,.stApp h1,.stApp h2,.stApp h3,.stApp summary {color:var(--text)!important;}
.stApp p,.stApp label,.stApp li {font-size:SIZEpx!important;line-height:1.65;}
[data-testid="stCaptionContainer"] p {color:var(--muted)!important;}
.block-container {max-width:760px;padding-top:4.5rem;}
h1 {border-bottom:3px solid var(--line);padding-bottom:12px!important;}
/* 入力部はダークモードでも白い紙として表示 */
[data-testid="stTextArea"] [data-baseweb="textarea"],
[data-testid="stTextInput"] [data-baseweb="input"],
textarea,input:not([type="checkbox"]) {background:#fff!important;color:#111827!important;-webkit-text-fill-color:#111827!important;caret-color:#111827!important;}
textarea::placeholder,input::placeholder {color:#526070!important;-webkit-text-fill-color:#526070!important;}
.stButton button,.stDownloadButton button,[data-testid="stFormSubmitButton"] button {background:#fff!important;color:#123e65!important;border:1px solid #86add0!important;border-radius:10px!important;min-height:56px!important;height:auto!important;padding:10px 14px!important;}
.stButton button *, .stDownloadButton button *,[data-testid="stFormSubmitButton"] button * {color:#123e65!important;white-space:normal!important;overflow-wrap:anywhere!important;visibility:visible!important;}
button:focus-visible,textarea:focus-visible,input:focus-visible {outline:3px solid #318dd0!important;outline-offset:3px;}
button:disabled {opacity:.45!important;}
[data-testid="stForm"], [data-testid="stExpander"] {border-color:var(--line)!important;background:transparent!important;}
[data-testid="stCheckbox"] [data-baseweb="checkbox"] > span:first-child {background:#fff!important;border:2px solid #3978aa!important;}
[data-testid="stCheckbox"] svg {fill:#155a91!important;}
[data-testid="stAlert"] {background:transparent!important;color:var(--text)!important;}
[data-testid="stHorizontalBlock"] {gap:12px!important;}
[data-testid="stColumn"] {min-width:0!important;}
.brand-cover {text-align:center;margin:20px auto;}
.brand-title {font-size:34px;font-weight:800;color:var(--text);}
.st-key-nav_previous button,.st-key-nav_home button {border:0!important;background:transparent!important;min-height:48px!important;height:auto!important;width:100%!important;padding:6px 4px!important;overflow:visible!important;}
.st-key-nav_previous,.st-key-nav_home {min-width:0!important;}
.st-key-nav_previous button *,.st-key-nav_home button * {font-size:18px!important;color:var(--text)!important;}
[data-testid="stMainBlockContainer"] {animation:appear .3s ease-out;}
@keyframes appear {from {opacity:.5;} to {opacity:1;}}
@media(prefers-reduced-motion:reduce) {* {animation:none!important;transition:none!important;}}
""".replace("VARS",variables).replace("SIZE",str(size))
if theme=="자동 (기기 설정)":
    css+="@media(prefers-color-scheme:dark){:root{"+dark+"}}"
st.markdown("<style>"+css+"</style>",unsafe_allow_html=True)

def brand():
    # 참고 이미지의 파란 앱 아이콘 구성을 응용한 독자적인 휴대폰 로고입니다.
    st.markdown('''<div class="brand-cover"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="180" height="180" role="img" aria-label="파란 바탕의 휴대폰과 확인 표시 로고"><rect x="4" y="4" width="232" height="232" rx="44" fill="#087dbd" stroke="#00548b" stroke-width="8"/><rect x="77" y="32" width="86" height="135" rx="16" fill="none" stroke="white" stroke-width="9"/><path d="M106 46h28M110 152h20" stroke="white" stroke-width="6" stroke-linecap="round"/><path d="m91 100 20 20 39-46" fill="none" stroke="white" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/><text x="120" y="207" text-anchor="middle" fill="white" font-family="sans-serif" font-weight="bold" font-size="24">차근차근</text></svg><div class="brand-title">차근차근 기기 도우미</div></div>''',unsafe_allow_html=True)

if not s.get("entered",False):
    brand()
    st.header("막히는 순간, 하나씩 함께 확인해요.")
    st.write("휴대폰과 컴퓨터가 어려울 때, 문제를 고르고 화면에서 확인한 답을 눌러주세요. 다음에 할 일을 한 가지씩 안내해드려요.")
    st.write("소리 · 글자 크기 · 복사와 붙여넣기 · 인터넷 · 카카오톡 사진 보내기 등을 도와드려요.")
    st.write("이 앱은 AI가 아니에요. 화면을 보거나 기기를 조작하지 않아요. 준비된 도움말을 선택한 답에 따라 보여드려요.")
    st.write("가입이나 API 결제가 없어요. 모르는 화면에서는 멈추고 가족에게 도움을 요청할 수 있어요.")
    if st.button("시작하기 →",key="enter_app"):
        s.entered=True
        st.rerun()
    st.caption(VERSION)
    st.stop()

nav_previous,nav_home=st.columns(2)
with nav_previous:
    if st.button("← 이전",key="nav_previous",disabled=s.topic is None and not s.family and not s.get("home_snapshot")):
        if s.family:
            s.family=False
        elif s.topic is None and s.get("home_snapshot"):
            saved=s.pop("home_snapshot")
            s.update(saved)
        elif s.confirm_done:
            s.confirm_done=False
        elif s.trail:
            item=s.trail.pop()
            s.node=item["node"]
        elif s.device is not None:
            s.device=None
        else:
            s.topic=None
        s.rev+=1
        s.miss=0
        st.rerun()
with nav_home:
    if st.button("⌂ 홈",key="nav_home"):
        if s.topic is not None:
            s.home_snapshot={k:s[k] for k in ["topic","device","node","trail","confirm_done"]}
        s.topic=None;s.device=None;s.node="start";s.trail=[];s.family=False;s.confirm_done=False;s.miss=0;s.rev+=1
        st.rerun()
st.title("어떤 도움이 필요하세요?")
st.caption("차근차근 기기 도우미 · "+VERSION)
with st.expander("글자 크기 · 이용 안내"):
    if st.button("앱 소개 보기",key="back_intro"):
        s.entered=False
        st.rerun()
    st.selectbox("화면 테마",["자동 (기기 설정)","라이트","다크"],key="appearance")
    st.slider("글자 크기",20,32,key="font_size",value=24)
    st.write("기록은 현재 접속에만 임시 유지돼요. 새로고침이나 연결 종료 시 사라질 수 있어요. 이 앱은 대화를 영구 저장하거나 외부 AI로 보내지 않아요. 호스팅 서비스의 접속 기록은 별개예요.")
    st.write("사진 분석·녹음·음성 읽기·직접 기기 조작 기능은 없어요. 메뉴는 버전에 따라 달라요. 비밀번호·인증번호는 입력하거나 공유하지 마세요.")
if s.family:
    st.header("개발자에게 도움 요청")
    st.write("가족에게 자동 전달되는 기능이 아니에요. 앱 개발자가 확인하는 비공개 메시지함이에요. 실시간 상담이나 긴급 신고용이 아니며 답변을 보장하지 않아요.")
    st.write("이름·연락처·비밀번호·인증번호·금융정보는 적지 마세요. 개발자는 메시지와 함께 전송을 선택한 진행 요약만 볼 수 있어요.")
    if s.get("sent_notice"):
        st.success("메시지를 접수했어요. 이 화면에서는 답변을 받을 수 없어요.")
    if not inbox_ready():
        st.write("메시지함 연결을 준비 중이에요. 아직 전송할 수 없어요.")
    else:
        with st.form("help_message",clear_on_submit=False):
            message=st.text_area("어떤 점이 어려우신가요?",placeholder="이 상자 안에 어려운 점을 입력해주세요. 예: 카카오톡에서 사진 보내는 버튼을 못 찾겠어요.",max_chars=2000,height=180)
            attach=st.checkbox("선택한 문제와 진행 요약도 함께 보내기",value=False)
            consent=st.checkbox("내용이 외부 저장소에 저장되고 개발자가 확인하는 데 동의해요")
            st.caption("기록은 Supabase에 저장돼요. 개발자에게 요청해 삭제할 수 있어요. 아래 접수번호를 보관해주세요. 서비스 제공자의 백업·운영 기록은 별개예요.")
            submit=st.form_submit_button("메시지 보내기")
        if submit:
            if not consent or not message.strip():st.write("내용을 작성하고 저장 동의를 확인해주세요.")
            elif time.time()-s.get("last_sent",0)<60:st.write("중복 전송을 막기 위해 잠시 기다려주세요.")
            else:
                token=s.setdefault("submission_id",secrets.token_hex(16))
                payload={"id":token,"message":message.strip(),"context":summary() if attach else ""}
                try:
                    db_request("POST",json=payload,headers={"Prefer":"resolution=ignore-duplicates,return=minimal"},params={"on_conflict":"id"})
                    s.last_sent=time.time();s.sent_notice=True;s.receipt=token;s.pop("submission_id",None)
                    st.success("메시지를 접수했어요.")
                except Exception:
                    st.write("접수 여부를 확인하지 못했어요. 작성한 내용을 유지했으니 잠시 뒤 다시 시도해주세요.")
    if s.get("receipt"):st.write("최근 접수번호: "+s.receipt)
    if st.button("안내로 돌아가기"):s.family=False;st.rerun()
elif s.topic is None:
    st.write("도움이 필요한 항목을 눌러주세요.")
    icons=["▤","♪","가","◎","▧","⚙","⚠","ϟ"]
    topics=list(FLOWS)
    for start in range(0,len(topics),2):
        cols=st.columns(2)
        for offset,col in enumerate(cols):
            i=start+offset
            if i<len(topics):
                topic=topics[i]
                with col:
                    if st.button(topic,key=topic,use_container_width=True):
                        s.topic=topic
                        st.rerun()
    st.caption("해당 문제가 없으면 아래 가족 도움 요청을 이용해주세요. 지원 범위를 억지로 추측하지 않아요.")
elif s.device is None:
    st.header("어떤 기기를 사용하시나요?")
    for device in DEVICES:
        if st.button(device):s.device=device;st.rerun()
else:
    st.subheader(s.topic)
    st.caption(s.device)
    if s.node=="done":
        st.write("해결됐다고 확인해주셨어요. 수고하셨습니다.")
        if st.button("다시 문제가 생겼어요"):move("help","문제가 다시 생김")
    elif s.node=="help":
        st.write("여기서 잠시 멈출게요. 같은 방법을 반복하거나 모르는 버튼을 누르지 않으셔도 괜찮아요.")
        st.write("가족이나 제조사·서비스의 공식 지원에 지금까지 확인한 내용을 전달해주세요.")
    elif s.confirm_done:
        st.header("이제 원하던 대로 잘 되나요?")
        if st.button("네, 해결됐어요"):move("done","직접 해결 확인")
        if st.button("아직 안 됐어요"):s.confirm_done=False;st.rerun()
    else:
        action,hint,choices=FLOWS[s.topic][s.node]
        st.header(action)
        st.write(hint)
        if s.topic=="글씨를 크게 하고 싶어요" and s.node=="search":
            st.write(TEXT_HINTS[s.device])
        for label,target in choices:
            if st.button(label,key=f"choice_{s.node}_{label}"):
                # 되풀이 경로는 두 번 이상 자동 반복하지 않습니다.
                if target not in TERMINALS and sum(i['node']==target for i in s.trail)>=2:
                    move("help",label+" / 반복 중단")
                move(target,label)
        with st.expander("설명이 어렵거나 화면이 다른가요?"):
            if st.button("못 찾겠어요"):
                s.miss+=1
                if s.miss>=2:move("help","두 번 찾지 못함")
                st.rerun()
            if s.miss:st.write("설명한 이름이 화면에 없으면 비슷한 버튼을 추측해 누르지 마세요. 가족에게 현재 화면을 확인해달라고 요청할 수 있어요.")
            if st.button("다른 화면이 나와요"):move("help","다른 화면이 나옴")
        if st.button("이미 해결됐어요"):s.confirm_done=True;st.rerun()
if not s.family:
    if st.button("개발자에게 도움 요청"):
        s.family=True;s.rev+=1;st.rerun()
st.caption("삭제·초기화·송금·보안 해제는 안내하지 않아요. 위험한 상황은 공식 지원이나 긴급 도움을 이용해주세요.")

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
VERSION="선택형 도움말 6.3"
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

# 실패는 문의가 아니라 사용자 선택형 추가 점검으로 연결합니다.
ALTERNATIVES={'복사한 글이 안 보여요': [('입력칸인지 확인', '글을 넣을 칸에 개인정보가 아닌 짧은 글자 한 개를 직접 입력해보세요.', '입력되지 않는다면 읽기 전용 화면일 수 있어요. 쓰기·답장·새 메시지 화면으로 이동해야 해요.'), ('컴퓨터 단축키 사용', '입력칸을 선택한 뒤 윈도우는 Ctrl+V, 맥은 Command+V를 눌러주세요.', '휴대폰은 이 방법 대신 입력칸 길게 누르기를 사용해요. 자동 전송하지 말고 결과만 확인해주세요.'), ('원문에서 복사 다시 확인', '원래 글을 선택해 복사를 눌러주세요.', '복사와 공유는 달라요. 선택 메뉴에 복사가 없다면 앱이 복사를 제한할 수 있어요.'), ('다른 입력칸에서 시험', '메모 앱의 새 메모에 붙여넣기를 시험해주세요.', '비밀번호·인증번호는 사용하지 마세요. 여기에 되면 원래 앱 입력칸이나 형식 문제일 수 있어요.'), ('복사가 제한된 문서', '원문을 열어 글자를 선택할 수 있는지 확인해주세요.', '사진 속 글자·일부 PDF는 일반 복사가 안 돼요. 짧은 내용은 직접 입력한 뒤 원문과 비교하는 방법이 있어요.')], '소리가 안 나요': [('앱 하나만 무음인지 확인', '다른 익숙한 앱에서 소리를 재생해주세요.', '다른 앱은 들리면 기기 전체보다 원래 앱의 음소거·재생 문제를 확인해요.'), ('재생 화면 음소거 확인', '영상의 스피커 표시가 음소거인지 확인해주세요.', '음소거가 표시되면 해당 영상의 음소거 버튼을 눌러 해제할 수 있어요. 광고는 누르지 마세요.'), ('소리 출력 기기 확인', '소리 설정에서 현재 출력 기기 이름을 확인해주세요.', '내장 스피커 대신 모니터·이어폰이 선택돼 있을 수 있어요. 본인이 아는 출력 기기만 선택하세요.'), ('벨소리·집중 모드 확인', '소리 설정에서 벨소리 음량이 낮은지 확인해주세요.', '본인이 켜둔 집중 모드나 무음 모드가 원인이라면 알림이 다시 울려도 괜찮은지 확인한 뒤 해제하세요.'), ('통화 소리 구분', '통화 중 스피커폰 버튼을 한 번 눌러 소리가 달라지는지 확인해주세요.', '휴대폰 통화에만 해당해요. 주변에 통화가 들리므로 사적인 통화에서는 하지 마세요.')], '글씨를 크게 하고 싶어요': [('설정 검색 사용', '설정 검색창에 글자 크기 또는 텍스트 크기를 입력해주세요.', '검색 결과가 없다면 기기별 메뉴 안내를 선택해주세요.'), ('안드로이드 경로', '설정에서 디스플레이 항목을 열어주세요.', '다음 화면에서 글자 크기 또는 글자 크기와 스타일을 찾고 조절해요. 제조사마다 달라요.'), ('아이폰 경로', '설정의 디스플레이 및 밝기를 열어주세요.', '텍스트 크기를 찾아 조금 키워요. 일부 앱에만 반영될 수 있어요.'), ('윈도우 경로', '시작 메뉴의 검색에 텍스트 크기를 입력해주세요.', '해당 설정에서 막대를 조절하고 적용해요. 화면 해상도는 바꾸지 않아요.'), ('웹페이지만 확대', '컴퓨터 브라우저 메뉴에서 확대/축소 항목을 찾아주세요.', '조금 키우고 페이지를 확인해요. 휴대폰은 두 손가락 벌리기가 허용되는 페이지에서만 가능해요.')], '인터넷이 안 돼요': [('와이파이 연결 다시 선택', 'Wi-Fi 목록에서 본인이 아는 평소 네트워크를 선택해주세요.', '암호를 모르면 임의로 입력하지 마세요. 네트워크 삭제·초기화는 필요 없어요.'), ('와이파이 껐다 켜기', '진행 중인 통화·다운로드가 없는지 확인해주세요.', '없다면 Wi-Fi를 껐다 켜고 평소 네트워크 연결을 확인할 수 있어요. 이때 다른 연결로 전환되면 데이터 요금이 생길 수 있어요.'), ('한 서비스만 안 됨', '같은 서비스의 공식 앱과 공식 웹사이트 중 다른 쪽을 열어보세요.', '이미 알고 있는 주소만 사용해요. 보안 경고가 뜨면 우회하지 마세요. 서비스 장애라면 기다려야 해요.'), ('브라우저 문제 구분', '설치돼 있는 다른 브라우저로 같은 공식 주소를 열어보세요.', '되면 원래 브라우저 문제일 수 있어요. 기록 삭제·보안 해제 없이 대체 브라우저를 이용할 수 있어요.'), ('여러 기기 모두 안 됨', '공유기 전원과 인터넷 표시등을 눈으로 확인해주세요.', '선이 빠졌는지 확인하되 RESET 버튼은 누르지 마세요. 전원·회선 장애는 통신사 확인이 필요할 수 있어요.')], '카카오톡으로 사진 보내기': [('채팅방 찾기', '카카오톡의 채팅 목록을 열어주세요.', '보낼 사람과의 기존 채팅방을 선택해요. 이름이 비슷하면 프로필을 다시 확인해요.'), ('사진 권한 확인', '휴대폰 설정에서 카카오톡의 사진 접근 권한을 확인해주세요.', '전체 사진을 허용할 필요 없이 보낼 사진만 허용하는 선택이 있을 수 있어요. Android는 앱 권한, iPhone은 앱 설정에서 찾아요.'), ('사진이 목록에 없음', '휴대폰 사진 앱에서 원래 사진이 실제로 열리는지 확인해주세요.', '클라우드에만 있거나 다른 폴더일 수 있어요. 원래 사진이 열리면 공유 기능을 대안으로 사용할 수 있어요.'), ('사진 앱에서 공유', '사진 앱에서 보낼 사진 한 장을 열고 공유 버튼을 찾아주세요.', '공유 대상에 카카오톡이 있으면 선택하고 상대방·사진을 재확인한 후 직접 전송해요.'), ('전송 지연 확인', '채팅방에서 사진에 전송 중 또는 실패 표시가 있는지 확인해주세요.', '이미 보내졌다면 재전송하지 마세요. 실패가 확실할 때 연결을 확인하고 한 번만 재시도해요.')], '앱이 열리지 않아요': [('장애 여부 구분', '앱의 공식 웹사이트가 정상적으로 열리는지 확인해주세요.', '웹도 안 되면 서비스 장애나 인터넷 문제일 수 있어요.'), ('저장 공간 확인', '기기 설정에서 저장 공간의 남은 용량을 확인해주세요.', '부족해도 자료를 바로 삭제하지 마세요. 다른 저장소로 백업한 뒤 필요 없는 항목을 직접 결정해야 해요.'), ('공식 업데이트 확인', '공식 앱 스토어에서 해당 앱에 업데이트가 있는지 확인해주세요.', '개발사와 앱 이름을 확인해요. 결제·로그인·진행 중 작업을 마치고 업데이트를 고려하세요.'), ('다른 앱도 멈춤', '작성 중인 작업이 있는지 확인해주세요.', '저장할 수 있는 작업은 저장하고 기기의 정상 재시작을 고려해요. 강제 종료·초기화는 하지 않아요.'), ('웹 버전 대안', '서비스가 제공하는 공식 웹 버전이 있는지 확인해주세요.', '공식 주소를 알고 있을 때만 이용해요. 앱 삭제나 재설치 없이 임시로 사용할 수 있어요.')], '의심스러운 문자·전화': [('아직 아무 행동 안 함', '문자 속 링크·전화번호 대신 평소 저장한 공식 연락처를 사용해주세요.', '이 앱은 진위를 판정하지 않아요. 답장·송금·인증 승인 없이 별도로 확인하는 것이 안전해요.'), ('링크만 열었음', '해당 페이지를 닫고 추가 다운로드·정보 입력을 중단해주세요.', '감염되지 않았다고 단정할 수는 없어요. 낯선 파일을 실행하지 말고 공식 보안 상담을 이용하세요.'), ('돈·정보 전달 또는 원격 제어', '다른 안전한 전화로 금융회사나 경찰에 즉시 연락해주세요.', '한국 범죄 신고 112. 즉시 대응이 필요한 상황이므로 개발자 답변을 기다리지 마세요.')], '충전·과열·배터리': [('위험 신호 다시 확인', '부풀음·냄새·물기·심한 열이 있는지 눈으로 확인해주세요.', '있거나 판단이 어려우면 충전·사용을 멈추고 공식 수리를 이용해요. 분해·가열·단자 청소 도구 사용 금지.'), ('전원 공급 확인', '같은 콘센트에서 다른 정상 기기가 작동하는지 안전하게 확인해주세요.', '젖었거나 손상된 콘센트는 만지지 마세요. 전기 작업은 하지 않아요.'), ('호환 케이블 대안', '손상 없는 호환 충전선이 이미 있다면 바꿔 연결해보세요.', '물기나 열이 있을 때는 시험하지 마세요. 규격이 불명확한 제품은 사용하지 마세요.'), ('완전 방전 가능성', '정상 호환 충전기에 연결한 뒤 잠시 기다려 표시를 다시 확인해주세요.', '제조사 권장 시간을 따르고 자리를 비우지 마세요. 열·냄새가 생기면 즉시 중단해요.'), ('계속 충전 안 됨', '충전선·전원 점검 결과를 정리해 공식 수리센터에 확인해주세요.', '내부 고장은 웹앱으로 수리할 수 없어요. 초기화나 배터리 분해는 하지 않아요.')]}

FAILURE_NOTES={'복사한 글이 안 보여요': ['직접 입력도 안 되면 붙여넣기 문제가 아니라 읽기 전용 화면일 가능성이 있어요. 답장·쓰기 화면인지 확인하거나 다른 입력칸에서 시험해보세요.', '단축키도 안 된다고 복사가 금지된 것은 아니에요. 원문 복사 여부와 입력칸을 나누어 확인해야 해요.', '복사 메뉴가 없으면 이미지·문서 형식 또는 앱 제한일 수 있어요. 제한을 우회하지 말고 직접 입력이나 제공자에게 텍스트 요청을 이용할 수 있어요.', '메모 앱에도 붙지 않으면 원문이 복사되지 않았거나 기기 간 복사 문제일 수 있어요. 같은 기기에서 원문을 다시 복사하거나 짧은 내용을 직접 입력해보세요.', '글자를 선택할 수 없다는 사실만으로 복사 금지라고 단정할 수는 없어요. 사진·스캔 문서는 텍스트가 없을 수 있어요. 명시적인 복사 제한이 있다면 일반 복사는 사용할 수 없으며 제한을 우회하지 않아요.'], '소리가 안 나요': ['다른 앱에서도 안 들리면 원래 영상 하나만의 문제는 아닐 수 있어요. 소리 출력 기기와 연결된 이어폰을 확인해보세요.', '영상 음소거를 풀어도 안 들리면 다른 앱 재생과 출력 기기를 나누어 확인해보세요.', '출력 기기를 확인해도 안 되면 앱 자체 음소거나 기기 문제일 수 있어요. 다른 앱에서 먼저 비교해보세요.', '벨소리와 통화·영상 음량은 다를 수 있어요. 어떤 소리가 안 나는지 다시 구분하면 다른 점검을 고를 수 있어요.', '스피커폰도 안 들리면 상대방 마이크나 통신 문제일 수도 있어요. 기기 고장이라고 단정하지 말고 다른 정상 통화와 비교하세요.'], '글씨를 크게 하고 싶어요': ['검색 결과가 없는 것은 그 기능이 없다는 확정 증거는 아니에요. 기기에 맞는 경로나 웹페이지 확대를 선택해보세요.', '제조사·버전에 따라 메뉴가 달라요. 설정 검색이나 해당 앱의 글자 크기 메뉴를 대안으로 이용해보세요.', '지원하지 않는 앱은 시스템 글자 크기를 따라 바뀌지 않을 수 있어요. 해당 앱의 표시 설정이나 웹 버전을 확인할 수 있어요.', '윈도우 버전에 따라 검색 결과가 달라요. 브라우저 글씨만 작다면 페이지 확대가 대안이에요. 해상도를 임의로 바꾸지 마세요.', '일부 앱·페이지는 확대를 제한해요. 시스템 텍스트 크기 또는 앱 자체 표시 설정을 확인해보세요.'], '인터넷이 안 돼요': ['알고 있는 네트워크에도 연결되지 않으면 암호·공유기·회선 문제를 구분해야 해요. 저장된 네트워크를 삭제하지 말고 다른 기기 결과를 확인하세요.', 'Wi-Fi 재연결로 해결되지 않으면 같은 조작을 반복하지 않아도 돼요. 다른 브라우저 또는 다른 기기로 범위를 좁혀보세요.', '서비스만 장애라면 기기 설정 변경으로 해결되지 않을 수 있어요. 공식 장애 안내와 복구 공지를 확인하고 기다리는 것이 대안이에요.', '다른 브라우저도 안 되면 원래 브라우저만의 문제는 아닐 수 있어요. 네트워크 연결과 다른 사이트를 확인하세요.', '여러 기기가 모두 안 되고 회선 장애가 확인되면 앱에서 복구할 수 없어요. 통신사의 복구를 기다리거나 본인이 동의한 별도 연결을 이용해야 해요. 데이터 요금에 유의하세요.'], '카카오톡으로 사진 보내기': ['대화방을 못 찾으면 사진 앱의 공유 경로를 이용할 수 있어요. 받는 사람의 신원을 확인하지 못하면 전송하지 마세요.', '사진 접근 권한을 확인해도 목록이 없으면 실제 사진의 저장 위치와 클라우드 다운로드 여부를 확인해보세요.', '사진 앱에서도 원본을 열지 못하면 카카오톡 전송보다 원본 접근 문제일 수 있어요. 원본 소유자에게 다시 요청하는 방법이 있어요.', '공유 목록에 카카오톡이 없거나 공유가 실패하면 채팅방의 사진 첨부 방식으로 시험할 수 있어요. 상대가 불확실하면 보내지 마세요.', '실패 표시가 계속되면 중복 전송하지 말고 인터넷 연결과 공식 장애 안내를 확인하세요. 급하면 상대와 합의한 다른 전달 수단을 이용하세요.'], '앱이 열리지 않아요': ['공식 사이트도 장애라면 기기 조작보다 복구를 기다리는 게 맞을 수 있어요. 웹 버전이 별도로 정상 운영되는지 확인할 수 있어요.', '공간이 충분한데 실행이 안 되면 용량만의 문제는 아닐 수 있어요. 공식 업데이트나 서비스 장애를 확인하세요.', '업데이트 후에도 안 되면 반복 설치하지 마세요. 웹 버전이 대안일 수 있어요. 재설치 전에는 자료 백업 여부를 확인해야 해요.', '정상 재시작 후에도 여러 앱이 멈추면 기기 점검이 필요할 수 있어요. 강제 초기화 대신 제조사 공식 진단을 이용하세요.', '공식 웹 버전도 없거나 안 열리면 현재 앱이 지원하는 안전한 우회 경로가 없을 수 있어요. 장애 복구를 기다리거나 공식 지원을 이용하세요.'], '의심스러운 문자·전화': ['진위를 확인할 수 없다면 응답하지 않고 보류해도 괜찮아요. 이미 알고 있던 연락처로 따로 확인하세요.', '감염 여부는 이 앱에서 확인할 수 없어요. 실행·정보 입력을 하지 말고 한국에서는 보안 상담 118 등 공식 지원을 이용할 수 있어요.', '금융 피해·정보 전달·원격 제어 상황은 일반 도움말로 해결할 수 없어요. 한국에서는 경찰 112 및 해당 금융회사에 즉시 연락하고 개발자 답변을 기다리지 마세요.'], '충전·과열·배터리': ['위험 신호가 있거나 판단하기 어렵다면 다른 충전 시험을 하지 마세요. 사용을 멈추고 공식 수리를 이용하세요. 연기·불꽃이면 안전한 곳으로 이동하고 긴급 도움을 요청하세요.', '전원 공급이 의심되면 해당 콘센트를 사용하지 마세요. 손상 없는 안전한 전원과 호환 충전기만 이용하고 전기 작업은 하지 마세요.', '정상 케이블로도 안 되면 케이블만의 문제는 아닐 수 있어요. 물기·열을 확인하고 안전한 조건에서만 다음 확인을 진행하세요.', '제조사 권장 대기 후에도 표시가 없다면 계속 충전하거나 버튼을 반복하지 마세요. 공식 수리에서 배터리·단자를 점검받아야 할 수 있어요.', '내부 고장이라면 앱 안에서 수리할 수 없어요. 공식 수리 예약과 백업 가능 여부 확인이 차선책이며 분해·초기화는 권하지 않아요.']}
for topic,items in ALTERNATIVES.items():
    flow=FLOWS[topic]
    for node,(action,hint,choices) in list(flow.items()):
        flow[node]=(action,hint,[(label,'alternatives' if target=='help' else target) for label,target in choices])
    flow['alternatives']=('다음 확인 방법을 선택해주세요.','실패한 방법의 결과 설명을 읽고 다른 방법을 선택할 수 있어요.',[(label,'alt_'+str(i)) for i,(label,_,_) in enumerate(items)]+[('처음 확인 질문으로 돌아가기','start')])
    for i,(label,action,hint) in enumerate(items):
        failure='failed_'+str(i)
        flow['alt_'+str(i)]=(action,hint,[('실제 결과 확인하기','check_'+str(i)),('해당하지 않거나 할 수 없어요',failure),('해봤지만 안 돼요',failure)])
        choices=[(other,'alt_'+str(j)) for j,(other,_,_) in enumerate(items) if j!=i]
        flow[failure]=('이 방법으로 해결되지 않은 경우',FAILURE_NOTES[topic][i],choices+[('처음 확인 질문부터 다시 구분하기','start')])
        flow['check_'+str(i)]=('실제로 문제가 해결됐나요?','안 됐다면 방금 시도의 결과에 맞는 설명과 차선책으로 이동해요.',[('네, 해결됐어요','done'),('아직 안 돼요',failure)])
    flow['check_result']=('다시 문제가 생겼나요?','기존에 시도한 내용을 참고해 다른 확인 방법을 선택하세요.',[('다른 방법 확인하기','alternatives'),('해결된 상태예요','done')])
    if topic=='복사한 글이 안 보여요':
        flow['failed_4']=(flow['failed_4'][0],flow['failed_4'][1],[('짧은 내용을 직접 입력하기','manual_text'),('제공자에게 텍스트 요청하기','request_text'),('복사 여부를 다른 입력칸에서 확인','alt_3')])
        flow['manual_text']=('원문을 보며 짧은 내용을 직접 입력해주세요.','개인정보는 이 앱에 입력하지 마세요. 원래 글을 넣으려던 앱에서 입력하고 원문과 비교하세요.',[('입력하고 확인했어요','check_4'),('직접 입력도 어려워요','request_text')])
        flow['request_text']=('문서 제공자에게 복사 가능한 텍스트나 접근 가능한 문서를 요청해주세요.','복사 제한이 명시됐다면 허가 없이 해제하지 않아요. 요청 후 전달을 기다려야 하며 아직 해결 완료는 아니에요.',[('다른 확인 방법 보기','alternatives'),('이전 원문 확인하기','recopy')])

# 기기별 도움말을 세션 데이터와 분리해 생성합니다.
def device_flow(topic,device):
    flow=dict(FLOWS[topic])
    mobile=device in ('갤럭시·안드로이드','아이폰·아이패드')
    computer=device in ('윈도우 컴퓨터','맥 컴퓨터')
    hidden=set()
    if topic=='복사한 글이 안 보여요':
        if not computer:hidden.add('alt_1')
        if computer:
            flow['menu']=('입력칸에서 마우스 오른쪽 버튼을 눌러주세요.','맥 트랙패드는 두 손가락 클릭으로 편집 메뉴를 열 수 있어요.',[('붙여넣기가 보여요','paste'),('메뉴가 안 떠요','failed_1'),('붙여넣기가 없어요','recopy')])
            flow['copy']=('원문에서 글자를 드래그해 선택한 뒤 복사해주세요.','윈도우는 Ctrl+C, 맥은 Command+C를 사용할 수 있어요.',[('복사했어요','retry'),('선택이나 복사가 안 돼요','failed_2')])
            if device=='맥 컴퓨터':
                flow['alt_1']=('입력칸을 선택한 뒤 Command+V를 눌러주세요.','아직 보내지 말고 붙여넣은 내용부터 확인해요.',flow['alt_1'][2])
            else:flow['alt_1']=('입력칸을 선택한 뒤 Ctrl+V를 눌러주세요.','아직 보내지 말고 붙여넣은 내용부터 확인해요.',flow['alt_1'][2])
        elif mobile:
            flow['menu']=('입력칸을 잠시 길게 눌러주세요.','손을 떼고 편집 메뉴가 나타나는지 확인해요.',[('붙여넣기가 보여요','paste'),('메뉴가 안 떠요','failed_0'),('붙여넣기가 없어요','recopy')])
            flow['copy']=('원래 글을 길게 눌러 복사 메뉴를 찾아주세요.','사진 속 글이나 제한된 문서는 일반 복사가 안 될 수 있어요.',[('복사했어요','retry'),('복사 메뉴가 없어요','failed_2')])
    if topic=='글씨를 크게 하고 싶어요':
        keep={'갤럭시·안드로이드':1,'아이폰·아이패드':2,'윈도우 컴퓨터':3}.get(device)
        hidden.update('alt_'+str(i) for i in (1,2,3) if i!=keep)
        if not computer:hidden.add('alt_4')
        if device=='맥 컴퓨터':
            flow['search']=('시스템 설정 검색창에서 텍스트 크기를 찾아주세요.','macOS 버전·앱에 따라 지원 범위가 달라요. 없으면 브라우저 확대 등 다른 방법을 선택할 수 있어요.',flow['search'][2])
        else:
            flow['search']=('설정 검색창에서 글자 크기 또는 텍스트 크기를 검색해주세요.',TEXT_HINTS.get(device,'기기 종류를 확인한 뒤 설정을 변경해주세요.'),flow['search'][2])
    if topic=='소리가 안 나요':
        if not mobile:hidden.add('alt_4')
        if computer:
            flow['start']=('어떤 소리가 안 들리나요?','기본 휴대폰 전화 안내는 컴퓨터에서 표시하지 않아요.',[('영상·음악 소리','play'),('회의 앱 소리','alternatives'),('알림 소리','alternatives')])
            flow['volume']=('작업 표시줄 또는 메뉴 막대의 소리 조절을 확인해주세요.','낮은 음량에서 조금씩 올려요.',flow['volume'][2])
    if topic=='카카오톡으로 사진 보내기' and computer:
        flow['start']=('컴퓨터 카카오톡에서 받을 사람의 채팅방을 열어주세요.','받는 사람이 맞는지 확인한 뒤 파일을 선택해야 해요.',[('열었어요','pc_attach'),('못 찾겠어요','alternatives')])
        flow['pc_attach']=('채팅방에서 파일 첨부 또는 클립 모양 버튼을 찾아주세요.','버전마다 아이콘이 달라요. 삭제·결제 버튼을 누르지 마세요.',[('파일 선택 창이 나와요','pc_file'),('못 찾겠어요','alt_3')])
        flow['pc_file']=('사진 파일 한 개를 선택해주세요.','개인정보가 없는지 미리 확인해요. 파일 선택만으로 전송될 수 있으니 받는 사람을 먼저 확인하세요.',[('채팅방에 사진이 보여요','done'),('안 보내졌어요','alt_4')])
        flow['alt_0']=('카카오톡 왼쪽 채팅 목록에서 기존 대화방을 찾아주세요.','새 상대방은 이름이 같아도 신원을 확인해야 해요.',flow['alt_0'][2])
        flow['alt_3']=('파일 탐색기 또는 Finder에서 사진 한 개를 찾아주세요.','받는 사람을 확인한 채팅방으로 드래그하는 대안이 있어요. 자동 전송될 수 있으니 민감한 사진은 사용하지 마세요.',flow['alt_3'][2])
        flow['alt_2']=('컴퓨터의 사진 파일을 기본 사진 보기 앱으로 열어주세요.','열리지 않으면 전송보다 원본 파일 접근 문제부터 확인해요.',flow['alt_2'][2])
        hidden.add('alt_1')
    # 차선책·결과 설명에서도 다른 기기의 방법을 제외합니다.
    for key,(action,hint,choices) in list(flow.items()):
        flow[key]=(action,hint,[(label,target) for label,target in choices if target not in hidden])
    if topic=='충전·과열·배터리':
        # 위험 확인 뒤에는 충전 시험으로 되돌리지 않습니다.
        for key in ('hazard','failed_0','failed_4'):
            action,hint,_=flow[key]
            flow[key]=(action,hint,[])
    if topic=='의심스러운 문자·전화':
        for key in ('urgent','failed_2'):
            action,hint,_=flow[key]
            flow[key]=(action,hint,[])
    return flow

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
        params={"select":"id,created_at,message,context,reply,replied_at","order":"created_at.desc","limit":"100"}
        if before:
            import datetime
            datetime.date.fromisoformat(before);params["created_at"]="lt."+before
        rows=db_request("GET",params=params).json()
        if not rows:st.write("접수된 메시지가 없어요.")
        for row in rows:
            with st.expander(str(row["created_at"])+" · "+row["id"]):
                st.text(row["message"])
                if row.get("context"):st.text(row["context"])
                st.write("기존 답변: "+(row.get("reply") or "아직 없음"))
                with st.form("reply_form_"+row["id"]):
                    answer=st.text_area("사용자에게 보낼 답변",value=row.get("reply") or "",max_chars=4000)
                    send=st.form_submit_button("답변 저장")
                if send:
                    if not answer.strip():st.write("답변을 입력해주세요.")
                    else:
                        import datetime
                        db_request("PATCH",params={"id":"eq."+row["id"]},json={"reply":answer.strip(),"replied_at":datetime.datetime.now(datetime.timezone.utc).isoformat()})
                        st.rerun()
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
dark="--page:#261e18;--text:#fff4e8;--muted:#e5c9b0;--line:#eda76e;"
light="--page:#fff7ed;--text:#33251b;--muted:#675345;--line:#b65d20;"
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
                payload={"id":token,"message":message.strip(),"context":summary() if attach else "","lookup_hash":hashlib.sha256(token.encode()).hexdigest()}
                try:
                    db_request("POST",json=payload,headers={"Prefer":"resolution=ignore-duplicates,return=minimal"},params={"on_conflict":"id"})
                    s.last_sent=time.time();s.sent_notice=True;s.receipt=token;s.pop("submission_id",None)
                    st.write("메시지를 접수했어요. 接수번호를 보관하고 내 문의·답변 확인에서 답변을 확인하세요.".replace("接수", "접수"))
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
        if st.button("다시 문제가 생겼어요"):move("alternatives","문제가 다시 생김")
    elif s.node=="help":
        st.write("여기서 잠시 멈출게요. 같은 방법을 반복하거나 모르는 버튼을 누르지 않으셔도 괜찮아요.")
        st.write("가족이나 제조사·서비스의 공식 지원에 지금까지 확인한 내용을 전달해주세요.")
    elif s.confirm_done:
        st.header("이제 원하던 대로 잘 되나요?")
        if st.button("네, 해결됐어요"):move("done","직접 해결 확인")
        if st.button("아직 안 됐어요"):s.confirm_done=False;st.rerun()
    else:
        active_flow=device_flow(s.topic,s.device)
        action,hint,choices=active_flow[s.node]
        st.header(action)
        st.write(hint)
        if s.topic=="글씨를 크게 하고 싶어요" and s.node=="search":
            pass  # 기기별 안내 본문에 이미 표시
        for label,target in choices:
            if st.button(label,key=f"choice_{s.node}_{label}"):
                move(target,label)
        with st.expander("설명이 어렵거나 화면이 다른가요?"):
            if st.button("못 찾겠어요"):
                s.miss+=1
                move("alternatives","안내를 찾기 어려움")
                st.rerun()
            if s.miss:st.write("화면이 다르면 추가 점검 목록에서 해당하는 상황을 골라주세요.")
            if st.button("다른 화면이 나와요"):move("alternatives","다른 화면이 나옴")
        if st.button("이미 해결됐어요"):s.confirm_done=True;st.rerun()
with st.expander("내 문의·답변 확인"):
    st.write("접수 시 받은 32자리 접수번호로 확인해요. 이 번호는 비밀번호와 같으니 다른 사람에게 공유하지 마세요. 자동 알림은 없어요.")
    with st.form("lookup_reply"):
        receipt=st.text_input("접수번호",type="password",max_chars=32)
        lookup=st.form_submit_button("답변 확인")
    if lookup:
        now=time.time()
        if now-s.get("lookup_last",0)<5:
            st.write("잠시 뒤 다시 확인해주세요.")
        elif not re.fullmatch(r"[0-9a-f]{32}",receipt.strip()):
            st.write("접수번호 32자리를 확인해주세요.")
        elif not inbox_ready():st.write("메시지 저장소 연결이 필요해요.")
        else:
            s.lookup_last=now
            try:
                digest=hashlib.sha256(receipt.strip().encode()).hexdigest()
                result=db_request("GET",params={"lookup_hash":"eq."+digest,"select":"message,reply,replied_at","limit":"1"}).json()
                if not result:st.write("접수번호가 없거나 이전 버전 문의예요. 이전 문의는 답변 조회를 지원하지 않아요.")
                else:
                    st.write("보낸 내용")
                    st.text(result[0]["message"])
                    st.write("개발자 답변")
                    st.text(result[0].get("reply") or "아직 답변 전이에요. 나중에 다시 확인해주세요.")
            except Exception:st.write("답변을 확인하지 못했어요. 연결과 데이터베이스 업데이트를 확인해주세요.")
if not s.family:
    if st.button("개발자에게 도움 요청"):
        s.family=True;s.rev+=1;st.rerun()
st.caption("삭제·초기화·송금·보안 해제는 안내하지 않아요. 위험한 상황은 공식 지원이나 긴급 도움을 이용해주세요.")

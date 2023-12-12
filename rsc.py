import requests
import json
import urllib3
from collections import Counter
import sqlite3

# 텍스트 요약 함수
def summarize_text(text):
    """
    입력된 텍스트를 네이버 오픈 API를 사용하여 요약한 후, 각 문장을 리스트로 반환합니다.
    """
    client_id = "-"
    client_secret = "-"
    url = 'https://naveropenapi.apigw.ntruss.com/text-summary/v1/summarize'

    input_content = text

    headers = {
        'Accept': 'application/json;UTF-8',
        'Content-Type': 'application/json;UTF-8',
        'X-NCP-APIGW-API-KEY-ID': client_id,
        'X-NCP-APIGW-API-KEY': client_secret
    }

    data = {
        "document": {
            "content": input_content
        },
        "option": {
            "language": "ko",
            "model": "general",
            "tone": 0,
            "summaryCount": 3
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(data).encode('UTF-8'))
    rescode = response.status_code

    if rescode != 200:
        print("Error : " + response.text)

    json_data = json.loads(response.text)
    summary_text = json_data["summary"]
    text_list = summary_text.split('\n')
    return text_list

def find_all_nng_elements(json_data):
    """
    JSON 데이터에서 모든 NNG 형태소 요소를 추출하여 리스트로 반환합니다.
    """
    nng_elements = []

    for sentence in json_data['return_object']['sentence']:
        for morp_eval in sentence['morp_eval']:
            for element in morp_eval['result'].split('+'):
                if '/NNG' in element:
                    word, _ = element.split('/')
                    nng_elements.append(word)

    return nng_elements

def makeP(text):
    """
    주어진 텍스트를 요약하고, 주요 명사를 추출하여 공백 처리된 텍스트와 함께 SQLite 데이터베이스에 저장합니다.
    """
    text_list = summarize_text(text)

    openApiURL = "http://aiopen.etri.re.kr:8000/WiseNLU"
    accessKey = "-"

    requestJson = {
        "argument": {
            "text": text,
            "analysis_code": "morp"
        }
    }

    http = urllib3.PoolManager()
    response = http.request(
        "POST",
        openApiURL,
        headers={"Content-Type": "application/json; charset=UTF-8", "Authorization": accessKey},
        body=json.dumps(requestJson)
    )

    with open("response.json", "w", encoding="utf-8") as json_file:
        json.dump(json.loads(str(response.data, "utf-8")), json_file, ensure_ascii=False, indent=2)
    print("응답 데이터를 'response.json' 파일로 저장했습니다.")

    json_file_path = 'response.json'
    with open(json_file_path, 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    all_nng_elements = find_all_nng_elements(json_data)
    element_counts = Counter(all_nng_elements)

    origin = text_list

    common_nng = []

    d = 0
    for i in range(len(text_list)):
        while True:
            if element_counts.most_common(i + 1 + d)[i + d][0] in text_list[i]:
                common_nng.append(element_counts.most_common(i + 1 + d)[i + d][0])
                text_list[i] = text_list[i].replace(common_nng[i], '□')
                break
            else:
                d += 1

    blanked = text_list
    conn = sqlite3.connect("./Cheetah.db")
    cursor = conn.cursor()
    mydata = (origin[0], origin[1], origin[2], blanked[0], blanked[1], blanked[2], common_nng[0], common_nng[1], common_nng[2])
    cursor.execute(
        "INSERT INTO PROBLEM ( sumT1,sumT2,sumT3,blankT1,blankT2,blankT3, word1,word2,word3) VALUES (?,?,?,?,?,?,?,?,?)",
        mydata)
    conn.commit()
    conn.close()
    return text_list

def submit(text):
    """
    주어진 선택지와 정답을 비교하여 점수를 계산하고, SQLite 데이터베이스에 시도 기록을 저장한 후 결과를 반환합니다.
    """
    point = 0
    biglist = []

    string_list = text.split(',')
    string1 = string_list[0]
    string2 = string_list[1]
    string3 = string_list[2]

    conn = sqlite3.connect("Cheetah.db")
    cursor = conn.cursor()
    res = cursor.execute("select word1,word2,word3 from PROBLEM ORDER BY Pid DESC")
    result = res.fetchone()

    res = cursor.execute("select * from PROBLEM ORDER BY Pid DESC")
    result2 = res.fetchone()

    myA1 = result[0]
    myA2 = result[1]
    myA3 = result[2]
    
    if string1 == myA1:
        point += 1
    if string2 == myA2:
        point += 1
    if string3 == myA3:
        point += 1

    mydata = (string1, string2, string3, point)

    biglist = list(result2) + string_list
    biglist.append(point)

    cursor.execute("INSERT INTO TRIAL (try1,try2,try3,answer) VALUES (?,?,?,?)", mydata)
    conn.commit()
    conn.close()
    print(biglist)

    return biglist

def getList(idx):
    """
    특정 인덱스(idx)에 해당하는 PROBLEM 테이블의 데이터를 가져와서 리스트로 반환합니다.
    """
    conn = sqlite3.connect("Cheetah.db")
    cursor = conn.cursor()
    query = "SELECT * FROM PROBLEM WHERE Pid=?"
    res = cursor.execute(query, (idx,))
    result = list(res.fetchone())
    conn.close()
    return result

def getNumP():
    """
    PROBLEM 테이블의 전체 행 개수를 가져와서 반환합니다.
    """
    conn = sqlite3.connect("Cheetah.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM PROBLEM")
    num_of_p_tuple = cursor.fetchone()
    num_of_p = num_of_p_tuple[0]
    #conn.close()  
    return num_of_p

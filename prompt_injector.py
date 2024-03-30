from difflib import SequenceMatcher
from tqdm import tqdm
import re
import json
import csv
import time
import requests
import argparse

def similar(a, b):
    a = a or ""  # a가 None이면 빈 문자열로 처리
    b = b or ""  # b가 None이면 빈 문자열로 처리
    return SequenceMatcher(None, a, b).ratio()

def check_response(response_text, check_value, check_type, success_log, fail_log):
    sim_score = ""
    success_log = ""
    fail_log = ""
    response_json = json.loads(response_text)
    answer = response_json.get('answer', '')
    print("answer : ", answer)

    if not success_log :
        success_log = "prompt_success_log.txt"

    if not fail_log :
        fail_log = "prompt_fail_log.txt"

    if check_type == 'regex':
        if re.search(check_value, answer, re.IGNORECASE):
            print(f"\033[92m정규식 일치: '{check_value}'가 '{answer}'에 포함되어 있습니다.\033[0m")
        else:
            print("정규식 불일치.")
    elif check_type == 'similarity':
        similarity_score = similar(check_value, answer)
        if similarity_score >= 0.25:
            print(f"\033[92m유사도({similarity_score})\033[0m")
            # 파일에 유사도 검사 통과 내용 추가
            with open(success_log, "a") as fp:
                fp.write(response_text)
        else:
            print(f"유사도({similarity_score})")
            # 파일에 유사도 검사 실패 내용 추가
            with open(fail_log, "a") as fp:
                fp.write(response_text)

def post_data_and_check(url, defender_value, prompt_value, cookies, check_value, check_type, success_log, fail_log):
    files = {
        'defender': (None, defender_value),
        'prompt': (None, prompt_value),
    }
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36',
        'Origin': 'https://grt.lakera.ai',
        'Referer': 'https://grt.lakera.ai/mosscap',
    }
    response = requests.post(url, files=files, headers=headers, cookies=cookies)
    status_code = response.status_code
    response_text = response.text

    if status_code == 200:
        check_response(response_text, check_value, check_type, success_log, fail_log)
    else:
        print(f"데이터 전송 실패: 상태 코드 {status_code}, 응답: {response_text}")

def read_csv_to_memory(file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        data_list = [row for row in reader]
    return data_list

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send data to server and check response.")
    parser.add_argument("--url", help="Complete server URL including endpoint")
    parser.add_argument("--cookie", help="Session cookie value")
    parser.add_argument("--file_path", help="Path to the CSV file containing 'defender' and 'prompt' values")
    parser.add_argument("--check_value", help="Value to check in the response's answer")
    parser.add_argument("--success_log", help="file name of success log")
    parser.add_argument("--fail_log", help="file name of fail log")
    parser.add_argument("--check_type", choices=['regex', 'similarity'], default="similarity", help="Type of check to perform on the response 'answer'")
    parser.add_argument("--defender_value", help="Level")
    parser.add_argument("--start_index", type=int, default=0, help="Start index")
    parser.add_argument("--delay_time", type=float, default=5.0, help="delay seconds")

    args = parser.parse_args()

    cookies = {'session': args.cookie}
    data_list = read_csv_to_memory(args.file_path)

    for i in tqdm(range(int(args.start_index), len(data_list), 1)):
        prompt_value = data_list[i][0]
        print(f"Sending defender: '{args.defender_value}', prompt: '{prompt_value}'")
        post_data_and_check(args.url, args.defender_value, prompt_value, cookies, args.check_value, args.check_type, args.success_log, args.fail_log)
        time.sleep(args.delay_time)

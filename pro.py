from flask import Flask, request, render_template
from rsc import summarize_text, makeP, submit, getList, getNumP

app = Flask(__name__)

@app.route('/')
def index():
    """
    루트 URL에 접근하면 input.html 파일을 렌더링하며,
    getNumP 함수를 사용하여 문제의 개수를 가져와 템플릿에 전달합니다.
    """
    num_of_p = getNumP()
    return render_template('input.html', num=num_of_p)


@app.route('/summarize', methods=['POST'])
def summarize():
    """
    입력된 텍스트를 요약하거나 문제를 생성하기 위한 POST 요청을 처리합니다.
    
    'Summarize' 버튼이 클릭된 경우 입력 텍스트를 요약합니다.
    'Make a Problem' 버튼이 클릭된 경우 입력 텍스트를 기반으로 문제를 생성합니다.
    """
    text = request.form['text_to_summarize']
    idx = request.form['index_to_find']
    button = request.form['action']

    if button == 'Summarize':
        # 'Summarize' 버튼이 클릭된 경우
        summarized_text_list = summarize_text(text)
        return render_template('output_sum.html', summarized_text=summarized_text_list)
    elif button == 'make a problem':
        # 'Make a Problem' 버튼이 클릭된 경우
        problem_text = makeP(text)
        return render_template('output_pro.html', problem_text=problem_text)
    elif button == 'find problem':
        # 'Make a Problem' 버튼이 클릭된 경우
        problem_list = getList(idx)
        return render_template('problem_list.html', result=problem_list)

@app.route('/problem', methods=['POST'])
def problem():
    """
    입력된 텍스트를 처리하고 결과를 problem.html에 렌더링합니다.

    입력 텍스트를 추출하고 추가 처리를 위해 submit 함수를 호출합니다.
    """
    input_text = request.form['text_to_problem']
    summarized_text = submit(input_text)
    return render_template('problem.html', bigList=summarized_text)

if __name__ == '__main__':
    app.run(debug=True)

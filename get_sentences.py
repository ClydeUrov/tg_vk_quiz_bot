def get_quiz():
    questions = []
    with open('questions/1vs1200.txt', 'r', encoding='KOI8-R') as file:
        raw_text = file.read()
    quiz_text = raw_text.split('\n\n\n')
    for one_quiz in quiz_text:
        quiz = one_quiz.split('\n\n')
        for sentence in quiz:
            if 'Вопрос' in sentence:
                one_ask = sentence.split('\n')[1:]
                ask = ' '.join(one_ask)
                questions.append(ask)
            elif 'Ответ' in sentence:
                one_answer = sentence.split('\n')[1:]
                answer = ' '.join(one_answer)
                questions.append(answer)
    return questions
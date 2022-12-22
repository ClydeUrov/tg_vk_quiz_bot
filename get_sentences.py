def get_quiz(file_path):
    quiz = []
    with open(file_path, 'r', encoding='KOI8-R') as file:
        raw_text = file.read()
    quiz_text = raw_text.split('\n\n\n')
    for one_quiz in quiz_text:
        quizzes_part = one_quiz.split('\n\n')
        for sentence in quizzes_part:
            if 'Вопрос' in sentence: 
                questions = ' '.join(sentence.split('\n')[1:])
                quiz.append(questions)
            elif 'Ответ' in sentence:
                answer = ' '.join(sentence.split('\n')[1:])
                quiz.append(answer)
    return quiz
